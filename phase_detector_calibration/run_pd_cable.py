"""Phase detector vs delay-cable length: the same sweeps for each cable pair, so the pairs can be compared.

Wiring (same as 1 Nov): Pluto TX -> 4 x ZX60-P162LN+ in series -> ZFRSC-42-S+ -> two cables (the pair under test) ->
ZX05-30W-S+ LO and RF -> IF to SDS1104X-E CH1 (1 Mohm, DC) and, through pads, the SM200B.

Passes, in order, saved point by point to pd_cable_<tag>.csv (rerun with the same --tag carries on):
  off      tone off, 10 readings (detector zero)
  fine     900-1200 MHz, 1 MHz, -50 dBm         (direct comparison with p162x4_fine_1nov.csv)
  wide     700-1600 MHz, 2 MHz, -50 dBm         (the whole curve, to fit the effective delay)
  fine     900-1200 MHz, 1 MHz, -60, -45, -55, -40 dBm  (how much the voltage moves with power)
  repeat   900-1200 MHz, 1 MHz, -50 dBm         (repeatability)

Limits: Pluto never above TOP_DBM and never below pluto_cw.ATT_MIN_DB; stops with the tone off if the detector passes STOP_MV.
Usage: python run_pd_cable.py --tag 1nov_4p5in [--check] [--note "..."]
"""
import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_pluto_full_range as full  # noqa: E402
from run_pluto_full_range import SCALE, Scope, _MAP, retry, tone_off, tone_on  # noqa: E402

full.RETRY_S = 600.0
TOP_DBM = -36.0
STOP_MV = 700.0
VDIV = 0.2


def att_for(f, want):
    if want > TOP_DBM:
        raise ValueError(f"refusing {want} dBm (limit {TOP_DBM})")
    return min(89.75, round((float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - want) * 4) / 4)


def points():
    for i in range(10):
        yield "off", i, 0.0, -999.0
    fine = np.arange(900.0, 1200.5, 1.0)
    for f in fine:
        yield "fine", 0, float(f), -50.0
    for f in np.arange(700.0, 1600.5, 2.0):
        yield "wide", 0, float(f), -50.0
    for want in (-60.0, -45.0, -55.0, -40.0):
        for f in fine:
            yield "fine", 0, float(f), want
    for f in fine:
        yield "repeat", 1, float(f), -50.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--check", action="store_true", help="tone off, then 1000 MHz at -50 dBm; nothing saved")
    a = ap.parse_args()
    scope = Scope(1, VDIV)

    def read():
        try:
            return scope.read()
        except Exception:
            scope.drop()
            raise

    if a.check:
        try:
            tone_off()
            time.sleep(0.5)
            m0 = retry(read, "scope")[0][0]
            f, want = 1000.0, -50.0
            att = att_for(f, want)
            retry(lambda: tone_on(f * 1e6, att, SCALE), "tone")
            time.sleep(0.5)
            m1, sd, r = retry(read, "scope")[0]
            print(f"tone off {m0*1e3:.1f} mV | 1000 MHz -50 dBm (att {att}) {m1*1e3:.1f} mV +/- {sd*1e3:.2f}, rms {r*1e3:.2f}", flush=True)
        finally:
            scope.drop()
            tone_off()
            print("tone off", flush=True)
        return

    out = HERE / f"pd_cable_{a.tag}.csv"
    meta = HERE / f"pd_cable_{a.tag}.json"
    if not meta.exists():
        meta.write_text(json.dumps(dict(tag=a.tag, note=a.note, started=dt.datetime.now().isoformat(timespec="seconds"),
                                        wiring="Pluto -> 4 x ZX60-P162LN+ -> ZFRSC-42-S+ -> cable pair -> ZX05-30W-S+ -> SDS1104X-E CH1 1 Mohm + SM200B via pads"), indent=1))
    done = set()
    new = not out.exists()
    if not new:
        done = {(r["pass"], int(r["rep"]), float(r["freq_mhz"]), float(r["pluto_want_dbm"])) for r in csv.DictReader(open(out))}
    last = None
    try:
        with open(out, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "pass", "rep", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v"])
            for ps, rep, f, want in points():
                if (ps, rep, f, want) in done:
                    continue
                if ps == "off":
                    tone_off()
                    att = 89.75
                    time.sleep(0.5)
                else:
                    att = att_for(f, want)
                    if att < full.ATT_MIN_DB:
                        continue
                    retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                    time.sleep(0.3)
                m, sd, r = retry(read, "scope")[0]
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), ps, rep, f, att, want, m, sd, r])
                fh.flush()
                if abs(m) * 1e3 > STOP_MV:
                    print(f"STOP RULE: {m*1e3:.1f} mV at {f} MHz, {want} dBm", flush=True)
                    return
                key = (ps, want)
                if key != last:
                    print(f"{dt.datetime.now():%H:%M:%S} {ps} {want:+.0f} dBm started", flush=True)
                    last = key
        print(f"{dt.datetime.now():%H:%M:%S} all passes finished", flush=True)
    finally:
        scope.drop()
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
