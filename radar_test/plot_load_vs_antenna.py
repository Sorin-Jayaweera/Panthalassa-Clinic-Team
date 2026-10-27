"""Peak reading at the SM200B: 50 ohm load directly on the input, 50 ohm load through the 29 dB pads, and the
Vivaldi through the 29 dB pads, at 3.96 m (13 ft) and 11.3-11.5 m. All Spike or Sorin readings, 3 MHz RBW, Min/Max, Max Hold."""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
NAME = "radar_sm200b_reading_load_direct_vs_load_29dB_vs_vivaldi_29dB"
C = {"load direct": "#2a78d6", "load + 29 dB": "#eb6834", "Vivaldi + 29 dB": "#1baf7a"}

# (distance group, label, kind, dBm, who read it)
ROWS = [
    ("3.96 m (13 ft), radar foam off", "Test 17: load on a cable, no pads", "load direct", -15.7, "Spike"),
    ("3.96 m (13 ft), radar foam off", "Test 21: load on SM200B input", "load direct", -22.5, "Spike"),
    ("3.96 m (13 ft), radar foam off", "Test 22: same, SM200B wrapped in AN-72", "load direct", -25.7, "Spike (Sorin: about -30)"),
    ("3.96 m (13 ft), radar foam off", "Test 23: same, whiteboard between", "load direct", -19.43, "Sorin"),
    ("3.96 m (13 ft), radar foam off", "Test 16: load -> 29 dB", "load + 29 dB", -20.5, "Spike"),
    ("3.96 m (13 ft), radar foam off", "Test 20: load -> 29 dB", "load + 29 dB", -22.9, "Spike"),
    ("3.96 m (13 ft), radar foam off", "Test 24: load -> 29 dB, wrapped, whiteboard", "load + 29 dB", -25.0, "Sorin"),
    ("3.96 m (13 ft), radar foam off", "Test 15: Vivaldi -> 29 dB", "Vivaldi + 29 dB", -25.9, "Spike"),
    ("11.3-11.5 m, radar foam off", "Test 25a: load -> 29 dB, whiteboard in", "load + 29 dB", -33.0, "Sorin (-34 to -32)"),
    ("11.3-11.5 m, radar foam off", "Test 25b: load -> 29 dB, whiteboard out", "load + 29 dB", -31.2, "Spike"),
    ("11.3-11.5 m, radar foam off", "Test 7: Vivaldi -> 29 dB", "Vivaldi + 29 dB", -20.3, "Spike"),
    ("11.3-11.5 m, radar foam off", "Test 11: Vivaldi -> 29 dB (later)", "Vivaldi + 29 dB", -29.4, "I/Q"),
]

fig, ax = plt.subplots(figsize=(11, 6.2))
y, ticks, labels, group_y = 0, [], [], []
last = None
for g, lab, kind, dbm, who in ROWS:
    if g != last:
        if last is not None:
            y += 0.8
        group_y.append((y, g))
        y += 0.9
        last = g
    ax.plot([-40, dbm], [y, y], color="#d9d8d3", lw=1, zorder=1)
    ax.plot(dbm, y, "o", ms=9, color=C[kind], mec="white", mew=2, zorder=3)
    ax.text(dbm + 0.4, y, f"{dbm:g} dBm  ({who})", va="center", fontsize=8.5, color="#3d3d3a")
    ticks.append(y)
    labels.append(lab)
    y += 1
for gy, g in group_y:
    ax.text(-40, gy, g, fontsize=10, fontweight="bold", va="center", color="#1f1f1d")
ax.set_yticks(ticks, labels, fontsize=9)
ax.invert_yaxis()
ax.set_xlim(-40, -8)
ax.set_xlabel("Peak at the SM200B input (dBm), 3 MHz RBW, Min/Max, Max Hold")
ax.grid(axis="x", color="#ecebe7")
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
for k, c in C.items():
    ax.plot([], [], "o", ms=8, color=c, label=k)
ax.legend(loc="lower right", frameon=False, fontsize=9)
ax.set_title("What the SM200B reads: 50 Ω load (leak only) vs the Vivaldi antenna", fontsize=12, loc="left", pad=22)
fig.text(0.01, 0.01, "At 13 ft the load reads as high as or higher than the antenna: the radar couples straight into the SM200B. "
         "At 11.5 m the antenna (test 7) is 11 dB above the load.", fontsize=8.5, color="#5f5e5a")
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = HERE / "plots" / f"{NAME}.png"
fig.savefig(out, dpi=120)
shutil.copy2(out, HERE.parent / "phase_detector_calibration" / "site" / "img" / f"{NAME}.png")
print(out)
