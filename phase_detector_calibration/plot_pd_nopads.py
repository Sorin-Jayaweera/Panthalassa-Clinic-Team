"""15 Nov: the same coarse sweep (1150-1550 MHz every 25 MHz, five Pluto levels, dithered) with and without the pads at the
mixer ports (3 dB at LO, 6 dB at RF). With pads: 11:42-12:09 (stage coarse). Pads removed by Sorin, then 18:53 on (stage coarse_np).
Each sweep has its own 1 min tone-off reading. Saves pd_nopads_15nov.png and prints the comparison."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
ALL = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)


def setup(pads):
    lo, rf = ("3 dB pad at the LO port", "6 dB pad at the RF port") if pads else ("no pad", "no pad")
    return ["Pluto TX\n-36 to -64 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.22-0.29 A", "ZFRSC-42-S+\nsplitter",
            [f"right arm (LO): cable D\n{lo}", f"left arm (RF): cable B + E\n{rf}"],
            "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n50 mV/div, dithered", "20 dB of pads\nthen SM200B (not read)"]]


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def off_med(rep):
    v = [mv(r) for r in ALL if r["stage"] == "off" and r["rep"] == str(rep)]
    return float(np.median(v)) if v else np.nan


def sweeps(stage, off0):
    """{rep: {level: (freqs, mV minus that sweep's tone-off)}}"""
    out = {}
    for n in sorted({int(r["rep"]) for r in ALL if r["stage"] == stage}):
        z = off_med(off0 + n)
        out[n] = {}
        for w in L5:
            a = sorted((float(r["freq_mhz"]), mv(r) - z) for r in ALL if r["stage"] == stage and int(r["rep"]) == n and float(r["pluto_want_dbm"]) == w)
            if a:
                out[n][w] = np.array(a)
    return out


def mean_of(S, w, grid):
    M = [np.interp(grid, s[w][:, 0], s[w][:, 1], left=np.nan, right=np.nan) if w in s and len(s[w]) == len(grid) else np.full(len(grid), np.nan) for s in S.values()]
    return np.nanmean(M, axis=0)


def main():
    P = sweeps("coarse", 50)
    N = sweeps("coarse_np", 60)
    col = dict(zip(L5, plt.cm.viridis(np.linspace(0, 0.9, len(L5)))))
    grid = P[1][-50.0][:, 0]
    fig, ax = wiring.figure(3, [setup(False), setup(True)], size=(14, 17),
                            titles=["Wiring WITHOUT pads, 15 Nov 18:53 on (solid lines)", "Wiring WITH pads, 15 Nov 11:42-12:09 (dashed lines)"])
    for n, s in N.items():
        for w, a in s.items():
            ax[0].plot(a[:, 0], a[:, 1], "-o" if n == 1 else "-s", color=col[w], ms=3, lw=1.3 if w != -64 else 0.9, alpha=1 if w != -64 else 0.5,
                       label=f"{w:.0f} dBm" if n == min(N) else None)
    ax[0].set(xlim=(1140, 1560), xlabel="Pluto frequency (MHz)", ylabel="detector minus tone-off (mV)",
              title=f"No pads: {len(N)} coarse sweep(s), 25 MHz steps, five Pluto levels (circles = sweep 1, squares = sweep 2)")
    ax[0].legend(fontsize=8, ncol=5)
    for w in L5:
        p, q = mean_of(P, w, grid), mean_of(N, w, grid)
        ax[1].plot(grid, q, "-o", color=col[w], ms=3, lw=1.4, alpha=1 if w != -64 else 0.5, label=f"{w:.0f} dBm, no pads")
        ax[1].plot(grid, p, "--", color=col[w], lw=1.2, alpha=0.8 if w != -64 else 0.4)
        ax[2].plot(grid, q - p, "-o", color=col[w], ms=3, lw=1.2, alpha=1 if w != -64 else 0.5, label=f"{w:.0f} dBm")
        print(f"{w:.0f} dBm: no pads minus pads, median {np.nanmedian(q - p):+.1f} mV, range {np.nanmin(q - p):+.1f} to {np.nanmax(q - p):+.1f} mV; "
              f"peak {np.nanmax(q):.1f} mV at {grid[np.nanargmax(q)]:.0f} MHz (pads {np.nanmax(p):.1f} at {grid[np.nanargmax(p)]:.0f}); "
              f"low {np.nanmin(q):.1f} at {grid[np.nanargmin(q)]:.0f} (pads {np.nanmin(p):.1f} at {grid[np.nanargmin(p)]:.0f})")
    ax[1].plot([], [], "k--", label="with pads (dashed)")
    ax[1].set(xlim=(1140, 1560), xlabel="Pluto frequency (MHz)", ylabel="detector minus tone-off (mV)",
              title="Without pads (solid, mean of the no-pads sweeps) against with pads (dashed, mean of the two 11:42-12:09 sweeps)")
    ax[1].legend(fontsize=8, ncol=6)
    ax[2].axhline(0, color="k", lw=0.8)
    ax[2].set(xlim=(1140, 1560), xlabel="Pluto frequency (MHz)", ylabel="no pads minus pads (mV)", title="Change from removing the pads, at each frequency and level")
    ax[2].legend(fontsize=8, ncol=5)
    for a in ax:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "pd_nopads_15nov.png", dpi=95)
    print("pd_nopads_15nov.png", f"no-pads sweeps {list(N)}; tone-off with pads {[round(off_med(50 + n), 2) for n in P]}, without {[round(off_med(60 + n), 2) for n in N]} mV")


if __name__ == "__main__":
    main()
