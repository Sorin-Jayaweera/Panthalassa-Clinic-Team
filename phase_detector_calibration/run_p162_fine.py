"""Four ZX60-P162LN+ chain: 900 to 1200 MHz in 1 MHz steps at the levels where the curves sit on the rail, to set how far the look up table depends on power.

Agilent E3630A supply. Same wiring as run_p162_map.py. Points below the Pluto attenuation floor are left out. Saves p162x4_fine_1nov.csv, rerun carries on.
Run from clinic/claude/signal_hound.
"""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_pluto_full_range as full  # noqa: E402
from run_pluto_full_range import SCALE, Scope, _MAP, retry, tone_off, tone_on  # noqa: E402

full.RETRY_S = 900.0
LEVELS = (-50.0, -40.0, -70.0, -65.0, -36.0, -60.0)
STOP_MV = 700.0
OUT = HERE / "p162x4_fine_1nov.csv"


def main():
    done = set()
    new = not OUT.exists()
    if not new:
        done = {(float(r["freq_mhz"]), float(r["pluto_want_dbm"])) for r in csv.DictReader(open(OUT))}
    scope = Scope(1, 0.2)

    def read():
        try:
            return scope.read()
        except Exception:
            scope.drop()
            raise

    try:
        with open(OUT, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v"])
            for want in LEVELS:
                for f in np.arange(900.0, 1200.5, 1.0):
                    if (float(f), want) in done:
                        continue
                    att = min(89.75, round((float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - want) * 4) / 4)
                    if att < full.ATT_MIN_DB:
                        continue
                    retry(lambda: tone_on(float(f) * 1e6, att, SCALE), f"tone {f:.0f}")
                    time.sleep(0.3)
                    m, sd, r = retry(read, "scope")[0]
                    w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, want, m, sd, r])
                    fh.flush()
                    if abs(m) * 1e3 > STOP_MV:
                        print(f"STOP RULE: {m*1e3:.1f} mV at {f} MHz, {want} dBm", flush=True)
                        return
                print(f"{want} dBm finished {dt.datetime.now():%H:%M:%S}", flush=True)
    finally:
        scope.drop()
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
