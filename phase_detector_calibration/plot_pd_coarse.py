"""15 Nov: repeated coarse sweeps (1150-1550 MHz every 25 MHz, five Pluto levels -36 to -64 dBm), each one a fresh launch of
the run script with its own 1 min tone-off reading first. Asks: do the repeats agree with each other, and with 14 Nov?
Saves pd_coarse_15nov.png and prints the spread."""
import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
ALL = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
WIRING = [["Pluto TX\n-36 to -64 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.22-0.29 A", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", "20 dB of pads\nthen SM200B (not read)"]]]
WT = ["Wiring, 14-15 Nov (unchanged; cables re-checked 15 Nov)"]


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def t(r):
    return dt.datetime.fromisoformat(r["timestamp"])


def off_med(rep):
    v = [mv(r) for r in ALL if r["stage"] == "off" and r["rep"] == str(rep)]
    return float(np.median(v)) if v else np.nan


def main():
    reps = sorted({int(r["rep"]) for r in ALL if r["stage"] == "coarse"})
    grid = sorted({float(r["freq_mhz"]) for r in ALL if r["stage"] == "coarse"})
    col = dict(zip(L5, plt.cm.viridis(np.linspace(0, 0.9, len(L5)))))
    D = {}   # (rep, level) -> {f: mV minus that rep's tone-off}
    for r in ALL:
        if r["stage"] == "coarse":
            n = int(r["rep"])
            D.setdefault((n, float(r["pluto_want_dbm"])), {})[float(r["freq_mhz"])] = mv(r) - off_med(50 + n)
    # 14 Nov evening (halving run) at the same frequencies, its own tone-off
    z14 = np.nanmedian([off_med(k) for k in (31, 32, 33)])
    E = {}
    for r in ALL:
        if r["stage"] in ("bisect5", "bisect5s") and float(r["freq_mhz"]) in grid:
            E.setdefault(float(r["pluto_want_dbm"]), {}).setdefault(float(r["freq_mhz"]), mv(r) - z14)

    fig, ax = wiring.figure(4, WIRING, size=(14, 20), titles=WT)
    for (n, w), d in sorted(D.items()):
        f = sorted(d)
        ax[0].plot(f, [d[x] for x in f], "-o", color=col[w], ms=3, lw=1.0, alpha=0.8, label=f"{w:.0f} dBm" if n == reps[0] else None)
    for w, d in E.items():
        f = sorted(d)
        ax[0].plot(f, [d[x] for x in f], "--", color=col[w], lw=1.6, alpha=0.6)
    ax[0].plot([], [], "k--", label="14 Nov evening, same frequencies")
    ax[0].set(xlim=(1140, 1560), ylabel="detector minus tone-off (mV)",
              title=f"{len(reps)} coarse sweeps, 15 Nov (solid, each a fresh launch with its own tone-off) and the 14 Nov evening run (dashed)")
    ax[0].legend(fontsize=8, ncol=6)

    # each rep minus the mean of all reps, per level
    spread = []
    for w in L5:
        M = np.array([[D.get((n, w), {}).get(f, np.nan) for f in grid] for n in reps])
        mean = np.nanmean(M, axis=0)
        for i, n in enumerate(reps):
            ax[1].plot(grid, M[i] - mean, "-", color=col[w], lw=0.9, alpha=0.7)
        if len(reps) > 1:
            spread.append(np.nanmax(M, axis=0) - np.nanmin(M, axis=0))
            print(f"{w:.0f} dBm: repeat spread median {np.nanmedian(spread[-1]):.2f} mV, max {np.nanmax(spread[-1]):.2f} mV at {grid[int(np.nanargmax(spread[-1]))]:.0f} MHz")
        e = np.array([E.get(w, {}).get(f, np.nan) for f in grid])
        print(f"{w:.0f} dBm: 15 Nov mean minus 14 Nov evening: median {np.nanmedian(mean - e):+.2f} mV (range {np.nanmin(mean - e):+.1f} to {np.nanmax(mean - e):+.1f})")
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set(xlim=(1140, 1560), xlabel="Pluto frequency (MHz)", ylabel="sweep minus mean of all sweeps (mV)",
              title="Repeatability: each 15 Nov sweep minus the average of the 15 Nov sweeps (colour = level)")
    ax[0].set_xlabel("Pluto frequency (MHz)")

    # long-term: 1350 MHz at -50 dBm and the tone-off reading, every session since 14 Nov afternoon
    t0 = dt.datetime(2026, 11, 14)
    for st, mk in (("sweep5", "s"), ("bisect5", "o"), ("bisect5s", "o"), ("repeat6", "D"), ("coarse", "^")):
        p = [((t(r) - t0).total_seconds() / 3600, mv(r)) for r in ALL if r["stage"] == st and float(r["freq_mhz"]) == 1350.0 and float(r["pluto_want_dbm"]) == -50.0]
        if p:
            a = np.array(p)
            ax[2].plot(a[:, 0], a[:, 1], mk, color=col[-50.0], ms=6, label=f"1350 MHz, -50 dBm ({st})")
    p = np.array([((t(r) - t0).total_seconds() / 3600, mv(r)) for r in ALL if r["stage"] == "off" and int(r["rep"]) >= 21])
    ax[3].plot(p[:, 0], p[:, 1], ".", color="#555", ms=4)
    for a in ax[2:4]:
        a.axvline(24 + 2.0, color="#d95f02", lw=1, ls=":")
        a.set_xlabel("hours since midnight 14 Nov (24 = midnight 15 Nov; orange dotted = PC restarted by Windows Update 02:01)")
    ax[2].set(ylabel="raw detector reading (mV)", title="Raw 1350 MHz, -50 dBm reading in every session (no tone-off subtracted)")
    ax[2].legend(fontsize=8, ncol=3)
    ax[3].set(ylabel="tone-off reading (mV)", title="Raw tone-off reading (Pluto at maximum attenuation, no tone) in every session")
    for a in ax[:4]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    out = HERE / "pd_coarse_15nov.png"
    fig.savefig(out, dpi=95)
    print(out, f"{len(reps)} coarse sweeps")


if __name__ == "__main__":
    main()
