"""Four ZX60-P162LN+ chain: 1 MHz sweeps at several Pluto levels, 900 to 1200 MHz, Agilent supply. Plot with the wiring, and the frequency error that power alone causes."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "p162x4_fine_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
levels = np.unique(d["pluto_want_dbm"])
fig, (a, b) = wiring.figure(2, [wiring.P162X4], size=(13, 11))
grid = np.arange(900.0, 1201.0)
V = {}
for i, want in enumerate(levels[::-1]):
    k = d["pluto_want_dbm"] == want
    f, v = d["freq_mhz"][k], d["detector_mean_v"][k] * 1e3
    V[want] = (f, v)
    for ax in (a, b):
        ax.plot(f, v, lw=1.1, color=plt.cm.viridis_r(i / max(len(levels) - 1, 1)), label=f"{want:.0f} dBm")
    print(want, "points", len(f), "from", f.min(), "to", f.max())
a.set_title("4 x ZX60-P162LN+ then the mixer: 1 MHz steps, 900 to 1200 MHz")
b.set_title("Same data, 950 to 1020 MHz")
b.set_xlim(950, 1020)
b.set_ylim(100, 300)
for ax in (a, b):
    ax.set_xlabel("Pluto frequency (MHz)")
    ax.set_ylabel("Phase detector output (mV)")
    ax.grid(alpha=0.3)
    ax.legend(title="Pluto level (table)", ncol=3, fontsize=8)
fig.tight_layout()
fig.savefig(HERE / "p162x4_fine_1nov.png", dpi=110)
for lo, hi in ((900, 950), (960, 1010), (1020, 1060), (1060, 1200)):
    fs = np.arange(lo, hi + 1.0)
    for name, use in (("-70 to -36", levels), ("-65 to -36", levels[levels >= -65]), ("-60 to -36", levels[levels >= -60])):
        M = np.array([np.interp(fs, *V[w]) for w in use if V[w][0].min() <= lo and V[w][0].max() >= hi])
        print(lo, hi, name, "levels", len(M), "mean spread mV", round(float(np.ptp(M, axis=0).mean()), 1), "max", round(float(np.ptp(M, axis=0).max()), 1))
ref = d["pluto_want_dbm"] == -60
m = np.genfromtxt(HERE / "p162x4_map_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
m = m[(m["pass"] == "repeat") & (m["rep"] == 0)]
x = np.interp(m["freq_mhz"], d["freq_mhz"][ref], d["detector_mean_v"][ref])
print("drift, final -60 sweep minus first repeat, mV: mean", round(float((x - m["detector_mean_v"]).mean() * 1e3), 1), "rms", round(float(np.sqrt(((x - m["detector_mean_v"]) ** 2).mean()) * 1e3), 1))
print("first", d["timestamp"][0], "last", d["timestamp"][-1], "rms_v median mV", round(float(np.median(d["rms_v"]) * 1e3), 1))
