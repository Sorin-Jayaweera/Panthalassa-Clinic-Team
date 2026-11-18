"""Which interferometer arm is the best engineering choice: cable C (no pads), cable E with pads, or cable E without pads?

The question (Sorin, 15 Nov): measure a voltage, add a small uncertainty dV; what frequency uncertainty does that give, when the
input power is NOT known but lies somewhere in the usable range? Also: how linear, how smooth, how wide is the one-to-one range,
and how far do the power levels spread.

Method, for each setup:
  1. Calibration curve = the mean of the power levels at each frequency (the one table the FPGA would hold).
  2. One-to-one region = the longest stretch where that curve keeps one direction with slope above 0.15 mV/MHz; for the two
     no-pads runs the steep rising edge 1340-1480 MHz is used instead (the automatic pick is the shallower 960-1135 MHz edge).
  3. For every true frequency f in it, every power level w, and a reading off by +/- dV: invert the calibration curve and take the
     worst |f_estimated - f|. That is the frequency error with unknown power and reading uncertainty dV.
  4. Usable width = the longest contiguous stretch where that worst error is <= 1 MHz and <= 2 MHz.
  5. Linearity: straight-line fit over the one-to-one region; residual in MHz. Smoothness: residual from a 15 MHz running
     line fit, in MHz (wiggles and steps that a smooth calibration would miss).
Data (each setup its own run; nothing is overlaid across runs):
  C:            p162x4_fine_1nov.csv, 900-1200 MHz every 1 MHz, levels -36/-40/-50/-60 dBm (no dither).
  E, pads:      pd_dither_14nov.csv stages bisect5/bisect5s, 1150-1550 MHz, 1.6-6.25 MHz steps, -36/-43/-50/-57 dBm (dithered).
  E, no pads:   pd_dither_14nov.csv stages hdr_pri/hdr_rest (15 Nov night, long IF cable) and ifs_pri/ifs_rest (short IF cable),
                600-1600 MHz, 0.6-10 MHz steps, -36/-50/-57 dBm (no dither).
Saves pd_resolution_compare.png and prints a table."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import pd_runs as R
import wiring

HERE = Path(__file__).resolve().parent
DVS = (0.5, 1.0, 2.0)          # reading uncertainty at the detector output (mV)
MAIN_DV = 1.0


def rd(name):
    return list(csv.DictReader(open(HERE / name)))


def curves(rows, levels):
    """{level: {f: mV}} keeping the first reading at each frequency."""
    out = {w: {} for w in levels}
    for f, w, v in rows:
        if w in out and f > 0:
            out[w].setdefault(f, v)
    grid = sorted(set.intersection(*[set(d) for d in out.values()]))
    return np.array(grid), np.array([[out[w][f] for f in grid] for w in levels])


def local_slope(f, v, half):
    return np.array([np.polyfit(f[(f >= x - half) & (f <= x + half)], v[(f >= x - half) & (f <= x + half)], 1)[0]
                     if np.sum((f >= x - half) & (f <= x + half)) >= 3 else np.nan for x in f])


def one_to_one(f, cal, half):
    s = local_slope(f, cal, half)
    best = (0, 0, 0, 1)
    for sg in (1, -1):
        ok = sg * s > 0.15
        i = 0
        while i < len(f):
            if ok[i]:
                j = i
                while j + 1 < len(f) and ok[j + 1] and sg * (cal[j + 1] - cal[j]) > -0.5:
                    j += 1
                if f[j] - f[i] > best[0]:
                    best = (f[j] - f[i], i, j, sg)
                i = j + 1
            else:
                i += 1
    return best


def worst_error(f, V, cal, i, j, sg, dv):
    """Worst |f_est - f| over levels and +/- dv, inverting the calibration curve on [i, j]."""
    fs, cs = f[i:j + 1], cal[i:j + 1]
    if sg < 0:
        fs, cs = fs[::-1], cs[::-1]
    cs = np.maximum.accumulate(cs)            # strictly usable as a lookup
    err = np.full(j - i + 1, np.nan)
    for k in range(i, j + 1):
        e = 0.0
        for v in V[:, k]:
            for x in (v - dv, v + dv):
                if x < cs[0] or x > cs[-1]:
                    e = np.inf
                else:
                    e = max(e, abs(np.interp(x, cs, fs) - f[k]))
        err[k - i] = e
    return err


def longest(f, ok):
    best, i = (0.0, np.nan, np.nan), 0
    while i < len(f):
        if ok[i]:
            j = i
            while j + 1 < len(f) and ok[j + 1]:
                j += 1
            if f[j] - f[i] > best[0]:
                best = (f[j] - f[i], f[i], f[j])
            i = j + 1
        else:
            i += 1
    return best


def setups():
    S = []
    C = [(float(r["freq_mhz"]), float(r["pluto_want_dbm"]), float(r["detector_mean_v"]) * 1e3) for r in rd("p162x4_fine_1nov.csv")]
    S.append(("Cable C, no pads (1 Nov)", (-36.0, -40.0, -50.0, -60.0), C, "#7570b3", setup_wiring("C", False, "0.1-0.2 V/div, no dither"), None))
    D = rd("pd_dither_14nov.csv")
    EP = [(float(r["freq_mhz"]), float(r["pluto_want_dbm"]), float(r["detector_mean_v"]) * 1e3) for r in D if r["stage"] in ("bisect5", "bisect5s")]
    S.append(("Cable E with pads (14 Nov)", (-36.0, -43.0, -50.0, -57.0), EP, "#1b9e77", setup_wiring("E", True, "50 mV/div, dithered"), None))
    for r in R.present(D):
        S.append((f"No pads, {r['desc']} ({r['day']})", R.LEVELS, [(float(x["freq_mhz"]), float(x["pluto_want_dbm"]), float(x["detector_mean_v"]) * 1e3)
                  for x in D if x["stage"] in (f"{r['tag']}_pri", f"{r['tag']}_rest")], r["col"], R.wiring_for(r), r["region"]))
    return S


def setup_wiring(arm, pads, scope):
    lo, rf = ("3 dB pad at the LO port", "6 dB pad at the RF port") if pads else ("no pad", "no pad")
    return ["Pluto TX", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", [f"right arm (LO): cable D\n{lo}", f"left arm (RF): cable B + {arm}\n{rf}"],
            "ZX05-30W-S+", [f"SDS1104X-E CH1\n{scope}"]]


def main():
    S = [s for s in setups() if len(s[2])]
    fig, AX = wiring.figure(4 * len(S), [s[4] for s in S], size=(15, 13 * len(S)),
                            titles=[f"Wiring, {s[0]}" for s in S], strip=0.12)
    table = []
    for n, (name, levels, rows, col, _, region) in enumerate(S):
        ax = AX[4 * n:4 * n + 4]
        f, V = curves(rows, levels)
        if len(f) < 10:
            continue
        cal = V.mean(axis=0)
        half = max(5.0, 3 * np.median(np.diff(f)))
        span, i, j, sg = one_to_one(f, cal, half)
        if region:      # the steep rising edge, chosen by hand: the automatic pick lands on the shallower 960-1135 MHz edge
            idx = np.where((f >= region[0]) & (f <= region[1]))[0]
            i, j = idx[0], idx[-1]
            sg = 1 if cal[j] > cal[i] else -1
            span = f[j] - f[i]
        lo, hi = f[i], f[j]
        cm = plt.cm.viridis(np.linspace(0, 0.85, len(levels)))
        for w, v, c in zip(levels, V, cm):
            ax[0].plot(f, v, "-", lw=1.1, color=c, label=f"{w:.0f} dBm")
        ax[0].axvspan(lo, hi, color=col, alpha=0.1, label=f"one-to-one {lo:.0f}-{hi:.0f} MHz ({span:.0f} MHz)")
        ax[0].set(ylabel="detector (mV, raw)", title=f"{name}: every level, full range of this run ({len(f)} frequencies per level)")
        m = (f >= lo) & (f <= hi)
        for w, v, c in zip(levels, V, cm):
            ax[1].plot(f[m], v[m], "-o", ms=2, lw=1.1, color=c, label=f"{w:.0f} dBm")
        k = np.polyfit(f[m], cal[m], 1)
        res_lin = (cal[m] - np.polyval(k, f[m])) / k[0]
        sm = np.array([np.polyval(np.polyfit(f[m][np.abs(f[m] - x) <= 7.5], cal[m][np.abs(f[m] - x) <= 7.5], 1), x) if np.sum(np.abs(f[m] - x) <= 7.5) >= 3 else np.nan for x in f[m]])
        sl = local_slope(f[m], cal[m], half)
        res_smooth = (cal[m] - sm) / np.abs(np.nanmedian(sl))
        ax[1].set(ylabel="detector (mV, raw)", title=f"{name}: zoom on the one-to-one region; straight line off by {np.std(res_lin):.1f} MHz rms, "
                                                     f"slope {np.nanpercentile(np.abs(sl), 10):.2f}-{np.nanpercentile(np.abs(sl), 90):.2f} mV/MHz")
        spread = (V[:, m].max(axis=0) - V[:, m].min(axis=0))
        ax[2].plot(f[m], spread / np.abs(sl), "-", color="k", lw=1.0, label="power-level spread / slope (no reading error)")
        row = [name, f"{lo:.0f}-{hi:.0f} ({span:.0f})", f"{np.nanmedian(np.abs(sl)):.2f}", f"{np.median(spread):.1f}", f"{np.std(res_lin):.1f}", f"{np.nanstd(res_smooth):.2f}"]
        for dv, ls in zip(DVS, (":", "-", "--")):
            e = worst_error(f, V, cal, i, j, sg, dv)
            ax[2].plot(f[m], np.where(np.isfinite(e), e, np.nan), ls, color=col, lw=1.4, label=f"worst error, reading +/- {dv:g} mV")
            for lim in (1.0, 2.0):
                w_, a_, b_ = longest(f[m], e <= lim)
                row.append(f"{w_:.0f}" + (f" ({a_:.0f}-{b_:.0f})" if w_ > 0 else ""))
        if -36.0 in levels and len(levels) > 2:
            keep = np.array([w != -36.0 for w in levels])
            cal2 = V[keep].mean(axis=0)
            e2 = worst_error(f, V[keep], cal2, i, j, sg, 0.5)
            ax[2].plot(f[m], np.where(np.isfinite(e2), e2, np.nan), "-", color="#888888", lw=1.2, label="worst error, +/- 0.5 mV, -36 dBm left out")
            row.append(f"{longest(f[m], e2 <= 1)[0]:.0f}/{longest(f[m], e2 <= 2)[0]:.0f}")
        else:
            row.append("-")
        table.append(row)
        ax[2].axhspan(0, 1, color="#1b9e77", alpha=0.10, label="<= 1 MHz")
        ax[2].axhspan(1, 2, color="#e6ab02", alpha=0.10, label="1-2 MHz")
        ax[2].set(ylim=(0, 10), ylabel="frequency error (MHz)",
                  title=f"{name}: worst frequency error with the power unknown ({levels[0]:.0f} to {levels[-1]:.0f} dBm) and the reading off by dV")
        ax[3].plot(f[m], res_lin, "-", color=col, lw=1.2, label="calibration curve minus a straight line (linearity)")
        ax[3].plot(f[m], res_smooth, "-", color="k", lw=0.9, label="calibration curve minus a 15 MHz running line (smoothness)")
        ax[3].axhline(0, color="k", lw=0.6)
        ax[3].set(ylabel="MHz", title=f"{name}: linearity and smoothness in MHz")
        for a in ax:
            a.grid(alpha=0.3)
            a.legend(fontsize=7, ncol=4)
            a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    fig.savefig(HERE / "pd_resolution_compare.png", dpi=85)
    head = ["setup", "one-to-one MHz", "median slope mV/MHz", "median level spread mV", "straight-line rms MHz", "smoothness rms MHz"] + \
           [f"width err<={l:g} MHz at dV={d:g} mV" for d in DVS for l in (1, 2)] + ["without -36 dBm, dV=0.5: width err<=1/<=2"]
    print(" | ".join(head))
    for r in table:
        print(" | ".join(r))


if __name__ == "__main__":
    main()
