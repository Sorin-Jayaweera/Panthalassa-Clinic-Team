"""Four ZX60-P162LN+ chain, unattended, scope only, about one hour.

  map:    700 to 1600 MHz, 5 MHz steps, nine Pluto levels, most useful level first
  hold:   1054 MHz, -60 dBm, one reading every 5 s for 5 min
  off:    tone off, one reading every 5 s for 3 min
  repeat: 900 to 1200 MHz, 1 MHz steps, -60 dBm, until the deadline

Stops with the tone off if the detector passes STOP_MV. Rerun carries on the map. The -60 dBm level and -50 dBm to 1395 MHz were taken at 100 mV/div, the rest at 200 mV/div. USB: retries for 15 min per point, then stops with the tone off.
The P162 stages saturate, so the top level here is a choice for mapping and is well under the amp input limit.
Saves p162x4_map_1nov.csv. Run from clinic/claude/signal_hound.
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
LEVELS = (-60.0, -50.0, -70.0, -45.0, -65.0, -75.0, -55.0, -80.0, -85.0)
TOP_DBM = -45.0
STOP_MV = 700.0   # scope at 200 mV/div reads to about 800 mV; the detector IF limit of 40 mA is about 2 V into 50 ohm
MINUTES = 90.0
OUT = HERE / "p162x4_map_1nov.csv"
DEADLINE = time.time() + MINUTES * 60


class Stop(Exception):
    pass


def att_for(f, want):
    if want > TOP_DBM:
        raise ValueError(f"refusing {want} dBm")
    return min(89.75, round((float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - want) * 4) / 4)


def main():
    scope = Scope(1, 0.2)

    def volts():
        def get():
            try:
                return scope.read()
            except Exception:
                scope.drop()
                raise
        return retry(get, "scope")[0]

    new = not OUT.exists()
    done = set()
    if not new:
        done = {(r["pass"], float(r["freq_mhz"]), float(r["pluto_want_dbm"])) for r in csv.DictReader(open(OUT)) if r["pass"] == "map"}
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "pass", "rep", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v"])

        def save(name, rep, f, att, want):
            m, sd, r = volts()
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), name, rep, f, att, want, m, sd, r])
            fh.flush()
            if abs(m) * 1e3 > STOP_MV:
                raise Stop(f"{m*1e3:.1f} mV at {f} MHz, {want} dBm")

        def sweep(name, rep, freqs, want):
            for f in freqs:
                if time.time() > DEADLINE:
                    return
                if (name, float(f), want) in done:
                    continue
                att = att_for(float(f), want)
                retry(lambda: tone_on(float(f) * 1e6, att, SCALE), f"tone {f:.0f}")
                time.sleep(0.3)
                save(name, rep, float(f), att, want)
            print(f"{name} {rep} {want} dBm finished {dt.datetime.now():%H:%M:%S}", flush=True)

        try:
            retry(tone_off, "tone off")
            time.sleep(1.0)
            save("start_off", 0, 0.0, 89.75, -999.0)
            for want in LEVELS:
                sweep("map", 0, np.arange(700.0, 1600.5, 5.0), want)
            att = att_for(1054.0, -60.0)
            retry(lambda: tone_on(1054e6, att, SCALE), "tone hold")
            for i in range(60):
                save("hold", i, 1054.0, att, -60.0)
                time.sleep(4.0)
            print(f"hold finished {dt.datetime.now():%H:%M:%S}", flush=True)
            retry(tone_off, "tone off")
            for i in range(36):
                save("off", i, 0.0, 89.75, -999.0)
                time.sleep(4.0)
            print(f"off finished {dt.datetime.now():%H:%M:%S}", flush=True)
            rep = 0
            while time.time() < DEADLINE:
                sweep("repeat", rep, np.arange(900.0, 1200.5, 1.0), -60.0)
                rep += 1
        except Stop as e:
            print(f"STOP RULE: {e}", flush=True)
        finally:
            scope.drop()
            try:
                tone_off()
                print("tone off", flush=True)
            except Exception as e:
                print(f"TONE OFF FAILED, Pluto may still be on: {str(e)[:160]}", flush=True)


if __name__ == "__main__":
    main()
