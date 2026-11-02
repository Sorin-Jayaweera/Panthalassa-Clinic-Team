"""Phase detector voltage against Pluto power and frequency, from the map2d pass in pluto_explore_1nov.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "pluto_explore_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
d = d[d["pass"] == "map2d"]
freqs = np.unique(d["freq_mhz"])
levels = np.unique(d["pluto_want_dbm"])
grid = np.full((len(levels), len(freqs)), np.nan)
for r in d:
    grid[np.searchsorted(levels, r["pluto_want_dbm"]), np.searchsorted(freqs, r["freq_mhz"])] = r["detector_mean_v"] * 1e3
fig, ax = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
for i, want in enumerate(levels):
    ax[0].plot(freqs, grid[i], lw=1, color=plt.cm.viridis(i / max(len(levels) - 1, 1)), label=f"{want:.0f} dBm")
ax[0].set_ylabel("Phase detector output (mV)")
ax[0].set_title(f"Phase detector voltage against Pluto power and frequency ({len(d)} points)")
ax[0].grid(alpha=0.3)
ax[0].legend(ncol=2, fontsize=8, title="Pluto level")
if len(levels) > 1:
    y = np.append(levels - np.diff(levels, prepend=levels[0] - 3) / 2, levels[-1] + 1.5)
    x = np.append(freqs - 5, freqs[-1] + 5)
    lim = np.nanmax(np.abs(grid))
    pc = ax[1].pcolormesh(x, y, np.ma.masked_invalid(grid), cmap="RdBu_r", vmin=-lim, vmax=lim)
    fig.colorbar(pc, ax=ax, label="mV", location="right", fraction=0.03)
ax[1].set_xlabel("Pluto frequency (MHz)")
ax[1].set_ylabel("Pluto level (dBm, table)")
ax[1].set_title("Same data as a map. Blank points are over the limit at the detector or not yet measured")
fig.savefig(HERE / "pluto_power_freq_map_1nov.png", dpi=110, bbox_inches="tight")
print(f"{len(d)} points, levels {levels.tolist()}")
