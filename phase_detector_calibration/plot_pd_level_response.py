"""Detector voltage against Pluto level, one line per frequency, coloured by frequency (Sorin, 19 Nov): how each frequency's reading
moves with input power. Top: raw mV. Bottom: minus that frequency's -36 dBm reading. Median over sweeps where a run has repeats.
Usage: python plot_pd_level_response.py [tag ...] (default pad10d pad10z). Saves pd_<tag>_voltage_vs_level.png."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import pd_runs as R
import wiring
from plot_pd_power_uncertainty import sweeps

HERE = Path(__file__).resolve().parent


def plot(D, run):
    f, V = sweeps(D, (run["tag"],), 600, 1600)
    L = np.array(sorted(V))
    M = np.array([np.nanmedian(V[w], 0) for w in L])          # levels x frequencies
    fig, ax = wiring.figure(2, [R.wiring_for(run)], size=(16, 15), strip=0.3, titles=[f"Wiring, {run['day']}: {run['desc']}"])
    cm, norm = plt.cm.turbo, plt.Normalize(f.min(), f.max())
    for a, Y, lab in ((ax[0], M, "detector (mV, raw)"), (ax[1], M - M[L == L.max()], f"detector minus its {L.max():.0f} dBm reading (mV)")):
        for k in range(len(f)):
            a.plot(L, Y[:, k], "-o", ms=2.5, lw=0.7, color=cm(norm(f[k])))
        a.set(xticks=L, ylabel=lab, xlabel="Pluto level (dBm)")
        a.grid(alpha=0.3)
        fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cm), ax=a, label="Pluto frequency (MHz)", pad=0.01)
    ax[0].set_title(f"{run['tag']}: detector voltage against Pluto level, one line per frequency ({len(f)} frequencies, {f.min():g}-{f.max():g} MHz)")
    ax[1].set_title("Same, relative to the strongest level: how far each frequency's reading moves with input power")
    fig.tight_layout()
    fig.savefig(HERE / f"pd_{run['tag']}_voltage_vs_level.png", dpi=85)


if __name__ == "__main__":
    D, tags = R.rows(), sys.argv[1:] or ["pad10hf", "pad10d", "pad10z"]
    for run in R.present(D):
        if run["tag"] in tags:
            plot(D, run)
