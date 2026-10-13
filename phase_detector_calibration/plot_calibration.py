"""Charts for phase_detector_calibration.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "phase_detector_calibration.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
up, down = d[d["direction"] == "up"], d[d["direction"] == "down"]


def panel(ax, xkey, ykey, xs, ys, xlabel, ylabel, title):
    ax.plot(up[xkey] * xs, up[ykey] * ys, "o-", ms=3.5, lw=1, label="Sweep up (0.05 V steps)")
    ax.plot(down[xkey] * xs, down[ykey] * ys, "x", ms=7, color="tab:red", label="Sweep back down (repeat check)")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()


fig, ax = plt.subplots(figsize=(8, 5))
panel(ax, "vt_meas_v", "vco_freq_hz", 1, 1e-6, "Tuning voltage Vt (V)", "VCO frequency (MHz)",
      "VCO: output frequency vs input voltage")
fig.tight_layout()
fig.savefig(HERE / "vco_frequency_vs_voltage.png", dpi=130)

fig, ax = plt.subplots(figsize=(8, 5))
panel(ax, "vco_freq_hz", "mixer_out_v", 1e-6, 1e3, "Input frequency (MHz)", "Mixer output (mV)",
      "Splitter / delay line / mixer: output voltage vs input frequency")
fig.tight_layout()
fig.savefig(HERE / "mixer_voltage_vs_frequency.png", dpi=130)

fig, ax = plt.subplots(figsize=(8, 5))
panel(ax, "vco_freq_hz", "vco_power_at_sa_dbm", 1e-6, 1, "Frequency (MHz)", "Power at spectrum analyzer (dBm)",
      "Power reaching the analyzer through the tee vs frequency")
fig.tight_layout()
fig.savefig(HERE / "power_at_analyzer_vs_frequency.png", dpi=130)

fig, ax = plt.subplots(figsize=(8, 5))
panel(ax, "vt_meas_v", "mixer_out_v", 1, 1e3, "Tuning voltage Vt (V)", "Mixer output (mV)",
      "Whole chain: mixer output vs tuning voltage")
fig.tight_layout()
fig.savefig(HERE / "mixer_voltage_vs_vt.png", dpi=130)
print("plots written")
