"""Phase detector voltage against frequency, one curve per Pluto power level, from the map2d pass in pluto_explore_1nov.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "pluto_explore_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
d = d[d["pass"] == "map2d"]
levels = np.unique(d["pluto_want_dbm"])
fig, ax = plt.subplots(figsize=(13, 7))
for i, want in enumerate(levels[::-1]):
    k = d["pluto_want_dbm"] == want
    ax.plot(d["freq_mhz"][k], d["detector_mean_v"][k] * 1e3, lw=1.2, color=plt.cm.viridis_r(i / max(len(levels) - 1, 1)), label=f"{want:.0f} dBm")
ax.set_xlabel("Pluto frequency (MHz)")
ax.set_ylabel("Phase detector output (mV)")
ax.set_title("Phase detector voltage against frequency at each Pluto power")
ax.grid(alpha=0.3)
ax.legend(title="Pluto level (table)", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "pluto_power_freq_map_1nov.png", dpi=110)
print(f"{len(d)} points, levels {levels.tolist()}")
