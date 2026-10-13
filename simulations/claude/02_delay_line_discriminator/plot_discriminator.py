"""
Delay-line frequency discriminator (1.0-1.2 GHz): run LTspice + make all plots.

    %USERPROFILE%\\radioconda\\python.exe plot_discriminator.py

Runs delay_line_discriminator.cir in several variants (your 4.5" design,
ideal multiplier vs. real double-balanced mixer, and the lengths that WOULD
centre quadrature on 1.1 GHz), then writes PNGs to ./plots and a summary to
./plots/results_summary.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from ltspice_tools import (read_raw, run_ltspice, parse_meas,  # noqa: E402
                           parse_step_params, spectrum_dbm)

BASE = HERE / "delay_line_discriminator.cir"
RUNS = HERE / "runs"
PLOTS = HERE / "plots"
C0 = 299792458.0
F_CENTER = 1.1e9


# ---------------------------------------------------------------- helpers
def get_param(text: str, name: str) -> float:
    m = re.search(rf"^\.param\s+{name}=([^\s;]+)", text, re.M | re.I)
    if not m:
        raise KeyError(name)
    return float(m.group(1))


def set_params(text: str, **kw) -> str:
    for k, v in kw.items():
        text, n = re.subn(rf"^(\.param\s+{k}=)[^\s;]+", rf"\g<1>{v}", text, flags=re.M | re.I)
        if n == 0:
            raise KeyError(k)
    return text


def fourier_c1(x: float) -> float:
    """1st Fourier coefficient of tanh(x cos th): 4/pi for a hard switch."""
    th = np.linspace(0, 2 * np.pi, 20001)[:-1]
    return 2 * np.mean(np.tanh(x * np.cos(th)) * np.cos(th))


def delta_t(dl_in, vf):
    return dl_in * 0.0254 / (vf * C0)


def theory(f, p):
    apk = np.sqrt(0.1 * 10 ** (p["P_DBM"] / 10))
    a = apk / 2                                    # each arm after the 6 dB resistive split
    dt = delta_t(p["DL_IN"], p["VF"])
    if int(p["MIXMODE"]) == 0:
        k = a * a / 2
    else:
        k = 10 ** (-p["CL_DB"] / 20) * np.pi / 2 * a * fourier_c1(a / p["VSW"]) / 2
    return k * np.cos(2 * np.pi * f * dt), k


def run_variant(tag: str, keep_raw=False, **params):
    RUNS.mkdir(exist_ok=True)
    txt = set_params(BASE.read_text(), **params)
    deck = RUNS / f"dld_{tag}.cir"
    deck.write_text(txt)
    raw, log = run_ltspice(deck)
    steps = parse_step_params(log)
    meas = parse_meas(log)
    freqs = np.array([s["freq"] for s in steps])
    vout = np.array(meas["vout"])
    p = {k: get_param(txt, k) for k in ("P_DBM", "VF", "DL_IN", "MIXMODE", "CL_DB", "VSW")}
    data = read_raw(raw) if keep_raw else None
    if not keep_raw:
        raw.unlink(missing_ok=True)
    return dict(tag=tag, f=freqs, v=vout, p=p, raw=data)


# ---------------------------------------------------------------- main
def main():
    PLOTS.mkdir(exist_ok=True)
    base_txt = BASE.read_text()
    vf = get_param(base_txt, "VF")
    dl_user = get_param(base_txt, "DL_IN")

    # lengths that put 90 / 270 degrees (cos = 0, max slope) exactly at 1.1 GHz
    dl_90 = 0.25 / F_CENTER * vf * C0 / 0.0254
    dl_270 = 0.75 / F_CENTER * vf * C0 / 0.0254

    print("running LTspice variants ...")
    runs = [
        run_variant("user_ideal", keep_raw=True, MIXMODE=0),
        run_variant("user_dbm", MIXMODE=1),
        run_variant("q90_ideal", MIXMODE=0, DL_IN=f"{dl_90:.4f}"),
        run_variant("q270_ideal", MIXMODE=0, DL_IN=f"{dl_270:.4f}"),
    ]
    labels = {
        "user_ideal": f'{dl_user:.2f}" extra (your design), ideal multiplier',
        "user_dbm": f'{dl_user:.2f}" extra, double-balanced mixer model',
        "q90_ideal": f'{dl_90:.2f}" extra -> 90 deg at 1.1 GHz',
        "q270_ideal": f'{dl_270:.2f}" extra -> 270 deg at 1.1 GHz',
    }
    colors = {"user_ideal": "#1f5fbf", "user_dbm": "#d9822b",
              "q90_ideal": "#2a9d55", "q270_ideal": "#8e44ad"}

    ff = np.linspace(1.0e9, 1.2e9, 401)
    summary = {"velocity_factor": vf, "user_extra_length_in": dl_user,
               "length_for_90deg_at_1p1GHz_in": dl_90,
               "length_for_270deg_at_1p1GHz_in": dl_270, "variants": {}}

    # ---------- Fig 1: sweep, sim vs theory
    fig, axs = plt.subplots(2, 1, figsize=(10, 9), sharex=True)
    for r in runs:
        th, k = theory(ff, r["p"])
        th_pts, _ = theory(r["f"], r["p"])
        err = np.max(np.abs(r["v"] - th_pts))
        dt = delta_t(r["p"]["DL_IN"], r["p"]["VF"])
        summary["variants"][r["tag"]] = {
            "extra_length_in": r["p"]["DL_IN"], "delta_t_ps": dt * 1e12,
            "phase_at_1p0GHz_deg": 360 * 1.0e9 * dt, "phase_at_1p1GHz_deg": 360 * 1.1e9 * dt,
            "phase_at_1p2GHz_deg": 360 * 1.2e9 * dt, "K_volts": k,
            "max_abs_sim_minus_theory_V": float(err),
            "vout_sim_V": dict(zip([f"{x/1e9:.3f}GHz" for x in r["f"]], map(float, r["v"]))),
        }
        c = colors[r["tag"]]
        if r["tag"].startswith("user"):
            axs[0].plot(ff / 1e9, th * 1e3, color=c, lw=1, alpha=.6)
            axs[0].plot(r["f"] / 1e9, r["v"] * 1e3, "o", color=c, ms=5, label=labels[r["tag"]] + " (LTspice o, theory -)")
        axs[1].plot(ff / 1e9, th / k, color=c, lw=1, alpha=.6)
        axs[1].plot(r["f"] / 1e9, r["v"] / k, "o", color=c, ms=4, label=labels[r["tag"]])
    axs[0].set_ylabel("Vout (mV)  @ 0 dBm tone")
    axs[0].set_title("Delay-line discriminator: DC out = K cos(2 pi f dt)   (LTspice points vs theory lines)")
    axs[0].legend(fontsize=8)
    axs[0].grid(alpha=.3)
    axs[1].axhline(0, color="k", lw=.6)
    axs[1].axvline(1.1, color="gray", ls="--", lw=.8)
    axs[1].set_ylabel("Vout / K   (normalised)")
    axs[1].set_xlabel("tone frequency (GHz)")
    axs[1].set_ylim(-1.1, 1.1)
    axs[1].legend(fontsize=8, loc="lower left")
    axs[1].grid(alpha=.3)
    axs[1].set_title(f"Normalised: only the curves crossing 0 at 1.1 GHz are centred (VF={vf})")
    fig.tight_layout()
    fig.savefig(PLOTS / "01_sweep_sim_vs_theory.png", dpi=140)
    plt.close(fig)

    # ---------- Fig 2: time domain at 1.1 GHz (user design, ideal)
    r0 = runs[0]
    d = r0["raw"]
    istep = int(np.argmin(np.abs(r0["f"] - 1.1e9)))
    t = d.time(istep)
    fig, axs = plt.subplots(4, 2, figsize=(13, 10), gridspec_kw=dict(width_ratios=[2, 1]))
    traces = [("V(split_in)", "splitter input (after feed cable)"),
              ("V(arm_a)", "arm A (reference) at mixer"),
              ("V(arm_b)", f'arm B (+{dl_user}" delay) at mixer'),
              ("V(mix_raw)", "raw product A*B: DC + 2f"),
              ]
    for i, (name, lab) in enumerate(traces):
        y = d.get(name, istep)
        axs[i, 0].plot(t * 1e9, y * 1e3, lw=.7)
        axs[i, 0].set_ylabel("mV")
        axs[i, 0].set_title(lab, fontsize=9, loc="left")
        k = (t > 30e-9) & (t < 32e-9)
        axs[i, 1].plot(t[k] * 1e9, y[k] * 1e3, lw=1)
        axs[i, 1].set_title("zoom 30-32 ns", fontsize=9)
    axs[3, 0].plot(t * 1e9, d.get("V(vout)", istep) * 1e3, color="crimson", lw=1.5, label="Vout after LPF")
    axs[3, 0].legend(fontsize=8)
    axs[1, 1].plot(t[k] * 1e9, d.get("V(arm_b)", istep)[k] * 1e3, lw=1, ls="--", label="arm B")
    axs[1, 1].legend(fontsize=7)
    axs[3, 0].set_xlabel("time (ns)")
    axs[3, 1].set_xlabel("time (ns)")
    fig.suptitle(f"Time domain at {r0['f'][istep]/1e9:.3f} GHz - arm B lags arm A by "
                 f"{360*r0['f'][istep]*delta_t(dl_user, vf):.0f} deg", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOTS / "02_time_domain_1p1GHz.png", dpi=140)
    plt.close(fig)

    # ---------- Fig 3: spectrum raw product vs filtered output
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, lab, c in [("V(mix_raw)", "raw mixer product", "#d9822b"),
                         ("V(vout)", "after 50 MHz low-pass (Vout)", "#1f5fbf"),
                         ("V(arm_a)", "arm A input tone", "#999999")]:
        f, pdb = spectrum_dbm(t, d.get(name, istep), 20e-9, 40e-9, fmax=5e9)
        ax.plot(f / 1e9, pdb, lw=1, label=lab, color=c)
    ax.axvline(2.2, color="k", ls=":", lw=.8)
    ax.text(2.22, -20, "f0+f1 = 2f = 2.2 GHz", fontsize=8)
    ax.text(0.05, -20, "f0-f1 = 0 (DC)\n= K cos(2 pi f dt)", fontsize=8)
    ax.set_xlabel("frequency (GHz)")
    ax.set_ylabel("dBm (50 ohm)")
    ax.set_ylim(-110, 10)
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    ax.set_title("Mixer output spectrum: sum term removed by the low-pass, difference term is DC")
    fig.tight_layout()
    fig.savefig(PLOTS / "03_spectrum_mixer_product.png", dpi=140)
    plt.close(fig)

    # ---------- Fig 4: design map
    dls = np.linspace(0, 8, 801)
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.5))
    for vfx in (0.66, 0.70, 0.76, 0.84, 1.0):
        ph = (360 * F_CENTER * delta_t(dls, vfx)) % 360
        axs[0].plot(dls, ph, lw=1.2, label=f"VF={vfx}")
    for q in (90, 270):
        axs[0].axhline(q, color="green", ls="--", lw=.8)
    axs[0].axhline(180, color="red", ls=":", lw=.8)
    axs[0].axvline(dl_user, color="k", lw=1)
    axs[0].text(dl_user + .05, 20, f'{dl_user}"', fontsize=9)
    axs[0].set_xlabel("extra cable length (inches)")
    axs[0].set_ylabel("phase shift at 1.1 GHz (deg, mod 360)")
    axs[0].set_title("Green = quadrature (max slope, centred)   red = null slope")
    axs[0].legend(fontsize=8)
    axs[0].grid(alpha=.3)
    # sensitivity & usable span across 1.0-1.2 GHz
    for vfx in (0.66, 0.70, 0.84):
        sens = []
        mono = []
        for dl in dls:
            dt = delta_t(dl, vfx)
            fgrid = np.linspace(1.0e9, 1.2e9, 41)
            v = np.cos(2 * np.pi * fgrid * dt)
            dv = np.diff(v)
            mono.append(np.all(dv > 0) or np.all(dv < 0))
            sens.append(np.min(np.abs(2 * np.pi * dt * np.sin(2 * np.pi * fgrid * dt))) * 1e9)
        sens = np.array(sens)
        mono = np.array(mono)
        axs[1].plot(dls, np.where(mono, sens, np.nan), lw=1.4, label=f"VF={vfx} (monotonic over band)")
        axs[1].plot(dls, np.where(~mono, sens, np.nan), lw=.6, color="gray")
    axs[1].axvline(dl_user, color="k", lw=1)
    axs[1].set_xlabel("extra cable length (inches)")
    axs[1].set_ylabel("worst-case slope |d(Vout/K)/df| over 1.0-1.2 GHz  (1/GHz)")
    axs[1].set_title("Frequency resolution: higher = better; gray = ambiguous (non-monotonic)")
    axs[1].legend(fontsize=8)
    axs[1].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(PLOTS / "04_design_map_cable_length.png", dpi=140)
    plt.close(fig)

    # ---------- Fig 5: frequency recovery from Vout
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    for r in runs:
        if r["tag"] == "user_dbm":
            continue
        _, k = theory(r["f"], r["p"])
        dt = delta_t(r["p"]["DL_IN"], r["p"]["VF"])
        x = np.clip(r["v"] / k, -1, 1)
        # choose the arccos branch that contains the band centre
        n_half = np.floor(2 * F_CENTER * dt)          # number of half-cycles
        base = np.arccos(x)
        phi = np.where(n_half % 2 == 0, base, 2 * np.pi - base) + 2 * np.pi * np.floor(F_CENTER * dt)
        f_exact = phi / (2 * np.pi * dt)
        coef = np.polyfit(r["v"], r["f"], 1)            # what a linear analog (S&H + op-amp) path does
        f_lin = np.polyval(coef, r["v"])
        c = colors[r["tag"]]
        axs[0].plot(r["f"] / 1e9, (f_exact - r["f"]) / 1e6, "o-", color=c, ms=3, label=labels[r["tag"]])
        axs[1].plot(r["f"] / 1e9, (f_lin - r["f"]) / 1e6, "o-", color=c, ms=3, label=labels[r["tag"]])
        summary["variants"][r["tag"]]["linear_map_max_error_MHz"] = float(np.max(np.abs(f_lin - r["f"])) / 1e6)
    axs[0].set_title("Recovered f using exact arccos inverse (digital / FPGA)")
    axs[1].set_title("Recovered f using best straight-line map (analog S&H -> op-amp -> VCO)")
    for a in axs:
        a.set_xlabel("true frequency (GHz)")
        a.set_ylabel("recovered - true (MHz)")
        a.grid(alpha=.3)
        a.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "05_frequency_recovery_error.png", dpi=140)
    plt.close(fig)

    (PLOTS / "results_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "variants"}, indent=2))
    for tag, v in summary["variants"].items():
        print(tag, {k: (round(x, 4) if isinstance(x, float) else x)
                    for k, x in v.items() if k != "vout_sim_V"})


if __name__ == "__main__":
    main()
