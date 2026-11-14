"""Power-level curves before the 14:53 stop and after the 15:18 restart (Pluto replugged; amplifiers then drew 0.26 A instead of 0.23 A at 4.03 V).
Before: levels pass 0 (14:00-14:53). After: the 15:29 recheck (5 frequencies x 7 levels) and any later levels passes (finer steps).
Saves pd_recheck_14nov.png and prints the shift per level."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
ALL = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
BREAK = "2026-11-14T15:00"
W = (-60.0, -56.0, -52.0, -48.0, -44.0, -40.0, -36.0)
WIRING = [["Pluto TX\n-60 to -36 dBm", "4 x ZX60-P162LN+\n4.03 V: 0.23 A before,\n0.26 A after the break", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", "20 dB of pads\nthen SM200B"]]]
WT = ["Wiring, 14 Nov (unchanged across the break; Sorin checked it at 15:30)"]


def z_of(rows):
    v = [float(r["detector_mean_v"]) * 1e3 for r in rows if r["stage"] in ("off", "drift_off")]
    return float(np.median(v)) if v else 0.0


def main():
    before = [r for r in ALL if r["timestamp"] < BREAK]
    after = [r for r in ALL if r["timestamp"] >= BREAK]
    zb, za = z_of(before), z_of(after)
    old = {(float(r["freq_mhz"]), float(r["pluto_want_dbm"])): float(r["detector_mean_v"]) * 1e3 - zb for r in before if r["stage"] == "levels"}
    newrows = [r for r in after if r["stage"] in ("recheck", "levels")]
    bf = np.array(sorted({k[0] for k in old}))
    band = sorted((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3 - zb) for r in before if r["stage"] == "band1")
    band = np.array(band)
    sl = np.array([np.polyfit(band[(band[:, 0] >= f - 6) & (band[:, 0] <= f + 6), 0], band[(band[:, 0] >= f - 6) & (band[:, 0] <= f + 6), 1], 1)[0] for f in band[:, 0]])

    fig, ax = wiring.figure(3, WIRING, size=(14, 16), titles=WT)
    cm = plt.cm.viridis(np.linspace(0, 0.9, len(W)))
    print(f"tone off before {zb:.2f} mV, after {za:.2f} mV")
    for c, w in zip(cm, W):
        ov = np.array([old.get((f, w), np.nan) for f in bf])
        ax[0].plot(bf, ov, "-", color=c, lw=1, alpha=0.6, label=f"{w:.0f} dBm before (14:00-14:53)")
        nr = sorted((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3 - za) for r in newrows if float(r["pluto_want_dbm"]) == w)
        if nr:
            a = np.array(nr)
            ax[0].plot(a[:, 0], a[:, 1], "o--" if len(a) < 20 else "--", color=c, ms=6, mfc="none", lw=1.3, label=f"{w:.0f} dBm after (from 15:29)")
            d = [(f, v - old[(f, w)]) for f, v in a if (f, w) in old]
            if d:
                d = np.array(d)
                ax[1].plot(d[:, 0], d[:, 1], "o-", color=c, ms=5, lw=1.2, label=f"{w:.0f} dBm")
                s = np.interp(d[:, 0], band[:, 0], sl)
                mhz = np.where(s > 0.15, d[:, 1] / s, np.nan)
                ax[2].plot(d[:, 0], mhz, "o-", color=c, ms=5, lw=1.2, label=f"{w:.0f} dBm")
                print(f"{w:.0f} dBm: shift after - before = " + ", ".join(f"{f:.0f}: {x:+.1f} mV" for f, x in d))
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
        a.set_xlabel("Pluto frequency (MHz)")
        a.set_xlim(1215, 1457)
    fig.tight_layout()
    out = HERE / "pd_recheck_14nov.png"
    fig.savefig(out, dpi=95)
    print(out)


if __name__ == "__main__":
    main()
