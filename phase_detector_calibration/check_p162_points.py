"""Quick repeat of a few points of the four amp map, -60 dBm, to see whether the chain still matches it."""
import csv
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_pluto_full_range import SCALE, Scope, _MAP, tone_off, tone_on  # noqa: E402

old = {float(r["freq_mhz"]): float(r["detector_mean_v"]) * 1e3 for r in csv.DictReader(open(HERE / "p162x4_map_1nov.csv"))
       if r["pass"] == "map" and r["pluto_want_dbm"] == "-60.0"}
scope = Scope(1, 0.2)
try:
    for f in (900.0, 950.0, 1000.0, 1050.0, 1100.0, 1200.0, 1400.0):
        att = round((float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) + 60.0) * 4) / 4
        tone_on(f * 1e6, att, SCALE)
        time.sleep(0.5)
        m, sd, r = scope.read()
        print(f"{f:.0f} MHz: now {m*1e3:6.1f} mV rms {r*1e3:4.1f}, map {old[f]:6.1f} mV, change {m*1e3-old[f]:+6.1f} mV", flush=True)
finally:
    scope.drop()
    tone_off()
    print("tone off", flush=True)
