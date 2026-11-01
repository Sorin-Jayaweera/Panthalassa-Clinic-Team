"""Plot the single-shot phase detector captures from read_furuno_detector.py, PLL on only."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
SETS = [("pll_on", "PLL on", "#1f5fa8")]

fig, ax = plt.subplots(figsize=(10, 5))
for name, label, color in SETS:
    files = sorted((HERE / f"furuno_detector_1nov_{name}").glob("shot_*.csv"))
    for i, fn in enumerate(files):
        t, v = np.loadtxt(fn, delimiter=",", skiprows=1).T
        ax.plot(t * 1e6, v * 1e3, lw=1, color=color, alpha=0.75, label=f"{label} ({len(files)} shots)" if i == 0 else None)
        pre = v[t < -0.5e-6].mean()
        print(fn.parent.name, fn.name, f"points {len(v)}, peak {v.max()*1e3:.1f} mV, baseline {pre*1e3:.1f} mV")
ax.set_xlim(-3, 3)
ax.set_xlabel("Time from trigger (µs)")
ax.set_ylabel("Phase detector output (mV)")
ax.set_title("Phase detector pulses, Furuno as source, PLL on (triggered at 200 mV)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(HERE / "furuno_detector_1nov_pulses.png", dpi=130)
