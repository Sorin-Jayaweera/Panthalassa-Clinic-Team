"""14 Nov final run: five Pluto levels (-36 = Pluto top, -43, -50, -57, -64 dBm), 1150-1550 MHz, interleaved at each frequency
(all five levels read back to back, so slow drift moves them together). Pass 1 every 2 MHz; pass 2 fills the odd MHz of the rise.
Shows the flat part below the rise, the rise and the flat part above, the slope, and the frequency error each level causes.
Saves pd_sweep5_14nov.png and prints the error statistics."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, L5, chain, colours, fv, mv, rows, runs, slope

ALL = rows("pd_dither_14nov.csv")
S5 = [r for r in ALL if r["stage"] == "sweep5"]
REF, RISE = -50.0, (1240.0, 1430.0)
WIRING = [chain("-36 to -64 dBm", "4.03 V, 0.26 A", scope=", 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", sm="20 dB of pads\nthen SM200B (not read)")]
WT = ["Wiring, 14 Nov afternoon (as in the sections above; amplifiers drawing 0.26 A since the 15:18 restart)"]


def main():
    v0 = [mv(r) for r in ALL if r["stage"] == "off" and r["rep"] in ("21", "22", "23")]
    z, zr = float(np.median(v0)), (min(v0), max(v0))
    C = {w: c for w in L5 if (c := fv([r for r in S5 if float(r["pluto_want_dbm"]) == w]) - [[0], [z]]).size}
    rf, rv = C[REF]
    sl = slope(rf, rv, 6, nmin=3)
    col = colours(L5)
    on = lambda c, grid: np.array([c[1][c[0] == f][0] if np.any(c[0] == f) else np.nan for f in grid])

    fig, ax = wiring.figure(5, WIRING, size=(14, 24), titles=WT)
    for w, c in C.items():
        ax[0].plot(*c, "-", color=col[w], lw=1.2, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else ""))
        ax[1].plot(*c, "-o", color=col[w], ms=2, lw=1.0, label=f"{w:.0f} dBm")
    ax[0].set(xlim=(1145, 1555), ylabel="detector minus tone-off (mV)",
              title=f"Five Pluto levels, 1150-1550 MHz, dithered; tone-off reading {z:.1f} mV subtracted (range {zr[0]:.1f} to {zr[1]:.1f} mV over the run)")
    ax[1].set(xlim=(1200, 1480), ylabel="detector minus tone-off (mV)", title="The rise and its two ends, 1200-1480 MHz (1 MHz steps in 1220-1450 once pass 2 is in)")
    ax[2].plot(rf, sl, color=col[REF], lw=1.2)
    ax[2].axhline(0, color="k", lw=0.8)
    g = (rf >= RISE[0]) & (rf <= RISE[1])
    ttl = "Slope of the -50 dBm curve (line fit over 13 MHz)"
    if g.any():
        ttl += f": {np.nanmin(sl[g]):.2f} to {np.nanmax(sl[g]):.2f}, median {np.nanmedian(sl[g]):.2f} mV/MHz in {RISE[0]:.0f}-{RISE[1]:.0f} MHz"
    ax[2].set(xlim=(1145, 1555), ylabel="slope (mV per MHz)", title=ttl)
    for w, c in C.items():
        m = np.isin(c[0], rf)
        if w == REF or not m.any():
            continue
        f, d = c[0][m], c[1][m] - on((rf, rv), c[0][m])
        ax[3].plot(f, d, "-", color=col[w], lw=1.1, label=f"{w:.0f} dBm")
        s = np.interp(f, rf, sl)
        ax[4].plot(f, np.where(s > 0.15, d / s, np.nan), "-o", color=col[w], ms=2, lw=1.1, label=f"{w:.0f} dBm")
    ax[3].axhline(0, color="k", lw=0.8)
    ax[3].set(xlim=(1145, 1555), ylabel="minus the -50 dBm reading (mV)", title="Each level minus the -50 dBm level at the same frequency (read seconds apart)")
    ax[4].axhspan(-2, 2, color="#1b9e77", alpha=0.12, label="+/- 2 MHz")
    ax[4].axhline(0, color="k", lw=0.8)
    ax[4].set(xlim=(1215, 1457), ylim=(-15, 15), ylabel="frequency error (MHz)",
              title="Frequency error from input power alone: (level - -50 dBm) / slope; left out where the slope is under 0.15 mV/MHz")
    for a, n in zip(ax, (5, 5, 0, 4, 5)):
        if n:
            a.legend(fontsize=8, ncol=n)
    for a in ax[:5]:
        a.grid(alpha=0.3)
        a.set_xlabel("Pluto frequency (MHz)")
    for a in (ax[1], ax[4]):
        a.axvspan(*RISE, color="#1b9e77", alpha=0.05)
    fig.tight_layout()
    fig.savefig(HERE / "pd_sweep5_14nov.png", dpi=95)
    print(HERE / "pd_sweep5_14nov.png")

    print("points per level: " + ", ".join(f"{w:.0f}: {c.shape[1]}" for w, c in C.items()))
    grid, s = rf[g], sl[g]
    E = {w: np.where(s > 0.15, (on(c, grid) - rv[g]) / s, np.nan) for w, c in C.items()}
    for sel in (L5, L5[:4], L5[1:4]):
        k = [w for w in sel if w in E]
        M = np.array([E[w] for w in k])
        span = np.nanmax(M, axis=0) - np.nanmin(M, axis=0)
        print(f"levels {k}: peak-to-peak best {np.nanmin(span):.2f} MHz at {grid[np.nanargmin(span)]:.0f}, worst {np.nanmax(span):.2f} at {grid[np.nanargmax(span)]:.0f}, "
              f"median {np.nanmedian(span):.2f}; within +/-2 MHz: " + ", ".join(f"{a:.0f}-{b:.0f}" for a, b in runs(grid, span <= 4)))
    for w in E:
        print(f"{w:.0f} dBm: mean error {np.nanmean(E[w]):+.2f} MHz, min {np.nanmin(E[w]):+.2f}, max {np.nanmax(E[w]):+.2f}")
    for lo, hi in ((1150, 1220), (1450, 1550)):
        for w, c in C.items():
            m = (c[0] >= lo) & (c[0] <= hi)
            if m.any():
                print(f"flat {lo}-{hi} MHz, {w:.0f} dBm: {np.min(c[1][m]):.1f} to {np.max(c[1][m]):.1f} mV")


if __name__ == "__main__":
    main()
