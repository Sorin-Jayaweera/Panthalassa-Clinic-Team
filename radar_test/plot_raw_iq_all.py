"""Every sample of one SM200B capture, unprocessed: I and Q as stored, no carrier removal by us, no filtering, no alignment.
raw_20261025_130811.npz: 3,000,000 complex samples, 50 MS/s, 60 ms, centred 9402.6 MHz. Values in sqrt(mW) at the SM200B input.
Three zooms of the same samples: the whole 60 ms, one pulse with its neighbourhood, and the pulse's first 200 ns sample by sample.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phase_detector_calibration"))
import wiring  # noqa: E402

d = np.load(HERE / "raw_20261025_130811.npz")
iq, fs = d["iq"], float(d["fs"])
t = np.arange(len(iq)) / fs
k = int(np.argmax(np.abs(iq)))
fig = plt.figure(figsize=(15, 13))
gs = fig.add_gridspec(4, 1, height_ratios=[3, 3, 3, 1], hspace=0.45, left=0.07, right=0.98, top=0.95, bottom=0.02)
for row, (lo, hi, unit, sc, title, mk) in enumerate((
        (0, len(iq), "ms", 1e3, "All 3,000,000 samples (60 ms)", ""),
        (k - 150, k + 100, "us", 1e6, "The strongest pulse, 5 us around it: every sample", "."),
        (k - 30, k + 12, "us", 1e6, "Its rising edge, 840 ns: every sample, 20 ns apart", "o"))):
    ax = fig.add_subplot(gs[row])
    ax.plot(t[lo:hi] * sc, iq.real[lo:hi], lw=0.6 if row == 0 else 1, marker=mk, ms=4, label="I")
    ax.plot(t[lo:hi] * sc, iq.imag[lo:hi], lw=0.6 if row == 0 else 1, marker=mk, ms=4, label="Q", alpha=0.85)
    ax.set_title(title)
    ax.set_xlabel(f"Time from start of capture ({unit})")
    ax.set_ylabel("Sample value (sqrt mW)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    ax.ticklabel_format(axis="x", useOffset=False, style="plain")
wiring.draw(fig.add_subplot(gs[3]), ["Furuno 1722C/NT"+chr(10)+"11.3 m, foam on radome", "Vivaldi R120", "long SMA cable", "JFW attenuator"+chr(10)+"at 0 dB",
                                     "10 + 2 + 2 dB"+chr(10)+"fixed pads", "SM200B: mixes 9402.6 MHz to 0,"+chr(10)+"stores I and Q at 50 MS/s"], "Wiring, 25 Oct 13:08")
fig.suptitle("Raw SM200B samples as stored, nothing removed or filtered by us. The carrier was taken out inside the SM200B before sampling")
fig.savefig(HERE / "plots" / "raw_iq_all.png", dpi=105)
np.savetxt(HERE / "raw_20261025_130811_strongest_pulse.csv", np.c_[np.arange(k - 150, k + 100), t[k - 150:k + 100] * 1e6, iq.real[k - 150:k + 100], iq.imag[k - 150:k + 100]],
           delimiter=",", header="sample,time_us,i_sqrt_mw,q_sqrt_mw", comments="", fmt=["%d", "%.3f", "%.6e", "%.6e"])
print("strongest sample", k, "at", round(t[k] * 1e3, 3), "ms")
