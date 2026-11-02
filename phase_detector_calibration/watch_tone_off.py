"""Watch the detector with the Pluto off: scope reading every 5 s. Run after powering the amps to see them settle.
Usage: python watch_tone_off.py <seconds>  Appends to p162x4_tone_off_watch_1nov.csv.
"""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_pluto_full_range import Scope, tone_off  # noqa: E402

SECONDS = float(sys.argv[1])
tone_off()
scope = Scope(1, 0.2)
t0 = time.time()
with open(HERE / "p162x4_tone_off_watch_1nov.csv", "a", newline="") as fh:
    w = csv.writer(fh)
    while time.time() - t0 < SECONDS:
        m, sd, r = scope.read()
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), m, sd, r])
        fh.flush()
        print(f"{time.time()-t0:5.0f} s {m*1e3:7.1f} mV rms {r*1e3:5.1f}", flush=True)
        time.sleep(5)
scope.drop()
