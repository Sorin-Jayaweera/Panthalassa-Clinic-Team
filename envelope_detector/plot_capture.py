"""Plot the raw captures from ed_capture.py: VENV ripple (CW) and the average 10 us pulse.

    ~/miniforge3/envs/gr/bin/python plot_capture.py data/ed_capture_ripple_<t>.csv data/ed_capture_pulse10us_<t>.csv
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def load(path):
    d = {}
    for r in csv.DictReader(line for line in open(path) if not line.startswith("#")):
        d.setdefault((r["state"], float(r["fs_hz"]), int(r["capture"])), []).append(float(r["venv_v"]))
    return {k: np.array(v) for k, v in d.items()}


def spectrum(v, fs):
    x = v - v.mean()
    w = np.hanning(len(x))
    return np.fft.rfftfreq(len(x), 1 / fs), np.abs(np.fft.rfft(x * w)) * 2 / w.sum()


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main(f_ripple, f_pulse):
    plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                         "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})
    rip = load(f_ripple)
    fs = 10e6
    on, off = rip[("RF", fs, 0)], rip[("no RF", fs, 0)]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), facecolor=SURFACE)
    for ax in axes:
        style(ax)

    ax = axes[0]
    t = np.arange(200) / fs * 1e6
    ax.plot(t, (on[:200] - on.mean()) * 1e3, color=ORANGE, lw=1.6, label="RF on, CW at TX 0 dB")
    ax.plot(t, (off[:200] - off.mean()) * 1e3, color=BLUE, lw=1.6, label="RF off")
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("VENV minus its mean (mV)")
    ax.set_title("A. VENV ripple, 10 MS/s", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right")

    ax = axes[1]
    for v, c, lab in ((on, ORANGE, "RF on"), (off, BLUE, "RF off")):
        f, s = spectrum(v, fs)
        ax.semilogy(f / 1e3, np.maximum(s * 1e3, 1e-3), color=c, lw=1.2, label=lab)
    for x, txt in ((400, "400 kHz, 13.7 mV"), (800, "800 kHz, 1.2 mV")):
        ax.annotate(txt, xy=(x, 13.7 if x == 400 else 1.2), xytext=(x + 120, 30 if x == 400 else 3), color=INK_2, fontsize=9,
                    arrowprops=dict(arrowstyle="->", color=INK_2, lw=0.8))
    ax.set_xlim(0, 2000)
    ax.set_ylim(0.01, 100)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Line amplitude (mV peak)")
    ax.set_title("B. Ripple spectrum: one line at 4 × the tone offset", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right")

    pul = load(f_pulse)
    fs = 40e6
    segs = []
    for k, v in pul.items():
        if k[0] != "RF" or k[1] != fs:
            continue
        mid = (np.percentile(v, 5) + np.percentile(v, 95)) / 2
        for i in np.where((v[:-1] < mid) & (v[1:] >= mid))[0]:
            if i - 80 >= 0 and i + 520 < len(v):
                segs.append(v[i - 80:i + 520])
    base = np.mean([v.mean() for k, v in pul.items() if k[0] == "no RF"])
    avg = np.mean(segs, axis=0)
    t = (np.arange(len(avg)) - 80) / fs * 1e6
    ax = axes[2]
    ax.plot(t, avg, color=ORANGE, lw=1.8, label=f"average of {len(segs)} pulses, 40 MS/s")
    ax.axhline(1.4005, ls="--", color=INK_2, lw=1, label="CW level at TX 0 dB")
    ax.axhline(base, ls=":", color=INK_2, lw=1, label="no-RF level")
    ax.set_xlabel("Time from rising edge (µs)")
    ax.set_ylabel("VENV (V)")
    ax.set_ylim(1.1, 1.46)
    ax.set_title("C. 10 µs pulse: 0.65 µs edges, ripple on top", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="center right")

    fig.suptitle("Test A extra checks, 1 Nov: VENV ripple source and pulse shape (1.1 GHz, Pluto …dfdb)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = os.path.join(os.path.dirname(os.path.abspath(f_ripple)), "ed_ripple_and_pulse_shape_20261101.png")
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    print("plot:", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
