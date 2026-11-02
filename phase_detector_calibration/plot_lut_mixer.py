"""Look up table plots and data for the phase detector: the mixer on its own, and 4 x ZX60-P162LN+ then the mixer.
Each figure has the full range, 900 to 1200 MHz, and the wiring. Saves lut_mixer_alone.png, lut_p162x4_mixer.png and lut_p162x4_mixer.csv.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent

# ---------------------------------------------------------------- mixer on its own
rows = list(csv.reader(open(HERE.parent / "data" / "Phase Detector Test  9_16_26.csv")))
SEPT = {}
for name, c in (("Pluto set -2 dBm", 1), ("Pluto set -6 dBm", 5), ("Pluto set -11 dBm", 10), ("Pluto set -12.25 dBm", 15)):
    pts = [(float(r[c]) * 1e3, float(r[c + 1])) for r in rows[5:64] if r[c] and r[c + 1] and float(r[c]) < 1.4]
    SEPT[name] = np.array(sorted(pts))
oct_ = np.genfromtxt(HERE / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
oct_ = oct_[oct_["direction"] == "up"]
oct_f, oct_mv = oct_["vco_freq_hz"] / 1e6, oct_["mixer_out_v"] * 1e3
fig, axes = wiring.figure(2, [wiring.MIXER_VCO, wiring.MIXER_PLUTO], size=(13, 10), titles=["Wiring, 10 Oct VCO sweep", "Wiring, 16 Sep Pluto sweeps"])
for ax, lim, title in ((axes[0], None, "Mixer on its own, no amplifiers: all the data, 744 to 1305 MHz"), (axes[1], (900, 1200), "Mixer on its own: 900 to 1200 MHz. No data from 920 to 1000 MHz")):
    ax.plot(oct_f, oct_mv, lw=1.2, color="0.25", label="VCO, about +0.6 dBm per port, 10 Oct")
    for name, a in SEPT.items():
        ax.plot(a[:, 0], a[:, 1], marker=".", ms=4, lw=1.1, label=name + ", 16 Sep")
    ax.set_xlabel("Input frequency (MHz)")
    ax.set_ylabel("Mixer output (mV)")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    if lim:
        ax.set_xlim(*lim)
fig.tight_layout()
fig.savefig(HERE / "lut_mixer_alone.png", dpi=110)
plt.close(fig)
with open(HERE / "lut_mixer_alone.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["source", "freq_mhz", "mixer_mv"])
    w.writerows(["VCO 10 Oct", round(float(a), 3), round(float(b), 2)] for a, b in zip(oct_f, oct_mv))
    for name, a in SEPT.items():
        w.writerows([name, x, y] for x, y in a)

# ---------------------------------------------------------------- 4 x P162 then the mixer
d = np.genfromtxt(HERE / "p162x4_map_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
m = d[d["pass"] == "map"]
m = m[~((m["freq_mhz"] == 1320) & (m["pluto_want_dbm"] == -65) & (m["detector_mean_v"] < 0.1))]
levels = np.unique(m["pluto_want_dbm"])
fig, axes = wiring.figure(2, [wiring.P162X4], size=(13, 11))
for ax, lim, title in ((axes[0], None, "4 x ZX60-P162LN+ then the mixer: 700 to 1600 MHz"), (axes[1], (900, 1200), "4 x ZX60-P162LN+ then the mixer: 900 to 1200 MHz")):
    for i, want in enumerate(levels[::-1]):
        k = np.where(m["pluto_want_dbm"] == want)[0]
        k = k[np.argsort(m["freq_mhz"][k])]
        ax.plot(m["freq_mhz"][k], m["detector_mean_v"][k] * 1e3, lw=1.1, color=plt.cm.viridis_r(i / (len(levels) - 1)), label=f"{want:.0f} dBm")
    ax.set_xlabel("Pluto frequency (MHz)")
    ax.set_ylabel("Phase detector output (mV)")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(title="Pluto level (table)", ncol=3, fontsize=8)
    if lim:
        ax.set_xlim(*lim)
        ax.set_ylim(60, 340)
fig.tight_layout()
fig.savefig(HERE / "lut_p162x4_mixer.png", dpi=110)
plt.close(fig)

rep = d[d["pass"] == "repeat"]
freqs = np.unique(rep["freq_mhz"])
med = np.array([np.median(rep["detector_mean_v"][rep["freq_mhz"] == f]) for f in freqs]) * 1e3
flat = m[m["pluto_want_dbm"] >= -65]
with open(HERE / "lut_p162x4_mixer.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["freq_mhz", "median_mv_at_-60dbm", "lowest_mv_-65_to_-30dbm", "highest_mv_-65_to_-30dbm", "levels_counted"])
    for f in np.arange(900.0, 1200.5, 5.0):
        v = flat["detector_mean_v"][flat["freq_mhz"] == f] * 1e3
        w.writerow([f, round(float(np.interp(f, freqs, med)), 1), round(float(v.min()), 1), round(float(v.max()), 1), len(v)])
fine = np.arange(900, 1201)
s = np.convolve(np.interp(fine, freqs, med), np.ones(5) / 5, mode="same")
top = fine[np.argmax(np.diff(s)[5:] < 0) + 5]
print("smoothed -60 dBm curve first stops rising at", top, "MHz")
for lo, hi in ((900, 950), (950, 1015), (960, 1010), (900, 1020), (900, 1200)):
    k = (freqs >= lo) & (freqs <= hi)
    a, b = np.polyfit(freqs[k], med[k], 1)
    print(lo, hi, "slope mV/MHz", round(a, 2), "rms off a line mV", round(float(np.std(med[k] - (a * freqs[k] + b))), 1))
print("spread -65 to -30 dBm at", {int(f): round(float(np.ptp(flat['detector_mean_v'][flat['freq_mhz'] == f]) * 1e3), 1) for f in (900, 950, 1000, 1015, 1050, 1100, 1200)})
