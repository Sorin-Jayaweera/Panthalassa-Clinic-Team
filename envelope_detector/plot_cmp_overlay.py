"""Overlay of Test B sweeps on 23 Nov: average output and toggling vs IN+ - IN-.
    ~/miniforge3/envs/gr/bin/python plot_cmp_overlay.py
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 9.5, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
RUNS = (("data/cmp_sweep_20261123_142549.csv", "sweep 6, 14:25", "#b5b5b5"),
        ("data/cmp_sweep_20261123_150456.csv", "triad 1, run 1, 15:05", "#7fb2ec"),
        ("data/cmp_sweep_20261123_150934.csv", "triad 1, run 2, 15:09", "#2a78d6"),
        ("data/cmp_sweep_20261123_151822.csv", "triad 1, run 3, 15:18 (charger)", "#16478a"),
        ("data/cmp_sweep_20261123_153128.csv", "baseline A, 15:31 (after wiring check)", "#f2a37f"),
        ("data/cmp_sweep_20261123_154607.csv", "triad 2, run 1, 15:46", "#eb6834"),
        ("data/cmp_sweep_20261123_155121.csv", "triad 2, run 2, 15:51", "#c44a14"),
        ("data/cmp_sweep_20261123_155549.csv", "triad 2, run 3, 15:55", "#7a2c0a"),
        ("data/cmp_sweep_20261123_172916.csv", "evening, run 1, 17:29", "#7fd1a8"),
        ("data/cmp_sweep_20261123_173336.csv", "evening, run 2, 17:33", "#1f9d6b"),
        ("data/cmp_sweep_20261123_173752.csv", "evening, run 3, 17:37", "#0e5a3c"))
fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), facecolor=SURFACE)
for ax in axes:
    ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
for f, lab, c in RUNS:
    r = list(csv.DictReader(open(f)))
    for d, ls in (("up", "-"), ("down", ":")):
        q = sorted([x for x in r if x["dir"] == d], key=lambda x: float(x["diff_in_mv"]))
        x = [float(v["diff_in_mv"]) for v in q]
        axes[0].plot(x, [1e3 * float(v["out_diff"]) for v in q], ls, color=c, lw=1.3, label=lab if d == "up" else None)
        axes[1].plot(x, [float(v["out_rms_mv"]) for v in q], ls, color=c, lw=1.3)
for ax in axes: ax.set_xlim(-110, 125); ax.set_xlabel("IN+ − IN− (mV, scope)")
axes[0].set_ylabel("OUT+ − OUT−, average (mV)"); axes[1].set_ylabel("Output variation, rms (mV)")
axes[0].set_title("A. Average output (solid: IN+ going up, dotted: down)", loc="left", fontweight="bold")
axes[1].set_title("B. Toggling strength", loc="left", fontweight="bold")
axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
fig.suptitle("Comparator Test B, 23 Nov: all sweeps (blue = triad 1, orange = triad 2, green = evening)", x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("data/cmp_testB_overlay_20261123.png", dpi=140, facecolor=SURFACE)
print("saved")
