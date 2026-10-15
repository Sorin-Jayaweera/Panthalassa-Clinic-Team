"""VCO look up table figure: output frequency against tuning voltage, run 3 (clean DC on Vt), 10 Oct 2026."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
d = np.genfromtxt(HERE / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
up, down = d[d["direction"] == "up"], d[d["direction"] == "down"]

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(up["vt_meas_v"], up["vco_freq_hz"] / 1e6, ".-", color="tab:green", lw=1, label=f"Sweep up ({len(up)} points, 0.02 V steps)")
ax.plot(down["vt_meas_v"], down["vco_freq_hz"] / 1e6, "x", ms=7, color="k", label=f"Sweep back down ({len(down)} points, repeat check)")
ax.set(xlabel="Tuning voltage Vt (V)", ylabel="VCO output frequency (MHz)",
       title="VCO output frequency against tuning voltage Vt\nRun 3, 10 Oct: clean DC on Vt, Vcc 11.5 V")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
for out in (HERE / "GOOD_vco_frequency_vs_voltage.png", HERE / "site" / "img" / "vco_f_vs_v.png"):
    fig.savefig(out, dpi=125)
