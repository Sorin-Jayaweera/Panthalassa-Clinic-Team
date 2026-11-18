"""Power-level curves before the 14:53 stop and after the 15:18 restart (Pluto replugged; amplifiers then drew 0.26 A instead of 0.23 A at 4.03 V).
Before: levels pass 0 (14:00-14:53). After: the 15:29 recheck (5 frequencies x 7 levels) and any later levels passes (finer steps).
Saves pd_recheck_14nov.png and prints the shift per level."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, chain, colours, fv, mv, rows, slope, zero

ALL = rows("pd_dither_14nov.csv")
BREAK = "2026-11-14T15:00"
W = (-60.0, -56.0, -52.0, -48.0, -44.0, -40.0, -36.0)
WIRING = [chain("-60 to -36 dBm", "4.03 V: 0.23 A before,\n0.26 A after the break", scope=", 1 Mohm\n50 mV/div, 4 offsets 1 mV apart")]
WT = ["Wiring, 14 Nov (unchanged across the break; Sorin checked it at 15:30)"]


def main():
    before, after = [r for r in ALL if r["timestamp"] < BREAK], [r for r in ALL if r["timestamp"] >= BREAK]
    zb, za = (zero(x, stages=("off", "drift_off"), default=0.0) for x in (before, after))
    old = {(float(r["freq_mhz"]), float(r["pluto_want_dbm"])): mv(r) - zb for r in before if r["stage"] == "levels"}
    newrows = [r for r in after if r["stage"] in ("recheck", "levels")]
    bf = np.array(sorted({k[0] for k in old}))
    band = fv([r for r in before if r["stage"] == "band1"]) - [[0], [zb]]
    sl = slope(*band, 6)

    fig, ax = wiring.figure(3, WIRING, size=(14, 16), titles=WT)
    print(f"tone off before {zb:.2f} mV, after {za:.2f} mV")
    for w, c in colours(W).items():
        ax[0].plot(bf, [old.get((f, w), np.nan) for f in bf], "-", color=c, lw=1, alpha=0.6, label=f"{w:.0f} dBm before (14:00-14:53)")
        f, v = fv([r for r in newrows if float(r["pluto_want_dbm"]) == w]) - [[0], [za]]
        if not len(f):
            continue
        ax[0].plot(f, v, "o--" if len(f) < 20 else "--", color=c, ms=6, mfc="none", lw=1.3, label=f"{w:.0f} dBm after (from 15:29)")
        k = [(x, (x, w) in old) for x in f]
        m = np.array([o for _, o in k])
        if m.any():
            df, dv = f[m], v[m] - [old[(x, w)] for x in f[m]]
            ax[1].plot(df, dv, "o-", color=c, ms=5, lw=1.2, label=f"{w:.0f} dBm")
            s = np.interp(df, band[0], sl)
            ax[2].plot(df, np.where(s > 0.15, dv / s, np.nan), "o-", color=c, ms=5, lw=1.2, label=f"{w:.0f} dBm")
            print(f"{w:.0f} dBm: shift after - before = " + ", ".join(f"{x:.0f}: {y:+.1f} mV" for x, y in zip(df, dv)))
    ax[0].set(ylabel="detector minus tone-off (mV)", title="Band at seven Pluto levels: before the break (lines) and after (dashed / circles); each run's own tone-off reading subtracted")
    ax[0].legend(fontsize=7, ncol=4)
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set(ylabel="after minus before (mV)", title="Shift at the same frequency and level")
    ax[1].legend(fontsize=8, ncol=7)
    ax[2].axhspan(-2, 2, color="#1b9e77", alpha=0.12)
    ax[2].axhline(0, color="k", lw=0.8)
    ax[2].set(ylabel="shift as frequency (MHz)", title="The same shift divided by the local slope (where the slope is over 0.15 mV/MHz); green = +/- 2 MHz")
    ax[2].legend(fontsize=8, ncol=7)
    for a in ax[:3]:
        a.grid(alpha=0.3)
        a.set(xlabel="Pluto frequency (MHz)", xlim=(1215, 1457))
    fig.tight_layout()
    fig.savefig(HERE / "pd_recheck_14nov.png", dpi=95)
    print(HERE / "pd_recheck_14nov.png")


if __name__ == "__main__":
    main()
