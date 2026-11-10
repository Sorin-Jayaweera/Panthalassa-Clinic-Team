"""Take apart every radar pulse and racon reply in a recording and draw it.

    python racon_analyze.py data/<file>.npz            # a recording from racon_capture.py (segmented or stream)
    python racon_analyze.py ../raw_20261025_130811.npz # any continuous I/Q npz (iq, fs, center) also works

What it finds, per snippet (one trigger, radar pulse plus whatever follows it):
  elements = runs above the noise (10 dB), edges at half power, split where the level or frequency steps.
  each element: start, duration, rise/fall, power at the SM200B, frequency (phase slope), frequency wobble and chirp inside it.
  radar pulse = the element whose duration is near the Furuno pulse (0.66 us); every other element is the racon.
  reply: delay after the radar pulse, Morse code (dots/dashes split by 2-means on duration), gaps, total length,
         racon frequency minus radar frequency, whether the racon keeps phase from one element to the next.
Across the recording: PRI, rotation, reply rate, power at our antenna for each source, EIRP, and the antenna gain this implies.

Writes plots/<tag>_*.png (every one with the wiring strip), data/<tag>_elements.csv, data/<tag>_summary.json.
"""
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "phase_detector_calibration"))
import racon_setup as S  # noqa: E402
import wiring  # noqa: E402

PLOTS, DATA = HERE / "plots", HERE / "data"
PLOTS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
RADAR_US = (0.45, 0.90)        # Furuno pulse measured 0.66 us; anything in this window, first in the snippet, is called the radar
THR_DB = 10.0                  # element = smoothed power this far above the mean noise
MORSE = {".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
         "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
         "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y", "--..": "Z"}
C_RADAR, C_RACON, C_DOT, C_DASH = "#1f4e9c", "#c06000", "#2a9d8f", "#8b3a9c"


# ----------------------------------------------------------------------------------------------------------------------- loading
def find_starts(p, thr, hold):
    """Indices where p first goes above thr, at least `hold` samples after the previous start."""
    hot = np.flatnonzero(p > thr)
    if not len(hot):
        return []
    out, last = [], -10 ** 18
    for k in hot[np.r_[True, np.diff(hot) > 1]]:
        if k - last >= hold:
            out.append(int(k))
            last = k
    return out


def from_continuous(iq, fs, pre_s=3e-6, win_s=60e-6, trig_db=15.0):
    p = iq.real ** 2 + iq.imag ** 2
    noise = np.median(p) / math.log(2)
    pre, L = int(pre_s * fs), int(win_s * fs)
    starts = [s for s in find_starts(p, noise * 10 ** (trig_db / 10), L) if s - pre >= 0 and s - pre + L <= len(iq)]
    return np.array([iq[s - pre:s - pre + L] for s in starts]), np.array(starts) / fs, pre


def load_sigmf(path):
    """A Spike zero-span I/Q recording (SigMF: .sigmf-meta JSON next to .sigmf-data raw samples)."""
    meta_p, data_p = path.with_suffix(".sigmf-meta"), path.with_suffix(".sigmf-data")
    m = json.loads(meta_p.read_text())
    g = m["global"]
    fs = float(g["core:sample_rate"])
    fc = float(m.get("captures", [{}])[0].get("core:frequency", g.get("core:frequency", S.CENTER_HZ)))
    dt_ = g["core:datatype"]
    raw = np.fromfile(data_p, dtype={"cf32_le": "<f4", "ci16_le": "<i2", "ci32_le": "<i4"}[dt_])
    iq = (raw[0::2] + 1j * raw[1::2]).astype(np.complex64)
    note = "" if dt_ == "cf32_le" else f" ({dt_}: integer samples, levels NOT in dBm until scaled)"
    snips, t, pre = from_continuous(iq, fs)
    return dict(snips=snips, t=t, pre=pre, fs=fs, fc=fc, extra={}, dur=len(iq) / fs,
                meta=dict(kind=f"Spike zero-span recording, SigMF {dt_}{note}", chain_gain_db=None))


def load(path):
    path = Path(path)
    if path.suffix in (".sigmf-meta", ".sigmf-data"):
        return load_sigmf(path)
    if path.is_dir():
        if (path / "stream.npz").exists():
            return load(path / "stream.npz")
        parts = [load(f) for f in sorted(path.glob("c*.npz"))]
        parts = [q for q in parts if len(q["snips"])]
        if not parts:
            raise SystemExit(f"no snippets in {path}")
        R = parts[0]
        R["snips"] = np.concatenate([q["snips"] for q in parts])
        R["t"] = np.concatenate([q["t"] for q in parts])
        R["meta"]["kind"] = R["meta"].get("kind", "") + f", {len(parts)} captures"
        return R
    d = np.load(path, allow_pickle=False)
    meta = json.loads(str(d["meta"])) if "meta" in d.files else {}
    fs, fc = float(d["fs"]), float(d["center"])
    if "snippets" in d.files:
        snips, t_abs, pre = d["snippets"], d["t_abs_s"], int(d["pre"])
        extra = {k: d[k] for k in ("all_t_s", "all_peak_dbm") if k in d.files}
        dur = float(d["duration_s"]) if "duration_s" in d.files else None
    else:
        snips, t_abs, pre = from_continuous(d["iq"].astype(np.complex64), fs)
        extra, dur = {}, len(d["iq"]) / fs
        meta.setdefault("kind", "continuous file, events found offline")
    if "chain_gain_db" not in meta:
        meta["chain_gain_db"] = None
    return dict(snips=snips.astype(np.complex64), t=np.asarray(t_abs, float), pre=pre, fs=fs, fc=fc, meta=meta, extra=extra, dur=dur)


# -------------------------------------------------------------------------------------------------------------------- elements
def smooth(x, n):
    return x if n <= 1 else np.convolve(x, np.ones(n) / n, "same")


def runs(mask):
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def inst_freq(x, fs, n):
    return smooth(np.diff(np.unwrap(np.angle(x))) * fs / (2 * np.pi), n)


