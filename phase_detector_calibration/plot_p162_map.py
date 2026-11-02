"""Phase detector voltage against frequency, one curve per Pluto power level, four ZX60-P162LN+ chain."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "p162x4_map_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
off = d[d["pass"] == "start_off"]["detector_mean_v"] * 1e3
d = d[d["pass"] == "map"]
# 1320 MHz at -65 dBm was hit by a tone off command sent during the sweep, 19:39
d = d[~((d["freq_mhz"] == 1320) & (d["pluto_want_dbm"] == -65) & (d["detector_mean_v"] < 0.1))]
levels = np.unique(d["pluto_want_dbm"])
fig, ax = plt.subplots(figsize=(13, 7))
for i, want in enumerate(levels[::-1]):
    k = np.where(d["pluto_want_dbm"] == want)[0]
    k = k[np.argsort(d["freq_mhz"][k])]
    ax.plot(d["freq_mhz"][k], d["detector_mean_v"][k] * 1e3, lw=1.2, color=plt.cm.viridis_r(i / max(len(levels) - 1, 1)), label=f"{want:.0f} dBm")
ax.axhline(np.median(off), color="0.4", ls="--", lw=1, label=f"Tone off, {np.median(off):.0f} mV")
ax.set_xlabel("Pluto frequency (MHz)")
ax.set_ylabel("Phase detector output (mV)")
ax.set_title("Phase detector voltage against frequency at each Pluto power, 4 x ZX60-P162LN+\n-85 to -45 dBm on the KUAIQU supply, -40 to -30 dBm on the Agilent E3630A")
ax.grid(alpha=0.3)
ax.legend(title="Pluto level (table)", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "p162x4_power_freq_map_1nov.png", dpi=110)
k = (d["freq_mhz"] >= 850) & (d["freq_mhz"] <= 950) & (d["pluto_want_dbm"] >= -70)
fmin = d["freq_mhz"][k][d["detector_mean_v"][k].argmin()]
print(f"lowest point near 900 MHz: {fmin:.0f} MHz, {d['detector_mean_v'][k].min()*1e3:.1f} mV")
ax.set_xlim(fmin, 1200)
ax.set_ylim(60, 340)
ax.set_title(f"{fmin:.0f} to 1200 MHz: phase detector voltage at each Pluto power, 4 x ZX60-P162LN+" + chr(10) + "-85 to -45 dBm on the KUAIQU supply, -40 to -30 dBm on the Agilent E3630A")
fig.savefig(HERE / "p162x4_power_freq_zoom_1nov.png", dpi=110)
print(f"{len(d)} points, levels {levels.tolist()}, tone off readings {np.round(off, 1).tolist()}")
for f in (900, 950, 1000, 1050, 1100, 1200, 1300, 1400, 1500):
    k = d["freq_mhz"] == f
    o = np.argsort(d["pluto_want_dbm"][k])
    print(f, [(int(a), int(round(b * 1e3))) for a, b in zip(d["pluto_want_dbm"][k][o], d["detector_mean_v"][k][o])])
