"""15 Nov: the same coarse sweep (1150-1550 MHz every 25 MHz, five Pluto levels, dithered) with and without the pads at the
mixer ports (3 dB at LO, 6 dB at RF). With pads: 11:42-12:09 (stage coarse). Pads removed by Sorin, then 18:53 on (stage coarse_np).
Each sweep has its own 1 min tone-off reading. Saves pd_nopads_15nov.png and prints the comparison."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, L5, chain, colours, fv, rows, zero

ALL = rows("pd_dither_14nov.csv")


def setup(pads):
    return chain("-36 to -64 dBm", "4.03 V, 0.22-0.29 A", pads=pads, scope=", 1 Mohm\n50 mV/div, dithered", sm="20 dB of pads\nthen SM200B (not read)")


def sweeps(stage, off0):
    """{rep: {level: 2 x n (freqs, mV minus that sweep's tone-off)}}"""
    out = {}
    for n in sorted({int(r["rep"]) for r in ALL if r["stage"] == stage}):
        z = zero(ALL, (str(off0 + n),))
        out[n] = {w: a - [[0], [z]] for w in L5 if (a := fv([r for r in ALL if r["stage"] == stage and int(r["rep"]) == n and float(r["pluto_want_dbm"]) == w])).size}
    return out


def mean_of(S, w, grid):
    return np.nanmean([np.interp(grid, *s[w], left=np.nan, right=np.nan) if w in s and s[w].shape[1] == len(grid) else np.full(len(grid), np.nan) for s in S.values()], axis=0)


def main():
    P, N = sweeps("coarse", 50), sweeps("coarse_np", 60)
    col, grid = colours(L5), P[1][-50.0][0]
    fade = lambda w, a=1.0, b=0.5: b if w == -64 else a
    fig, ax = wiring.figure(3, [setup(False), setup(True)], size=(14, 17),
                            titles=["Wiring WITHOUT pads, 15 Nov 18:53 on (solid lines)", "Wiring WITH pads, 15 Nov 11:42-12:09 (dashed lines)"])
    for n, s in N.items():
        for w, (f, v) in s.items():
            ax[0].plot(f, v, "-o" if n == 1 else "-s", color=col[w], ms=3, lw=fade(w, 1.3, 0.9), alpha=fade(w), label=f"{w:.0f} dBm" if n == min(N) else None)
    ax[0].set(xlim=(1140, 1560), xlabel="Pluto frequency (MHz)", ylabel="detector minus tone-off (mV)",
              title=f"No pads: {len(N)} coarse sweep(s), 25 MHz steps, five Pluto levels (circles = sweep 1, squares = sweep 2)")
    ax[0].legend(fontsize=8, ncol=5)
    for w in L5:
        p, q = mean_of(P, w, grid), mean_of(N, w, grid)
        ax[1].plot(grid, q, "-o", color=col[w], ms=3, lw=1.4, alpha=fade(w), label=f"{w:.0f} dBm, no pads")
        ax[1].plot(grid, p, "--", color=col[w], lw=1.2, alpha=fade(w, 0.8, 0.4))
        ax[2].plot(grid, q - p, "-o", color=col[w], ms=3, lw=1.2, alpha=fade(w), label=f"{w:.0f} dBm")
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
    print("pd_nopads_15nov.png", f"no-pads sweeps {list(N)}; tone-off with pads {[round(zero(ALL, (str(50 + n),)), 2) for n in P]}, without {[round(zero(ALL, (str(60 + n),)), 2) for n in N]} mV")


if __name__ == "__main__":
    main()
