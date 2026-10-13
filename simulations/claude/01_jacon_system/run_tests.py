"""
run_tests.py - run the JACON LTspice model test-by-test and plot everything.

    %USERPROFILE%\\radioconda\\python.exe run_tests.py            # all tests
    %USERPROFILE%\\radioconda\\python.exe run_tests.py 6 10       # just some
    %USERPROFILE%\\radioconda\\python.exe run_tests.py ac 2 --keep-raw

Each test = JACON_system.asc with ".param TEST=n" (exactly what you would do
by hand in LTspice) plus a ".save" of the nets it plots. PNGs go to ./plots,
numbers to ./plots/test_summary.json and ./plots/RESULTS.md.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.ndimage import maximum_filter1d  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE))
from ltspice_tools import find_ltspice, read_raw, spectrum_dbm, vpk_to_dbm  # noqa: E402
from build_jacon import TESTS  # noqa: E402

ASC = HERE / "JACON_system.asc"
PLOTS = HERE / "plots"
RESULTS = HERE / "results"
C0 = 299792458.0
SUMMARY: dict = {}
KEEP_RAW = False

# --------------------------------------------------------------------------- params
_SUF = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9, "t": 1e12}


def spice_num(s) -> float:
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().lower().strip("{}")
    m = re.match(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)(meg|[fpnumkgt])?", s)
    if not m:
        raise ValueError(s)
    return float(m.group(1)) * _SUF.get(m.group(2) or "", 1.0)


def asc_params() -> dict[str, str]:
    txt = ASC.read_text()
    return {m.group(1).upper(): m.group(2) for m in re.finditer(r"\.param\s+(\w+)=([^\s\\;]+)", txt)}


BASE = asc_params()


def P(name: str, ov: dict | None = None) -> float:
    ov = ov or {}
    return spice_num(ov.get(name, BASE[name]))


def tstop(test: int) -> float:
    return spice_num([t for t in TESTS if t[0] == test][0][2])


# --------------------------------------------------------------------------- run
def run_case(tag: str, test: int, overrides: dict | None = None, save=(), step: str | None = None):
    overrides = overrides or {}
    text = ASC.read_text()
    text, n = re.subn(r"(\.param TEST=)\d+", rf"\g<1>{test}", text, count=1)
    assert n == 1
    for k, v in overrides.items():
        text, n = re.subn(rf"(\.param {k}=)[^\s\\;]+", rf"\g<1>{v}", text)
        if n != 1:
            raise KeyError(f"param {k} found {n} times")
    dirs = [".options plotwinsize=0"]
    if save:
        dirs.append(".save " + " ".join(f"V({s})" for s in save))
    if step:
        dirs.append(step)
    text = text.rstrip("\n") + "\nTEXT 0 4800 Left 2 !" + "\\n".join(dirs) + "\n"

    work = Path(tempfile.gettempdir()) / "jacon_run" / tag
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    for f in HERE.glob("jacon_*.asy"):
        shutil.copy2(f, work)
    shutil.copy2(HERE / "jacon_blocks.inc", work)
    asc = work / f"{tag}.asc"
    asc.write_text(text)
    t0 = time.time()
    print(f"  [{tag}] LTspice TEST={test} {overrides or ''} {step or ''} ...", flush=True)
    subprocess.run([str(find_ltspice()), "-b", str(asc)], timeout=4 * 3600, check=False)
    log, raw = work / f"{tag}.log", work / f"{tag}.raw"
    RESULTS.mkdir(exist_ok=True)
    if log.exists():
        shutil.copy2(log, RESULTS / f"{tag}.log")
        lt = log.read_text(errors="ignore")
        for ln in lt.splitlines():
            if re.search(r"error|singular|failed|aborted", ln, re.I):
                print("    LOG:", ln)
    if not raw.exists():
        raise RuntimeError(f"no .raw for {tag}; see {RESULTS / (tag + '.log')}")
    if KEEP_RAW:
        shutil.copy2(raw, RESULTS / f"{tag}.raw")
    d = read_raw(raw)
    print(f"    done in {time.time() - t0:.1f}s, {d.data.shape[1]} points", flush=True)
    return d


# --------------------------------------------------------------------------- dsp
def dbm(v):
    return vpk_to_dbm(np.maximum(np.asarray(v), 1e-9))


def envelope(t, v, period, win_periods=1.5):
    dt = period / 20
    tu = np.arange(t[0], t[-1], dt)
    vu = np.interp(tu, t, v)
    return tu, maximum_filter1d(np.abs(vu), max(3, int(round(win_periods * 20))))


def crossings(t, v):
    s = np.signbit(v)
    i = np.where(s[:-1] & ~s[1:])[0]
    return t[i] - v[i] * (t[i + 1] - t[i]) / (v[i + 1] - v[i])


def freq_between(t, v, t0, t1):
    k = (t >= t0) & (t <= t1)
    tc = crossings(t[k], v[k])
    return (len(tc) - 1) / (tc[-1] - tc[0]) if len(tc) > 3 else float("nan")


def freq_track(t, v, win):
    tc = crossings(t, v)
    per = np.diff(tc)
    n = max(1, int(win / np.median(per)))
    ker = np.ones(n) / n
    ps = np.convolve(per, ker, mode="valid")
    tm = np.convolve((tc[1:] + tc[:-1]) / 2, ker, mode="valid")
    return tm, 1 / ps


def fit_cos(f, v, dt_min=0.05e-9, dt_max=3e-9, n=3000):
    """brute-force dt search for v = a*cos(2 pi f dt) + b (a signed = mixer polarity)."""
    def resid(dt):
        M = np.c_[np.cos(2 * np.pi * f * dt), np.ones_like(f)]
        c, *_ = np.linalg.lstsq(M, v, rcond=None)
        return float(np.sum((M @ c - v) ** 2)), c
    best = min(((resid(dt)[0], dt) for dt in np.linspace(dt_min, dt_max, n)))
    span = 2 * (dt_max - dt_min) / n
    best = min(((resid(dt)[0], dt) for dt in np.linspace(best[1] - span, best[1] + span, 801)))
    c = resid(best[1])[1]
    return float(best[1]), float(c[0]), float(c[1])


def tone_level(f, p, f0, bw=60e6):
    k = (f > f0 - bw) & (f < f0 + bw)
    return float(np.max(p[k])) if np.any(k) else float("nan")


def save(fig, name):
    PLOTS.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(PLOTS / name, dpi=130)
    plt.close(fig)
    print(f"    -> plots/{name}")


def shade(ax, t0, t1, color, label=None, scale=1.0):
    ax.axvspan(t0 * scale, t1 * scale, color=color, alpha=0.15, label=label)


# =========================================================================== tests
def test_ac():
    deck = HERE / "filters_ac.cir"
    work = Path(tempfile.gettempdir()) / "jacon_run" / "AC"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    shutil.copy2(deck, work)
    shutil.copy2(HERE / "jacon_blocks.inc", work)
    print("  [AC] filters_ac.cir ...")
    subprocess.run([str(find_ltspice()), "-b", str(work / deck.name)], check=False)
    d = read_raw(work / "filters_ac.raw")
    f = d.time()
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    items = [("V(irf_out)", "image-reject HPF (TX)", 0), ("V(mixif_out)", "RX mixer IF port LPF", 1),
             ("V(pdlpf_out)", "phase-detector LPF", 1), ("V(limlpf_out)", "limiter harmonic LPF", 1),
             ("V(ifamp_out)", "IF amplifier (small signal)", 1)]
    res = {}
    for name, lab, ax in items:
        h = 20 * np.log10(np.abs(d[name]) + 1e-15)
        axs[ax].semilogx(f / 1e9, h, label=lab)
        res[lab] = {f"{x:g} GHz": float(np.interp(x * 1e9, f, h)) for x in (0.1, 1.1, 2.2, 3.3, 7.2, 8.3, 9.4, 17.7)}
    axs[0].set_xlim(4, 20)
    axs[0].set_ylim(-80, 5)
    for x, lab in ((7.2, "image 7.2"), (8.3, "LO 8.3"), (9.4, "TX 9.4")):
        axs[0].axvline(x, ls="--", color="gray", lw=.8)
        axs[0].text(x, -75, lab, rotation=90, fontsize=8)
    axs[1].set_ylim(-60, 30)
    for x, lab in ((0.1, "PD LPF"), (1.1, "IF"), (2.2, "2f"), (3.3, "3f")):
        axs[1].axvline(x, ls="--", color="gray", lw=.8)
        axs[1].text(x, -55, lab, rotation=90, fontsize=8)
    for a in axs:
        a.grid(alpha=.3, which="both")
        a.legend(fontsize=8)
        a.set_xlabel("frequency (GHz)")
        a.set_ylabel("|H| (dB)")
    axs[0].set_title("TX image-reject filter")
    axs[1].set_title("IF / baseband filters and IF amp")
    save(fig, "AC_filter_responses.png")
    SUMMARY["AC"] = res


def test2():
    nets = ["lo_pll", "lo_buf", "lo_rx", "lo_tx"]
    d = run_case("T02_lo_chain", 2, save=nets)
    t = d.time()
    k = t > t[-1] - 2e-9
    lv = {n: float(dbm(np.max(np.abs(d[f"V({n})"][k])))) for n in nets}
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5))
    axs[0].bar(nets, [lv[n] for n in nets], color=["#888", "#1f5fbf", "#2a9d55", "#d9822b"])
    for i, n in enumerate(nets):
        axs[0].text(i, lv[n] + .3, f"{lv[n]:.1f} dBm", ha="center")
    axs[0].axhline(P("MIX_LO_NOM"), color="red", ls="--", label=f"ZX05-14LH-S+ needs +{P('MIX_LO_NOM'):.0f} dBm")
    axs[0].axhline(7, color="orange", ls=":", label="ZX05-14-S+ needs +7 dBm")
    axs[0].set_ylabel("LO amplitude (dBm)")
    axs[0].legend(fontsize=8)
    axs[0].set_title("LO drive at each point")
    kk = t > t[-1] - 0.4e-9
    for n in nets:
        axs[1].plot(t[kk] * 1e12, d[f"V({n})"][kk], label=n)
    axs[1].set_xlabel("time (ps)")
    axs[1].set_ylabel("V")
    axs[1].legend(fontsize=8)
    axs[1].set_title("8.3 GHz LO waveforms (buffer compression visible)")
    save(fig, "T02_lo_chain.png")
    SUMMARY["T2_lo_chain"] = {"levels_dBm": lv, "mixer_LO_required_dBm": P("MIX_LO_NOM"),
                              "LO_margin_at_rx_mixer_dB": lv["lo_rx"] - P("MIX_LO_NOM")}


def test1():
    nets = ["rf_ant", "rf_lim", "rf_lna"]
    d = run_case("T01_rx_front_end", 1, save=nets)
    t = d.time()
    fr = P("F_RADAR")
    ts, a_in = envelope(t, d["V(rf_ant)"], 1 / fr)
    _, a_lim = envelope(t, d["V(rf_lim)"], 1 / fr)
    _, a_lna = envelope(t, d["V(rf_lna)"], 1 / fr)
    pin = P("P1_START") + (P("P1_STOP") - P("P1_START")) * ts / tstop(1)
    k = ts > 0.3e-9
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    ax = axs[0]
    ax.plot(pin[k], dbm(a_lim[k]), label="after limiter (= LNA input)")
    ax.plot(pin[k], dbm(a_lna[k]), label="LNA output")
    ax.plot(pin[k], pin[k] + P("LNA_G") - P("LIM_IL") - P("ATT_RX"), ls=":", color="gray", label="ideal linear LNA out")
    ax.axhline(15, color="red", ls="--", lw=1, label="LNA max input +15 dBm")
    ax.axhline(P("LNA_P1DB"), color="orange", ls="--", lw=1, label=f"LNA P1dB +{P('LNA_P1DB'):.0f} dBm")
    ax.axvspan(-50, -10, color="green", alpha=.08, label="expected echo range")
    ax.set_xlabel("power at RX antenna port (dBm)")
    ax.set_ylabel("dBm")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    ax.set_title("Limiter + LNA transfer (9.4 GHz CW ramp)")
    for p0, c in ((-30, "#1f5fbf"), (15, "#d9822b")):
        tt = (p0 - P("P1_START")) / (P("P1_STOP") - P("P1_START")) * tstop(1)
        kk = (t > tt) & (t < tt + 0.4e-9)
        axs[1].plot((t[kk] - tt) * 1e12, d["V(rf_lna)"][kk], color=c, label=f"LNA out @ {p0} dBm in")
    axs[1].set_xlabel("time (ps)")
    axs[1].set_ylabel("V")
    axs[1].legend(fontsize=8)
    axs[1].grid(alpha=.3)
    axs[1].set_title("waveform: linear vs. compressed")
    save(fig, "T01_rx_front_end.png")
    max_lim = float(np.max(dbm(a_lim[k])))
    SUMMARY["T1_rx_front_end"] = {
        "max_power_into_LNA_dBm": max_lim,
        "extra_attenuation_needed_for_15dBm_dB": max(0.0, max_lim - 15),
        "LNA_out_at_-50dBm_in": float(np.interp(-50, pin[k], dbm(a_lna[k]))),
        "LNA_out_at_-10dBm_in": float(np.interp(-10, pin[k], dbm(a_lna[k]))),
    }


def test3():
    nets = ["rf_ant", "rf_lna", "lo_rx", "if_mix", "if_amp"]
    d = run_case("T03_rx_downconversion", 3, save=nets)
    t = d.time()
    fr, flo = P("F_RADAR"), P("F_LO")
    fif = abs(fr - flo)
    fig, axs = plt.subplots(2, 1, figsize=(13, 9))
    marks = {"IF": fif, "LO": flo, "RF": fr, "RF+LO": fr + flo, "2 IF": 2 * fif}
    levels = {}
    for n, c in (("rf_lna", "#888"), ("if_mix", "#d9822b"), ("if_amp", "#1f5fbf")):
        f, p = spectrum_dbm(t, d[f"V({n})"], 5e-9, 20e-9, fmax=22e9)
        axs[0].plot(f / 1e9, p, lw=.9, label=n, color=c)
        levels[n] = {m: tone_level(f, p, fm) for m, fm in marks.items()}
    for m, fm in marks.items():
        axs[0].axvline(fm / 1e9, color="k", ls=":", lw=.7)
        axs[0].text(fm / 1e9, 22, m, fontsize=8, rotation=90, va="top")
    axs[0].set_ylim(-100, 25)
    axs[0].set_xlabel("frequency (GHz)")
    axs[0].set_ylabel("dBm")
    axs[0].grid(alpha=.3)
    axs[0].legend(fontsize=8)
    axs[0].set_title(f"RX down-conversion, {P('P_RADAR'):.0f} dBm @ {fr/1e9:.2f} GHz: spectra")
    k = (t > 10e-9) & (t < 13e-9)
    axs[1].plot(t[k] * 1e9, d["V(if_mix)"][k], label="if_mix (mixer out)")
    axs[1].plot(t[k] * 1e9, d["V(if_amp)"][k], label="if_amp (after IF amp)")
    axs[1].set_xlabel("time (ns)")
    axs[1].set_ylabel("V")
    axs[1].legend(fontsize=8)
    axs[1].grid(alpha=.3)
    save(fig, "T03_rx_downconversion.png")
    SUMMARY["T3_rx_downconversion"] = {"tone_levels_dBm": levels,
                                       "mixer_conversion_gain_dB": levels["if_mix"]["IF"] - levels["rf_lna"]["RF"]}


def test4():
    nets = ["if_split_in", "env", "vth", "det_raw"]
    d = run_case("T04_pulse_detection", 4, save=nets)
    t = d.time()
    per, pw = P("T4_PER"), P("T4_PW")
    npulse = int((tstop(4) - 20e-9 - pw) // per) + 1
    fig, axs = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    axs[0].plot(t * 1e9, d["V(if_split_in)"] * 1e3, lw=.4)
    axs[0].set_ylabel("IF at splitter (mV)")
    axs[1].plot(t * 1e9, d["V(env)"] * 1e3, label="envelope detector out")
    axs[1].plot(t * 1e9, d["V(vth)"] * 1e3, "r--", label="DAC threshold")
    axs[1].set_ylabel("mV")
    axs[1].set_yscale("symlog", linthresh=1)
    axs[1].legend(fontsize=8)
    axs[2].plot(t * 1e9, d["V(det_raw)"], color="k")
    axs[2].set_ylabel("comparator (logic)")
    axs[2].set_xlabel("time (ns)")
    res = []
    for i in range(npulse):
        t0 = 20e-9 + i * per
        pp = P("P4_START") + i * P("P4_STEP")
        k = (t > t0) & (t < t0 + pw + 10e-9)
        hit = bool(np.max(d["V(det_raw)"][k]) > 0.5)
        lat = float((t[k][np.argmax(d["V(det_raw)"][k] > 0.5)] - t0) * 1e9) if hit else None
        res.append({"power_at_IF_splitter_dBm": pp, "power_at_env_det_dBm": pp - 6.02, "detected": hit, "latency_ns": lat})
        axs[0].text((t0 + pw / 2) * 1e9, axs[0].get_ylim()[1] * .8, f"{pp:.0f} dBm", ha="center", fontsize=8)
        axs[2].text((t0 + pw / 2) * 1e9, 0.5, "DETECT" if hit else "missed", ha="center", fontsize=9,
                    color="green" if hit else "red")
    for a in axs:
        a.grid(alpha=.3)
    axs[0].set_title("Pulse detection: ADL5511 envelope vs nanoDAC threshold -> ADCMP600")
    save(fig, "T04_pulse_detection.png")
    SUMMARY["T4_pulse_detection"] = {"threshold_V": P("VTH_DAC"), "pulses": res}


def test5():
    nets = ["lim_in", "lim_out"]
    d = run_case("T05_limiting_amp", 5, save=nets)
    t = d.time()
    fif = P("F_IF_TEST")
    ts, ai = envelope(t, d["V(lim_in)"], 1 / fif)
    _, ao = envelope(t, d["V(lim_out)"], 1 / fif)
    pin = P("P5_START") + (P("P5_STOP") - P("P5_START")) * ts / tstop(5)
    k = ts > 3e-9
    po = dbm(ao[k])
    pmax = float(np.max(po))
    within = pin[k][po > pmax - 1]
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    axs[0].plot(pin[k], po, label="limiter output")
    axs[0].plot(pin[k], pin[k] + 3 * P("LIMA_G"), ":", color="gray", label="linear gain (3 stages)")
    axs[0].axhline(pmax - 1, color="green", ls="--", lw=.8, label="within 1 dB of max")
    axs[0].axvspan(-37 - 6, 3 - 6, color="orange", alpha=.08, label="drawing IF range (-37..+3 dBm) after 6 dB split")
    axs[0].set_ylim(pmax - 40, pmax + 5)
    axs[0].set_xlabel("limiter input (dBm)")
    axs[0].set_ylabel("output (dBm)")
    axs[0].grid(alpha=.3)
    axs[0].legend(fontsize=8)
    axs[0].set_title("Limiting amp: output flat above the knee")
    for p0, c in ((-45, "#1f5fbf"), (-20, "#2a9d55"), (0, "#d9822b")):
        tt = (p0 - P("P5_START")) / (P("P5_STOP") - P("P5_START")) * tstop(5)
        kk = (t > tt) & (t < tt + 2e-9)
        axs[1].plot((t[kk] - tt) * 1e9, d["V(lim_out)"][kk], color=c, label=f"out @ {p0} dBm in")
    axs[1].set_xlabel("time (ns)")
    axs[1].set_ylabel("V")
    axs[1].grid(alpha=.3)
    axs[1].legend(fontsize=8)
    save(fig, "T05_limiting_amp.png")
    SUMMARY["T5_limiting_amp"] = {"max_output_dBm": pmax,
                                  "input_dBm_where_output_within_1dB": float(within.min()) if len(within) else None}


def test6(tag="T06_discriminator", overrides=None, plot=True):
    ov = overrides or {}
    nets = ["lim_out", "pd_rf", "pd_lo", "pd_out"]
    d = run_case(tag, 6, overrides=ov, save=nets)
    t = d.time()
    T = P("T6_STEP", ov)
    nstep = int(round(tstop(6) / T)) - 1      # staircase step 0 is repeated once so the chain can settle
    f = np.array([P("F6_START", ov) + i * P("F6_STEP", ov) for i in range(nstep)])
    v = np.array([np.mean(d["V(pd_out)"][(t > (i + 1.6) * T) & (t < (i + 2) * T)]) for i in range(nstep)])
    dt_nom = P("DL_IN", ov) * 0.0254 / (P("VF", ov) * C0)
    # a 200 MHz sweep cannot identify dt uniquely -> search within +/-50 % of the cable estimate
    dt_fit, a_fit, b_fit = fit_cos(f, v, 0.5 * dt_nom, 1.5 * dt_nom, 2000)
    amp = abs(a_fit)
    slope, icpt = np.polyfit(f, v, 1)
    fnom = P("F_IF_NOM", ov)
    pd_v0 = float(slope * fnom + icpt)
    kvco = (P("VCO_F2", ov) - P("VCO_F1", ov)) / (P("VCO_V2", ov) - P("VCO_V1", ov))
    gain = float(1 / (slope * kvco))
    ferr = (v - (slope * f + icpt)) / slope
    cal = {"DL_IN_in": P("DL_IN", ov), "VF": P("VF", ov), "delta_t_ps_nominal": dt_nom * 1e12,
           "delta_t_ps_fit": dt_fit * 1e12, "cos_amplitude_V": amp, "slope_V_per_GHz": float(slope * 1e9),
           "PD_V0": pd_v0, "OPA_GAIN": gain, "linear_map_max_freq_error_MHz": float(np.max(np.abs(ferr)) / 1e6),
           "pd_out_V": [float(x) for x in v], "freq_Hz": [float(x) for x in f]}
    if plot:
        fig, axs = plt.subplots(2, 2, figsize=(14, 9))
        axs[0, 0].plot(t * 1e9, d["V(pd_out)"], lw=.8)
        axs[0, 0].plot((np.arange(nstep) + 1.8) * T * 1e9, v, "o", ms=4, color="crimson", label="step average")
        axs[0, 0].set_xlabel("time (ns)")
        axs[0, 0].set_ylabel("pd_out (V)")
        axs[0, 0].set_title("phase detector output while IF steps 10 MHz every step")
        axs[0, 0].legend(fontsize=8)
        ff = np.linspace(f[0], f[-1], 300)
        axs[0, 1].plot(f / 1e9, v, "o", label="LTspice")
        axs[0, 1].plot(ff / 1e9, slope * ff + icpt, "--", label=f"linear fit ({slope*1e9:.3f} V/GHz)")
        axs[0, 1].plot(ff / 1e9, a_fit * np.cos(2 * np.pi * ff * dt_fit) + b_fit, "-", lw=.8,
                       label=f"a cos(2 pi f dt)+b fit: dt = {dt_fit*1e12:.1f} ps (nominal {dt_nom*1e12:.1f})")
        axs[0, 1].axvline(fnom / 1e9, color="gray", ls=":")
        axs[0, 1].set_xlabel("IF frequency (GHz)")
        axs[0, 1].set_ylabel("pd_out (V)")
        axs[0, 1].legend(fontsize=8)
        axs[0, 1].set_title(f'discriminator curve, DL_IN = {P("DL_IN", ov):.2f}" VF = {P("VF", ov)}')
        axs[1, 1].plot(f / 1e9, ferr / 1e6, "o-")
        axs[1, 1].set_xlabel("IF frequency (GHz)")
        axs[1, 1].set_ylabel("MHz")
        axs[1, 1].set_title("frequency error of a straight-line (analog) inverse")
        tz = 10.5 * T
        kk = (t > tz) & (t < tz + 2e-9)
        axs[1, 0].plot((t[kk] - tz) * 1e12, d["V(pd_rf)"][kk], label="pd_rf (reference arm)")
        axs[1, 0].plot((t[kk] - tz) * 1e12, d["V(pd_lo)"][kk], label="pd_lo (delayed arm)")
        axs[1, 0].plot((t[kk] - tz) * 1e12, d["V(lim_out)"][kk] / 2, ":", label="lim_out / 2")
        axs[1, 0].set_xlabel("time (ps)")
        axs[1, 0].set_ylabel("V")
        axs[1, 0].legend(fontsize=8)
        axs[1, 0].set_title("the two arms at the phase detector (1.1 GHz)")
        for a in axs.flat:
            a.grid(alpha=.3)
        fig.suptitle(f"Calibration -> PD_V0 = {pd_v0:.4f} V,  OPA_GAIN = {gain:.3f} V/V", fontsize=12)
        save(fig, f"{tag}.png")
    SUMMARY[tag] = cal
    CAL_DONE.add(tag)
    return cal


def test7():
    nets = ["sh_in", "det", "sh_ctrl", "sh_hold", "vtune_opa"]
    runs = {}
    for gbw in ("8e6", "100e6"):
        runs[gbw] = run_case(f"T07_sh_opamp_gbw{gbw}", 7, overrides={"OPA_GBW": gbw}, save=nets)
    kvco = (P("VCO_F2") - P("VCO_F1")) / (P("VCO_V2") - P("VCO_V1"))
    tol_v = 1e6 / kvco
    fig, axs = plt.subplots(4, 1, figsize=(13, 12), sharex=True)
    d = runs["8e6"]
    t = d.time()
    axs[0].plot(t * 1e6, d["V(sh_in)"], label="sh_in (phase detector)")
    axs[0].plot(t * 1e6, d["V(sh_hold)"], label="sh_hold (100 pF)")
    axs[0].set_ylabel("V")
    axs[0].legend(fontsize=8)
    axs[1].plot(t * 1e6, d["V(det)"], label="det (radar detected)")
    axs[1].plot(t * 1e6, d["V(sh_ctrl)"], label="sh_ctrl (sample window)")
    axs[1].legend(fontsize=8)
    res = {}
    for gbw, dd in runs.items():
        tt = dd.time()
        axs[2].plot(tt * 1e6, dd["V(vtune_opa)"], label=f"vtune_opa, GBW = {spice_num(gbw)/1e6:.0f} MHz")
        per = P("T7_PER")
        settle = []
        for i in range(1, int(tstop(7) / per)):
            tend = i * per + 100e-9 + P("SH_DLY") + P("SH_WIDTH")
            k = (tt > tend) & (tt < (i + 1) * per)
            y = dd["V(vtune_opa)"][k]
            final = y[-1]
            bad = np.where(np.abs(y - final) > tol_v)[0]
            settle.append(float((tt[k][bad[-1]] - tend) * 1e9) if len(bad) else 0.0)
        res[gbw] = {"settle_to_1MHz_ns": settle}
    axs[2].set_ylabel("VCO tune (V)")
    axs[2].legend(fontsize=8)
    per = P("T7_PER")
    t1 = per + 100e-9
    for gbw, dd in runs.items():
        tt = dd.time()
        k = (tt > t1 - 20e-9) & (tt < t1 + 1.2e-6)
        axs[3].plot((tt[k]) * 1e6, dd["V(vtune_opa)"][k], label=f"GBW {spice_num(gbw)/1e6:.0f} MHz (zoom)")
    axs[3].set_ylabel("V (zoom 2nd sample)")
    axs[3].set_xlabel("time (us)")
    axs[3].legend(fontsize=8)
    for a in axs:
        a.grid(alpha=.3)
    axs[0].set_title(f"S&H + op-amp: settling to 1 MHz (+/-{tol_v*1e3:.1f} mV): "
                     + ", ".join(f"GBW {spice_num(g)/1e6:.0f} MHz -> {max(r['settle_to_1MHz_ns']):.0f} ns" for g, r in res.items()))
    save(fig, "T07_sample_hold_opamp.png")
    SUMMARY["T7_sample_hold_opamp"] = res


def test8():
    nets = ["vtune", "vco_f_GHz", "if_vco"]
    d = run_case("T08_vco", 8, save=nets)
    t = d.time()
    tm, fm = freq_track(t, d["V(if_vco)"], 1e-9)
    vt = np.interp(tm, t, d["V(vtune)"])
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    axs[0].plot(t * 1e9, d["V(vtune)"], label="vtune")
    ax2 = axs[0].twinx()
    ax2.plot(tm * 1e9, fm / 1e9, color="crimson", label="measured f (zero crossings)")
    ax2.set_ylabel("GHz", color="crimson")
    axs[0].set_xlabel("time (ns)")
    axs[0].set_ylabel("V")
    axs[1].plot(vt, fm / 1e9, label="LTspice VCO (measured)")
    axs[1].plot([P("VCO_V1"), P("VCO_V2")], [P("VCO_F1") / 1e9, P("VCO_F2") / 1e9], "o", ms=9, label="drawing: 6 V -> 1.0 GHz, 9.5 V -> 1.2 GHz")
    axs[1].axhspan(1.0, 1.2, color="green", alpha=.08, label="needed IF band")
    axs[1].set_xlabel("tune voltage (V)")
    axs[1].set_ylabel("VCO frequency (GHz)")
    axs[1].legend(fontsize=8)
    for a in axs:
        a.grid(alpha=.3)
    axs[0].set_title("VCO tuning ramp")
    axs[1].set_title("CVCO55BE tuning curve (linear model - replace with datasheet table if needed)")
    save(fig, "T08_vco.png")
    SUMMARY["T8_vco"] = {"f_at_6V_GHz": float(np.interp(6, vt, fm) / 1e9), "f_at_9p5V_GHz": float(np.interp(9.5, vt, fm) / 1e9)}


def morse_windows(start, U):
    return {"dot1": (start, start + U), "gap1": (start + U, start + 2 * U),
            "dash": (start + 2 * U, start + 5 * U), "gap2": (start + 5 * U, start + 6 * U),
            "dot2": (start + 6 * U, start + 7 * U)}


def tx_spectrum_panel(ax, t, sigs, t0, t1, flo, fvco, title):
    marks = {"image f_LO-f_IF": flo - fvco, "LO leak": flo, "wanted f_LO+f_IF": flo + fvco}
    table = {}
    for name, y, c in sigs:
        f, p = spectrum_dbm(t, y, t0, t1, fmax=14e9, oversample=8)
        k = f > 4e9
        ax.plot(f[k] / 1e9, p[k], lw=.9, label=name, color=c)
        table[name] = {m: tone_level(f, p, fm, 40e6) for m, fm in marks.items()}
    for m, fm in marks.items():
        ax.axvline(fm / 1e9, color="k", ls=":", lw=.7)
        ax.text(fm / 1e9, 38, m, rotation=90, fontsize=8, va="top")
    ax.set_ylim(-80, 40)
    ax.set_xlabel("frequency (GHz)")
    ax.set_ylabel("dBm")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    ax.set_title(title)
    return table


def test9():
    nets = ["key", "if_vco", "if_keyed", "tx_mix", "tx_filt", "tx_out"]
    d = run_case("T09_tx_chain", 9, save=nets)
    t = d.time()
    U, flo = P("MORSE_UNIT"), P("F_LO")
    start = 20e-9
    w = morse_windows(start, U)
    fvco = freq_between(t, d["V(if_vco)"], *w["dash"])
    fig = plt.figure(figsize=(14, 11))
    gs = fig.add_gridspec(3, 2)
    ax = fig.add_subplot(gs[0, :])
    ts, a = envelope(t, d["V(tx_out)"], 1 / (flo + fvco), win_periods=6)
    ax.plot(ts * 1e9, dbm(a), label="tx_out envelope (dBm)")
    ax.set_ylabel("dBm")
    ax2 = ax.twinx()
    ax2.plot(t * 1e9, d["V(key)"], "k", lw=.8, label="key (FPGA)")
    ax2.set_ylabel("key")
    for nm, (a0, a1) in w.items():
        if nm.startswith(("dot", "dash")):
            shade(ax, a0, a1, "green", scale=1e9)
    ax.set_xlabel("time (ns)")
    ax.set_title("TX Morse '. - .'  (dot/dash shaded)")
    ax.grid(alpha=.3)
    ax.legend(loc="lower left", fontsize=8)
    tab_on = tx_spectrum_panel(fig.add_subplot(gs[1, :]), t,
                               [("tx_mix (mixer out)", d["V(tx_mix)"], "#d9822b"),
                                ("tx_filt (after image-reject HPF)", d["V(tx_filt)"], "#2a9d55"),
                                ("tx_out (after PA)", d["V(tx_out)"], "#1f5fbf")],
                               w["dash"][0] + 10e-9, w["dash"][1] - 10e-9, flo, fvco, "TX spectrum during the dash")
    tab_off = tx_spectrum_panel(fig.add_subplot(gs[2, 0]), t, [("tx_out key OFF (gap)", d["V(tx_out)"], "#8e44ad")],
                                w["gap1"][0] + 10e-9, w["gap1"][1] - 5e-9, flo, fvco, "tx_out during the gap (key off)")
    ax = fig.add_subplot(gs[2, 1])
    k = (t > w["dash"][0] + 30e-9) & (t < w["dash"][0] + 31e-9)
    ax.plot(t[k] * 1e9, d["V(tx_out)"][k], label="tx_out")
    ax.plot(t[k] * 1e9, d["V(tx_mix)"][k] * 10, alpha=.6, label="tx_mix x10")
    ax.set_xlabel("time (ns)")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    ax.set_title("RF waveform during dash")
    save(fig, "T09_tx_chain.png")
    on = tab_on["tx_out (after PA)"]
    SUMMARY["T9_tx_chain"] = {
        "vco_freq_GHz": fvco / 1e9,
        "levels_dash_dBm": tab_on, "levels_gap_dBm": tab_off,
        "image_rejection_dBc_at_tx_out": on["image f_LO-f_IF"] - on["wanted f_LO+f_IF"],
        "LO_leak_dBc_at_tx_out": on["LO leak"] - on["wanted f_LO+f_IF"],
        "on_off_ratio_dB": on["wanted f_LO+f_IF"] - tab_off["tx_out key OFF (gap)"]["wanted f_LO+f_IF"],
    }


CAL_DONE: set[str] = set()


def load_cal(tag, ov):
    """calibration from a TEST 6 run made in THIS session (never a stale json entry)."""
    if tag not in CAL_DONE:
        test6(tag, ov, plot=True)
    return SUMMARY[tag]


def test10():
    flist = [9.30e9, 9.35e9, 9.40e9, 9.45e9, 9.50e9]
    nets = ["if_vco", "vco_f_GHz", "pd_out", "sh_hold", "vtune", "det"]
    dl90 = 0.25 / 1.1e9 * P("VF") * C0 / 0.0254
    dl270 = 0.75 / 1.1e9 * P("VF") * C0 / 0.0254
    configs = [("as drawn", {}, "T06_discriminator"),
               (f'{dl270:.2f}" (270 deg @1.1 GHz)', {"DL_IN": f"{dl270:.3f}"}, "T06_discriminator_dl270"),
               (f'{dl90:.2f}" (90 deg @1.1 GHz)', {"DL_IN": f"{dl90:.3f}"}, "T06_discriminator_dl90")]
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    out = {}
    for label, ov, caltag in configs:
        cal = load_cal(caltag, ov)
        ov2 = dict(ov, OPA_GBW="1e9", PD_V0=f"{cal['PD_V0']:.5f}", OPA_GAIN=f"{cal['OPA_GAIN']:.4f}")
        tag = "T10_freq_transfer_" + (caltag.split("_")[-1] if ov else "asdrawn")
        d = run_case(tag, 10, overrides=ov2, save=nets,
                     step=".step param F_RADAR list " + " ".join(f"{x:g}" for x in flist))
        tx = []
        for i, fr in enumerate(flist):
            t = d.time(i)
            fv = freq_between(t, d.get("V(if_vco)", i), tstop(10) - 80e-9, tstop(10))
            tx.append(P("F_LO") + fv)
        tx = np.array(tx)
        err = (tx - np.array(flist)) / 1e6
        L = f'DL_IN = {P("DL_IN", ov):.2f}"  {label}'
        axs[0].plot(np.array(flist) / 1e9, tx / 1e9, "o-", label=L)
        axs[1].plot(np.array(flist) / 1e9, err, "o-", label=L)
        out[label] = {"radar_GHz": [f / 1e9 for f in flist], "tx_GHz": list(map(float, tx / 1e9)),
                      "error_MHz": list(map(float, err)), "PD_V0": cal["PD_V0"], "OPA_GAIN": cal["OPA_GAIN"]}
    axs[0].plot([9.3, 9.5], [9.3, 9.5], "k:", label="ideal")
    axs[0].set_xlabel("radar frequency (GHz)")
    axs[0].set_ylabel("racon TX frequency (GHz)")
    axs[1].axhline(0, color="k", lw=.6)
    axs[1].set_xlabel("radar frequency (GHz)")
    axs[1].set_ylabel("TX - radar (MHz)")
    axs[1].set_title("frequency error after one pulse (analog linear S&H -> VCO path)")
    for a in axs:
        a.grid(alpha=.3)
        a.legend(fontsize=8)
    save(fig, "T10_rx_to_tx_frequency_transfer.png")
    SUMMARY["T10_frequency_transfer"] = out


def test0():
    nets = ["rf_ant", "env", "vth", "det", "lim_out", "pd_out", "sh_ctrl", "sh_hold", "vtune", "vco_f_GHz",
            "key", "if_vco", "tx_out"]
    d = run_case("T00_full_system", 0, save=nets)
    t = d.time()
    fr, flo, U, HO = P("F_RADAR"), P("F_LO"), P("MORSE_UNIT"), P("MORSE_HOLDOFF")
    det = d["V(det)"]
    tdet = float(t[np.argmax(det > 0.5)]) if det.max() > 0.5 else float("nan")
    res = {"radar_GHz": fr / 1e9, "P_radar_dBm": P("P_RADAR"), "detect_time_ns": tdet * 1e9}
    tsh = (tdet + P("SH_DLY"), tdet + P("SH_DLY") + P("SH_WIDTH"))
    if np.isfinite(tdet):
        start = tdet + HO
        w = morse_windows(start, U)
        fv = freq_between(t, d["V(if_vco)"], start, start + 7 * U)
        k = (t > w["dash"][0] + 10e-9) & (t < w["dash"][1] - 10e-9)
        f, p = spectrum_dbm(t, d["V(tx_out)"], w["dash"][0] + 10e-9, w["dash"][1] - 10e-9, fmax=12e9, oversample=16)
        kk = (f > 9e9) & (f < 10e9)
        ftx_fft = float(f[kk][np.argmax(p[kk])])
        res.update({"sampled_pd_V": float(np.interp(tsh[1] + 1e-9, t, d["V(sh_hold)"])),
                    "vtune_at_morse_V": float(np.interp(start, t, d["V(vtune)"])),
                    "vco_GHz": fv / 1e9, "tx_GHz": (flo + fv) / 1e9, "tx_GHz_fft_peak": ftx_fft / 1e9,
                    "tx_error_MHz": (flo + fv - fr) / 1e6,
                    "tx_power_dBm": float(dbm(np.max(np.abs(d["V(tx_out)"][k]))))})
    SUMMARY["T0_full_system"] = res

    def panels(ax, t0, t1, scale, unit):
        k = (t >= t0) & (t <= t1)
        ts, a = envelope(t[k], d["V(rf_ant)"][k], 1 / fr, 3)
        ax[0].plot(ts * scale, dbm(a))
        ax[0].set_ylabel("RX ant (dBm)")
        ax[1].plot(t[k] * scale, d["V(env)"][k] * 1e3, label="env")
        ax[1].plot(t[k] * scale, d["V(vth)"][k] * 1e3, "r--", label="threshold")
        axb = ax[1].twinx()
        axb.plot(t[k] * scale, det[k], "k", lw=.8)
        axb.set_ylabel("det")
        ax[1].set_ylabel("mV")
        ax[1].legend(fontsize=7, loc="upper right")
        ts, a = envelope(t[k], d["V(lim_out)"][k], 1 / 1.1e9, 3)
        ax[2].plot(ts * scale, a)
        ax[2].set_ylabel("limiter out (Vpk)")
        ax[3].plot(t[k] * scale, d["V(pd_out)"][k], label="pd_out")
        ax[3].plot(t[k] * scale, d["V(sh_hold)"][k], label="sh_hold")
        ax[3].set_ylabel("V")
        ax[3].legend(fontsize=7)
        ax[4].plot(t[k] * scale, d["V(vtune)"][k])
        ax[4].set_ylabel("VCO tune (V)")
        ax[5].plot(t[k] * scale, d["V(vco_f_GHz)"][k])
        ax[5].axhline(abs(fr - flo) / 1e9, color="green", ls=":", label="needed IF")
        ax[5].set_ylabel("VCO (GHz)")
        ax[5].legend(fontsize=7)
        ax[6].plot(t[k] * scale, d["V(key)"][k], "k")
        ax[6].set_ylabel("Morse key")
        ts, a = envelope(t[k], d["V(tx_out)"][k], 1 / fr, 6)
        ax[7].plot(ts * scale, dbm(a))
        ax[7].set_ylim(-40, 35)
        ax[7].set_ylabel("TX out (dBm)")
        ax[7].set_xlabel(f"time ({unit})")
        for a_ in ax:
            a_.grid(alpha=.3)
            if np.isfinite(tdet):
                shade(a_, *tsh, "orange", scale=scale)

    fig, ax = plt.subplots(8, 1, figsize=(13, 17), sharex=True)
    panels(ax, 0, t[-1], 1e6, "us")
    ax[0].set_title("JACON full system: radar pulse -> detect -> sample frequency (orange) -> hold -> VCO -> Morse TX\n"
                    + (f"TX {res.get('tx_GHz', float('nan')):.4f} GHz for radar {fr/1e9:.4f} GHz "
                       f"(error {res.get('tx_error_MHz', float('nan')):+.1f} MHz), TX {res.get('tx_power_dBm', float('nan')):.1f} dBm"))
    save(fig, "T00_full_system_timeline.png")
    fig, ax = plt.subplots(8, 1, figsize=(13, 17), sharex=True)
    panels(ax, 0, 300e-9, 1e9, "ns")
    ax[0].set_title("JACON full system - zoom on the radar pulse (receive side)")
    save(fig, "T00_full_system_rx_zoom.png")
    if np.isfinite(tdet):
        fig, axs = plt.subplots(2, 1, figsize=(13, 9))
        tab = tx_spectrum_panel(axs[0], t, [("tx_out", d["V(tx_out)"], "#1f5fbf")], w["dash"][0] + 10e-9,
                                w["dash"][1] - 10e-9, flo, fv, "TX spectrum during the dash")
        axs[0].axvline(fr / 1e9, color="red", lw=1.5, alpha=.5, label="radar frequency")
        axs[0].legend(fontsize=8)
        k = (t > w["dot1"][0] - 20e-9) & (t < w["dot2"][1] + 20e-9)
        ts, a = envelope(t[k], d["V(tx_out)"][k], 1 / fr, 6)
        axs[1].plot(ts * 1e6, dbm(a))
        axs[1].set_xlabel("time (us)")
        axs[1].set_ylabel("TX out (dBm)")
        axs[1].grid(alpha=.3)
        axs[1].set_title("Morse '. - .' at the TX antenna")
        save(fig, "T00_full_system_tx.png")
        res["tx_spectrum_dash_dBm"] = tab


# =========================================================================== report
def write_report():
    PLOTS.mkdir(exist_ok=True)
    (PLOTS / "test_summary.json").write_text(json.dumps(SUMMARY, indent=2, default=float))
    md = ["# JACON LTspice results (auto-generated by run_tests.py)", ""]
    for png in sorted(PLOTS.glob("*.png")):
        md += [f"## {png.stem}", f"![{png.stem}]({png.name})", ""]
    md += ["## Numbers", "```json", json.dumps(SUMMARY, indent=2, default=float), "```"]
    (PLOTS / "RESULTS.md").write_text("\n".join(md))


ORDER = ["ac", "2", "1", "3", "4", "5", "6", "7", "8", "9", "10", "0"]
FUNCS = {"ac": test_ac, "0": test0, "1": test1, "2": test2, "3": test3, "4": test4, "5": test5,
         "6": test6, "7": test7, "8": test8, "9": test9, "10": test10}


def main():
    global KEEP_RAW
    ap = argparse.ArgumentParser()
    ap.add_argument("tests", nargs="*", default=["all"])
    ap.add_argument("--keep-raw", action="store_true", help="copy .raw files to ./results")
    a = ap.parse_args()
    KEEP_RAW = a.keep_raw
    sel = ORDER if "all" in a.tests else [x for x in ORDER if x in a.tests]
    old = PLOTS / "test_summary.json"
    if old.exists():
        SUMMARY.update(json.loads(old.read_text()))
    for s in sel:
        print(f"=== TEST {s} ===", flush=True)
        FUNCS[s]()
        write_report()
    print("summary ->", PLOTS / "test_summary.json")


if __name__ == "__main__":
    main()
