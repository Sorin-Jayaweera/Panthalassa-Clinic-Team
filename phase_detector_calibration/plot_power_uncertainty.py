"""Newest phase detector calibration (4 x ZX60-P162LN+, Agilent supply) and the frequency error from not knowing the power, -40 dBm up to the
highest level measured here (-33 dBm; -30 dBm was below the Pluto attenuation floor from 880 to 1200 MHz, so it has no points).

Curves used: the 1 MHz sweeps at -40 and -36 dBm (p162x4_fine_1nov.csv) and the 5 MHz map at -40, -36 and -33 dBm (p162x4_map_1nov.csv),
all on 1 Nov, interpolated to 1 MHz. Upper and lower edges of the band are the highest and lowest of those curves at each frequency.
Worst case: for a reading V, every frequency whose band contains V could have produced it; the frequency error is the width of that set.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent
fine = np.genfromtxt(HERE / "p162x4_fine_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
mp = np.genfromtxt(HERE / "p162x4_map_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
mp = mp[mp["pass"] == "map"]
F = np.arange(880.0, 1201.0)
curves = []
for name, src, lvl in (("-40 dBm, 1 MHz", fine, -40), ("-36 dBm, 1 MHz", fine, -36), ("-40 dBm, 5 MHz map", mp, -40),
                       ("-36 dBm, 5 MHz map", mp, -36), ("-33 dBm, 5 MHz map", mp, -33)):
    k = src["pluto_want_dbm"] == lvl
    f, v = src["freq_mhz"][k], src["detector_mean_v"][k] * 1e3
    o = np.argsort(f)
    lo = max(F[0], f.min())
    curves.append((name, np.where((F >= lo) & (F <= f.max()), np.interp(F, f[o], v[o]), np.nan)))
M = np.array([c for _, c in curves])
U, L = np.nanmax(M, axis=0), np.nanmin(M, axis=0)
dV = U - L


def freq_width(lo_f, hi_f):
    """Worst case over readings V of the span of frequencies in [lo_f, hi_f] whose band contains V."""
    k = (F >= lo_f) & (F <= hi_f)
    Vs = np.arange(np.floor(L[k].min()), np.ceil(U[k].max()) + 0.1, 0.1)
    widths = []
    for V in Vs:
        hit = F[k][(L[k] <= V) & (U[k] >= V)]
        widths.append(hit.max() - hit.min() if len(hit) else np.nan)
    return Vs, np.array(widths)


fig = plt.figure(figsize=(13, 14))
gs = fig.add_gridspec(4, 1, height_ratios=[3.2, 1.6, 2.2, 0.9], hspace=0.42, left=0.08, right=0.97, top=0.95, bottom=0.02)
a, b, c = (fig.add_subplot(gs[i]) for i in range(3))
for (name, v), col in zip(curves, ("#1f4e9c", "#2a9d8f", "#1f4e9c", "#2a9d8f", "#c06000")):
    a.plot(F, v, lw=1.1 if "1 MHz" in name else 0.9, ls="-" if "1 MHz" in name else "--", color=col, label=name)
a.fill_between(F, L, U, color="0.6", alpha=0.3, label="band: lowest to highest")
a.set_title("Phase detector calibration, 4 x ZX60-P162LN+ then the mixer, 1 Nov, Pluto -40 to -33 dBm")
a.set_ylabel("Detector output (mV)")
b.plot(F, dV, color="0.2")
b.set_title("Voltage uncertainty from power alone (band width)")
b.set_ylabel("mV")
for ax in (a, b):
    ax.set_xlabel("Pluto frequency (MHz)")
    ax.grid(alpha=0.3)
    ax.set_xlim(F[0], F[-1])
a.legend(fontsize=8, ncol=2)
rows = []
for lo_f, hi_f, col in ((900, 1010, "#1f4e9c"), (950, 1010, "#2a9d8f"), (960, 1000, "#c06000")):
    Vs, w = freq_width(lo_f, hi_f)
    c.plot(Vs, w, color=col, label=f"frequencies limited to {lo_f}-{hi_f} MHz: worst {np.nanmax(w):.0f} MHz")
    k = (F >= lo_f) & (F <= hi_f)
    rows.append((lo_f, hi_f, dV[k].max(), F[k][np.argmax(dV[k])], np.nanmax(w), Vs[np.nanargmax(w)], np.nanmedian(w)))
c.set_title("Frequency uncertainty: for a detector reading, how wide is the range of frequencies that could give it")
c.set_xlabel("Detector reading (mV)")
c.set_ylabel("Frequency span (MHz)")
c.grid(alpha=0.3)
c.legend(fontsize=8)
wiring.draw(fig.add_subplot(gs[3]), wiring.P162X4, "Wiring, 1 Nov, Agilent E3630A at 3.94 V for the amps")
fig.savefig(HERE / "p162x4_power_uncertainty.png", dpi=110)
for r in rows:
    print(f"{r[0]}-{r[1]} MHz: worst voltage band {r[2]:.1f} mV at {r[3]:.0f} MHz; worst frequency span {r[4]:.1f} MHz at reading {r[5]:.1f} mV; median span {r[6]:.1f} MHz")
print("whole 880-1200 worst band", round(float(np.nanmax(dV)), 1), "mV at", F[np.nanargmax(dV)])
