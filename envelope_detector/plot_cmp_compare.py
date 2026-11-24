"""Compare Test B sweeps: 19 Nov (sweep 2) and 23 Nov (E3630A, local grounding).
    ~/miniforge3/envs/gr/bin/python plot_cmp_compare.py
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                     "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
RUNS = (("data/cmp_sweep_20261119_122720.csv", "19 Nov: KUAIQU-type switching supply, grounds on one long wire", ORANGE),
        ("data/cmp_sweep_20261123_142549.csv", "23 Nov: linear E3630A, grounds tied locally", BLUE))
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), facecolor=SURFACE)
for ax in axes:
    ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
for f, lab, c in RUNS:
    r = [x for x in csv.DictReader(open(f)) if x["dir"] == "up"]
    x = [float(q["diff_in_mv"]) for q in r]
    axes[0].plot(x, [1e3 * float(q["out_diff"]) for q in r], "o-", ms=3, lw=1.2, color=c, label=lab)
    axes[1].plot(x, [float(q["out_rms_mv"]) for q in r], "o-", ms=3, lw=1.2, color=c, label=lab)
axes[0].set(xlabel="IN+ − IN− (mV, scope)", ylabel="OUT+ − OUT−, average (mV)", xlim=(-110, 120))
axes[0].set_title("A. Average output vs input (IN+ going up)", loc="left", fontweight="bold")
axes[1].set(xlabel="IN+ − IN− (mV, scope)", ylabel="Output variation, rms (mV)", xlim=(-110, 120))
axes[1].set_title("B. How much the output moves at each step", loc="left", fontweight="bold")
axes[0].legend(frameon=False, fontsize=8, loc="upper left")
fig.suptitle("Comparator Test B: transition region before and after the supply and grounding changes",
             x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("data/cmp_testB_compare_20261123.png", dpi=150, facecolor=SURFACE)
print("saved")
