"""Plot all four channels in three states (quiet, inside the band, latched back at -95 mV).
    ~/miniforge3/envs/gr/bin/python plot_cmp_states.py data/cmp_states_20261123_2013.csv
"""
import csv, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GREEN, PURPLE = "#2a78d6", "#eb6834", "#1f9d6b", "#7b4fc4"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 9.5, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
f = sys.argv[1]
d = {}
for q in csv.DictReader(open(f)):
    d.setdefault(q["state"], []).append([float(q[k]) for k in ("t_ns", "in_p", "in_m", "out_p", "out_m")])
titles = {"1_quiet_-95mV": "IN+ 95 mV below IN−, freshly reset",
          "2_inside_band_+10mV": "IN+ 10 mV above IN− (inside the transition)",
          "3_back_to_-95mV": "Back to 95 mV below IN−: still oscillating (latched)"}
fig, axes = plt.subplots(3, 2, figsize=(15, 10), facecolor=SURFACE, sharex=True)
for row, (k, v) in enumerate(sorted(d.items())):
    a = np.array(v); t = a[:, 0]
    lag = ""
    x = a[:, 2] - a[:, 2].mean(); y = a[:, 3] - a[:, 3].mean()
    if y.std() > 0.05:
        cc = np.correlate(x, y, "full"); k0 = np.argmax(np.abs(cc)) - (len(x) - 1)
        lag = f"   IN− wiggle vs OUT+: correlation {np.corrcoef(x, y)[0,1]:+.2f}"
    for col in (0, 1):
        ax = axes[row, col]
        ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax = axes[row, 0]
    ax.plot(t, a[:, 1], color=BLUE, lw=1.4, label=f"IN+ (CH1), {1e3*np.ptp(a[:,1]):.0f} mV pk-pk")
    ax.plot(t, a[:, 2], color=ORANGE, lw=1.4, label=f"IN− (CH2), {1e3*np.ptp(a[:,2]):.0f} mV pk-pk")
    ax.set_ylim(1.0, 1.4); ax.set_ylabel("V")
    ax.set_title(f"Inputs: {titles.get(k, k)}", loc="left", fontweight="bold", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax = axes[row, 1]
    ax.plot(t, a[:, 3], color=GREEN, lw=1.4, label=f"OUT+ (CH3), {1e3*np.ptp(a[:,3]):.0f} mV pk-pk")
    ax.plot(t, a[:, 4], color=PURPLE, lw=1.4, label=f"OUT− (CH4), {1e3*np.ptp(a[:,4]):.0f} mV pk-pk")
    ax.axhspan(1.10, 1.50, color=INK_2, alpha=0.06)
    ax.set_ylim(0.6, 2.0)
    ax.set_title("Outputs (grey band = normal LVDS levels 1.10–1.50 V)" + lag, loc="left", fontweight="bold", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
for col in (0, 1): axes[2, col].set_xlabel("Time (ns)")
for ax in axes.flat: ax.set_xlim(0, 300)
fig.suptitle("Comparator, 23 Nov 20:11: all four channels in three states (50 ns/div, 500 MS/s; outputs at 200 mV/div so they do not clip)",
             x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = f.replace(".csv", ".png"); fig.savefig(out, dpi=140, facecolor=SURFACE); print("saved", out)
