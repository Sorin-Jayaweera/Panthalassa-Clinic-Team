"""Fine map, level test and 1400 to 1700 MHz run from pluto_map_runs_1nov.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
d = np.genfromtxt(HERE / "pluto_map_runs_1nov.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
v = d["detector_mean_v"] * 1e3
fig, ax = plt.subplots(1, 3, figsize=(16, 5))
m = d["run"] == "fine"
ax[0].plot(d["freq_mhz"][m], v[m], ".-", ms=2, lw=0.8, color="#1f5fa8")
ax[0].set_title("Fine map, Pluto -36 dBm")
ax[0].set_xlabel("Pluto frequency (MHz)")
ax[0].set_ylabel("Phase detector output (mV)")
fv = dict(zip(d["freq_mhz"][m], v[m]))
print("fine:", {int(k): round(float(fv[k]), 1) for k in (900, 950, 1000, 1020, 1054, 1090, 1105, 1150, 1200)})
for f in np.unique(d["freq_mhz"][d["run"] == "level"]):
    k = (d["run"] == "level") & (d["freq_mhz"] == f)
    ax[1].plot(d["pluto_want_dbm"][k], v[k], ".-", label=f"{f:.0f} MHz")
    print(f"level {f:.0f} MHz:", np.round(v[k], 1).tolist())
ax[1].set_title("Level test")
ax[1].set_xlabel("Pluto level (dBm, table)")
ax[1].set_ylabel("Phase detector output (mV)")
ax[1].legend()
m = d["run"] == "wide"
ax[2].plot(d["freq_mhz"][m], v[m], ".-", ms=2, lw=0.8, color="#1f5fa8")
ax[2].set_title("1400 to 1700 MHz, Pluto -36 dBm")
ax[2].set_xlabel("Pluto frequency (MHz)")
ax[2].set_ylabel("Phase detector output (mV)")
print("wide:", [(int(a), round(float(b), 1)) for a, b in zip(d["freq_mhz"][m], v[m]) if int(a) % 50 == 0])
print("attenuation in wide:", d["pluto_att_db"][m].min(), d["pluto_att_db"][m].max())
print("largest rms mV:", round(float((d["rms_v"] * 1e3).max()), 2))
for a in ax:
    a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / "pluto_map_runs_1nov.png", dpi=110)
