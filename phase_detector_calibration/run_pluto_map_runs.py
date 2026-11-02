"""Three Pluto runs into the 3 amps and detector, read on the scope at 1 Mohm, with the SM200B still attached.

  fine:  900 to 1200 MHz, 1 MHz steps, -36 dBm (the look up table range)
  level: -61 to -31 dBm in 3 dB steps at 950, 1000, 1020, 1054 and 1090 MHz (how much voltage depends on power)
  wide:  1400 to 1700 MHz, 2 MHz steps, -36 dBm (is that slope real with a fixed Pluto level)

Attenuation never goes below pluto_cw.ATT_MIN_DB, and the level is refused above -28 dBm.
Rerun to carry on from the last saved point. Saves pluto_map_runs_1nov.csv.
Usage: python run_pluto_map_runs.py [--check-only]
"""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

from run_pluto_full_range import ATT_MIN_DB, P_LIMIT_DBM, SCALE, Scope, _MAP, retry, tone_off, tone_on
from run_pluto_calibration import attenuation_for

HERE = Path(__file__).resolve().parent
OUT = HERE / "pluto_map_runs_1nov.csv"
LEVEL_FREQS = (950.0, 1000.0, 1020.0, 1054.0, 1090.0)
LEVELS = np.arange(-61.0, -30.0, 3.0)


def att_for(f_mhz, want):
    if want > P_LIMIT_DBM:
        raise ValueError(f"refusing {want} dBm")
    if want == -36.0 and f_mhz <= 1200.0:
        return attenuation_for(f_mhz * 1e6, want)
    att = float(np.interp(f_mhz, _MAP[:, 0], _MAP[:, 1])) - want
    return min(89.75, round(max(att, ATT_MIN_DB) * 4) / 4)


def points():
    for f in np.arange(900.0, 1200.5, 1.0):
        yield "fine", float(f), -36.0
    for f in LEVEL_FREQS:
        for want in LEVELS:
            yield "level", f, float(want)
    for f in np.arange(1400.0, 1700.5, 2.0):
        yield "wide", float(f), -36.0


def main():
    done = set()
    if OUT.exists():
        done = {(r["run"], float(r["freq_mhz"]), float(r["pluto_want_dbm"])) for r in csv.DictReader(open(OUT))}
    scope = Scope(1, 0.1)

    def get():
        try:
            return scope.read()
        except Exception:
            scope.drop()
            raise

    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if not done:
            w.writerow(["timestamp", "run", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v", "tries"])
        try:
            retry(tone_off, "tone off")
            time.sleep(1.0)
            m, _, r = retry(get, "scope")[0]
            print(f"tone off: {m*1e3:.2f} mV, rms {r*1e3:.2f} mV", flush=True)
            att = att_for(1105.0, -36.0)
            retry(lambda: tone_on(1105e6, att, SCALE), "tone on")
            time.sleep(1.0)
            m, _, r = retry(get, "scope")[0]
            print(f"check 1105 MHz, att {att}: {m*1e3:.2f} mV, rms {r*1e3:.2f} mV", flush=True)
            if "--check-only" in sys.argv:
                return
            for run, f, want in points():
                if (run, f, want) in done:
                    continue
                att = att_for(f, want)
                _, t1 = retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                time.sleep(0.3)
                (m, sd, r), t2 = retry(get, f"scope {f:.0f}")
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), run, f, att, want, m, sd, r, t1 + t2 - 1])
                fh.flush()
                print(f"{run:5s} {f:7.1f} MHz {want:6.1f} dBm att {att:5.2f} | {m*1e3:8.2f} mV (rms {r*1e3:.2f})", flush=True)
        finally:
            scope.drop()
            try:
                tone_off()
                print("tone off")
            except Exception as e:
                print(f"TONE OFF FAILED, Pluto may still be on: {str(e)[:160]}")


if __name__ == "__main__":
    main()
