"""Plots for a run folder produced by run_step_test.py.

Usage: python plot_results.py data/<timestamp>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main(folder):
    folder = Path(folder)
    d = np.genfromtxt(folder / "summary.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    d = np.atleast_1d(d)
    tr = np.load(folder / "mean_traces.npz")
    t_ns = tr["t"] * 1e9
    his = d["v_hi_set"]
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(his)))

    # 1. frequency vs time for every step, with the drive edge
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True, gridspec_kw={"height_ratios": [1, 2.5]})
    for hi, c in zip(his, colors):
        ax1.plot(t_ns, tr[f"hi{hi:.2f}_drive_v"], color=c, lw=1)
        ax2.plot(t_ns, tr[f"hi{hi:.2f}_freq_hz"] / 1e6, color=c, lw=1, label=f"{hi:.2f} V")
    ax1.set_ylabel("Drive on Vt (V)")
    ax1.set_title(f"VCO step response, low level {d['v_lo_set'][0]:.2f} V, {d['square_wave_hz'][0]/1e3:.0f} kHz square wave")
    ax2.set_ylabel("VCO frequency (MHz)")
    ax2.set_xlabel("Time after drive 50 % crossing (ns)")
    ax2.set_xlim(-300, 1500)
    ax2.legend(title="High level", ncol=2, fontsize=8)
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(folder / "freq_vs_time.png", dpi=130)

    # 2. rise time vs high voltage
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(his, d["f_rise_10_90_s"] * 1e9, yerr=d["f_rise_10_90_group_std_s"] * 1e9, fmt="o-", capsize=3,
                label="VCO frequency, 10-90 %")
    ax.plot(his, d["drive_rise_10_90_s"] * 1e9, "s--", color="gray", label="Drive voltage on Vt, 10-90 %")
    ax.set_xlabel("Square-wave high level (V); low level %.2f V" % d["v_lo_set"][0])
    ax.set_ylabel("Rise time (ns)")
    ax.set_title("Rise time vs input voltage")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "rise_time_vs_voltage.png", dpi=130)

    # 3. settled frequency vs voltage: scope measurement against expectations
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(d["v_hi_meas"], d["f_hi_meas_hz"] / 1e6, "o-", label="Scope, settled after step")
    ax.plot(d["v_hi_meas"], d["f_hi_static_today_hz"] / 1e6, "x:", label="Scope, static DC (today)")
    ax.plot(d["v_hi_meas"], d["f_hi_expected_hz"] / 1e6, "s--", label="Expected (spectrum-analyzer table)")
    ax.plot(d["v_hi_meas"], d["f_hi_datasheet_hz"] / 1e6, ":", color="gray", label="0.8 GHz + 60 MHz/V line")
    ax.set_xlabel("Tuning voltage (V)")
    ax.set_ylabel("VCO frequency (MHz)")
    ax.set_title("Settled VCO frequency vs tuning voltage")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "freq_vs_voltage.png", dpi=130)
    print("plots written to", folder)


if __name__ == "__main__":
    main(sys.argv[1])
