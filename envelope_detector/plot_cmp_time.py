"""Time views of Test B on 23 Nov: (A) sweep 6 step by step, (B) 2.8 us waveform snapshots at six IN+ levels.
    ~/miniforge3/envs/gr/bin/python plot_cmp_time.py
"""
import csv
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GREEN, PURPLE = "#2a78d6", "#eb6834", "#1f9d6b", "#7b4fc4"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 9.5, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
def style(ax):
    ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)

fig = plt.figure(figsize=(16, 10), facecolor=SURFACE)
gs = fig.add_gridspec(4, 6, height_ratios=[1, 1, 0.15, 1.3], hspace=0.55, wspace=0.35)

# ---- A: sweep 6 against time
r = list(csv.DictReader(open("data/cmp_sweep_20261123_142549.csv")))
t0 = datetime.fromisoformat(r[0]["time"])
t = np.array([(datetime.fromisoformat(q["time"]) - t0).total_seconds() for q in r])
dv = np.array([float(q["diff_in_mv"]) for q in r]); setv = np.array([float(q["set_v"]) for q in r])
od = np.array([1e3 * float(q["out_diff"]) for q in r]); rms = np.array([float(q["out_rms_mv"]) for q in r])
ax1 = fig.add_subplot(gs[0, :]); style(ax1)
ax1.step(t, 1e3 * setv, where="post", color=BLUE, lw=1.6, label="CGR-201 C2BJ0VL setting (mV)")
ax1b = ax1.twinx(); ax1b.step(t, dv, where="post", color=ORANGE, lw=1.2, label="IN+ − IN− at the board (scope, mV)")
ax1b.axhspan(-8, 32, color=ORANGE, alpha=0.08)
ax1.set_ylabel("Setting (mV)", color=BLUE); ax1b.set_ylabel("IN+ − IN− (mV)", color=ORANGE)
ax1.set_title("A. Input: the staircase fed into J1 during sweep 6 (14:25, up then down; shaded = transition)", loc="left", fontweight="bold")
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax1b.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
ax2 = fig.add_subplot(gs[1, :], sharex=ax1); style(ax2)
ax2.fill_between(t, od - rms, od + rms, step="post", color=GREEN, alpha=0.25, label="± output variation (rms) in each 14 µs capture")
ax2.step(t, od, where="post", color=GREEN, lw=1.6, label="OUT+ − OUT−, average")
ax2.set_ylabel("OUT+ − OUT− (mV)"); ax2.set_xlabel("Time since the sweep started (s)")
ax2.set_title("Output: low (−395 mV), then the transition, then high (+375 mV), and back", loc="left", fontweight="bold")
ax2.legend(frameon=False, fontsize=8, loc="upper left")

# ---- B: snapshots
s = {}
for q in csv.DictReader(open("data/cmp_snapshots_20261123.csv")):
    d = s.setdefault(int(q["code"]), {k: [] for k in ("t", "inp", "inm", "op", "om")})
    d["t"].append(float(q["t_ns"])); d["inp"].append(float(q["in_p"])); d["inm"].append(float(q["in_m"]))
    d["op"].append(float(q["out_p"])); d["om"].append(float(q["out_m"]))
for i, code in enumerate(sorted(s)):
    d = {k: np.array(v) for k, v in s[code].items()}
    ax = fig.add_subplot(gs[3, i]); style(ax)
    diff = 1e3 * (d["inp"].mean() - d["inm"].mean())
    ax.plot(d["t"], 1e3 * (d["op"] - d["om"]), color=GREEN, lw=1.0, label="OUT+ − OUT−")
    ax.plot(d["t"], 1e3 * (d["inp"] - d["inp"].mean()) * 5, color=BLUE, lw=0.9, alpha=0.8, label="IN+ wiggle ×5")
    ax.set_ylim(-900, 900); ax.set_xlim(0, 400)
    ax.set_title(f"IN+ − IN− = {diff:+.0f} mV", loc="left", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time (ns)")
    if i == 0:
        ax.set_ylabel("mV"); ax.legend(frameon=False, fontsize=7.5, loc="upper right")
fig.text(0.01, 0.37, "B. Output waveform snapshots taken at 15:01 (first 400 ns of 2.8 µs, 500 MS/s), IN+ held still at each level",
         fontsize=11, fontweight="bold")
fig.suptitle("Comparator Test B, 23 Nov: input and output against time", x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig("data/cmp_testB_time_20261123.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
print("saved")
