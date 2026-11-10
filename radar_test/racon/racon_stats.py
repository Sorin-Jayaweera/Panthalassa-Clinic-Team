"""Characterise the SeaBeacon 2 racon reply (and the Furuno pulse that triggers it) across every 9 Nov recording.

    python racon_stats.py            # all recordings listed in RECS
    python racon_stats.py 20261109_215716

For every snippet: radar pulse edges at half power (interpolated), its frequency from the phase slope; then every racon element
after it, edges at half of that element's own level, frequency (phase slope over the middle 80 %), chirp (quadratic phase fit),
10-90 % rise and fall, level. A reply counts as a full Morse R only if it is exactly short-long-short (dot 4-15 us, dash 18-35 us).
The fixed split at 17 us replaces the 2-means split, which mislabelled weak recordings as 'O'.

Writes plots/stats_<tag>_*.png (all with the wiring strip), data/stats_<tag>_replies.csv, data/stats_<tag>_radar.csv,
data/racon_stats_summary.csv/.json, and the cross-recording plots plots/racon_all_*.png and plots/sweeps_*.png.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import racon_analyze as A  # noqa: E402
import racon_setup as S  # noqa: E402
import setups_9nov as Z  # noqa: E402

PLOTS, DATA = A.PLOTS, A.DATA
DOT, DASH = (4.0, 15.0), (18.0, 35.0)
SPLIT_US = 17.0
VSPLIT_US = 22.4      # two versions of the R seen: long (dash 25.6 us) and short (dash 19.2 us, everything x 0.75)
VCOL = {"long": "#264653", "short": "#e9c46a"}
RECS = ["20261109_211913", "20261109_212012", "20261109_212124", "20261109_213227", "20261109_213542", "20261109_213625",
        "20261109_213716", "20261109_214452", "20261109_215120", "20261109_215332", "20261109_215716", "seg_horn_racon_250M"]
SHORT = {"20261109_213542": "Vivaldi 21:35", "20261109_213625": "Vivaldi 21:36", "20261109_213716": "Vivaldi 21:37",
         "20261109_214452": "Vivaldi 21:44", "20261109_215716": "horn 21:57", "seg_horn_racon_250M": "horn 22:24, 250 MS/s"}
EL = ["dot1", "dash", "dot2"]
C_EL = {"dot1": "#2a9d8f", "dash": "#8b3a9c", "dot2": "#e76f51"}


def path_for(rec):
    if rec.startswith("seg_"):
        return sorted(DATA.glob(rec + "_*"))[-1]
    return DATA / f"raw_{rec}.npz"


# ------------------------------------------------------------------------------------------------------------------ measuring
def _edges(ps, i0, i1, level, frac=0.5):
    """Interpolated sample positions where ps crosses frac*level going up near i0 and down near i1."""
    h = level * frac
    a = i0
    while a > 0 and ps[a - 1] >= h:
        a -= 1
    while a < i1 and ps[a] < h:
        a += 1
    b = i1 - 1
    while b < len(ps) - 1 and ps[b + 1] >= h:
        b += 1
    while b > a and ps[b] < h:
        b -= 1
    lo = a - (ps[a] - h) / max(ps[a] - ps[a - 1], 1e-30) if a > 0 else float(a)
    hi = b + (ps[b] - h) / max(ps[b] - ps[b + 1], 1e-30) if b < len(ps) - 1 else float(b)
    return lo, hi


def _ten90(pf, lo, hi, level, w):
    """10 and 90 % crossings near the rising edge (lo) and falling edge (hi), on the lightly smoothed power.
    Rising: last sample below 10 % before lo, first at or above 90 % after it. Falling: the mirror image. Sample resolution."""
    n = len(pf)
    w = max(5, w)
    a0, a1 = max(0, lo - w), min(n, lo + w)
    seg = pf[a0:a1]
    i90 = np.flatnonzero(seg >= 0.9 * level)
    r90 = a0 + (i90[0] if len(i90) else len(seg) - 1)
    below = np.flatnonzero(pf[a0:r90] < 0.1 * level)
    r10 = a0 + (below[-1] if len(below) else 0)
    b0, b1 = max(0, hi - w), min(n, hi + w)
    seg = pf[b0:b1]
    j90 = np.flatnonzero(seg >= 0.9 * level)
    f90 = b0 + (j90[-1] if len(j90) else 0)
    below = np.flatnonzero(pf[f90:b1] < 0.1 * level)
    f10 = f90 + (below[0] if len(below) else b1 - f90)
    return float(r10), float(r90), float(f90), float(f10)


def _freq(x, a, b, fs, quad=False):
    """Frequency (Hz, baseband) from the phase slope over samples a..b; with quad also the chirp (Hz/s)."""
    a, b = int(math.ceil(a)), int(math.floor(b))
    if b - a < 4:
        return (float("nan"), float("nan")) if quad else float("nan")
    ph = np.unwrap(np.angle(x[a:b]))
    t = (np.arange(b - a) - (b - a) / 2) / fs
    if quad:
        c = np.polyfit(t, ph, 2)
        return c[1] / (2 * np.pi), 2 * c[0] / (2 * np.pi)
    return np.polyfit(t, ph, 1)[0] / (2 * np.pi)


def measure(x, fs, pre, noise):
    p = (x.real ** 2 + x.imag ** 2).astype(float)
    ps = A.smooth(p, max(1, round(0.1e-6 * fs)))
    pf = A.smooth(p, max(1, round(0.04e-6 * fs)))      # lighter smoothing for the 10-90 % edge times
    wide = fs > 100e6                                  # 250 MS/s: 7 dB more noise in the band, so detect on a 0.3 us average at 6 dB
    thr = noise * (10 ** 0.6 if wide else 10.0)
    pdet = A.smooth(p, round(0.3e-6 * fs)) if wide else ps
    out = dict(radar=None, els=[])
    w0, w1 = max(1, pre - int(1e-6 * fs)), pre + int(2e-6 * fs)
    seg = ps[w0:w1]
    if seg.size and seg.max() > thr * 3:
        k = w0 + int(np.argmax(seg))
        lo, hi = _edges(ps, k, k + 1, ps[k])
        d = (hi - lo) / fs * 1e6
        if 0.3 < d < 1.5:
            m0, m1 = lo + 0.2 * (hi - lo), hi - 0.2 * (hi - lo)
            out["radar"] = dict(i0=lo, i1=hi, dur_us=d, f_bb=_freq(x, m0, m1, fs),
                                p_dbm=10 * math.log10(np.mean(p[int(m0):int(m1) + 1]) + 1e-30), peak_dbm=10 * math.log10(ps[k] + 1e-30))
    r = out["radar"]
    s0 = int(r["i1"] + 1.0e-6 * fs) if r else pre + int(1.5e-6 * fs)
    mask = np.zeros(len(ps), bool)
    mask[s0:] = pdet[s0:] > thr
    rr = A.runs(mask)
    merged = []
    for a, b in rr:
        if merged and (a - merged[-1][1]) < 2e-6 * fs:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    for a, b in merged:
        if (b - a) < 2e-6 * fs:
            continue
        core = p[a + (b - a) // 5: b - (b - a) // 5]
        level = float(np.median(ps[a + (b - a) // 5: b - (b - a) // 5])) if len(core) > 3 else float(ps[a:b].max())
        lo, hi = _edges(ps, a, b, level)
        l10, l90, h90, h10 = _ten90(pf, int(lo), int(hi), level, int(0.5e-6 * fs))
        m0, m1 = lo + 0.1 * (hi - lo), hi - 0.1 * (hi - lo)
        f, ch = _freq(x, m0, m1, fs, quad=True)
        out["els"].append(dict(i0=lo, i1=hi, dur_us=(hi - lo) / fs * 1e6, f_bb=f, chirp=ch, p_dbm=10 * math.log10(level + 1e-30),
                               rise_ns=(l90 - l10) / fs * 1e9, fall_ns=(h10 - h90) / fs * 1e9))
    return out


def code_of(els):
    return "".join("-" if e["dur_us"] > SPLIT_US else "." for e in els)


def is_full_r(m):
    e = m["els"]
    return (m["radar"] is not None and len(e) == 3 and DOT[0] <= e[0]["dur_us"] <= DOT[1] and DASH[0] <= e[1]["dur_us"] <= DASH[1]
            and DOT[0] <= e[2]["dur_us"] <= DOT[1])


# ------------------------------------------------------------------------------------------------------------------ one recording
def process(rec):
    path = path_for(rec)
    R = A.load(path)
    entry = Z.apply(S, rec)
    snips, fs, fc, pre = R["snips"], R["fs"], R["fc"], R["pre"]
    pr = snips[:, :max(8, pre - int(0.5e-6 * fs))]
    noise = float(np.median(pr.real ** 2 + pr.imag ** 2)) / math.log(2)
    if np.any(R["t"] > 1e6) and np.any(R["t"] < 1e6):        # 250 MS/s captures mix epoch times with a few relative ones
        good = R["t"] > 1e6
        R["t"] = np.where(good, R["t"], np.min(R["t"][good]))
    order = np.argsort(R["t"])
    ms = []
    for k in order:
        m = measure(snips[k], fs, pre, noise)
        m["k"], m["t"] = int(k), float(R["t"][k])
        if not entry["RACON_ON"]:
            m["els"] = []
        ms.append(m)
    radar = [m for m in ms if m["radar"]]
    rows = []
    for m in ms:
        if not (m["els"] and is_full_r(m)):
            continue
        r, (d1, da, d2) = m["radar"], m["els"]
        us = lambda i: (i - r["i0"]) / fs * 1e6  # noqa: E731
        fr = fc + r["f_bb"]
        row = dict(snip=m["k"], t_s=m["t"] - R["t"].min(), radar_f_mhz=fr / 1e6, radar_dur_us=r["dur_us"], radar_dbm=r["p_dbm"],
                   delay_us=us(d1["i0"]), dot1_us=d1["dur_us"], gap1_us=(da["i0"] - d1["i1"]) / fs * 1e6, dash_us=da["dur_us"],
                   gap2_us=(d2["i0"] - da["i1"]) / fs * 1e6, dot2_us=d2["dur_us"], total_us=(d2["i1"] - d1["i0"]) / fs * 1e6,
                   end_us=us(d2["i1"]), dot1_to_dash_us=(da["i0"] - d1["i0"]) / fs * 1e6, dash_to_dot2_us=(d2["i0"] - da["i0"]) / fs * 1e6)
        for n, e in zip(EL, m["els"]):
            row[f"{n}_off_mhz"] = (fc + e["f_bb"] - fr) / 1e6
            row[f"{n}_f_mhz"] = (fc + e["f_bb"]) / 1e6
            row[f"{n}_chirp_mhz_per_us"] = e["chirp"] / 1e12
            row[f"{n}_dbm"] = e["p_dbm"]
            row[f"{n}_rise_ns"] = e["rise_ns"]
            row[f"{n}_fall_ns"] = e["fall_ns"]
        row["drift_dot1_to_dot2_mhz"] = row["dot2_off_mhz"] - row["dot1_off_mhz"]
        row["dash_minus_2dots_us"] = row["dash_us"] - row["dot1_us"] - row["dot2_us"]
        row["variant"] = "long" if row["dash_us"] > VSPLIT_US else "short"
        rows.append(row)
    codes = Counter(code_of(m["els"]) for m in ms if m["els"])
    rad = [dict(snip=m["k"], t_s=m["t"] - R["t"].min(), f_mhz=(fc + m["radar"]["f_bb"]) / 1e6, dur_us=m["radar"]["dur_us"],
                p_dbm=m["radar"]["p_dbm"], peak_dbm=m["radar"]["peak_dbm"]) for m in radar]
    tag = f"stats_{rec}"
    for name, rr in (("replies", rows), ("radar", rad)):
        if rr:
            with open(DATA / f"{tag}_{name}.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rr[0]))
                w.writeheader()
                w.writerows(rr)
    D = dict(rec=rec, R=R, ms=ms, rows=rows, rad=rad, codes=codes, noise=noise, entry=entry, tag=tag,
             title=f"{rec} ({Z.REF_DBM.get(Z.key_for(rec), '')} dBm ref): {entry['LABEL']}; {fs/1e6:.0f} MS/s")
    print(f"{rec}: {len(ms)} snippets, {len(rad)} radar pulses, {len(rows)} full R replies; element codes {codes.most_common(6)}", flush=True)
    return D


def stat(v):
    v = np.asarray([x for x in v if np.isfinite(x)], float)
    if not len(v):
        return None
    return dict(n=len(v), mean=float(v.mean()), sd=float(v.std(ddof=1)) if len(v) > 1 else 0.0, min=float(v.min()),
                p5=float(np.percentile(v, 5)), median=float(np.median(v)), p95=float(np.percentile(v, 95)), max=float(v.max()))


STAT_KEYS = [("delay_us", "delay, radar start to dot 1 start", "us"), ("dot1_us", "dot 1", "us"), ("gap1_us", "gap 1", "us"),
             ("dash_us", "dash", "us"), ("gap2_us", "gap 2", "us"), ("dot2_us", "dot 2", "us"), ("total_us", "whole R, dot 1 start to dot 2 end", "us"),
             ("dot1_to_dash_us", "dot 1 start to dash start", "us"), ("dash_to_dot2_us", "dash start to dot 2 start", "us"),
             ("dot1_off_mhz", "dot 1 freq minus radar", "MHz"), ("dash_off_mhz", "dash freq minus radar", "MHz"), ("dot2_off_mhz", "dot 2 freq minus radar", "MHz"),
             ("drift_dot1_to_dot2_mhz", "drift dot 1 to dot 2", "MHz"), ("dash_chirp_mhz_per_us", "chirp inside the dash", "MHz/us"),
             ("dot1_chirp_mhz_per_us", "chirp inside dot 1", "MHz/us"),
             ("dash_dbm", "dash level at SM200B", "dBm"), ("radar_f_mhz", "radar frequency (these pulses)", "MHz"), ("radar_dur_us", "radar pulse, half power", "us")]


# ------------------------------------------------------------------------------------------------------------------ plots
def save(fig, D, name):
    fig.suptitle(D["title"], fontsize=10)
    out = PLOTS / f"{D['tag']}_{name}.png"
    fig.savefig(out, dpi=105)
    plt.close(fig)
    return out


def stack_img(ax, img, x, cmap, label, fig, vmin=None, vmax=None, ylabel="Reply number, in time order"):
    im = ax.imshow(img, aspect="auto", origin="lower", extent=[x[0], x[-1], 0, len(img)], cmap=cmap, interpolation="nearest",
                   vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=ax, pad=0.01, label=label)
    ax.set_ylabel(ylabel)
    return im


def rows_env(D, align, t0_us, t1_us):
    """Envelope dBm per full-R reply, x from t0_us to t1_us relative to the radar start ('radar') or to dot 1 start ('dot1')."""
    R, fs = D["R"], D["R"]["fs"]
    n0, n1 = int(t0_us * 1e-6 * fs), int(t1_us * 1e-6 * fs)
    ms = {m["k"]: m for m in D["ms"]}
    img, inst = [], []
    for row in D["rows"]:
        m = ms[row["snip"]]
        x = R["snips"][row["snip"]]
        ref = m["radar"]["i0"] if align == "radar" else m["els"][0]["i0"]
        c = int(round(ref))
        idx = np.arange(c + n0, c + n1)
        ok = (idx >= 0) & (idx < len(x))
        seg = np.full(len(idx), np.nan + 0j, complex)
        seg[ok] = x[idx[ok]]
        img.append(seg)
    t = np.arange(n0, n1) / fs * 1e6
    return t, np.array(img)


def plot_stacks(D):
    if not D["rows"]:
        return []
    fs = D["R"]["fs"]
    outs = []
    t, X = rows_env(D, "radar", -2, 72)
    P = 10 * np.log10(np.abs(X) ** 2 + 1e-30)
    t2, X2 = rows_env(D, "dot1", -3, 62)
    P2 = 10 * np.log10(np.abs(X2) ** 2 + 1e-30)
    lo, hi = np.nanpercentile(P, 40), np.nanpercentile(P, 99.9)
    fig, gs = A.fig_with_strip([1.3, 1.3, 1.1], (15, 17))
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    stack_img(a, P, t, "magma", "dBm at SM200B", fig, lo, hi)
    a.set(title=f"All {len(P)} full Morse R replies, one row each, lined up on the radar pulse start (x = 0): the delay jitter shows as row-to-row shifts",
          xlabel="Time from the radar pulse start (us)")
    stack_img(b, P2, t2, "magma", "dBm at SM200B", fig, lo, hi)
    b.set(title="Same replies lined up on the start of dot 1: what is left is how much each dot, gap and dash length varies",
          xlabel="Time from the start of dot 1 (us)")
    rows = D["rows"]
    N = np.abs(X2) ** 2 / np.array([10 ** (r["dash_dbm"] / 10) for r in rows])[:, None]
    pick = np.linspace(0, len(N) - 1, min(300, len(N))).astype(int)
    for i in pick:
        c.plot(t2, N[i], lw=0.3, alpha=0.25, color="0.4")
    mu, sd = np.nanmean(N, 0), np.nanstd(N, 0)
    c.plot(t2, mu, color="k", lw=1.4, label=f"mean of all {len(N)}")
    c.fill_between(t2, mu - sd, mu + sd, color="tab:orange", alpha=0.35, label="mean +- 1 sd")
    for key, col in (("dot1_us", C_EL["dot1"]),):
        pass
    st = {k: np.mean([r[k] for r in rows]) for k in ("dot1_us", "gap1_us", "dash_us", "gap2_us", "dot2_us")}
    e = np.cumsum([0, st["dot1_us"], st["gap1_us"], st["dash_us"], st["gap2_us"], st["dot2_us"]])
    for v in e:
        c.axvline(v, color="tab:blue", lw=0.7, ls="--")
    for (n, k), x0, x1 in zip([("dot 1", "dot1_us"), ("gap 1", "gap1_us"), ("dash", "dash_us"), ("gap 2", "gap2_us"), ("dot 2", "dot2_us")], e[:-1], e[1:]):
        v = [r[k] for r in rows]
        c.text((x0 + x1) / 2, 1.32, f"{n}\n{np.mean(v):.2f} +- {np.std(v):.2f} us", ha="center", fontsize=8)
    c.set(ylim=(-0.05, 1.5), xlim=(t2[0], t2[-1]), xlabel="Time from the start of dot 1 (us)", ylabel="Power / that reply's dash level",
          title=f"{len(pick)} replies overlaid (grey), normalised to their own dash level; blue dashed = mean edges")
    c.legend(fontsize=8, loc="center right")
    for ax in (a, b, c):
        ax.grid(alpha=0.25)
    outs.append(save(fig, D, "stack_envelope"))

    # ---- frequency: instantaneous frequency stack and per-reply spectrum stack
    ms = {m["k"]: m for m in D["ms"]}
    sm = max(1, round(0.4e-6 * fs))
    F = []
    for row, x in zip(rows, X):
        prod = x[1:] * np.conj(x[:-1])
        prod = np.where(np.isfinite(prod), prod, 0)
        f = np.angle(A.smooth(prod, sm)) * fs / (2 * np.pi) / 1e6 + (D["R"]["fc"] / 1e6 - row["radar_f_mhz"])
        pw = A.smooth(np.abs(x[1:]) ** 2, sm)
        f[~(pw > D["noise"] * 30)] = np.nan
        F.append(f)
    F = np.array(F)
    fig, gs = A.fig_with_strip([1.3, 1.3, 1.3], (15, 17))
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    off = np.nanmedian([r["dash_off_mhz"] for r in rows])
    stack_img(a, F, t[1:], "coolwarm", "racon frequency minus this pulse's radar frequency (MHz)", fig, off - 2.5, off + 2.5)
    a.set(title="Instantaneous frequency of every reply (0.4 us smoothing), relative to the radar pulse that triggered it; blank = below the noise",
          xlabel="Time from the radar pulse start (us)")
    nfft = 1 << int(math.ceil(math.log2(80e-6 * fs * 8)))
    fa = (np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs)) + D["R"]["fc"]) / 1e6
    Sp, So = [], []
    for row in rows:
        m = ms[row["snip"]]
        x = D["R"]["snips"][row["snip"]]
        a0, a1 = int(m["els"][0]["i0"] - 1e-6 * fs), int(m["els"][2]["i1"] + 1e-6 * fs)
        seg = x[max(0, a0):a1] * np.hanning(len(x[max(0, a0):a1]))
        s = np.abs(np.fft.fftshift(np.fft.fft(seg, nfft))) ** 2
        s = 10 * np.log10(s / s.max() + 1e-12)
        Sp.append(s)
        So.append(np.interp(fa - D["R"]["fc"] / 1e6, fa - row["radar_f_mhz"], s))
    Sp, So = np.array(Sp), np.array(So)
    fr = np.median([r["radar_f_mhz"] for r in rows])
    fsel = (fa > fr - 4) & (fa < fr + off + 6)
    stack_img(b, Sp[:, fsel], fa[fsel], "viridis", "dB relative to that reply's peak", fig, -40, 0)
    b.axvline(fr, color="w", lw=0.8, ls="--")
    b.set(title=f"Spectrum of every whole reply (Hann, dot 1 to dot 2), absolute frequency; white dashed = median radar {fr:.3f} MHz", xlabel="MHz")
    osel = (fa - D["R"]["fc"] / 1e6 > -4) & (fa - D["R"]["fc"] / 1e6 < off + 6)
    xo = (fa - D["R"]["fc"] / 1e6)[osel]
    stack_img(c, So[:, osel], xo, "viridis", "dB relative to that reply's peak", fig, -40, 0)
    c.axvline(0, color="w", lw=0.8, ls="--")
    c.set(title="Same spectra shifted so each reply's own radar pulse is at 0: a straight vertical line = the racon tracks the radar exactly",
          xlabel="Frequency minus that reply's radar frequency (MHz)")
    outs.append(save(fig, D, "stack_freq"))
    return outs


def plot_radar_stack(D):
    rad = D["rad"]
    if not rad:
        return []
    R, fs, fc = D["R"], D["R"]["fs"], D["R"]["fc"]
    ms = [m for m in D["ms"] if m["radar"]]
    n0, n1 = int(-0.5e-6 * fs), int(1.6e-6 * fs)
    X = []
    for m in ms:
        c = int(round(m["radar"]["i0"]))
        x = R["snips"][m["k"]]
        idx = np.arange(c + n0, c + n1)
        idx = idx[(idx >= 0) & (idx < len(x))]
        seg = np.full(n1 - n0, np.nan + 0j, complex)
        seg[idx - (c + n0)] = x[idx]
        X.append(seg)
    X = np.array(X)
    t = np.arange(n0, n1) / fs * 1e6
    P = 10 * np.log10(np.abs(X) ** 2 + 1e-30)
    fig, gs = A.fig_with_strip([1.2, 1.2, 1.0], (15, 15))
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
    stack_img(a, P, t, "magma", "dBm at SM200B", fig, np.nanpercentile(P, 30), np.nanpercentile(P, 99.9), "Pulse number, in time order")
    a.set(title=f"All {len(P)} radar pulses lined up on their half-power start: the antenna sweeping past shows as level bands", xlabel="Time from the pulse start (us)")
    nfft = 1 << int(math.ceil(math.log2(len(t) * 64)))
    fa = (np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs)) + fc) / 1e6
    Sp = []
    for x in X:
        x = np.nan_to_num(x)
        s = np.abs(np.fft.fftshift(np.fft.fft(x * np.hanning(len(x)), nfft))) ** 2
        Sp.append(10 * np.log10(s / s.max() + 1e-12))
    Sp = np.array(Sp)
    fr = np.median([r["f_mhz"] for r in rad])
    sel = (fa > fr - 8) & (fa < fr + 8)
    stack_img(b, Sp[:, sel], fa[sel], "viridis", "dB relative to the pulse's peak", fig, -30, 0, "Pulse number, in time order")
    b.set(title=f"Spectrum of every radar pulse (2.1 us window); median {fr:.3f} MHz", xlabel="MHz")
    N = np.abs(X) ** 2 / np.nanmax(np.abs(X) ** 2, axis=1, keepdims=True)
    for i in np.linspace(0, len(N) - 1, min(300, len(N))).astype(int):
        c.plot(t, N[i], lw=0.3, alpha=0.25, color="0.4")
    c.plot(t, np.nanmean(N, 0), color="k", lw=1.4, label="mean")
    d = [r["dur_us"] for r in rad]
    c.set(xlabel="Time from the pulse start (us)", ylabel="Power / that pulse's peak",
          title=f"Radar pulses overlaid: half-power width {np.mean(d):.3f} +- {np.std(d):.3f} us (sample spacing {1e6/fs*1e3:.0f} ns)")
    c.legend(fontsize=8)
    for ax in (a, b, c):
        ax.grid(alpha=0.25)
    return [save(fig, D, "stack_radar")]


def hist(ax, v, label, unit, color="tab:blue", bins=60):
    v = np.asarray([x for x in v if np.isfinite(x)])
    if not len(v):
        ax.set_title(label + ": none")
        return
    lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.5)
    if hi <= lo:
        lo, hi = lo - 1e-3, hi + 1e-3
    ax.hist(v, bins=np.linspace(lo, hi, bins), color=color, alpha=0.8)
    ax.axvline(np.mean(v), color="k", lw=1)
    ax.set_title(f"{label}\n{np.mean(v):.3f} +- {np.std(v, ddof=1) if len(v) > 1 else 0:.3f} {unit} (N {len(v)})", fontsize=9)
    ax.set_xlabel(unit)
    ax.grid(alpha=0.25)


def vhist(ax, rows, k, label, unit, bins=60):
    """Histogram stacked by reply version (long / short R), title gives mean +- sd of each."""
    vs = {v: np.array([r[k] for r in rows if r["variant"] == v and np.isfinite(r[k])]) for v in ("long", "short")}
    allv = np.concatenate([x for x in vs.values()])
    if not len(allv):
        return
    lo, hi = np.percentile(allv, 0.5), np.percentile(allv, 99.5)
    if hi <= lo:
        lo, hi = lo - 1e-3, hi + 1e-3
    ax.hist([vs["long"], vs["short"]], bins=np.linspace(lo, hi, bins), stacked=True, color=[VCOL["long"], VCOL["short"]],
            label=[f"long R (N {len(vs['long'])})", f"short R (N {len(vs['short'])})"])
    txt = "\n".join(f"{v}: {x.mean():.3f} +- {x.std(ddof=1) if len(x) > 1 else 0:.3f}" for v, x in vs.items() if len(x))
    ax.set_title(f"{label} ({unit})\n{txt}", fontsize=8)
    ax.set_xlabel(unit)
    ax.grid(alpha=0.25)


def plot_stats(D):
    rows = D["rows"]
    if not rows:
        return []
    outs = []
    g = lambda k: [r[k] for r in rows]  # noqa: E731
    items = [("delay_us", "Delay: radar start to dot 1 start", "us"), ("dot1_us", "Dot 1 length (half power)", "us"),
             ("gap1_us", "Gap 1", "us"), ("dash_us", "Dash length", "us"), ("gap2_us", "Gap 2", "us"), ("dot2_us", "Dot 2 length", "us"),
             ("total_us", "Whole R: dot 1 start to dot 2 end", "us"), ("end_us", "Radar start to end of reply", "us"),
             ("dot1_to_dash_us", "Dot 1 start to dash start", "us"), ("dash_to_dot2_us", "Dash start to dot 2 start", "us"),
             ("dash_minus_2dots_us", "Dash minus the two dots", "us"), ("radar_dur_us", "Radar pulse length (these replies)", "us"),
             ("dash_dbm", "Dash level at the SM200B", "dBm"), ("dash_off_mhz", "Dash frequency minus radar", "MHz"),
             ("drift_dot1_to_dot2_mhz", "Drift, dot 2 minus dot 1", "MHz")]
    for v in ("long", "short"):
        vr = [r for r in rows if r["variant"] == v]
        if len(vr) < 5:
            continue
        fig, gs = A.fig_with_strip([1, 1, 1, 1], (16, 17))
        sub = gs[:-1].subgridspec(4, 4, hspace=0.75, wspace=0.3)
        for i, (k, lab, u) in enumerate(items):
            vals = np.array([r[k] for r in vr])
            ax = fig.add_subplot(sub[i // 4, i % 4])
            if u == "ns":                                   # edge times have a long tail from fades and overlaps: show 0-400 ns
                lab = f"{lab}, median {np.median(vals):.0f} ns; {np.mean(vals > 400) * 100:.0f} % above 400 ns not shown"
                vals = vals[vals <= 400]
            hist(ax, vals, lab, u, VCOL[v] if v == "long" else "#c99a2e")
        ax = fig.add_subplot(sub[3, 3])
        ax.scatter([r["delay_us"] for r in vr], [r["dash_us"] for r in vr], s=3, alpha=0.4, color=VCOL[v] if v == "long" else "#c99a2e")
        ax.set(xlabel="delay (us)", ylabel="dash (us)", title="Delay vs dash length")
        ax.grid(alpha=0.25)
        fig.text(0.07, 0.955, f"Morse timing of the {len(vr)} {v} R replies ({100 * len(vr) / len(rows):.0f} % of {len(rows)} full R). "
                 f"Edges at half of each element's own power, interpolated between samples ({1e9 / D['R']['fs']:.0f} ns apart). Black line = mean.", fontsize=9)
        outs.append(save(fig, D, f"morse_timing_{v}"))

    fig, gs = A.fig_with_strip([1, 1, 1], (16, 14))
    sub = gs[:-1].subgridspec(3, 4, hspace=0.8, wspace=0.3)
    for i, n in enumerate(EL):
        vhist(fig.add_subplot(sub[0, i]), rows, f"{n}_off_mhz", f"{n.replace('1', ' 1').replace('2', ' 2')} frequency minus radar", "MHz")
    vhist(fig.add_subplot(sub[0, 3]), rows, "drift_dot1_to_dot2_mhz", "Drift over the reply: dot 2 minus dot 1", "MHz")
    fig.axes[-1].legend(fontsize=7)
    for i, n in enumerate(EL):
        vhist(fig.add_subplot(sub[1, i]), rows, f"{n}_chirp_mhz_per_us", f"Chirp inside {n}", "MHz/us")
    hist(fig.add_subplot(sub[1, 3]), g("radar_f_mhz"), "Radar frequency of the triggering pulses", "MHz", "#1f4e9c")
    ax = fig.add_subplot(sub[2, 0:2])
    for n in EL:
        ax.scatter(g("radar_f_mhz"), g(f"{n}_f_mhz"), s=3, alpha=0.4, color=C_EL[n], label=n)
    x, y = np.array(g("radar_f_mhz")), np.array(g("dash_f_mhz"))
    if np.ptp(x) > 0.05:
        c = np.polyfit(x, y, 1)
        xx = np.linspace(x.min(), x.max(), 2)
        ax.plot(xx, np.polyval(c, xx), "k-", lw=1, label=f"dash fit: slope {c[0]:.2f}")
    ax.set(xlabel="Radar frequency of that pulse (MHz)", ylabel="Racon element frequency (MHz)",
           title="Does the racon follow the radar from pulse to pulse? slope 1 = tracks exactly")
    ax.legend(fontsize=8, markerscale=4)
    ax.grid(alpha=0.25)
    ax = fig.add_subplot(sub[2, 2])
    for n in EL:
        ax.hist(g(f"{n}_dbm"), bins=50, alpha=0.5, color=C_EL[n], label=n)
    ax.set(title="Element level at the SM200B", xlabel="dBm")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    ax = fig.add_subplot(sub[2, 3])
    ax.scatter(g("dash_dbm"), g("dash_off_mhz"), s=3, alpha=0.4, color=C_EL["dash"])
    ax.set(xlabel="dash level (dBm)", ylabel="dash offset (MHz)", title="Offset vs level (a level-dependent estimate would slope)")
    ax.grid(alpha=0.25)
    outs.append(save(fig, D, "freq"))

    fig, gs = A.fig_with_strip([1, 1, 1, 1], (15, 15))
    t = np.array(g("t_s"))
    for i, (ks, lab) in enumerate([(["delay_us"], "delay (us)"), (["dot1_us", "dash_us", "dot2_us"], "element length (us)"),
                                   ([f"{n}_off_mhz" for n in EL], "freq minus radar (MHz)"), (["radar_f_mhz"], "radar freq (MHz)")]):
        ax = fig.add_subplot(gs[i])
        for k in ks:
            ax.plot(t, g(k), ".", ms=2, color=C_EL.get(k.split("_")[0], "#1f4e9c"), label=k)
        ax.set(ylabel=lab)
        ax.legend(fontsize=8, markerscale=4, loc="upper right")
        ax.grid(alpha=0.25)
    ax.set_xlabel("Time in the recording (s): gaps are when the racon was quiet or the radar beam was away")
    outs.append(save(fig, D, "vs_time"))

    fig, gs = A.fig_with_strip([1, 1, 0.7], (16, 20), left=0.2)
    for gi, v in enumerate(("long", "short")):
        ax = fig.add_subplot(gs[gi])
        ax.axis("off")
        vr = [r for r in rows if r["variant"] == v]
        cell = [[lab, u, f"{s['n']}", f"{s['mean']:.3f}", f"{s['sd']:.3f}", f"{s['min']:.3f}", f"{s['p5']:.3f}", f"{s['median']:.3f}", f"{s['p95']:.3f}", f"{s['max']:.3f}"]
                for k, lab, u in STAT_KEYS if (s := stat([r[k] for r in vr]))]
        if cell:
            tb = ax.table(cellText=cell, colLabels=["", "unit", "N", "mean", "sd", "min", "5 %", "median", "95 %", "max"], loc="upper center", cellLoc="right")
            tb.auto_set_font_size(False)
            tb.set_fontsize(8)
            tb.scale(1, 1.2)
        ax.set_title(f"{v} R: {len(vr)} replies ({100 * len(vr) / len(rows):.0f} %)", fontsize=10)
    ax = fig.add_subplot(gs[2])
    cc = D["codes"].most_common(10)
    ax.barh([c if c else "(none)" for c, _ in cc][::-1], [n for _, n in cc][::-1], color="0.5")
    ax.set(title="What every snippet with racon energy decoded to\n(fixed 17 us dot/dash split; partial = weak, faded or cut)", xlabel="count")
    ax.grid(alpha=0.25)
    outs.append(save(fig, D, "table"))
    return outs


def edge_curves(D, which):
    """Every reply's power around one edge, resampled 8x finer and lined up on that edge's own half-power crossing,
    divided by the element level (or the radar peak). which = (element index or 'radar', 'rise' or 'fall')."""
    R, fs = D["R"], D["R"]["fs"]
    ms = {m["k"]: m for m in D["ms"]}
    span = 0.6e-6 if which[0] == "radar" else 1.0e-6
    tau = np.arange(-span, span, 1 / fs / 8)
    out = []
    for row in D["rows"]:
        m = ms[row["snip"]]
        x = R["snips"][row["snip"]]
        p = x.real ** 2 + x.imag ** 2
        if which[0] == "radar":
            e = m["radar"]
            lev = 10 ** (e["peak_dbm"] / 10)
        else:
            e = m["els"][which[0]]
            lev = 10 ** (e["p_dbm"] / 10)
        c = e["i0"] if which[1] == "rise" else e["i1"]
        out.append((np.interp(c + tau * fs, np.arange(len(p)), p) - D["noise"]) / (lev - D["noise"]))   # noise power taken off
    return tau * 1e9, np.array(out)


def ten90(t, y):
    """10-90 % (or 90-10 %) time of a mean edge, linear interpolation."""
    rising = y[len(y) // 4] < y[3 * len(y) // 4]
    yy = y if rising else y[::-1]
    tt = t if rising else -t[::-1]
    sel = np.abs(tt) <= 300                       # only the edge itself, so the radar pulse before dot 1 does not count
    yy, tt = yy[sel], tt[sel]
    k = np.argmax(yy)
    yy, tt = np.maximum.accumulate(yy[:k + 1]), tt[:k + 1]
    t10, t90 = np.interp(0.1, yy, tt), np.interp(0.9, yy, tt)
    return abs(t90 - t10)


def plot_edges(D):
    if len(D["rows"]) < 5:
        return []
    fig, gs = A.fig_with_strip([1, 1], (16, 10))
    sub = gs[:-1].subgridspec(2, 4, hspace=0.5, wspace=0.25)
    edges = [(("radar", "rise"), "radar pulse rising"), (("radar", "fall"), "radar pulse falling"), ((0, "rise"), "dot 1 rising"), ((0, "fall"), "dot 1 falling"),
             ((1, "rise"), "dash rising"), ((1, "fall"), "dash falling"), ((2, "rise"), "dot 2 rising"), ((2, "fall"), "dot 2 falling")]
    res = {}
    for i, (w, lab) in enumerate(edges):
        t, Y = edge_curves(D, w)
        ax = fig.add_subplot(sub[i // 4, i % 4])
        for y in Y[np.linspace(0, len(Y) - 1, min(15, len(Y))).astype(int)]:
            ax.plot(t, y, lw=0.3, color="0.6", alpha=0.35)
        mu, sd = Y.mean(0), Y.std(0)
        ax.fill_between(t, mu - sd, mu + sd, color="tab:orange", alpha=0.35)
        ax.plot(t, mu, color="k", lw=1.3)
        r = ten90(t, mu)
        res[lab] = r
        ax.set_title(f"{lab}\n10-90 % {r:.0f} ns (mean of {len(Y)})", fontsize=9)
        ax.set(xlabel="ns from the half-power crossing", ylim=(-0.2, 1.6))
        ax.grid(alpha=0.25)
    bw = 41.5e6 if D["R"]["fs"] < 100e6 else 160e6
    fig.text(0.07, 0.948, f"Replies lined up on each edge's half-power crossing, 8x resampled, noise subtracted; black mean, orange +-1 sd, grey 15 replies. "
             f"{1e9 / D['R']['fs']:.0f} ns samples; {bw / 1e6:g} MHz bandwidth alone limits 10-90 % to about {0.35 / bw * 1e9:.0f} ns.", fontsize=8)
    D["edges_ns"] = res
    return [save(fig, D, "edges")]


def plot_bursts(D):
    """Zoom on the busiest bursts: racon and radar absolute frequency, offset, delay and reply version, reply by reply."""
    rows = D["rows"]
    if len(rows) < 20:
        return []
    t = np.array([r["t_s"] for r in rows])
    groups = np.split(np.arange(len(t)), np.flatnonzero(np.diff(t) > 1.0) + 1)
    groups = sorted(sorted(groups, key=len, reverse=True)[:3], key=lambda g: t[g[0]])
    fig, gs = A.fig_with_strip([1, 1, 1], (16, 14))
    sub = gs[:-1].subgridspec(3, len(groups), hspace=0.45, wspace=0.25)
    for j, g in enumerate(groups):
        rr = [rows[i] for i in g]
        tt = np.array([r["t_s"] for r in rr]) - rr[0]["t_s"]
        a, b, c = (fig.add_subplot(sub[i, j]) for i in range(3))
        a.plot(tt, [r["radar_f_mhz"] for r in rr], ".", ms=3, color="#1f4e9c", label="radar pulse")
        for v in ("long", "short"):
            sel = [i for i, r in enumerate(rr) if r["variant"] == v]
            a.plot(tt[sel], [rr[i]["dash_f_mhz"] for i in sel], "o", ms=3, mfc="none", color=VCOL[v], label=f"racon dash, {v} R")
            b.plot(tt[sel], [rr[i]["dash_off_mhz"] for i in sel], "o", ms=3, mfc="none", color=VCOL[v])
            c.plot(tt[sel], [rr[i]["delay_us"] for i in sel], "o", ms=3, mfc="none", color=VCOL[v])
        a.set(title=f"burst at {rr[0]['t_s']:.1f} s: {len(rr)} replies over {tt[-1]:.2f} s", ylabel="MHz")
        b.set(ylabel="racon minus radar (MHz)")
        c.set(ylabel="delay (us)", xlabel="seconds into the burst")
        if j == 0:
            a.legend(fontsize=7, markerscale=2)
        for ax in (a, b, c):
            ax.grid(alpha=0.25)
    return [save(fig, D, "bursts")]


# ------------------------------------------------------------------------------------------------------------------ across recordings
def combined_strip():
    Z.apply(S, "20261109_215716")
    S.CHAIN = [("Vivaldi R120 (21:35-21:50)\nor horn (21:57, 22:24)", 0.0, "")] + S.CHAIN[1:-1] + [("SM200B\nI/Q 50 or 250 MS/s", 0.0, "")]
    S.SOURCES = ["Furuno 1722C/NT radar\n40 ft (12.2 m)", "SeaBeacon 2 racon\n23 ft (7.0 m)"]
    S.CHAIN_DATE = "9 Nov, triangle setup, every recording with racon replies"


def plot_all(Ds):
    Ds = [D for D in Ds if D["rows"]]
    if not Ds:
        return []
    outs = []
    combined_strip()
    cols = plt.cm.tab10(np.arange(len(Ds)))
    fig, gs = A.fig_with_strip([1, 1, 1], (16, 14))
    sub = gs[:-1].subgridspec(3, 4, hspace=0.7, wspace=0.35)
    keys = [k for k, _, _ in STAT_KEYS][:12]
    for i, k in enumerate(keys):
        ax = fig.add_subplot(sub[i // 4, i % 4])
        for j, D in enumerate(Ds):
            for v, dx, mk in (("long", -0.15, "o"), ("short", 0.15, "s")):
                s = stat([r[k] for r in D["rows"] if r["variant"] == v])
                if not s:
                    continue
                ax.errorbar(j + dx, s["median"], yerr=s["sd"], fmt=mk, color=cols[j], capsize=3, ms=5, mfc="white" if v == "short" else cols[j])
                ax.plot([j + dx, j + dx], [s["p5"], s["p95"]], color=cols[j], lw=0.6, alpha=0.6)
        ax.set_xticks(range(len(Ds)), [SHORT.get(D["rec"], D["rec"]) for D in Ds], rotation=35, ha="right", fontsize=7)
        lab = dict((a, b) for a, b, _ in STAT_KEYS)[k]
        ax.set_title(lab + f" ({dict((a, c) for a, _, c in STAT_KEYS)[k]})", fontsize=9)
        ax.grid(alpha=0.25)
    fig.text(0.07, 0.955, "Each recording, long R (filled circle, left) and short R (open square, right): marker = median, bar = +-1 sd, thin line = 5-95 %", fontsize=9)
    fig.suptitle("Racon reply across recordings: is the timing and frequency the same every time?", fontsize=10)
    out = PLOTS / "racon_all_compare.png"
    fig.savefig(out, dpi=105)
    plt.close(fig)
    outs.append(out)

    fig, gs = A.fig_with_strip([1.3, 1], (15, 12))
    ax = fig.add_subplot(gs[0])
    X, Y = [], []
    for j, D in enumerate(Ds):
        x, y = [r["radar_f_mhz"] for r in D["rows"]], [r["dash_f_mhz"] for r in D["rows"]]
        ax.scatter(x, y, s=3, alpha=0.4, color=cols[j], label=SHORT.get(D["rec"], D["rec"]))
        X += x
        Y += y
    c = np.polyfit(X, Y, 1)
    xx = np.linspace(min(X), max(X), 2)
    ax.plot(xx, np.polyval(c, xx), "k-", lw=1.2, label=f"fit: racon = {c[0]:.3f} x radar {c[1]:+.1f}")
    ax.plot(xx, xx + np.median(np.array(Y) - np.array(X)), "k:", lw=1, label="slope 1 through the median offset")
    ax.set(xlabel="Radar frequency of the triggering pulse (MHz)", ylabel="Racon dash frequency (MHz)",
           title="Racon frequency against the radar frequency, every full R from every recording")
    ax.legend(fontsize=8, markerscale=4)
    ax.grid(alpha=0.25)
    ax = fig.add_subplot(gs[1])
    for j, D in enumerate(Ds):
        ax.hist([r["dash_off_mhz"] for r in D["rows"]], bins=80, histtype="step", color=cols[j], lw=1.2, density=True,
                label=SHORT.get(D["rec"], D["rec"]))
    ax.set(xlabel="Dash frequency minus radar (MHz)", ylabel="density", title="Racon offset above the radar, per recording")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    out = PLOTS / "racon_all_tracking.png"
    fig.savefig(out, dpi=105)
    plt.close(fig)
    outs.append(out)

    fig, gs = A.fig_with_strip([1, 1], (16, 11))
    sub = gs[:-1].subgridspec(2, 4, hspace=0.6, wspace=0.3)
    for i, k in enumerate(["delay_us", "dot1_us", "gap1_us", "dash_us", "gap2_us", "dot2_us", "total_us", "drift_dot1_to_dot2_mhz"]):
        ax = fig.add_subplot(sub[i // 4, i % 4])
        allv = np.concatenate([[r[k] for r in D["rows"]] for D in Ds])
        bins = np.linspace(np.percentile(allv, 0.5), np.percentile(allv, 99.5), 70)
        ax.hist([[r[k] for r in D["rows"]] for D in Ds], bins=bins, stacked=True, color=cols[:len(Ds)],
                label=[SHORT.get(D["rec"], D["rec"]) for D in Ds])
        ax.set_title(f"{dict((a, b) for a, b, _ in STAT_KEYS)[k]}\nall: {allv.mean():.3f} +- {allv.std(ddof=1):.3f} (N {len(allv)})", fontsize=9)
        ax.grid(alpha=0.25)
        if i == 0:
            ax.legend(fontsize=7)
    fig.suptitle("All full R replies pooled, stacked by recording", fontsize=10)
    out = PLOTS / "racon_all_hist.png"
    fig.savefig(out, dpi=105)
    plt.close(fig)
    outs.append(out)

    summ = {}
    with open(DATA / "racon_stats_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["recording", "quantity", "unit", "n", "mean", "sd", "min", "p5", "median", "p95", "max"])
        pooled = [r for D in Ds for r in D["rows"]]
        groups = [dict(rec=f"{D['rec']} {v}", rows=[r for r in D["rows"] if r["variant"] == v]) for D in Ds for v in ("long", "short")]
        for D in Ds + groups + [dict(rec="ALL", rows=pooled)] + [dict(rec=f"ALL {v}", rows=[r for r in pooled if r["variant"] == v]) for v in ("long", "short")]:
            summ[D["rec"]] = {}
            for k, lab, u in STAT_KEYS:
                s = stat([r[k] for r in D["rows"]])
                if s:
                    summ[D["rec"]][k] = s
                    w.writerow([D["rec"], lab, u] + [round(s[x], 4) for x in ("n", "mean", "sd", "min", "p5", "median", "p95", "max")])
    (DATA / "racon_stats_summary.json").write_text(json.dumps(summ, indent=1))
    return outs


def plot_radar_all(Ds):
    combined_strip()
    S.CHAIN[0] = ("Vivaldi R120 or horn\n(per recording)", 0.0, "")
    S.CHAIN_DATE = "9 Nov, every recording (far setup 21:19-21:22, triangle after)"
    fig, gs = A.fig_with_strip([1, 1], (15, 11))
    sub = gs[:-1].subgridspec(2, 2, hspace=0.45, wspace=0.25)
    cols = plt.cm.tab20(np.arange(len(Ds)))
    a, b, c, d = (fig.add_subplot(sub[i // 2, i % 2]) for i in range(4))
    for j, D in enumerate(Ds):
        if not D["rad"]:
            continue
        lab = D["rec"]
        t = [r["t_s"] for r in D["rad"]]
        a.hist([r["dur_us"] for r in D["rad"]], bins=np.linspace(0.4, 1.0, 61), histtype="step", color=cols[j], label=lab, density=True)
        b.boxplot([[r["f_mhz"] for r in D["rad"]]], positions=[j], widths=0.6, showfliers=False)
        c.plot(t, [r["peak_dbm"] for r in D["rad"]], ".", ms=1.5, color=cols[j])
        d.plot(np.full(len(t), j) + np.random.uniform(-0.3, 0.3, len(t)), [r["dur_us"] for r in D["rad"]], ".", ms=1, color=cols[j], alpha=0.4)
    a.set(xlabel="Radar pulse length, half power (us)", ylabel="density", title="Radar pulse length per recording")
    a.legend(fontsize=6, ncol=2)
    b.set_xticks(range(len(Ds)), [D["rec"][-6:] for D in Ds], rotation=45, fontsize=7)
    b.set(ylabel="MHz", title="Radar frequency per recording (box = 25-75 %, whiskers 5-95 %): it wanders by MHz over the evening")
    c.set(xlabel="time in each recording (s)", ylabel="dBm at SM200B", title="Pulse peak level vs time (beam sweeps, every recording overlaid)")
    d.set_xticks(range(len(Ds)), [D["rec"][-6:] for D in Ds], rotation=45, fontsize=7)
    d.set(ylabel="us", title="Every pulse length")
    for ax in (a, b, c, d):
        ax.grid(alpha=0.25)
    fig.suptitle("Furuno radar pulses in every 9 Nov recording", fontsize=10)
    out = PLOTS / "radar_all_9nov.png"
    fig.savefig(out, dpi=105)
    plt.close(fig)
    return [out]


def plot_sweeps():
    outs = []
    bands = [("9to10", "9-10 GHz", None), ("harm2", "18.6-19.0 GHz: 2nd harmonic of the radar", None), ("wide", "0.1-20 GHz", None)]
    for b, title, _ in bands:
        files = {who: sorted(DATA.glob(f"survey_horn_{who}_{b}_*/survey.npz")) for who in ("radar", "racon")}
        if not all(files.values()):
            continue
        Z.apply(S, f"horn_racon_{b}")
        S.CHAIN = [("horn antenna\naimed at the radar, then at the racon", 0.0, "")] + S.CHAIN[1:]
        S.SOURCES = ["Furuno 1722C/NT radar\n40 ft (12.2 m)", "SeaBeacon 2 racon\n23 ft (7.0 m)"]
        S.CHAIN_DATE = f"9 Nov 22:10-22:21, both sources on, sweeps {title.split(':')[0]}"
        fig, gs = A.fig_with_strip([1.2, 1, 1], (15, 14))
        a = fig.add_subplot(gs[0])
        res = {}
        for (who, fl), col in zip(files.items(), ("#1f4e9c", "#c06000")):
            d = np.load(fl[-1])
            f, W = d["f"] / 1e6, d["W"].astype(np.float32)
            W[W > 30] = np.nan
            hold, med = np.nanmax(W, 0), np.nanmedian(W, 0)
            res[who] = (f, W, hold, d["t"])
            a.plot(f, hold, lw=0.6, color=col, label=f"horn at the {who}: max hold of {len(W)} sweeps")
            a.plot(f, med, lw=0.4, color=col, alpha=0.4, label=f"horn at the {who}: median")
            i = int(np.nanargmax(hold))
            a.annotate(f"{f[i]:.2f} MHz {hold[i]:+.1f} dBm", (f[i], hold[i]), xytext=(8, -12 if who == "racon" else 4), textcoords="offset points",
                       fontsize=8, color=col)
        if b == "harm2":
            for who, col in (("radar", "#1f4e9c"), ("racon", "#c06000")):
                for x in sorted(DATA.glob(f"survey_horn_{who}_9to10_*/survey.npz"))[-1:]:
                    d = np.load(x)
                    W = d["W"].astype(np.float32)
                    W[W > 30] = np.nan
                    h = np.nanmax(W, 0)
                    f1 = d["f"][int(np.nanargmax(h))] / 1e6
                    a.axvline(2 * f1, color=col, ls=":", lw=1, label=f"2 x the strongest line at {f1:.2f} MHz (horn at the {who})")
        a.set(xlabel="MHz", ylabel="dBm at SM200B", title=f"Sweep {title}, 100 kHz RBW, min/max detector. Chain loss at 18.8 GHz NOT known: levels are at the SM200B only")
        a.legend(fontsize=7)
        a.grid(alpha=0.25)
        for ax_i, who in ((1, "radar"), (2, "racon")):
            f, W, _, t = res[who]
            ax = fig.add_subplot(gs[ax_i])
            dec = max(1, W.shape[1] // 4000)
            Wd = W[:, :W.shape[1] // dec * dec].reshape(len(W), -1, dec).max(2)
            im = ax.imshow(Wd, aspect="auto", origin="lower", extent=[f[0], f[-1], t[0], t[-1]], cmap="magma",
                           vmin=np.nanpercentile(Wd, 50), vmax=np.nanmax(Wd), interpolation="nearest")
            fig.colorbar(im, ax=ax, pad=0.01, label="dBm at SM200B")
            ax.set(ylabel="s", xlabel="MHz", title=f"Every sweep, horn aimed at the {who}")
        fig.suptitle(f"Sweeps {title}", fontsize=10)
        out = PLOTS / f"sweeps_{b}.png"
        fig.savefig(out, dpi=105)
        plt.close(fig)
        outs.append(out)
    return outs


if __name__ == "__main__":
    recs = sys.argv[1:] or RECS
    Ds, outs = [], []
    for rec in recs:
        D = process(rec)
        Z.apply(S, rec)
        outs += plot_stacks(D) + plot_radar_stack(D) + plot_stats(D) + plot_bursts(D) + plot_edges(D)
        Ds.append(dict((k, D[k]) for k in ("rec", "rows", "rad", "codes")))
        Ds[-1]["edges_ns"] = D.get("edges_ns")
        del D
    if len(recs) > 1:
        outs += plot_all(Ds) + plot_radar_all(Ds) + plot_sweeps()
        with open(DATA / "racon_stats_codes.json", "w") as fh:
            json.dump({D["rec"]: dict(D["codes"]) for D in Ds}, fh, indent=1)
        with open(DATA / "racon_stats_edges.json", "w") as fh:
            json.dump({D["rec"]: D["edges_ns"] for D in Ds if D.get("edges_ns")}, fh, indent=1)
    print("\n".join(str(o) for o in outs))
