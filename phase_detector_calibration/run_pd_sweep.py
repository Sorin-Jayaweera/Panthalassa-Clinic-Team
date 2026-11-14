"""One phase detector sweep for a cable pair, appended to pd_cable_<tag>.csv (same columns as run_pd_cable.py).

Wiring: Pluto TX -> 4 x ZX60-P162LN+ (4.03 V, 0.23 A) -> ZFRSC-42-S+ -> cable pair -> ZX05-30W-S+ -> SDS1104X-E CH1 1 Mohm + SM200B.
Limits as run_pd_cable.py: Pluto never above -36 dBm, never below the attenuation floor; stops with the tone off past 700 mV.
The scope session is reopened after any read error.
Usage: python run_pd_sweep.py --tag E --name coarse --fmin 600 --fmax 1700 --step 50 --dbm -50 [--note "..."]
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
import run_pd_cable as P  # noqa: E402
import run_pluto_full_range as full  # noqa: E402
from run_pluto_full_range import SCALE, retry, tone_off, tone_on  # noqa: E402

full.RETRY_S = 120.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--fmin", type=float, required=True)
    ap.add_argument("--fmax", type=float, required=True)
    ap.add_argument("--step", type=float, required=True)
    ap.add_argument("--dbm", type=float, default=-50.0)
    ap.add_argument("--note", default="")
    ap.add_argument("--att", type=float, default=None, help="fixed Pluto attenuation instead of a fixed level (refused if any point would pass -36 dBm)")
    a = ap.parse_args()
    out, meta = HERE / f"pd_cable_{a.tag}.csv", HERE / f"pd_cable_{a.tag}.json"
    if not meta.exists():
        meta.write_text(json.dumps(dict(tag=a.tag, note=a.note, started=dt.datetime.now().isoformat(timespec="seconds"),
                                        wiring="Pluto -> 4 x ZX60-P162LN+ (4.03 V, 0.23 A) -> ZFRSC-42-S+ -> cable pair -> ZX05-30W-S+ -> SDS1104X-E CH1 1 Mohm + SM200B"), indent=1))
    new = not out.exists()
    s = P.Scope(1, P.VDIV)

    def rd():
        try:
            return s.read()
        except Exception:
            s.drop()
            time.sleep(2)
            raise

    try:
        with open(out, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "pass", "rep", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v"])
            tone_off()
            time.sleep(0.5)
            m, sd, r = retry(rd, "scope")[0]
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), a.name + "_off", 0, 0.0, 89.75, -999.0, m, sd, r])
            print(f"tone off: {m*1e3:.1f} mV", flush=True)
            for f in np.arange(a.fmin, a.fmax + a.step / 2, a.step):
                f = float(f)
                if a.att is None:
                    att = P.att_for(f, a.dbm)
                else:
                    att = a.att
                    lvl = float(np.interp(f, P._MAP[:, 0], P._MAP[:, 1])) - att
                    if lvl > P.TOP_DBM:
                        raise ValueError(f"fixed {att} dB gives {lvl:.1f} dBm at {f} MHz, over {P.TOP_DBM}")
                if att < full.ATT_MIN_DB:
                    print(f"{f:.0f} MHz skipped: below the attenuation floor", flush=True)
                    continue
                retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                time.sleep(0.3)
                m, sd, r = retry(rd, "scope")[0]
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), a.name, 0, f, att, a.dbm, m, sd, r])
                fh.flush()
                print(f"{f:7.1f} MHz {m*1e3:7.1f} mV (+/- {sd*1e3:.2f})", flush=True)
                if abs(m) * 1e3 > P.STOP_MV:
                    print("STOP RULE", flush=True)
                    return
    finally:
        s.drop()
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
