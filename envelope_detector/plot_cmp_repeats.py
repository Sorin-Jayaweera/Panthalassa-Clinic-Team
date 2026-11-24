"""23 Nov Test B: sweep 6 vs the three repeats, plus a time view of repeat 1 and the 15:05 snapshots.
    ~/miniforge3/envs/gr/bin/python plot_cmp_repeats.py
"""
import csv
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, GREEN = "#2a78d6", "#1f9d6b"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 9.5, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
def style(ax):
    ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
RUNS = (("data/cmp_sweep_20261123_142549.csv", "sweep 6, 14:25 (earlier wiring)", "#9a9a9a"),
        ("data/cmp_sweep_20261123_150456.csv", "repeat 1, 15:05", "#2a78d6"),
        ("data/cmp_sweep_20261123_150934.csv", "repeat 2, 15:09", "#1f9d6b"),
        ("data/cmp_sweep_20261123_151822.csv", "repeat 3, 15:18, Mac charger in", "#eb6834"))

fig = plt.figure(figsize=(16, 11.5), facecolor=SURFACE)
gs = fig.add_gridspec(4, 6, height_ratios=[1.2, 0.9, 0.2, 1.1], hspace=0.6, wspace=0.35)
axA = fig.add_subplot(gs[0, :3]); axB = fig.add_subplot(gs[0, 3:])
for ax in (axA, axB): style(ax)
for f, lab, c in RUNS:
    r = list(csv.DictReader(open(f)))
    for d, ls in (("up", "-"), ("down", ":")):
        q = sorted([x for x in r if x["dir"] == d], key=lambda x: float(x["diff_in_mv"]))
        x = [float(v["diff_in_mv"]) for v in q]
        axA.plot(x, [1e3 * float(v["out_diff"]) for v in q], ls, color=c, lw=1.4, label=f"{lab}" if d == "up" else None)
        axB.plot(x, [float(v["out_rms_mv"]) for v in q], ls, color=c, lw=1.4)
for ax in (axA, axB): ax.set_xlim(-60, 80); ax.set_xlabel("IN+ − IN− (mV, scope)")
axA.set_ylabel("OUT+ − OUT−, average (mV)")
axA.set_title("A. Average output (solid: IN+ going up, dotted: down)", loc="left", fontweight="bold")
axA.legend(frameon=False, fontsize=8, loc="upper left")
axB.set_ylabel("Output variation, rms (mV)")
axB.set_title("B. How hard the output toggles at each step", loc="left", fontweight="bold")

# time view of repeat 1
r = list(csv.DictReader(open(RUNS[1][0])))
t0 = datetime.fromisoformat(r[0]["time"])
t = np.array([(datetime.fromisoformat(q["time"]) - t0).total_seconds() for q in r])
dv = np.array([float(q["diff_in_mv"]) for q in r]); od = np.array([1e3 * float(q["out_diff"]) for q in r]); rms = np.array([float(q["out_rms_mv"]) for q in r])
axC = fig.add_subplot(gs[1, :]); style(axC)
axC.fill_between(t, od - rms, od + rms, step="post", color=GREEN, alpha=0.22, label="± output variation (rms)")
axC.step(t, od, where="post", color=GREEN, lw=1.5, label="OUT+ − OUT− average (mV, left)")
axC2 = axC.twinx(); axC2.step(t, dv, where="post", color=BLUE, lw=1.2, label="IN+ − IN− (mV, right)")
axC2.set_ylim(-160, 160); axC.set_ylim(-1100, 1100)
axC.set_xlabel("Time since repeat 1 started (s)"); axC.set_ylabel("Output (mV)"); axC2.set_ylabel("Input (mV)", color=BLUE)
h1, l1 = axC.get_legend_handles_labels(); h2, l2 = axC2.get_legend_handles_labels()
axC.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left", ncol=3)
axC.set_title("C. Repeat 1 against time: input staircase (blue) and output (green)", loc="left", fontweight="bold")

s = {}
for q in csv.DictReader(open("data/cmp_snapshots_20261123_1505.csv")):
    d = s.setdefault(int(q["code"]), {k: [] for k in ("t", "inp", "inm", "op", "om")})
    for k, col in (("t", "t_ns"), ("inp", "in_p"), ("inm", "in_m"), ("op", "out_p"), ("om", "out_m")):
        d[k].append(float(q[col]))
for i, code in enumerate(sorted(s)):
    d = {k: np.array(v) for k, v in s[code].items()}
    ax = fig.add_subplot(gs[3, i]); style(ax)
    ax.plot(d["t"], 1e3 * (d["op"] - d["om"]), color=GREEN, lw=1.0, label="OUT+ − OUT−")
    ax.plot(d["t"], 1e3 * (d["inp"] - d["inp"].mean()) * 5, color=BLUE, lw=0.9, alpha=0.8, label="IN+ wiggle ×5")
    ax.set_ylim(-900, 900); ax.set_xlim(0, 400); ax.set_xlabel("Time (ns)")
    ax.set_title(f"IN+ − IN− = {1e3*(d['inp'].mean()-d['inm'].mean()):+.0f} mV", loc="left", fontsize=10, fontweight="bold")
    if i == 0: ax.set_ylabel("mV"); ax.legend(frameon=False, fontsize=7.5, loc="upper right")
y0 = fig.axes[-1].get_position().y1 + 0.035
fig.text(0.125, y0, "D. Snapshots at 15:05, IN+ held still at each level (first 400 ns, 500 MS/s)", fontsize=11, fontweight="bold")
fig.suptitle("Comparator Test B, 23 Nov: three repeats after the wiring fixes, against the earlier sweep 6",
             x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig("data/cmp_testB_repeats_20261123.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
print("saved")
