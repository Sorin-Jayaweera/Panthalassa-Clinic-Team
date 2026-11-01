"""Plot Pluto frequency against phase detector output from run_pluto_calibration.py files, joined.

Usage: python plot_pluto_calibration.py out.png file1.csv [file2.csv ...]
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
rows = [r for n in sys.argv[2:] for r in csv.DictReader(open(HERE / n))]
rows.sort(key=lambda r: float(r["freq_set_hz"]))
f = np.array([float(r["freq_set_hz"]) for r in rows]) / 1e6
v = np.array([float(r["detector_mean_v"]) for r in rows]) * 1e3

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(f, v, "-o", ms=2.5, lw=1.2, color="#1f5fa8")
ax.set_xlabel("Pluto frequency (MHz)")
ax.set_ylabel("Phase detector output (mV)")
ax.set_title(f"Phase detector, Pluto at -36 dBm, 3 x ZX60-P103LN+, 4.5 in delay ({len(f)} points)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / sys.argv[1], dpi=130)
print(len(f), f"{f.min():.0f} to {f.max():.0f} MHz, {v.min():.1f} to {v.max():.1f} mV")