def split(x, ps, s, e, fs):
    """Split a run where the level (4 dB) or frequency (3 MHz) steps: catches a racon reply that starts before the radar pulse ends."""
    w = max(3, int(0.2e-6 * fs))
    if e - s < max(int(1.0e-6 * fs), 3 * w):
        return [(s, e)]
    db = 10 * np.log10(ps[s:e] + 1e-30)
    f = np.r_[inst_freq(x[s:e], fs, max(1, w // 2)), 0.0]
    c_db, c_f = np.r_[0, np.cumsum(db)], np.r_[0, np.cumsum(f)]
    ks = np.arange(w + w // 2, e - s - w - w // 2)      # windows stay half a window clear of the edges, where noise sets the phase
    if not len(ks):
        return [(s, e)]
    mb = lambda c, a, b: (c[b] - c[a]) / (b - a)
    score = np.maximum(np.abs(mb(c_db, ks - w, ks) - mb(c_db, ks, ks + w)) / 4.0, np.abs(mb(c_f, ks - w, ks) - mb(c_f, ks, ks + w)) / 3e6)
    j = int(np.argmax(score))
    if score[j] < 1.0:
        return [(s, e)]
    k = s + int(ks[j])
    return split(x, ps, s, k, fs) + split(x, ps, k, e, fs)


def elements(x, fs, noise):
    p = x.real ** 2 + x.imag ** 2
    sw = max(1, int(round(0.03e-6 * fs)))
    ps = smooth(p, sw)
    rr = runs(ps > noise * 10 ** (THR_DB / 10))
    merged = []
    for s, e in rr:
        if merged and s - merged[-1][1] < int(0.15e-6 * fs):
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    out = []
    for s0, e0 in merged:
        if (e0 - s0) / fs < 0.08e-6:
            continue
        for s, e in split(x, ps, s0, e0, fs):
            lvl = float(np.median(ps[s:e]))
            m = 2 * sw
            a, b = max(0, s - m), min(len(ps), e + m)
            hi = np.flatnonzero(ps[a:b] >= lvl / 2) + a
            hi = hi[(hi >= max(0, s - m)) & (hi < min(len(ps), e + m))]
            st, en = (int(hi[0]), int(hi[-1])) if len(hi) else (s, e - 1)
            st, en = max(st, s - m), min(en, e - 1 + m)
            n = en - st + 1
            if n < 3:
                continue
            lead = ps[max(0, st - m):st + n // 2]
            r10, r90 = np.argmax(lead >= 0.1 * lvl), np.argmax(lead >= 0.9 * lvl)
            trail = ps[st + n // 2:min(len(ps), en + m + 1)][::-1]
            f10, f90 = np.argmax(trail >= 0.1 * lvl), np.argmax(trail >= 0.9 * lvl)
            core = x[st + int(0.15 * n):en + 1 - int(0.15 * n)] if n >= 12 else x[st:en + 1]
            ph = np.unwrap(np.angle(core))
            tt = np.arange(len(ph)) / fs
            slope, ph0 = np.polyfit(tt, ph, 1) if len(ph) >= 3 else (0.0, ph[0])
            fi = inst_freq(core, fs, max(1, int(0.05e-6 * fs)))
            fi = fi[len(fi) // 10: len(fi) - len(fi) // 10] if len(fi) > 20 else fi
            chirp = np.polyfit(np.arange(len(fi)) / fs * 1e6, fi / 1e6, 1)[0] if len(fi) >= 4 else np.nan
            out.append(dict(i0=st, i1=en, dur_us=n / fs * 1e6, rise_ns=(r90 - r10) / fs * 1e9, fall_ns=(f90 - f10) / fs * 1e9,
                            p_mw=lvl, p_dbm=10 * math.log10(lvl), peak_dbm=10 * math.log10(float(ps[st:en + 1].max())),
                            f_off_hz=slope / (2 * np.pi), f_std_khz=float(np.std(fi)) / 1e3 if len(fi) > 2 else np.nan,
                            f_p2p_mhz=float(np.ptp(fi)) / 1e6 if len(fi) > 2 else np.nan, chirp_mhz_per_us=chirp,
                            phase_mid=float(ph0 + slope * tt[len(tt) // 2]) if len(ph) else 0.0, t_mid_core=(st + int(0.15 * n) + len(ph) // 2) / fs))
    return out


def clean(els, radar, fs):
    """9 Nov racon data: drop the step on the radar pulse's falling edge and anything shorter than 0.5 us
    (racon elements are microseconds long), and join pieces of one racon element split by a fade shorter than 2 us."""
    end = radar["i1"] if radar else (els[0]["i1"] if els else 0)
    out = [radar] if radar else []
    for e in els:
        if e is radar or e["dur_us"] < 0.5 or (e["i0"] - end) / fs < 0.5e-6:
            continue
        prev = out[-1] if out and out[-1] is not radar else None
        if prev is not None and (e["i0"] - prev["i1"]) / fs < 2e-6:
            w0, w1 = prev["dur_us"], e["dur_us"]
            prev["p_mw"] = (prev["p_mw"] * w0 + e["p_mw"] * w1) / (w0 + w1)
            prev["p_dbm"] = 10 * math.log10(prev["p_mw"])
            prev["peak_dbm"] = max(prev["peak_dbm"], e["peak_dbm"])
            prev["f_off_hz"] = (prev["f_off_hz"] * w0 + e["f_off_hz"] * w1) / (w0 + w1)
            prev["i1"] = e["i1"]
            prev["dur_us"] = (prev["i1"] - prev["i0"] + 1) / fs * 1e6
            prev["fall_ns"] = e["fall_ns"]
            continue
        out.append(e)
    return out


def two_means(d):
    """Split durations into dots and dashes on a log scale. Returns the split value, or None if they are all one kind."""
    d = np.sort(np.asarray(d, float))
    if len(d) < 4:
        return None
    ld = np.log(d)
    best, cut = np.inf, None
    for k in range(1, len(d)):
        v = ld[:k].var() * k + ld[k:].var() * (len(d) - k)
        if v < best:
            best, cut = v, k
    lo, hi = np.median(d[:cut]), np.median(d[cut:])
    return math.sqrt(lo * hi) if hi / lo > 1.8 else None


# ------------------------------------------------------------------------------------------------------------------------ analysis
def analyze(path, show=True):
    path = Path(path)
    R = load(path)
    import setups_9nov
    raw = R["meta"].get("raw") or (path.stem[4:] if path.stem.startswith("raw_") else None)
    entry = setups_9nov.apply(S, raw) if raw else None
    if entry:
        R["meta"]["chain_gain_db"] = S.chain_gain_db()
    snips, fs, fc, pre = R["snips"], R["fs"], R["fc"], R["pre"]
    tag = path.stem if path.suffix else path.name
    if not len(snips):
        print("no events above the trigger in", path.name)
        return None
    pre_region = snips[:, :max(8, pre - int(0.5e-6 * fs))]
    noise = float(np.median(pre_region.real ** 2 + pre_region.imag ** 2)) / math.log(2)
    rows, replies = [], []
    for k, x in enumerate(snips):
        els = elements(x, fs, noise)
        radar = None
        if els and RADAR_US[0] <= els[0]["dur_us"] <= RADAR_US[1]:
            radar = els[0]
        els = clean(els, radar, fs)
        for j, e in enumerate(els):
            e.update(snip=k, idx=j, t_rel_us=(e["i0"] - pre) / fs * 1e6, t_abs_s=R["t"][k] + (e["i0"] - pre) / fs,
                     f_abs_mhz=(fc + e["f_off_hz"]) / 1e6, src="radar" if e is radar else "racon")
            rows.append(e)
        rac = [e for e in els if e is not radar]
        if rac:
            replies.append(dict(snip=k, radar=radar, els=rac))
    if entry and not entry["RACON_ON"]:            # racon switched off: anything after the pulse is not the racon
        rows = [e for e in rows if e["src"] == "radar"]
        replies = []
    rac_d = [e["dur_us"] for r in replies for e in r["els"]]
    cut = two_means(rac_d)
    for r in replies:
        r["code"] = "".join(("-" if e["dur_us"] > cut else ".") if cut else "." for e in r["els"])
        for e in r["els"]:
            e["kind"] = ("dash" if e["dur_us"] > cut else "dot") if cut else "element"
    for e in rows:
        e.setdefault("kind", "radar pulse" if e["src"] == "radar" else "element")
    gain = R["meta"].get("chain_gain_db")
    gain = S.chain_gain_db() if gain is None else gain
    summ = summarize(R, rows, replies, cut, noise, gain)
    summ["file"] = path.name
    write_tables(tag, rows, summ)
    title = f"{path.name}: {R['meta'].get('kind', '')}, {fs/1e6:.0f} MS/s, centre {fc/1e6:.1f} MHz"
    figs = [plot_chain(tag, R, rows, replies, title), plot_parts(tag, R, replies, title), plot_replies(tag, R, rows, replies, title),
            plot_stats(tag, R, rows, replies, summ, title), plot_loudness(tag, summ, title)]
    if "all_t_s" in R["extra"] and len(R["extra"]["all_t_s"]):
        figs.append(plot_timeline(tag, R, rows, gain, title))
    print_summary(summ)
    return [f for f in figs if f]


def summarize(R, rows, replies, cut, noise, gain):
    radar = [e for e in rows if e["src"] == "radar"]
    racon = [e for r in replies for e in r["els"]]
    s = dict(n_snippets=len(R["snips"]), n_radar_pulses=len(radar), n_replies=len(replies), noise_dbm_per_sample=10 * math.log10(noise),
             fs=R["fs"], center_mhz=R["fc"] / 1e6, chain_gain_db=gain, meta=R["meta"])
    med = lambda a: float(np.median(a)) if len(a) else None
    pct = lambda a, q: float(np.percentile(a, q)) if len(a) else None
    if radar:
        p = np.array([e["p_dbm"] for e in radar])
        s["radar"] = dict(dur_us=med([e["dur_us"] for e in radar]), rise_ns=med([e["rise_ns"] for e in radar]), fall_ns=med([e["fall_ns"] for e in radar]),
                          f_mhz=med([e["f_abs_mhz"] for e in radar]), f_sd_khz=float(np.std([e["f_abs_mhz"] for e in radar]) * 1e3),
                          f_in_pulse_sd_khz=med([e["f_std_khz"] for e in radar]),
                          p_sm_max_dbm=float(p.max()), p_sm_p90_dbm=pct(p, 90), p_sm_median_dbm=float(np.median(p)))
        t = np.sort([e["t_abs_s"] for e in radar])
        dt_ = np.diff(t)
        pri = dt_[(dt_ > 0.5e-3) & (dt_ < 3e-3)]
        s["radar"]["pri_us_values"] = sorted({round(v * 1e6, 1) for v in pri})[:40]
        s["radar"]["pri_us_median"] = med(pri * 1e6)
        passes = np.split(t, np.flatnonzero(dt_ > 0.3) + 1)
        if len(passes) >= 2:
            centers = [pa[np.argmax([0])] if len(pa) == 1 else pa.mean() for pa in passes if len(pa) >= 3]
            if len(centers) >= 2:
                s["radar"]["rotation_s_median"] = float(np.median(np.diff(centers)))
        s["radar"]["p_ant_max_dbm"] = s["radar"]["p_sm_max_dbm"] - gain
        s["radar"]["eirp_dbm"] = s["radar"]["p_ant_max_dbm"] + S.fspl_db(S.D_RADAR_M) - S.G_RX_DBI
        s["radar"]["g_inferred_dbi"] = s["radar"]["eirp_dbm"] - S.RADAR_TX_DBM
        s["radar"]["at_racon_dbm"] = s["radar"]["eirp_dbm"] - S.fspl_db(S.D_RADAR_RACON_M) + S.RACON_G_SPEC_DBI
        s["radar"]["trigger_range_m"] = 10 ** ((s["radar"]["eirp_dbm"] + S.RACON_G_SPEC_DBI - S.RACON_SENS_DBM - S.fspl_db(1.0)) / 20)
    if racon:
        p = np.array([e["p_dbm"] for e in racon])
        f = np.array([e["f_abs_mhz"] for e in racon])
        s["racon"] = dict(dot_dash_split_us=cut, p_sm_median_dbm=float(np.median(p)), p_sm_max_dbm=float(p.max()), p_sm_sd_db=float(np.std(p)),
                          f_mhz=float(np.median(f)), f_sd_khz=float(np.std(f) * 1e3), f_in_element_sd_khz=med([e["f_std_khz"] for e in racon]),
                          chirp_mhz_per_us=med([e["chirp_mhz_per_us"] for e in racon]), rise_ns=med([e["rise_ns"] for e in racon]),
                          fall_ns=med([e["fall_ns"] for e in racon]))
        for kind in ("dot", "dash", "element"):
            d = [e["dur_us"] for e in racon if e["kind"] == kind]
            if d:
                s["racon"][f"{kind}_us"] = dict(median=med(d), sd=float(np.std(d)), n=len(d))
        codes = Counter(r["code"] for r in replies)
        s["racon"]["codes"] = dict(codes.most_common(6))
        top = codes.most_common(1)[0][0]
        s["racon"]["letter"] = MORSE.get(top, "?")
        full = [r for r in replies if r["code"] == top]
        gaps = [b["i0"] - a["i1"] for r in full for a, b in zip(r["els"], r["els"][1:])]
        s["racon"]["gap_us"] = dict(median=med(np.array(gaps) / R["fs"] * 1e6), sd=float(np.std(np.array(gaps) / R["fs"] * 1e6)) if gaps else None)
        s["racon"]["reply_len_us"] = med([(r["els"][-1]["i1"] - r["els"][0]["i0"]) / R["fs"] * 1e6 for r in full])
        dl = [(r["els"][0]["i0"] - r["radar"]["i0"]) / R["fs"] * 1e6 for r in replies if r["radar"]]
        s["racon"]["delay_from_radar_start_us"] = dict(median=med(dl), sd=float(np.std(dl)) if dl else None, n=len(dl))
        df = [np.mean([e["f_abs_mhz"] for e in r["els"]]) - r["radar"]["f_abs_mhz"] for r in replies if r["radar"]]
        s["racon"]["f_minus_radar_khz"] = dict(median=med(np.array(df) * 1e3), sd=float(np.std(df) * 1e3) if df else None)
        coh = []
        for r in full:
            for a, b in zip(r["els"], r["els"][1:]):
                fm = (a["f_off_hz"] + b["f_off_hz"]) / 2
                pred = a["phase_mid"] + 2 * np.pi * fm * (b["t_mid_core"] - a["t_mid_core"])
                coh.append(np.angle(np.exp(1j * (b["phase_mid"] - pred))))
        if coh:
            s["racon"]["phase_carry_R"] = float(abs(np.mean(np.exp(1j * np.array(coh)))))
        s["racon"]["reply_rate"] = len([r for r in replies if r["radar"]]) / max(1, len(radar))
        s["racon"]["p_ant_dbm"] = s["racon"]["p_sm_median_dbm"] - gain
        s["racon"]["eirp_dbm"] = s["racon"]["p_ant_dbm"] + S.fspl_db(S.D_RACON_M) - S.G_RX_DBI
        s["racon"]["g_inferred_dbi"] = s["racon"]["eirp_dbm"] - S.RACON_TX_DBM
        t = np.sort([r["els"][0]["t_abs_s"] for r in replies])
        if len(t) > 2:
            gaps_s = np.diff(t)
            s["racon"]["longest_silence_s"] = float(gaps_s.max())
    return s


def write_tables(tag, rows, summ):
    keys = ["snip", "idx", "src", "kind", "t_abs_s", "t_rel_us", "dur_us", "rise_ns", "fall_ns", "p_dbm", "peak_dbm", "f_abs_mhz",
            "f_std_khz", "f_p2p_mhz", "chirp_mhz_per_us"]
    with open(DATA / f"{tag}_elements.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(keys)
        for e in rows:
            w.writerow([e[k] if isinstance(e[k], (str, int)) else f"{e[k]:.6g}" for k in keys])
    with open(DATA / f"{tag}_summary.json", "w") as fh:
        json.dump(summ, fh, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


# --------------------------------------------------------------------------------------------------------------------------- plots
def fig_with_strip(rows_ratio, size, left=0.07):
    fig = plt.figure(figsize=size)
    gs = fig.add_gridspec(len(rows_ratio) + 1, 1, height_ratios=list(rows_ratio) + [sum(rows_ratio) * 0.16], hspace=0.45,
                          left=left, right=0.98, top=0.93, bottom=0.02)
    wiring.draw(fig.add_subplot(gs[-1]), S.stages(), S.strip_title())
    return fig, gs


def stft_db(x, fs, n=None):
    n = n or (16 if fs < 100e6 else 64)
    f, t, Z = signal.stft(x, fs=fs, window="hann", nperseg=n, noverlap=n - max(1, n // 8), return_onesided=False, boundary=None, padded=False)
    P = np.abs(np.fft.fftshift(Z, axes=0)) ** 2
    P *= 1.0 / (np.sum(signal.get_window("hann", n) ** 2) / n) / n     # scale so a tone reads about its power in dBm
    return np.fft.fftshift(f), t, 10 * np.log10(P + 1e-30)


def best_reply(replies, rows):
    """The strongest reply that has a radar pulse and the most common code."""
    if not replies:
        return None
    codes = Counter(r["code"] for r in replies).most_common(1)[0][0]
    cand = [r for r in replies if r["code"] == codes and r["radar"]] or [r for r in replies if r["code"] == codes] or replies
    return max(cand, key=lambda r: min(e["p_dbm"] for e in r["els"]) + (r["radar"]["p_dbm"] if r["radar"] else -100) * 0.01)


def label(e):
    return "radar pulse" if e["src"] == "radar" else e["kind"]


def plot_chain(tag, R, rows, replies, title):
    r = best_reply(replies, rows)
    if r is None:
        k = int(np.argmax([np.abs(x).max() for x in R["snips"]]))
        els = [e for e in rows if e["snip"] == k]
    else:
        k = r["snip"]
        els = ([r["radar"]] if r["radar"] else []) + r["els"]
    x, fs, fc, pre = R["snips"][k], R["fs"], R["fc"], R["pre"]
    t = (np.arange(len(x)) - pre) / fs * 1e6
    last = max([e["i1"] for e in els], default=len(x) - 1)
    hi = min(len(x), last + int(4e-6 * fs))
    lo = max(0, (els[0]["i0"] if els else pre) - int(2e-6 * fs))
    xs, ts = x[lo:hi], t[lo:hi]
    fig, gs = fig_with_strip([1.2, 1.6, 1.0, 1.2], (14, 15))
    a, b, c, d = (fig.add_subplot(gs[i]) for i in range(4))
    p = 10 * np.log10(smooth(np.abs(xs) ** 2, max(1, int(0.02e-6 * fs))) + 1e-30)
    a.plot(ts, p, color="0.25", lw=0.8)
    ymax = p.max() + 6
    for e in els:
        col = C_RADAR if e["src"] == "radar" else (C_DASH if e["kind"] == "dash" else C_DOT)
        t0, t1 = (e["i0"] - pre) / fs * 1e6, (e["i1"] - pre) / fs * 1e6
        a.axvspan(t0, t1, color=col, alpha=0.18)
        a.text((t0 + t1) / 2, ymax - 1, f"{label(e)}\n{e['dur_us']:.2f} us\n{e['p_dbm']:.1f} dBm", ha="center", va="top", fontsize=7.5)
    ymid = (np.median(p) + min(e['p_dbm'] for e in els)) / 2 if els else ymax - 14
    if r and r["radar"]:
        d0 = (r["els"][0]["i0"] - r["radar"]["i0"]) / fs * 1e6
        a.annotate("", xy=((r["els"][0]["i0"] - pre) / fs * 1e6, ymid), xytext=((r["radar"]["i0"] - pre) / fs * 1e6, ymid),
                   arrowprops=dict(arrowstyle="<->", lw=0.8))
        a.text((r["radar"]["i0"] - pre) / fs * 1e6, ymid + 1, f"  racon starts {d0:.2f} us after the radar pulse starts", fontsize=7.5, va="bottom")
    a.set_ylim(max(p.min(), np.percentile(p, 2) - 8) - 2, ymax + 2)
    a.set_ylabel("Power at SM200B (dBm)")
    a.set_title("Envelope, one interaction: the Furuno pulse and the racon's reply" + (f" ({r['code']})" if r else ""))
    f, tt, P = stft_db(xs, fs)
    span = 20e6 if fs < 100e6 else 40e6
    m = np.abs(f) <= span
    im = b.pcolormesh(ts[0] + tt * 1e6, (fc + f[m]) / 1e6, P[m], shading="auto", cmap="magma", vmin=P.max() - 50, vmax=P.max())
    fig.colorbar(im, ax=b, pad=0.01, label="dBm per bin")
    b.set_ylabel("Frequency (MHz)")
    b.set_title(f"STFT of the whole interaction ({16 if fs < 100e6 else 64}-point Hann, {(16 if fs < 100e6 else 64)/fs*1e9:.0f} ns window)")
    ref = (r["radar"]["f_abs_mhz"] if r and r["radar"] else fc / 1e6)
    for e in els:
        seg = x[e["i0"]:e["i1"] + 1]
        fi = inst_freq(seg, fs, max(1, int(0.05e-6 * fs)))
        te = (np.arange(len(fi)) + e["i0"] - pre) / fs * 1e6
        c.plot(te, (fc + fi) / 1e6 * 1e3 - ref * 1e3, lw=0.8, color=C_RADAR if e["src"] == "radar" else C_RACON)
    c.set_ylabel(f"kHz from {ref:.3f} MHz")
    c.set_title("Instantaneous frequency inside each element (phase derivative, 50 ns smoothing). Blue radar, orange racon")
    c.set_ylim(-3000, 3000)
    amp = np.sqrt(2 * 50 * 1e-3) * 1e3
    d.plot(ts, xs.real * amp, lw=0.5, color=C_RADAR, label="I")
    d.plot(ts, xs.imag * amp, lw=0.5, color=C_RACON, alpha=0.8, label="Q")
    d.set_ylabel("mV peak at SM200B")
    d.set_title("Raw I and Q samples (the SM200B has removed the 9.4 GHz carrier)")
    d.legend(fontsize=8, loc="upper right")
    for ax in (a, b, c, d):
        ax.set_xlim(ts[0], ts[-1])
        ax.grid(alpha=0.25)
        ax.set_xlabel("Time from the trigger (us)")
    fig.suptitle(title, fontsize=10)
    out = PLOTS / f"{tag}_chain.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def plot_parts(tag, R, replies, title):
    r = best_reply(replies, [])
    if r is None:
        return None
    els = ([r["radar"]] if r["radar"] else []) + r["els"][:6]
    x, fs, fc, pre = R["snips"][r["snip"]], R["fs"], R["fc"], R["pre"]
    n = len(els)
    fig = plt.figure(figsize=(3.3 * n + 1, 10))
    gs = fig.add_gridspec(4, n, height_ratios=[1.1, 1.6, 1.0, 0.7], hspace=0.5, wspace=0.3, left=0.06, right=0.98, top=0.9, bottom=0.02)
    wiring.draw(fig.add_subplot(gs[3, :]), S.stages(), S.strip_title())
    ref = r["radar"]["f_abs_mhz"] if r["radar"] else els[0]["f_abs_mhz"]
    for j, e in enumerate(els):
        m = int(0.4e-6 * fs)
        a0, a1 = max(0, e["i0"] - m), min(len(x), e["i1"] + m)
        seg = x[a0:a1]
        t = (np.arange(a0, a1) - pre) / fs * 1e6
        col = C_RADAR if e["src"] == "radar" else (C_DASH if e["kind"] == "dash" else C_DOT)
        a, b, c = fig.add_subplot(gs[0, j]), fig.add_subplot(gs[1, j]), fig.add_subplot(gs[2, j])
        a.plot(t, 10 * np.log10(np.abs(seg) ** 2 + 1e-30), lw=0.6, color=col)
        a.set_title(f"{label(e)} {j if e['src'] == 'racon' else ''}\n{e['dur_us']:.2f} us, {e['p_dbm']:.1f} dBm\nrise {e['rise_ns']:.0f} ns, fall {e['fall_ns']:.0f} ns", fontsize=8)
        nps = int(2 ** np.clip(np.floor(np.log2(max(16, (e['i1'] - e['i0']) / 3))), 4, 9))
        f, tt, P = stft_db(seg, fs, nps)
        k = np.abs(f - e['f_off_hz']) <= max(6e6, 3 * fs / nps)
        b.pcolormesh(t[0] + tt * 1e6, (fc + f[k]) / 1e6, P[k], shading="auto", cmap="magma", vmin=P.max() - 45, vmax=P.max())
        b.axhline(e["f_abs_mhz"], color="w", lw=0.5, ls=":")
        b.set_title(f"STFT {nps/fs*1e9:.0f} ns window, {e['f_abs_mhz']:.3f} MHz", fontsize=8)
        fi = inst_freq(x[e["i0"]:e["i1"] + 1], fs, max(1, int(0.05e-6 * fs)))
        c.plot((np.arange(len(fi)) + e["i0"] - pre) / fs * 1e6, ((fc + fi) / 1e6 - ref) * 1e3, lw=0.8, color=col)
        c.set_ylim(-2000, 2000)
        c.set_title(f"{(e['f_abs_mhz'] - ref)*1e3:+.0f} kHz from radar; wobble {e['f_std_khz']:.0f} kHz rms", fontsize=8)
        for ax in (a, b, c):
            ax.grid(alpha=0.25)
            ax.set_xlim(t[0], t[-1])
            ax.tick_params(labelsize=7)
        c.set_xlabel("us from trigger", fontsize=8)
        if j == 0:
            a.set_ylabel("dBm at SM200B")
            b.set_ylabel("MHz")
            c.set_ylabel("kHz from radar")
    fig.suptitle(f"Each part of one interaction on its own (code {r['code']}). {title}", fontsize=10)
    out = PLOTS / f"{tag}_parts.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def plot_replies(tag, R, rows, replies, title):
    """Every snippet as one row of a waterfall, plus a ridgeline of the first 40 interactions with a reply."""
    snips, fs, pre = R["snips"], R["fs"], R["pre"]
    order = np.argsort(R["t"])
    L = snips.shape[1]
    last = max([e["i1"] for e in rows], default=L)
    L2 = min(L, int(np.percentile([e["i1"] for e in rows], 99)) + int(4e-6 * fs)) if rows else L
    dec = max(1, L2 // 2000)
    P = 10 * np.log10(np.abs(snips[order, :L2]) ** 2 + 1e-30)
    P = P[:, :P.shape[1] // dec * dec].reshape(len(order), -1, dec).max(axis=2)
    t = (np.arange(P.shape[1]) * dec - pre) / fs * 1e6
    fig, gs = fig_with_strip([1.4, 1.6], (14, 14))
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    im = a.pcolormesh(t, np.arange(len(order)), P, shading="auto", cmap="magma", vmin=np.percentile(P, 50), vmax=P.max())
    fig.colorbar(im, ax=a, pad=0.01, label="dBm at SM200B")
    a.set_ylabel("Snippet, in time order")
    a.set_title(f"All {len(order)} triggers lined up on the trigger: radar pulse at 0, racon reply after it")
    pick = [r for r in sorted(replies, key=lambda r: R["t"][r["snip"]])][:40]
    if pick:
        amp = np.sqrt(2 * 50 * 1e-3) * 1e3
        env = [np.abs(snips[r["snip"], :L2]) * amp for r in pick]
        step = max(e.max() for e in env) * 1.05
        tt = (np.arange(L2) - pre) / fs * 1e6
        for n, (r, e) in enumerate(zip(pick, env)):
            b.plot(tt, n * step + snips[r["snip"], :L2].real * amp, lw=0.5, color=plt.cm.viridis(n / max(1, len(pick) - 1)))
            b.plot(tt, n * step + e, lw=0.4, color="0.55", ls=":")
        b.set_yticks([n * step for n in range(0, len(pick), 5)], [str(n + 1) for n in range(0, len(pick), 5)])
    b.set_ylabel(f"Interaction number (one row = {step:.1f} mV)" if pick else "")
    b.set_title("Raw I samples of the first 40 interactions with a reply, stacked; dotted grey is the envelope")
    for ax in (a, b):
        ax.set_xlabel("Time from the trigger (us)")
        ax.set_xlim(t[0], t[-1])
        ax.grid(alpha=0.25)
    fig.suptitle(title, fontsize=10)
    out = PLOTS / f"{tag}_replies.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def plot_stats(tag, R, rows, replies, summ, title):
    fig, gs0 = fig_with_strip([1, 1, 1], (15, 14))
    gs = [gs0[i].subgridspec(1, 3, wspace=0.28) for i in range(3)]
    ax = [fig.add_subplot(g[0, j]) for g in gs for j in range(3)]
    rac = [e for r in replies for e in r["els"]]
    rad = [e for e in rows if e["src"] == "radar"]
    fs = R["fs"]
    # 1 durations
    for kind, col in (("dot", C_DOT), ("dash", C_DASH), ("element", C_RACON)):
        d = [e["dur_us"] for e in rac if e["kind"] == kind]
        if d:
            ax[0].hist(d, bins=40, color=col, alpha=0.75, label=f"racon {kind}: median {np.median(d):.2f} us (n {len(d)})")
    if rad:
        ax[0].hist([e["dur_us"] for e in rad], bins=40, color=C_RADAR, alpha=0.75, label=f"radar: median {np.median([e['dur_us'] for e in rad]):.3f} us")
    ax[0].set(title="Element durations (half-power)", xlabel="us", ylabel="count")
    # 2 gaps
    g = [(b["i0"] - a["i1"]) / fs * 1e6 for r in replies for a, b in zip(r["els"], r["els"][1:])]
    if g:
        ax[1].hist(g, bins=40, color=C_RACON, alpha=0.8, label=f"median {np.median(g):.2f} us, sd {np.std(g)*1e3:.0f} ns")
    ax[1].set(title="Gaps between racon elements", xlabel="us", ylabel="count")
    # 3 delay
    dl = [(r["els"][0]["i0"] - r["radar"]["i0"]) / fs * 1e6 for r in replies if r["radar"]]
    if dl:
        ax[2].hist(dl, bins=40, color="0.35", label=f"median {np.median(dl):.3f} us, sd {np.std(dl)*1e3:.0f} ns")
    ax[2].set(title="Racon reply start minus radar pulse start", xlabel="us", ylabel="count")
    # 4 freq racon vs radar
    pr = [(r["radar"]["f_abs_mhz"], np.mean([e["f_abs_mhz"] for e in r["els"]])) for r in replies if r["radar"]]
    if pr:
        a_, b_ = np.array(pr).T
        ax[3].plot(a_, (b_ - a_) * 1e3, "o", ms=3, color=C_RACON, label=f"racon minus radar: {np.median(b_-a_)*1e3:+.0f} kHz median")
    ax[3].set(title="Does the racon reply on the radar's frequency?", xlabel="radar pulse frequency (MHz)", ylabel="racon minus radar (kHz)")
    # 5 frequency over the recording
    if rad:
        ax[4].plot([e["t_abs_s"] - R["t"].min() for e in rad], [e["f_abs_mhz"] for e in rad], ".", ms=3, color=C_RADAR, label="radar pulses")
    if rac:
        ax[4].plot([e["t_abs_s"] - R["t"].min() for e in rac], [e["f_abs_mhz"] for e in rac], ".", ms=3, color=C_RACON, label="racon elements")
    ax[4].set(title="Frequency of every element over the recording", xlabel="s", ylabel="MHz")
    # 6 wobble inside elements
    for src, col, els in (("radar", C_RADAR, rad), ("racon", C_RACON, rac)):
        v = [e["f_std_khz"] for e in els if np.isfinite(e["f_std_khz"])]
        if v:
            ax[5].hist(v, bins=40, color=col, alpha=0.7, label=f"{src}: median {np.median(v):.0f} kHz rms")
    ax[5].set(title="Frequency wobble inside one element", xlabel="kHz rms", ylabel="count")
    # 7 power over time at our antenna
    gain = summ["chain_gain_db"]
    for src, col, els in (("radar", C_RADAR, rad), ("racon", C_RACON, rac)):
        if els:
            ax[6].plot([e["t_abs_s"] - R["t"].min() for e in els], [e["p_dbm"] - gain for e in els], ".", ms=3, color=col, label=src)
    ax[6].set(title="Power at our antenna port over the recording", xlabel="s", ylabel="dBm")
    # 8 reply power vs radar power (does the racon reply louder when hit harder?)
    pp = [(r["radar"]["p_dbm"] - gain, np.median([e["p_dbm"] for e in r["els"]]) - gain) for r in replies if r["radar"]]
    if pp:
        a_, b_ = np.array(pp).T
        ax[7].plot(a_, b_, "o", ms=3, color=C_RACON)
    ax[7].set(title="Racon reply level vs radar pulse level", xlabel="radar at our antenna (dBm)", ylabel="racon at our antenna (dBm)")
    # 9 codes
    codes = Counter(r["code"] for r in replies).most_common(8)
    if codes:
        ax[8].barh([f"{c}  {MORSE.get(c, '?')}" for c, _ in codes][::-1], [n for _, n in codes][::-1], color=C_RACON)
    ax[8].set(title="Codes decoded (dot/dash split by duration)", xlabel="replies")
    for a in ax:
        a.grid(alpha=0.25)
        if a.get_legend_handles_labels()[0]:
            a.legend(fontsize=7)
    fig.suptitle(title, fontsize=10)
    out = PLOTS / f"{tag}_stats.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def plot_loudness(tag, s, title):
    items = []
    if "radar" in s:
        r = s["radar"]
        items += [("Furuno, at the SM200B (strongest pulse)", r["p_sm_max_dbm"], C_RADAR, "measured"),
                  ("Furuno, at our antenna port", r["p_ant_max_dbm"], C_RADAR, f"minus chain gain {s['chain_gain_db']:+.1f} dB"),
                  ("Furuno EIRP, from this recording", r["eirp_dbm"], C_RADAR, f"+{S.fspl_db(S.D_RADAR_M):.1f} dB spreading at {S.D_RADAR_M:g} m, -{S.G_RX_DBI:g} dBi Vivaldi"),
                  ("Furuno EIRP, specification", S.RADAR_TX_DBM + S.RADAR_G_SPEC_DBI, "0.55", f"{S.RADAR_TX_DBM} dBm + {S.RADAR_G_SPEC_DBI} dBi, no foam"),
                  ("Furuno at the racon's antenna port", r["at_racon_dbm"], C_RADAR, f"racon needs {S.RACON_SENS_DBM:g} dBm")]
    if "racon" in s:
        c = s["racon"]
        items += [("Racon, at the SM200B (median element)", c["p_sm_median_dbm"], C_RACON, "measured"),
                  ("Racon, at our antenna port", c["p_ant_dbm"], C_RACON, f"minus chain gain {s['chain_gain_db']:+.1f} dB"),
                  ("Racon EIRP, from this recording", c["eirp_dbm"], C_RACON, f"+{S.fspl_db(S.D_RACON_M):.1f} dB spreading at {S.D_RACON_M:g} m, -{S.G_RX_DBI:g} dBi Vivaldi"),
                  ("Racon EIRP, specification", S.RACON_TX_DBM + S.RACON_G_SPEC_DBI, "0.55", f"{S.RACON_TX_DBM} dBm + {S.RACON_G_SPEC_DBI} dBi")]
    if not items:
        return None
    fig, gs = fig_with_strip([1.6, 0.45], (14, 8.5), left=0.24)
    a = fig.add_subplot(gs[0])
    y = np.arange(len(items))[::-1]
    for yy, (name, v, col, note) in zip(y, items):
        a.plot([min(v for _, v, _, _ in items) - 10, v], [yy, yy], color="0.85", lw=1, zorder=1)
        a.plot(v, yy, "o", ms=9, color=col, zorder=3)
        a.text(v + 1.5, yy, f"{v:+.1f} dBm   {note}", va="center", fontsize=8)
    a.set_yticks(y, [n for n, _, _, _ in items], fontsize=8.5)
    a.set_xlabel("dBm (peak, while transmitting)")
    a.set_xlim(min(v for _, v, _, _ in items) - 10, max(v for _, v, _, _ in items) + 45)
    a.grid(axis="x", alpha=0.3)
    a.set_title("How loud is each source? Same scale for everything")
    t = fig.add_subplot(gs[1])
    t.axis("off")
    lines = []
    if "radar" in s:
        r = s["radar"]
        lines.append(f"Furuno antenna gain implied: {r['g_inferred_dbi']:+.1f} dBi (spec {S.RADAR_G_SPEC_DBI:g} dBi, {S.RADAR_FOAM}); "
                     f"the racon would be triggered out to about {r['trigger_range_m']/1852:.2f} nmi by this radar (free space, {S.RACON_SENS_DBM:g} dBm sensitivity).")
    if "racon" in s:
        c = s["racon"]
        lines.append(f"Racon antenna gain implied: {c['g_inferred_dbi']:+.1f} dBi (spec {S.RACON_G_SPEC_DBI:g} dBi, with {S.RACON_TX_DBM:g} dBm into it). "
                     f"Racon level spread between elements: {c['p_sm_sd_db']:.1f} dB rms.")
    lines.append(f"Every EIRP assumes {S.G_RX_DBI:g} dBi for our Vivaldi (not measured): if it is 1 dB higher, every EIRP and implied gain is 1 dB lower. "
                 "Distances and the chain gain come from racon_setup.py.")
    t.text(0, 1, "\n\n".join(lines), va="top", fontsize=9, wrap=True)
    fig.suptitle(title, fontsize=10)
    out = PLOTS / f"{tag}_loudness.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def plot_timeline(tag, R, rows, gain, title):
    """Every event in the stream (not only the saved snippets): level against time, to show rotations and the racon's on/off cycle."""
    t, pk = R["extra"]["all_t_s"], R["extra"]["all_peak_dbm"]
    fig, gs = fig_with_strip([1.3, 1.0], (14, 10))
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    a.plot(t, pk - gain, ".", ms=2, color="0.3", label=f"every event ({len(t)}), strongest sample in its window")
    for src, col in (("radar", C_RADAR), ("racon", C_RACON)):
        e = [x for x in rows if x["src"] == src]
        if e:
            a.plot([x["t_abs_s"] for x in e], [x["p_dbm"] - gain for x in e], ".", ms=3, color=col, label=f"{src}, from the saved snippets")
    a.set(title="Level of every event at our antenna port over the stream", xlabel="s from the start of the stream", ylabel="dBm at antenna port")
    a.legend(fontsize=8)
    if len(t) > 1:
        d = np.diff(t) * 1e3
        b.hist(d[d < 20], bins=400, color="0.3")
    b.set(title="Time between consecutive events (below 20 ms): PRI lines and racon reply spacing", xlabel="ms", ylabel="count")
    for ax in (a, b):
        ax.grid(alpha=0.25)
    fig.suptitle(title, fontsize=10)
    out = PLOTS / f"{tag}_timeline.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def survey_plot(path):
    path = Path(path)
    d = np.load(path)
    f, W, t = d["f"] / 1e6, d["W"].astype(float), d["t"]
    bad = W > 30                                     # the SM200B returns occasional bins of +100 to +190 dBm: not real, dropped
    if bad.any():
        print(f"survey: {int(bad.sum())} impossible bins (> +30 dBm) dropped")
    W = np.where(bad, np.nan, W)
    meta = json.loads(str(d["meta"]))
    gain = meta["setup"]["chain_gain_db"]
    tag = path.parent.name
    fig, gs = fig_with_strip([1.0, 1.4], (14, 11))
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    hold = np.nanmax(W, axis=0)
    a.plot(f, hold, lw=0.6, color="0.2", label=f"max hold, {len(W)} sweeps")
    a.plot(f, np.nanmedian(W, axis=0), lw=0.5, color="0.6", label="median")
    a.axhline(S.SM_LIMIT_DBM, color="red", ls="--", lw=0.8, label="+20 dBm SM200B limit")
    a.axvspan(9300, 9500, color=C_RACON, alpha=0.07, label="racon band 9.3-9.5 GHz")
    i = int(np.argmax(hold))
    a.annotate(f"{f[i]:.2f} MHz, {hold[i]:+.1f} dBm", (f[i], hold[i]), xytext=(10, -5), textcoords="offset points", fontsize=8)
    a.set(title=f"Survey 9.0-10.0 GHz, {meta.get('rbw', 100e3)/1e6:g} MHz RBW, min/max detector, max hold", xlabel="MHz", ylabel="dBm at SM200B")
    a.legend(fontsize=8)
    im = b.pcolormesh(f, t, W, shading="auto", cmap="magma", vmin=np.nanpercentile(W, 50), vmax=np.nanmax(W))
    fig.colorbar(im, ax=b, pad=0.01, label="dBm at SM200B")
    b.set(title="Every sweep: a racon that sweeps its frequency shows as a slanted line, an agile one sits on the radar", xlabel="MHz", ylabel="s")
    for ax in (a, b):
        ax.grid(alpha=0.25)
    fig.suptitle(f"{tag}: chain gain {gain:+.1f} dB, so antenna port = SM200B reading {-gain:+.1f} dB", fontsize=10)
    out = PLOTS / f"{tag}_survey.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    peaks = f[hold > np.nanmedian(hold) + 20]
    print("survey: above median + 20 dB at", np.round(peaks[np.r_[True, np.diff(peaks) > 1]], 1) if len(peaks) else "nothing", "MHz")
    return [out]


def print_summary(s):
    print(f"snippets {s['n_snippets']}, radar pulses {s['n_radar_pulses']}, replies {s['n_replies']}, noise {s['noise_dbm_per_sample']:.1f} dBm/sample")
    if "radar" in s:
        r = s["radar"]
        print(f"RADAR  {r['dur_us']:.3f} us, rise {r['rise_ns']:.0f} ns, {r['f_mhz']:.3f} MHz (sd {r['f_sd_khz']:.0f} kHz), "
              f"strongest {r['p_sm_max_dbm']:.1f} dBm at SM200B = {r['p_ant_max_dbm']:.1f} dBm at antenna, EIRP {r['eirp_dbm']:.1f} dBm, "
              f"G {r['g_inferred_dbi']:+.1f} dBi, PRI median {r['pri_us_median']}")
    if "racon" in s:
        c = s["racon"]
        print(f"RACON  code {c['codes']} -> {c['letter']}; dot {c.get('dot_us', {}).get('median')} dash {c.get('dash_us', {}).get('median')} "
              f"gap {c['gap_us']['median']} us; reply {c['reply_len_us']} us; delay {c['delay_from_radar_start_us']['median']} us; "
              f"{c['f_mhz']:.3f} MHz, {c['f_minus_radar_khz']['median']} kHz from radar; {c['p_sm_median_dbm']:.1f} dBm at SM200B = "
              f"{c['p_ant_dbm']:.1f} at antenna, EIRP {c['eirp_dbm']:.1f} dBm, G {c['g_inferred_dbi']:+.1f} dBi; reply rate {c['reply_rate']:.2f}; "
              f"phase carried {c.get('phase_carry_R')}")


if __name__ == "__main__":
    arg = Path(sys.argv[1])
    for f in (survey_plot(arg / "survey.npz" if arg.is_dir() and (arg / "survey.npz").exists() else arg) if "survey" in arg.name else analyze(arg)) or []:
        print("plot", f)
