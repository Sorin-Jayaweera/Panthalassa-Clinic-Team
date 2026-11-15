"""14 Nov final run: five Pluto levels (-36 = Pluto top, -43, -50, -57, -64 dBm), 1150-1550 MHz, interleaved at each frequency
(all five levels read back to back, so slow drift moves them together). Pass 1 every 2 MHz; pass 2 fills the odd MHz of the rise.
Shows the flat part below the rise, the rise and the flat part above, the slope, and the frequency error each level causes.
Saves pd_sweep5_14nov.png and prints the error statistics."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
ALL = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
S5 = [r for r in ALL if r["stage"] == "sweep5"]
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
REF = -50.0
RISE = (1240.0, 1430.0)
WIRING = [["Pluto TX\n-36 to -64 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.26 A", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", "20 dB of pads\nthen SM200B (not read)"]]]
WT = ["Wiring, 14 Nov afternoon (as in the sections above; amplifiers drawing 0.26 A since the 15:18 restart)"]


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def zero():
    v = [mv(r) for r in ALL if r["stage"] == "off" and r["rep"] in ("21", "22", "23")]
    return float(np.median(v)), (float(np.min(v)), float(np.max(v))) if v else (0, 0)


def curve(w):
    a = sorted((float(r["freq_mhz"]), mv(r)) for r in S5 if float(r["pluto_want_dbm"]) == w)
    return np.array(a) if a else np.zeros((0, 2))


def slope(f, v, half=6):
    return np.array([np.polyfit(f[(f >= x - half) & (f <= x + half)], v[(f >= x - half) & (f <= x + half)], 1)[0]
                     if np.sum((f >= x - half) & (f <= x + half)) >= 3 else np.nan for x in f])


def main():
    z, zr = zero()
    C = {w: curve(w) for w in L5}
    C = {w: c for w, c in C.items() if len(c)}
    ref = C[REF]
    rf, rv = ref[:, 0], ref[:, 1] - z
    sl = slope(rf, rv)
    cm = plt.cm.viridis(np.linspace(0, 0.9, len(L5)))
    col = dict(zip(L5, cm))

    fig, ax = wiring.figure(5, WIRING, size=(14, 24), titles=WT)
    for w, c in C.items():
        ax[0].plot(c[:, 0], c[:, 1] - z, "-", color=col[w], lw=1.2, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else ""))
    ax[0].set(xlim=(1145, 1555), ylabel="detector minus tone-off (mV)",
              title=f"Five Pluto levels, 1150-1550 MHz, dithered; tone-off reading {z:.1f} mV subtracted (range {zr[0]:.1f} to {zr[1]:.1f} mV over the run)")
    ax[0].legend(fontsize=8, ncol=5)
    for w, c in C.items():
        ax[1].plot(c[:, 0], c[:, 1] - z, "-o", color=col[w], ms=2, lw=1.0, label=f"{w:.0f} dBm")
    ax[1].set(xlim=(1200, 1480), ylabel="detector minus tone-off (mV)", title="The rise and its two ends, 1200-1480 MHz (1 MHz steps in 1220-1450 once pass 2 is in)")
    ax[1].legend(fontsize=8, ncol=5)
    ax[2].plot(rf, sl, color=col[REF], lw=1.2)
    ax[2].axhline(0, color="k", lw=0.8)
    g = (rf >= RISE[0]) & (rf <= RISE[1])
    ttl = "Slope of the -50 dBm curve (line fit over 13 MHz)"
    if g.any():
        ttl += f": {np.nanmin(sl[g]):.2f} to {np.nanmax(sl[g]):.2f}, median {np.nanmedian(sl[g]):.2f} mV/MHz in {RISE[0]:.0f}-{RISE[1]:.0f} MHz"
    ax[2].set(xlim=(1145, 1555), ylabel="slope (mV per MHz)", title=ttl)
    for w, c in C.items():
        if w == REF:
            continue
        d = np.array([(f, v - z - rv[rf == f][0]) for f, v in c if np.any(rf == f)])
        if len(d):
            ax[3].plot(d[:, 0], d[:, 1], "-", color=col[w], lw=1.1, label=f"{w:.0f} dBm")
            s = np.interp(d[:, 0], rf, sl)
            ax[4].plot(d[:, 0], np.where(s > 0.15, d[:, 1] / s, np.nan), "-o", color=col[w], ms=2, lw=1.1, label=f"{w:.0f} dBm")
    ax[3].axhline(0, color="k", lw=0.8)
    ax[3].set(xlim=(1145, 1555), ylabel="minus the -50 dBm reading (mV)", title="Each level minus the -50 dBm level at the same frequency (read seconds apart)")
    ax[3].legend(fontsize=8, ncol=4)
    ax[4].axhspan(-2, 2, color="#1b9e77", alpha=0.12, label="+/- 2 MHz")
    ax[4].axhline(0, color="k", lw=0.8)
    ax[4].set(xlim=(1215, 1457), ylim=(-15, 15), ylabel="frequency error (MHz)",
              title="Frequency error from input power alone: (level - -50 dBm) / slope; left out where the slope is under 0.15 mV/MHz")
    ax[4].legend(fontsize=8, ncol=5)
    for a in ax[:5]:
        a.grid(alpha=0.3)
        a.set_xlabel("Pluto frequency (MHz)")
    for a in (ax[1], ax[4]):
        a.axvspan(*RISE, color="#1b9e77", alpha=0.05)
    fig.tight_layout()
    out = HERE / "pd_sweep5_14nov.png"
    fig.savefig(out, dpi=95)
    print(out)

    # statistics on the common grid inside the rise
    print(f"points per level: " + ", ".join(f"{w:.0f}: {len(c)}" for w, c in C.items()))
    grid = rf[g]
    E = {}
    for w, c in C.items():
        v = np.array([c[c[:, 0] == f, 1][0] - z if np.any(c[:, 0] == f) else np.nan for f in grid])
        s = sl[g]
        E[w] = np.where(s > 0.15, (v - rv[g]) / s, np.nan)
    for sel in ((-36.0, -43.0, -50.0, -57.0, -64.0), (-36.0, -43.0, -50.0, -57.0), (-43.0, -50.0, -57.0)):
        k = [w for w in sel if w in E]
        M = np.array([E[w] for w in k])
        span = np.nanmax(M, axis=0) - np.nanmin(M, axis=0)
        ok = span <= 4
        runs, st = [], None
        for f, o in zip(grid, ok):
            if o and st is None:
                st = f
            if not o and st is not None:
                runs.append((st, prev)); st = None
            prev = f
        if st is not None:
            runs.append((st, prev))
        print(f"levels {k}: peak-to-peak best {np.nanmin(span):.2f} MHz at {grid[np.nanargmin(span)]:.0f}, worst {np.nanmax(span):.2f} at {grid[np.nanargmax(span)]:.0f}, "
              f"median {np.nanmedian(span):.2f}; within +/-2 MHz: " + ", ".join(f"{a:.0f}-{b:.0f}" for a, b in runs))
    for w in E:
        print(f"{w:.0f} dBm: mean error {np.nanmean(E[w]):+.2f} MHz, min {np.nanmin(E[w]):+.2f}, max {np.nanmax(E[w]):+.2f}")
    for lo, hi in ((1150, 1220), (1450, 1550)):
        for w, c in C.items():
            m = (c[:, 0] >= lo) & (c[:, 0] <= hi)
            if m.any():
                print(f"flat {lo}-{hi} MHz, {w:.0f} dBm: {np.min(c[m, 1] - z):.1f} to {np.max(c[m, 1] - z):.1f} mV")


if __name__ == "__main__":
    main()
