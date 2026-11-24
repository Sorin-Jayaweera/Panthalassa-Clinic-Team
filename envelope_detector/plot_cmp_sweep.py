"""Plot the 19 Nov Test B sweeps and the oscillation waveform.
    ~/miniforge3/envs/gr/bin/python plot_cmp_sweep.py
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GREEN, PURPLE = "#2a78d6", "#eb6834", "#1f9d6b", "#7b4fc4"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})

def style(ax):
    ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)

fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), facecolor=SURFACE)
for ax in axes: style(ax)

ax = axes[0]
for f, lab, c in (("data/cmp_sweep_20261119_122720.csv", "sweep 2", BLUE), ("data/cmp_sweep_20261119_123216.csv", "sweep 3", ORANGE)):
    r = list(csv.DictReader(open(f)))
    for d, m in (("up", "o"), ("down", "x")):
        x = [float(q["diff_in_mv"]) for q in r if q["dir"] == d]
        y = [float(q["out_rms_mv"]) for q in r if q["dir"] == d]
        ax.plot(x, y, m, ms=4, color=c, label=f"{lab}, IN+ going {d}", mfc="none" if m == "o" else c)
ax.set_xlabel("IN+ − IN− (mV, scope)"); ax.set_ylabel("OUT+ − OUT− variation, rms (mV)")
ax.set_title("A. Output toggles from −42 to +52 mV", loc="left", fontweight="bold")
ax.legend(frameon=False, fontsize=8, loc="center left")

ax = axes[1]
r = list(csv.DictReader(open("data/cmp_sweep_20261119_122720.csv")))
up = [q for q in r if q["dir"] == "up"]
x = [float(q["diff_in_mv"]) for q in up]
ax.plot(x, [float(q["frac_low"]) for q in up], "-", color=BLUE, label="low")
ax.plot(x, [float(q["frac_mid"]) for q in up], "-", color=INK_2, label="in between")
ax.plot(x, [float(q["frac_high"]) for q in up], "-", color=ORANGE, label="high")
ax.set_xlabel("IN+ − IN− (mV, scope)"); ax.set_ylabel("Fraction of samples")
ax.set_title("B. Inside the band the split hardly changes", loc="left", fontweight="bold")
ax.legend(frameon=False, fontsize=8)

ax = axes[2]
w = {}
for q in csv.DictReader(open("data/cmp_waveforms_20261119.csv")):
    if q["state"] == "mid_band":
        for k in ("t_ns", "in_p", "in_m", "out_p", "out_m"): w.setdefault(k, []).append(float(q[k]))
t = np.array(w["t_ns"])
for k, c, lab in (("out_p", GREEN, "OUT+ (CH3)"), ("out_m", PURPLE, "OUT− (CH4)"), ("in_p", BLUE, "IN+ (CH1)"), ("in_m", ORANGE, "IN− (CH2)")):
    ax.plot(t, w[k], color=c, lw=1.4, label=lab)
ax.set_xlim(0, 120); ax.set_xlabel("Time (ns)"); ax.set_ylabel("Volts")
ax.set_title("C. Mid-band: ≈ 94 MHz on outputs and inputs", loc="left", fontweight="bold")
ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)

fig.suptitle("Comparator Test B, 19 Nov: IN+ stepped through IN− ≈ 1.235 V (100 Ω at J1, 100 Ω at J7/J8, ×10 probes on all four nodes)",
             x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("data/cmp_testB_20261119.png", dpi=150, facecolor=SURFACE)
print("saved data/cmp_testB_20261119.png")
