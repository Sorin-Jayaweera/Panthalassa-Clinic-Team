"""Phase detector calibration with the Pluto as the source, 1.0 to 1.2 GHz.

Setup: Pluto TX -> 3 x ZX60-P103LN+ (5.0 V) -> ZFRSC-42-S+ -> two cables, one 4.5 in longer ->
ZX05-30W-S+ LO and RF -> IF to the scope (1 Mohm, DC).

Hard limit: the Pluto level comes from the measured table and is refused above P_LIMIT_DBM.
Worst case at that limit: -28 + 3 x 15.6 - 6 = +12.8 dBm at each detector port (absolute max +17 dBm);
third amp input +3.2 dBm (absolute max +21 dBm).

Usage:
  python run_pluto_calibration.py --check             # tone off, then one tone at 1.1 GHz, nothing saved
  python run_pluto_calibration.py --ch 1 --dbm -36    # the sweep, saved point by point
"""
import argparse
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sdr"))
sys.path.insert(0, str(HERE.parent / "vco_rise_time"))
from pluto_cw import set_attenuation, tone_off, tone_on  # noqa: E402
from pluto_level import pluto_dbm, pluto_setting  # noqa: E402
from sds import SDS  # noqa: E402

P_LIMIT_DBM = -28.0
SCALE = 0.5


def attenuation_for(freq_hz, want_dbm):
    if want_dbm > P_LIMIT_DBM:
        raise ValueError(f"refusing {want_dbm} dBm: limit is {P_LIMIT_DBM} dBm")
    att = pluto_setting(freq_hz, want_dbm, SCALE)
    if pluto_dbm(freq_hz, att, SCALE) > P_LIMIT_DBM:
        raise ValueError(f"{att} dB would exceed {P_LIMIT_DBM} dBm at {freq_hz/1e6:.0f} MHz")
    return att


def read(s, ch, n=3):
    vals, rms = [], []
    for _ in range(n):
        time.sleep(0.2)
        _, v = s.waveform(ch)
        vals.append(v.mean())
        rms.append(v.std())
    return float(np.mean(vals)), float(np.std(vals)), float(np.mean(rms))


def setup_scope(s, chans, vdiv):
    for ch in chans:
        for c in (f"C{ch}:TRA ON", f"C{ch}:ATTN 1", f"C{ch}:CPL D1M", f"BWL C{ch},ON",
                  f"C{ch}:VDIV {vdiv:.2E}V", f"C{ch}:OFST 0V"):
            s.write(c)
    s.write("TDIV 1.00E-03S")
    s.write("TRMD AUTO")
    time.sleep(1.0)


def check(s, dbm):
    setup_scope(s, (1, 2), 0.1)
    tone_off()
    time.sleep(1.0)
    for ch in (1, 2):
        m, sd, r = read(s, ch)
        print(f"tone off  C{ch}: mean {m*1e3:8.2f} mV, repeat {sd*1e3:.2f} mV, rms {r*1e3:.2f} mV")
    f = 1.1e9
    att = attenuation_for(f, dbm)
    tone_on(f, att, SCALE)
    time.sleep(1.0)
    print(f"tone on   1100 MHz, att {att} dB, table {pluto_dbm(f, att, SCALE):.2f} dBm")
    for ch in (1, 2):
        m, sd, r = read(s, ch)
        print(f"tone on   C{ch}: mean {m*1e3:8.2f} mV, repeat {sd*1e3:.2f} mV, rms {r*1e3:.2f} mV")


def sweep(s, a):
    setup_scope(s, (a.ch,), a.vdiv)
    fs = np.arange(a.fmin, a.fmax + a.step / 2, a.step) * 1e6
    plan = list(fs)
    out = HERE / a.out
    new = not out.exists()
    first_att = attenuation_for(plan[0], a.dbm)
    tone_on(plan[0], first_att, SCALE)
    time.sleep(1.0)
    with open(out, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "freq_set_hz", "pluto_att_db", "pluto_table_dbm", "detector_mean_v",
                        "repeat_sd_v", "rms_v", "scope_vdiv"])
        for f in plan:
            att = attenuation_for(f, a.dbm)
            tone_on(f, att, SCALE)
            time.sleep(0.4)
            m, sd, r = read(s, a.ch)
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), int(f), att,
                        round(pluto_dbm(f, att, SCALE), 2), m, sd, r, a.vdiv])
            fh.flush()
            print(f"{f/1e6:7.1f} MHz att {att:5.2f} | {m*1e3:8.2f} mV (+/- {sd*1e3:.2f}, rms {r*1e3:.2f})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--ch", type=int, default=1)
    ap.add_argument("--dbm", type=float, default=-36.0)
    ap.add_argument("--fmin", type=float, default=1000.0)
    ap.add_argument("--fmax", type=float, default=1200.0)
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--vdiv", type=float, default=0.1)
    ap.add_argument("--out", default="pluto_calibration_31oct.csv")
    a = ap.parse_args()
    s = SDS()
    try:
        if a.check:
            check(s, a.dbm)
        else:
            sweep(s, a)
    finally:
        tone_off()
        s.close()
        print("tone off")


if __name__ == "__main__":
    main()
