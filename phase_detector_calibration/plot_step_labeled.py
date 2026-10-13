"""Step response plots with every panel and curve labelled."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RUN = HERE / "step_response" / "20261010_182707"
tr = np.genfromtxt(RUN / "mean_traces_clean_calibration.csv", delimiter=",", names=True)
rows = {(r["edge"], float(r["v_lo_set"]), float(r["v_hi_set"])): r for r in csv.DictReader(open(RUN / "summary_clean_calibration.csv"))}
t = tr["time_ns"]
HI = (0.4, 0.6, 0.8, 1.0, 1.15)
COL = plt.cm.viridis(np.linspace(0, 0.85, len(HI)))
X0, X1 = -150, 600

for edge in ("rise", "fall"):
    rising = edge == "rise"
    fig, ax = plt.subplots(3, 1, figsize=(11, 12.5), sharex=True)
    for hi, c in zip(HI, COL):
        tag = f"{edge}_lo020_hi{hi:.2f}".replace(".", "")
        r = rows[(edge, 0.2, hi)]
        d, m, f = tr[tag + "_drive_V"], tr[tag + "_mixer_mV"], tr[tag + "_freq_MHz"]
        end = (t > 450) & (t < 600)
        step = f"0.20 to {hi:.2f} V" if rising else f"{hi:.2f} to 0.20 V"
        ax[0].plot(t, d, color=c, lw=1.6, label=f"{step}   (10-90 % in {float(r['drive_rise_10_90_ns']):.0f} ns)")
        ax[1].plot(t, m, color=c, lw=1.6, label=f"{step}   (10-90 % in {float(r['mixer_rise_10_90_ns']):.0f} ns)")
        ax[2].plot(t, f, color=c, lw=1.6, label=f"{step}   (10-90 % in {float(r['freq_rise_10_90_ns']):.0f} ns)")
        start = t < -100
        for a, y, unit, fmt in ((ax[0], d, "V", "{:.2f}"), (ax[1], m, "mV", "{:.1f}"), (ax[2], f, "MHz", "{:.1f}")):
            if rising:      # label where the curves are apart: the end for rising steps, the start for falling steps
                a.annotate(fmt.format(np.median(y[end])) + " " + unit, (X1, np.median(y[end])), xytext=(6, 0), textcoords="offset points",
                           va="center", fontsize=9, color=c, annotation_clip=False)
            else:
                a.annotate(fmt.format(np.median(y[start])) + " " + unit, (X0, np.median(y[start])), xytext=(5, 4), textcoords="offset points",
                           va="bottom", fontsize=9, color=c)
                if hi == HI[0]:
                    a.annotate("all end at " + fmt.format(np.median(y[end])) + " " + unit, (X1, np.median(y[end])), xytext=(-6, 6),
                               textcoords="offset points", ha="right", va="bottom", fontsize=9, color="k")
    titles = ("1. INPUT: voltage on the VCO tuning pin (Syscomp output, read on scope CH1)",
              "2. OUTPUT: mixer voltage (read on scope CH2)",
              "3. OUTPUT converted to frequency (panel 2 passed through the mixer look up table)")
    ylabels = ("Tuning voltage (V)", "Mixer output (mV)", "Frequency (MHz)")
    for a, ti, yl in zip(ax, titles, ylabels):
        a.set_title(ti, loc="left", fontsize=11, fontweight="bold")
        a.set_ylabel(yl)
        a.axvline(0, color="gray", lw=0.9, ls="--")
        a.grid(alpha=0.3)
        a.margins(y=0.12)
        a.legend(title="Step on the tuning pin", fontsize=8.5, title_fontsize=9, loc="upper left" if rising else "upper right")
    ax[0].set_xlim(X0, X1)
    y0, y1 = ax[0].get_ylim()
    ax[0].annotate("time 0 = input crosses half-way", (0, y0 + (0.04 if rising else 0.5) * (y1 - y0)), xytext=(8, 0), textcoords="offset points", fontsize=9, color="gray")
    tag = f"{edge}_lo020_hi115"
    d = tr[tag + "_drive_V"]
    sel = (t > -80) & (t < -20)
    k = np.argmax(d[sel]) if rising else np.argmin(d[sel])
    ax[0].annotate("spike at the start of the edge.\nIt comes from the Syscomp, not the VCO.", (t[sel][k], d[sel][k]),
                   xytext=(130, 0.27 if rising else 0.95), textcoords="data", fontsize=9, arrowprops=dict(arrowstyle="->", color="k"))
    ax[2].set_xlabel("Time after the input crosses half-way (ns)")
    kind = "rising" if rising else "falling"
    where = "right end" if rising else "left end"
    lines = [f"Step response, {kind} steps: input and output on the same time axis",
             "50 kHz square wave on the tuning pin. Each curve is the average of about 420 edges.",
             f"The number at the {where} of each curve is its {'final' if rising else 'starting'} value."]
    fig.suptitle(chr(10).join(lines), fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 0.94, 0.985))
    for out in (RUN / f"step_response_{edge}.png", HERE / "site" / "img" / f"step_{edge}.png"):
        fig.savefig(out, dpi=125)
    plt.close(fig)
print("done")
