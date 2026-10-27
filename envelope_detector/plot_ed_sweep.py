"""Plot and summarize an ed_sweep.py CSV (Test A, Step 4).

    ~/miniforge3/envs/gr/bin/python plot_ed_sweep.py data/ed_sweep_1.10GHz_<time>.csv

Input power comes from the two ADL5511 outputs and the datasheet gains at
~1.1 GHz (interpolated between the 900 MHz and 1.9 GHz columns):
    VRMS        = 1.91 x Vin_rms + offset   (offset = mean VRMS with no RF)
    VENV - EREF = 1.47 x Vin_rms            (VENV rise over the no-RF baseline)
"""

import csv
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

GAIN_VRMS = 1.91
GAIN_VENV = 1.47
NO_RF_LEVEL_DB = -50  # rows at or below this level count as "no signal"
FIT_FROM_DB = -10  # anchor the Pluto calibration on the strongest steps, far above the ED floor

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def dbm(v_rms):
    return 10 * math.log10(v_rms**2 / 50 / 1e-3) if v_rms > 0 else float("nan")


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(line for line in f if not line.startswith("#")))
    return [{k: float(v) if v not in ("",) and k != "time" else v for k, v in r.items()} for r in rows]


def main(path):
    rows = load(path)
    level = [r["tx_level_db"] for r in rows]
    rise = [r["venv_rise_v"] for r in rows]
    vrms = [r["vrms_dmm_v"] for r in rows]
    noise = [r["venv_noise_mv"] for r in rows]

    vrms0 = sum(v for v, l in zip(vrms, level) if l <= NO_RF_LEVEL_DB) / sum(l <= NO_RF_LEVEL_DB for l in level)
    p_vrms = [dbm((v - vrms0) / GAIN_VRMS) for v in vrms]
    p_venv = [dbm(r / GAIN_VENV) for r in rise]
    ratio = [r / (v - vrms0) if v - vrms0 > 0.005 else float("nan") for r, v in zip(rise, vrms)]

    # Pin = TX level + p0, from both outputs on the strongest steps; the Pluto's
    # attenuator then sets every lower level (it steps in exact dB).
    fit = [(l, pv) for l, pv, pe in zip(level, p_vrms, p_venv) if l >= FIT_FROM_DB for pv in (pv, pe)]
    p0 = sum(pv - l for l, pv in fit) / len(fit)
    worst_dev = max(abs(p - (l + p0)) for l, p in fit)
    p_true = [l + p0 for l in level]
    vin_true = [math.sqrt(10 ** (p / 10) * 1e-3 * 50) for p in p_true]

    # ---- figure: three small multiples sharing the TX-level axis
    plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK_2,
                         "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
                         "text.color": INK})
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), facecolor=SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xlabel("Pluto TX level (dB, = -attenuation)")
        ax.set_xlim(-50, 2)

    # A: both ED outputs above their no-RF values, log scale
    ax = axes[0]
    pos = lambda xs: [x * 1e3 if x > 0 else float("nan") for x in xs]
    ax.semilogy(level, pos(rise), "-o", color=BLUE, lw=2, ms=6, mec=SURFACE, mew=1.5, label="VENV − baseline")
    # below ~2 mV the VRMS rise is just the DMM's 1 mV resolution
    ax.semilogy(level, [x if x > 2 else float("nan") for x in pos([v - vrms0 for v in vrms])], "-s", color=ORANGE, lw=2, ms=6, mec=SURFACE, mew=1.5,
                label=f"VRMS − {vrms0 * 1e3:.1f} mV offset")
    ref = [rise[-1] * 1e3 * 10 ** ((l - level[-1]) / 20) for l in level]
    ax.semilogy(level, ref, "--", color=INK_2, lw=1, label="ideal: ×10 per 20 dB")
    ax.set_ylim(0.2, 1000)
    ax.set_ylabel("Output rise (mV)")
    ax.set_title("A. ED outputs vs TX level", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

    # B: input power from each output, with the calibration line
    ax = axes[1]
    ax.plot(level, p_vrms, "-s", color=ORANGE, lw=2, ms=6, mec=SURFACE, mew=1.5, label="from VRMS (DMM)")
    ax.plot(level, p_venv, "-o", color=BLUE, lw=2, ms=6, mec=SURFACE, mew=1.5, label="from VENV (CGR-201)")
    xs = [-45, 0]
    ax.plot(xs, [x + p0 for x in xs], "--", color=INK_2, lw=1,
            label=f"calibration: Pin = TX level {p0:+.2f} dB".replace("-", "−"))
    ax.set_ylim(-50, 5)
    ax.set_ylabel("Power at ED RFIN (dBm)")
    ax.set_title("B. Pluto calibration at 1.1 GHz", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

    # C: VENV rise vs the calibrated input power = the comparator threshold lookup
    ax = axes[2]
    pts = [(p, r * 1e3) for p, r in zip(p_true, rise) if r > 0.002]
    ax.semilogy([p for p, _ in pts], [r for _, r in pts], "-o", color=BLUE, lw=2, ms=6, mec=SURFACE, mew=1.5,
                label="measured VENV − baseline")
    xs = [x / 2 for x in range(-90, 5)]
    ax.semilogy(xs, [GAIN_VENV * math.sqrt(10 ** (x / 10) * 1e-3 * 50) * 1e3 for x in xs], "--", color=INK_2,
                lw=1, label=f"datasheet: {GAIN_VENV} × Vin")
    ax.set_xlim(-45, 3)
    ax.set_ylim(0.2, 1000)
    ax.set_xlabel("Power at ED RFIN (dBm, calibrated)")
    ax.set_ylabel("VENV − baseline (mV)")
    ax.set_title("C. Threshold lookup: VENV vs input power", loc="left", fontweight="bold")
    ax.annotate("ED floor ≈ −30 dBm:\nbelow it VENV sinks\ninto its offset", xy=(-30, 4.2), xytext=(-24, 0.45),
                color=INK_2, fontsize=9, arrowprops=dict(arrowstyle="->", color=INK_2, lw=0.8))
    ax.legend(frameon=False, loc="upper left")

    fig.suptitle(f"Test A — ADL5511 envelope detector, CW sweep at {rows[0]['freq_hz'] / 1e9:.2f} GHz",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out_png = os.path.splitext(path)[0] + ".png"
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)

    print(f"plot: {out_png}")
    print(f"VRMS no-RF offset: {vrms0 * 1e3:.1f} mV")
    print(f"Pluto calibration: Pin = TX level {p0:+.2f} dB (from TX >= {FIT_FROM_DB} dB, both outputs,"
          f" worst deviation {worst_dev:.2f} dB)")
    print("tx_db | Pin cal dBm | VENV rise mV | VENV gain V/V | VRMS V | Pin(VRMS) | Pin(VENV) | ratio | noise mV")
    for l, pt, vt, r, v, pv, pe, ra, nz in zip(level, p_true, vin_true, rise, vrms, p_vrms, p_venv, ratio, noise):
        print(f"{l:5.0f} | {pt:11.1f} | {r * 1e3:12.1f} | {r / vt:13.2f} | {v:6.3f} | {pv:9.1f} | {pe:9.1f}"
              f" | {ra:5.2f} | {nz:6.1f}")
    print("threshold above baseline -> trips at (calibrated input power, log-interpolated):")
    pts = [(r, p) for p, r in zip(p_true, rise) if r > 0.002]
    for dv in (0.005, 0.010, 0.020, 0.050, 0.100, 0.200):
        for (r1, p1), (r2, p2) in zip(pts, pts[1:]):
            if r1 <= dv <= r2:
                f = math.log10(dv / r1) / math.log10(r2 / r1)
                print(f"  +{dv * 1e3:5.0f} mV -> {p1 + f * (p2 - p1):6.1f} dBm")


if __name__ == "__main__":
    main(sys.argv[1])
