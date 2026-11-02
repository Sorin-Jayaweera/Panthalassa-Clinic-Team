"""Four ZX60-P162LN+ chain on the Agilent supply: repeated 900 to 1200 MHz sweeps at -60 dBm, then the 1054 MHz hold and tone off readings."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "p162x4_map_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
fig, (a, b) = wiring.figure(2, [wiring.P162X4], size=(13, 9.5))
for rep in np.unique(d["rep"][d["pass"] == "repeat"]):
    k = (d["pass"] == "repeat") & (d["rep"] == rep)
    a.plot(d["freq_mhz"][k], d["detector_mean_v"][k] * 1e3, lw=1, label=f"Sweep {rep + 1}")
k = (d["pass"] == "map") & (d["pluto_want_dbm"] == -60) & (d["freq_mhz"] >= 900) & (d["freq_mhz"] <= 1200)
a.plot(d["freq_mhz"][k], d["detector_mean_v"][k] * 1e3, "k--", lw=1, label="First map, KUAIQU supply")
a.set_xlabel("Pluto frequency (MHz)")
a.set_ylabel("Phase detector output (mV)")
a.set_title("Repeat sweeps at -60 dBm, Agilent supply")
a.grid(alpha=0.3)
a.legend(fontsize=9)
for name, label in (("hold", "1054 MHz, -60 dBm"), ("off", "Tone off")):
    k = (d["pass"] == name) & (d["timestamp"] > "2026-11-01T20:30")   # earlier hold rows were on the KUAIQU supply
    v = d["detector_mean_v"][k] * 1e3
    b.plot(d["rep"][k] * 5, v, marker=".", lw=1, label=f"{label}: mean {v.mean():.1f} mV, sd {v.std():.1f} mV")
    print(label, len(v), round(v.mean(), 1), round(v.std(), 1), round(v.min(), 1), round(v.max(), 1))
b.set_xlabel("Time from start of that run (s)")
b.set_ylabel("Phase detector output (mV)")
b.set_title("Holding one tone, then tone off")
b.grid(alpha=0.3)
b.legend(fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "p162x4_stability_1nov.png", dpi=110)
s = [d["detector_mean_v"][(d["pass"] == "repeat") & (d["rep"] == r)] * 1e3 for r in np.unique(d["rep"][d["pass"] == "repeat"])]
n = min(map(len, s[:2])) if len(s) > 1 else 0
if n:
    print("sweep 1 to 2 rms change mV", round(float(np.sqrt(np.mean((s[0][:n] - s[1][:n]) ** 2))), 1))
