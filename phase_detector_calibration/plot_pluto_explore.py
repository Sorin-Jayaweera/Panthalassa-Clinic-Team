"""Plots and summary numbers from the two hour unattended run, pluto_explore_1nov.csv and pluto_explore_kitty_1nov.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "pluto_explore_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
v = d["detector_mean_v"] * 1e3
for name in np.unique(d["pass"]):
    k = d["pass"] == name
    print(f"{name}: {k.sum()} points, {d['timestamp'][k][0]} to {d['timestamp'][k][-1]}, {v[k].min():.1f} to {v[k].max():.1f} mV")
fig, ax = plt.subplots(2, 3, figsize=(17, 9.5))

a = ax[0, 0]
for want in np.unique(d["pluto_want_dbm"][d["pass"] == "levelmap"]):
    k = (d["pass"] == "levelmap") & (d["pluto_want_dbm"] == want)
    a.plot(d["freq_mhz"][k], v[k], lw=1, label=f"{want:.0f} dBm")
    print(f"levelmap {want:.0f} dBm: 950 {np.interp(950, d['freq_mhz'][k], v[k]):.1f}, 1054 {np.interp(1054, d['freq_mhz'][k], v[k]):.1f}, 1090 {np.interp(1090, d['freq_mhz'][k], v[k]):.1f}, 1105 {np.interp(1105, d['freq_mhz'][k], v[k]):.1f} mV, peak at {d['freq_mhz'][k][v[k].argmax()]:.0f} MHz")
a.set_title("Fine map at five Pluto levels")
a.set_xlabel("Pluto frequency (MHz)")
a.legend()

a = ax[0, 1]
g = d["pass"] == "grid"
for f in np.unique(d["freq_mhz"][g]):
    k = g & (d["freq_mhz"] == f)
    a.plot(d["pluto_want_dbm"][k], v[k], ".-", lw=0.8, label=f"{f:.0f}")
a.set_title("Voltage against Pluto level")
a.set_xlabel("Pluto level (dBm, table)")
a.legend(fontsize=7, ncol=2, title="MHz")

a = ax[0, 2]
r = d["pass"] == "repeat"
reps = np.unique(d["rep"][r])
ref = None
spread = []
for rep in reps:
    k = r & (d["rep"] == rep)
    if k.sum() < 301:
        print(f"repeat {rep}: only {k.sum()} points, left out")
        continue
    if ref is None:
        ref = v[k]
    a.plot(d["freq_mhz"][k], v[k] - ref, lw=0.8, label=f"{d['timestamp'][k][0][11:16]}")
    spread.append(v[k])
    print(f"repeat {rep} start {d['timestamp'][k][0][11:19]}: mean change {np.mean(v[k]-ref):.2f} mV, largest {np.abs(v[k]-ref).max():.2f} mV")
a.set_title("Fine map repeats, change from the first")
a.set_xlabel("Pluto frequency (MHz)")
a.legend(fontsize=7)
if spread:
    s = np.array(spread)
    print(f"repeat spread: median of peak to peak {np.median(s.max(0)-s.min(0)):.2f} mV, largest {(s.max(0)-s.min(0)).max():.2f} mV")

a = ax[1, 0]
h = d["pass"] == "hold"
o = d["pass"] == "off"
a.plot(np.arange(h.sum()) * 5 / 60, v[h] - v[h][0], lw=0.8, color="#1f5fa8", label=f"1054 MHz tone on, start {v[h][0]:.1f} mV")
a.plot(np.arange(o.sum()) * 5 / 60, v[o] - v[o][0], lw=0.8, color="#c8691c", label=f"Tone off, start {v[o][0]:.1f} mV")
a.set_title("Drift while held")
a.set_xlabel("Time (about, min)")
a.legend()
print(f"hold: mean {v[h].mean():.2f}, sd {v[h].std():.2f}, range {np.ptp(v[h]):.2f} mV; off: mean {v[o].mean():.2f}, sd {v[o].std():.2f}, range {np.ptp(v[o]):.2f} mV")

a = ax[1, 1]
k = d["pass"] == "att31"
a.plot(d["freq_mhz"][k], v[k], lw=1, color="#1f5fa8")
a.set_title("1200 to 2090 MHz, attenuation fixed at 31 dB")
a.set_xlabel("Pluto frequency (MHz)")
print("att31:", [(int(x), round(float(y), 1)) for x, y in zip(d["freq_mhz"][k], v[k]) if int(x) % 100 == 0])
z = d["pass"] == "scope29"
print(f"scope29: {z.sum()} of 63 points, last {d['freq_mhz'][z][-1] if z.sum() else 'none'} MHz")

for a in ax.flat[:5]:
    a.set_ylabel("mV")
    a.grid(alpha=0.3)

a = ax[1, 2]
kp = HERE / "pluto_explore_kitty_1nov.csv"
if kp.exists():
    K = np.genfromtxt(kp, delimiter=",", names=True, dtype=None, encoding="utf-8")
    a.plot(K["freq_mhz"], K["tone_dbm"], ".-", ms=3, lw=0.8, label="Tone")
    a.plot(K["freq_mhz"], K["double_dbm"], ".-", ms=3, lw=0.8, label="Twice the tone")
    a.plot(K["freq_mhz"], K["low_dbm"], ".-", ms=3, lw=0.8, label="Strongest near DC")
    a.set_ylabel("dBm before pads")
    a.legend()
    print(f"kitty {len(K)} points: tone {K['tone_dbm'].min():.1f} to {K['tone_dbm'].max():.1f}, double {K['double_dbm'].min():.1f} to {K['double_dbm'].max():.1f}, low {K['low_dbm'].min():.1f} to {K['low_dbm'].max():.1f} dBm")
    print("kitty tone:", [(int(x), round(float(y), 1)) for x, y in zip(K["freq_mhz"], K["tone_dbm"]) if int(x) % 200 == 100])
    print("kitty double:", [(int(x), round(float(y), 1)) for x, y in zip(K["freq_mhz"], K["double_dbm"]) if int(x) % 200 == 100])
a.set_title("Kitty: leak through the detector, about +2.7 dBm at it")
a.set_xlabel("Pluto frequency (MHz)")
a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / "pluto_explore_1nov.png", dpi=105)
