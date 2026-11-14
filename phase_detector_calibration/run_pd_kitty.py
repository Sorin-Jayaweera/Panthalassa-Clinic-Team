"""Phase detector sweep with the SM200B on the IF port: detector DC on the scope, plus the tone, 2x and 3x the tone
leaking out of the IF port, referred to before the pads (PAD_DB).

Wiring: Pluto -> 4 x ZX60-P162LN+ (4.03 V) -> ZFRSC-42-S+ -> arms -> ZX05-30W-S+ -> IF -> SDS1104X-E CH1 1 Mohm and,
through PAD_DB of pads, the SM200B. Appends to pd_cable_<tag>.csv's sibling pd_kitty_<tag>.csv.
Usage: python run_pd_kitty.py --tag 13nov_cableE --pad 29 [--fmin 600 --fmax 1700 --step 25 --dbm -50]
"""
import argparse
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_p162_sm200b as K  # noqa: E402  (sets the signal_hound path)
import run_pd_cable as P  # noqa: E402
from run_pluto_full_range import SCALE, retry, tone_off, tone_on  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

STOP_DBM = 5.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--pad", type=float, required=True)
    ap.add_argument("--fmin", type=float, default=600.0)
    ap.add_argument("--fmax", type=float, default=1700.0)
    ap.add_argument("--step", type=float, default=25.0)
    ap.add_argument("--dbm", type=float, default=-50.0)
    a = ap.parse_args()
    K.PAD_DB = a.pad
    out = HERE / f"pd_kitty_{a.tag}.csv"
    new = not out.exists()
    s = P.Scope(1, P.VDIV)
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        sm_set_ref_level(h, 0.0)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, 1)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        with open(out, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "rms_v", "pad_db",
                            "if_tone_dbm", "if_double_dbm", "if_triple_dbm"])
            tone_off()
            time.sleep(0.5)
            m0, sd0, r0 = retry(s.read, "scope")[0]
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), 0.0, 89.75, -999.0, m0, r0, a.pad, "", "", ""])
            print(f"tone off: {m0*1e3:.1f} mV", flush=True)
            fs = np.arange(a.fmin, a.fmax + a.step / 2, a.step)
            for j, f in enumerate(fs):
                f = float(f)
                att = P.att_for(f, a.dbm)
                retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                time.sleep(0.3)
                m, sd, r = retry(s.read, "scope")[0]
                t1, t2, t3 = K.near(h, f), K.near(h, 2 * f), K.near(h, 3 * f)
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, a.dbm, m, r, a.pad, round(t1, 2), round(t2, 2), round(t3, 2)])
                fh.flush()
                print(f"{f:7.1f} MHz {m*1e3:7.1f} mV | IF: f {t1:6.1f}  2f {t2:6.1f}  3f {t3:6.1f} dBm  [{100*(j+1)//len(fs)}%]", flush=True)
                if max(t1, t2, t3) > STOP_DBM or abs(m) * 1e3 > P.STOP_MV:
                    print("STOP RULE", flush=True)
                    return
    finally:
        s.drop()
        sm_close_device(h)
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
