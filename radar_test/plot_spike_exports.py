"""Plot Sorin's Spike max-hold exports of the Furuno radar (25 Oct 2026, 11 m, 14 dB of 8 GHz pads):
data/Furino Characterization/14db8G_11meters_100khzrbw.csv and ..._3mhzrbw.csv."""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "data" / "Furino Characterization"
NAME = "furuno_spike_maxhold_9370-9430MHz_rbw100kHz_vs_3MHz_11m_14dB_pads"
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"


def mark(ax, x, y, text, dx, dy, color="tab:red"):
    ax.plot([x], [y], "v", color=color, ms=7)
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=8, color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.6), arrowprops=dict(arrowstyle="-", color=color, lw=0.6))


a = np.genfromtxt(SRC / "14db8G_11meters_100khzrbw.csv", delimiter=",")
b = np.genfromtxt(SRC / "14db8G_11meters_3mhzrbw.csv", delimiter=",")
fa, ya, fb, yb = a[:, 0] / 1e6, a[:, 1], b[:, 0] / 1e6, b[:, 1]
fig, ax = plt.subplots(2, 1, figsize=(13, 9))

ia = int(np.argmax(ya))
ax[0].plot(fa, ya, lw=0.8, color="tab:blue")
mark(ax[0], fa[ia], ya[ia], f"peak {ya[ia]:.1f} dBm at {fa[ia]:.3f} MHz", 15, 10)
half = ya[ia] - 3
lo = ia
while lo > 0 and ya[lo - 1] > half:
    lo -= 1
hi = ia
while hi < len(ya) - 1 and ya[hi + 1] > half:
    hi += 1
ax[0].annotate("", xy=(fa[lo], half), xytext=(fa[hi], half), arrowprops=dict(arrowstyle="<->", color="tab:red", lw=0.8))
ax[0].text(fa[hi] + 0.3, half, f"-3 dB: {fa[hi]-fa[lo]:.2f} MHz", fontsize=8, color="tab:red", va="center")
# sidelobe peaks on the high side
pk = [i for i in range(ia + 20, min(len(ya) - 1, ia + 600)) if ya[i] == ya[max(0, i - 15):i + 16].max() and ya[i] > np.median(ya) + 10]
for n, i in enumerate(pk[:4]):
    mark(ax[0], fa[i], ya[i], f"{ya[i]-ya[ia]:+.1f} dB, {fa[i]-fa[ia]:+.2f} MHz", 20 + 25 * n, 30 + 4 * n, color="tab:purple")
nf = float(np.median(ya))
ax[0].axhline(nf, color="gray", ls=":", lw=1)
ax[0].text(fa[0] + 0.5, nf + 1.5, f"noise {nf:.1f} dBm", fontsize=8, color="gray")
ax[0].set(xlabel="Frequency (MHz)", ylabel="Max hold (dBm at the SM200B)", title="RBW 100 kHz: the pulse spectrum (narrow filter shows the sidelobes; peak reads low)")

ib = int(np.argmax(yb))
ax[1].plot(fb, yb, "o-", ms=3, lw=0.9, color="tab:orange")
mark(ax[1], fb[ib], yb[ib], f"peak {yb[ib]:.1f} dBm at {fb[ib]:.3f} MHz\n= {10**(yb[ib]/10)*1e3:.1f} µW pulse peak", 15, -10)
nfb = float(np.median(yb))
ax[1].axhline(nfb, color="gray", ls=":", lw=1)
ax[1].text(fb[0] + 0.5, nfb + 1.5, f"noise {nfb:.1f} dBm", fontsize=8, color="gray")
ax[1].set(xlabel="Frequency (MHz)", ylabel="Max hold (dBm at the SM200B)", title=f"RBW 3 MHz: wide enough to hold the 0.68 µs pulse, so this peak is close to the true pulse peak ({yb[ib]-ya[ia]:+.1f} dB vs 100 kHz)")
for x in ax:
    x.grid(alpha=0.3)
    x.set_xlim(9370, 9430)
fig.suptitle("Furuno 1722C, Spike max-hold exports: Vivaldi at 11.3 m facing the radar, AN-72 foam on the radar, whiteboard out, 14 dB of 8 GHz pads, manual attenuator 0 dB", fontsize=10, fontweight="bold")
fig.tight_layout()
out = HERE / "plots" / f"{NAME}.png"
fig.savefig(out, dpi=115)
shutil.copy2(out, IMG / f"{NAME}.png")
print(NAME, f"100k peak {ya[ia]:.2f} @ {fa[ia]:.4f}; -3 dB {fa[hi]-fa[lo]:.3f} MHz; 3M peak {yb[ib]:.2f} @ {fb[ib]:.4f}; sidelobes", [(round(fa[i]-fa[ia], 3), round(ya[i]-ya[ia], 1)) for i in pk[:4]])
