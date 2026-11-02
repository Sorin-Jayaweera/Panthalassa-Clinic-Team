"""Pluto leak test: spectrum at each SM200B centre, tone off and on, levels referred to before the 23 dB pads."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent
z = np.load(HERE / "pluto_leak_1nov.npz")
fs, pad = float(z["fs"]), float(z["pad_db"])
CASES = [("near_dc", 21e6, "near DC"), ("if_1p105GHz", 1.105e9, "1.105 GHz")]
STATES = [("tone_off", "Pluto OFF", "#c8691c"), ("tone_on", "Pluto ON, 1105 MHz, -36 dBm", "#1f5fa8")]
n = 65536
win = np.hanning(n)
fig, axes = plt.subplots(2, 2, figsize=(13, 7), sharey=True)
for col, (case, center, title) in enumerate(CASES):
    for row, (state, label, color) in enumerate(STATES):
        ax = axes[row, col]
        iq = z[f"{state}_{case}"]
        sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq[:n] * win))) / win.sum() + 1e-20) + pad
        fr = (center + np.fft.fftshift(np.fft.fftfreq(n, 1 / fs))) / 1e6
        ax.plot(fr, sp, lw=0.6, color=color)
        k = int(sp.argmax())
        ax.annotate(f"{sp[k]:.1f} dBm at {fr[k]:.2f} MHz", (fr[k], sp[k]), xytext=(8, -2), textcoords="offset points", fontsize=9)
        ax.set_title(f"{label}: {title} window")
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("dBm before pads")
        ax.grid(alpha=0.3)
fig.tight_layout()
wiring.add_strip(fig, wiring.P103X3)
fig.savefig(HERE / "pluto_leak_1nov.png", dpi=110)
