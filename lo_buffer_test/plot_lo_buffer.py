"""Plots for the LO buffer amp (ZX60-14012L-S+) gain test of 12 Oct 2026."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"


def load(name):
    return list(csv.DictReader(open(HERE / name)))


a_lvl = {float(r["att_db"]): float(r["level_dbm"]) for r in load("runA_direct_20261012.csv") if r["att_db"] != "off"}
b = load("runB_amp_20261012.csv")
b_lvl = {float(r["att_db"]): float(r["level_dbm"]) for r in b if r["run"] == "B_amp" and r["att_db"] != "off"}
b_frq = {float(r["freq_set_hz"]): float(r["level_dbm"]) for r in b if r["run"] == "B_amp_freq"}
a_frq = {float(r["freq_set_hz"]): float(r["level_dbm"]) for r in load("runA_direct_freq_20261012.csv")}

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
f = np.array(sorted(a_frq))
g = np.array([b_frq[x] - a_frq[x] for x in f])
ax[0].plot(f / 1e6, g, "o-", color="tab:green", lw=1.8, label="Measured gain (with amp minus without amp)")
for x, y in zip(f / 1e6, g):
    ax[0].annotate(f"{y:.1f} dB", (x, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9)
ax[0].axhline(11.03, color="gray", ls="--", lw=1, label="Datasheet typical at 1000 MHz: 11.03 dB")
ax[0].axhline(9.0, color="tab:red", ls=":", lw=1.2, label="Datasheet minimum: 9 dB")
ax[0].set(xlabel="Frequency (MHz)", ylabel="Gain (dB)", ylim=(8, 13), title="Gain vs frequency, input about -39 dBm")
ax[0].grid(alpha=0.3)
ax[0].legend(fontsize=8, loc="lower center")

att = np.array(sorted(a_lvl, reverse=True))
pin = np.array([a_lvl[x] for x in att])
pout = np.array([b_lvl[x] for x in att])
ax[1].plot(pin, pout, "o-", color="tab:green", lw=1.8, label="Measured")
gm = float(np.mean(pout - pin))
xx = np.array([pin.min() - 2, pin.max() + 2])
ax[1].plot(xx, xx + gm, "--", color="gray", lw=1, label=f"Straight line: output = input + {gm:.1f} dB")
for x, y in zip(pin, pout):
    ax[1].annotate(f"gain {y - x:.1f} dB", (x, y), xytext=(8, -4), textcoords="offset points", fontsize=9)
ax[1].set(xlabel="Input power, measured without the amp (dBm)", ylabel="Output power, measured with the amp (dBm)",
          title="Output vs input at 1100 MHz")
ax[1].grid(alpha=0.3)
ax[1].legend(fontsize=8, loc="upper left")
fig.suptitle("LO buffer amp ZX60-14012L-S+ at 12 V: gain test with the Pluto as source, 12 Oct 2026", fontweight="bold")
fig.tight_layout()
for out in (HERE / "lo_buffer_gain.png", IMG / "lobuf_gain.png"):
    fig.savefig(out, dpi=125)
print("mean gain vs level %.2f dB; vs frequency mean %.2f, min %.2f, max %.2f" % (gm, g.mean(), g.min(), g.max()))
