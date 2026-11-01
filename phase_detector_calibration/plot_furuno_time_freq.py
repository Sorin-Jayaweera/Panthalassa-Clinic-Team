"""Time (scope) and frequency (SSA3021X) views of the phase detector output, Furuno as source, PLL on."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = Path(__file__).parent / "furuno_detector_1nov_pll_on"
C = "#1f5fa8"
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7.5))
for fn in sorted(D.glob("shot_*.csv")):
    t, v = np.loadtxt(fn, delimiter=",", skiprows=1).T
    a.plot(t * 1e6, v * 1e3, lw=1, color=C, alpha=0.7)
a.set_xlim(-3, 3)
a.set_xlabel("Time from trigger (µs)")
a.set_ylabel("Output (mV)")
a.set_title("Time: scope, 1 MΩ, 3 single shots, triggered at 200 mV")
a.grid(alpha=0.3)
f, p = np.loadtxt(D / "ssa_0p1_to_50MHz.csv", delimiter=",", skiprows=1).T
b.plot(f / 1e6, p, lw=1, color=C)
k = int(p.argmax())
b.annotate(f"{p[k]:.1f} dBm at {f[k]/1e6:.1f} MHz", (f[k] / 1e6, p[k]), xytext=(10, -4), textcoords="offset points")
b.set_xlabel("Frequency (MHz)")
b.set_ylabel("dBm (Max Hold, RBW 1 MHz)")
b.set_title("Frequency: SSA3021X, 0.1 to 50 MHz")
b.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(D.parent / "furuno_detector_1nov_time_freq.png", dpi=130)
print(f"peak {p[k]:.1f} dBm at {f[k]/1e6:.2f} MHz, median {np.median(p):.1f}")
