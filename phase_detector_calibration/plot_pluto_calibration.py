"""Plot Pluto frequency against phase detector output from a run_pluto_calibration.py file."""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

src = Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else "pluto_calibration_1nov_-36dBm.csv")
rows = list(csv.DictReader(open(src)))
f = np.array([float(r["freq_set_hz"]) for r in rows]) / 1e6
v = np.array([float(r["detector_mean_v"]) for r in rows]) * 1e3

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(f, v, "-o", ms=2.5, lw=1.2, color="#1f5fa8")
ax.set_xlabel("Pluto frequency (MHz)")
ax.set_ylabel("Phase detector output (mV)")
ax.set_title(f"Phase detector, Pluto at -36 dBm, 3 x ZX60-P103LN+, 4.5 in delay ({len(f)} points)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(src.with_suffix(".png"), dpi=130)
print(len(f), f"{f.min():.0f} to {f.max():.0f} MHz, {v.min():.1f} to {v.max():.1f} mV")
d = np.diff(v) / np.diff(f)
print(f"slope {d.min():.2f} to {d.max():.2f} mV/MHz, sign changes {int(np.sum(np.diff(np.sign(d)) != 0))}")
