"""Phase detector voltage against Pluto frequency over the range reached, with the single-valued runs listed."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "pluto_full_range_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
f, v, rms = d["freq_mhz"], d["detector_mean_v"] * 1e3, d["rms_v"] * 1e3
print(f"{len(f)} points, {f.min():.0f} to {f.max():.0f} MHz, {v.min():.1f} to {v.max():.1f} mV")
s = np.convolve(v, np.ones(3) / 3, mode="same")
s[0], s[-1] = v[0], v[-1]
TOL = 3.0
runs = []
i = 0
while i < len(f) - 1:
    sign = np.sign(s[i + 1] - s[i]) or 1
    j, ext = i, s[i]
    while j + 1 < len(f) and sign * (s[j + 1] - ext) > -TOL:
        j += 1
        if sign * (s[j] - ext) > 0:
            ext = s[j]
    k = i + int(np.argmax(sign * s[i:j + 1]))
    runs.append((f[i], f[k], s[i], s[k]))
    i = max(k, i + 1)
print("runs that keep one direction, allowing 3 mV of ripple:")
for a, b, va, vb in sorted(runs, key=lambda r: abs(r[3] - r[2]), reverse=True)[:8]:
    print(f"  {a:6.0f} to {b:6.0f} MHz: {va:7.1f} to {vb:7.1f} mV, {abs(vb-va)/max(b-a,1):.2f} mV/MHz")
for lo, hi in [(300, 3000)]:
    m = (f >= lo) & (f <= hi)
    print(f"largest rms in {lo} to {hi} MHz: {rms[m].max():.1f} mV at {f[m][rms[m].argmax()]:.0f} MHz; median {np.median(rms[m]):.2f} mV")
fig, ax = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True, height_ratios=[3, 1])
ax[0].plot(f, v, ".-", ms=3, lw=0.8, color="#1f5fa8")
ax[0].axvspan(f.min(), 300, color="0.9", label="Below the detector's 300 MHz rating")
ax[0].axvline(2090, color="0.4", ls="--", lw=1, label="Above 2090 MHz: Pluto level not in table, attenuation 39 dB")
ax[0].set_ylabel("Phase detector output (mV, scope)")
ax[0].set_title(f"Phase detector voltage, Pluto {f.min():.0f} to {f.max():.0f} MHz, about +2.7 dBm at detector up to 1.5 GHz")
ax[0].grid(alpha=0.3)
ax[0].legend()
ax[1].plot(f, d["pluto_want_dbm"], color="#c8691c", label="Requested level")
ax[1].plot(f, -d["pluto_att_db"], color="0.3", lw=0.8, label="Minus attenuation setting")
ax[1].set_ylabel("dBm / dB")
ax[1].set_xlabel("Pluto frequency (MHz)")
ax[1].grid(alpha=0.3)
ax[1].legend()
fig.tight_layout()
fig.savefig(HERE / "pluto_full_range_1nov.png", dpi=120)
