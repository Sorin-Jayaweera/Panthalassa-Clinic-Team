"""Phase detector DC output over the whole Pluto range, 50 to 6000 MHz, read on the scope at 1 Mohm.

Setup: Pluto -> 3 x ZX60-P103LN+ -> ZFRSC-42-S+ -> 4.5 in delay -> ZX05-30W-S+ -> IF -> scope and SM200B.

Level: the Pluto is set for a constant +2.7 dBm at the detector, from the datasheet amp gain (25 dB each at 50 MHz,
7 dB at 3 GHz), which is what -36 dBm gave at 1105 MHz. Limits, so low frequency gain cannot overdrive the chain:
  - never above -28 dBm from the Pluto (P_LIMIT_DBM)
  - outside the measured table (350 to 2090 MHz) the Pluto level is not known, so attenuation is at least 39 dB,
    which holds -28 dBm even at the +11 dBm worst case. Those points fall short of +2.7 dBm above about 2 GHz.
The amps are specified to 3000 MHz, the splitter to 4200 MHz, and the detector from 300 to 4000 MHz.

USB drops: each point retries for RETRY_S, reopening the scope, then the run stops with the tone off.
Rerun with the same --out to carry on from the last saved point.
Usage: python run_pluto_full_range.py [--fmin 50] [--fmax 6000] [--step 10] [--out file.csv]
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
from pluto_cw import ATT_MIN_DB, tone_off, tone_on  # noqa: E402
from sds import SDS  # noqa: E402

P_LIMIT_DBM = -28.0
P_WORST_DBM = 11.0
SCALE = 0.5
DETECTOR_DBM = 2.7
SPLIT_DB = 6.0
RETRY_S = 180.0
_GAIN = np.array([[50, 25.29], [100, 25.05], [400, 21.49], [800, 17.27], [1200, 14.22], [1600, 11.92], [2000, 10.03], [2400, 8.60], [2800, 7.25]])
_MAP = np.genfromtxt(HERE.parent / "pluto_characterization" / "pluto_map_table.csv", delimiter=",", skip_header=1)


def plan(f_mhz):
    """Attenuation in dB, the wanted Pluto level, and whether the frequency is inside the measured table."""
    want = min(DETECTOR_DBM + SPLIT_DB - 3 * np.interp(f_mhz, _GAIN[:, 0], _GAIN[:, 1]), P_LIMIT_DBM)
    att = float(np.interp(f_mhz, _MAP[:, 0], _MAP[:, 1])) - want
    inside = _MAP[0, 0] <= f_mhz <= _MAP[-1, 0]
    att = max(att, P_WORST_DBM - P_LIMIT_DBM if not inside else float(np.max(_MAP[:, 1])) - P_LIMIT_DBM)
    att = max(att, ATT_MIN_DB)
    return min(89.75, round(att * 4) / 4), want, inside


def setup_scope(s, ch, vdiv):
    for c in (f"C{ch}:TRA ON", f"C{ch}:ATTN 1", f"C{ch}:CPL D1M", f"BWL C{ch},ON", f"C{ch}:VDIV {vdiv:.2E}V", f"C{ch}:OFST 0V"):
        s.write(c)
    s.write("TDIV 1.00E-03S")
    s.write("TRMD AUTO")
    time.sleep(1.0)


def read(s, ch, n=2):
    vals, rms = [], []
    for _ in range(n):
        time.sleep(0.2)
        _, v = s.waveform(ch)
        vals.append(v.mean())
        rms.append(v.std())
    return float(np.mean(vals)), float(np.std(vals)), float(np.mean(rms))


class Scope:
    def __init__(self, ch, vdiv):
        self.ch, self.vdiv, self.s = ch, vdiv, None

    def read(self):
        if self.s is None:
            self.s = SDS()
            setup_scope(self.s, self.ch, self.vdiv)
        return read(self.s, self.ch)

    def drop(self):
        try:
            if self.s is not None:
                self.s.close()
        except Exception:
            pass
        self.s = None


def retry(fn, what):
    """Call fn until it works or RETRY_S has passed. Returns the result and how many tries it took."""
    start, tries = time.time(), 0
    while True:
        tries += 1
        try:
            return fn(), tries
        except Exception as e:
            if time.time() - start > RETRY_S:
                print(f"{what}: gave up after {tries} tries: {str(e)[:160]}", flush=True)
                raise
            print(f"{what}: try {tries} failed, {str(e)[:100]}", flush=True)
            time.sleep(5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ch", type=int, default=1)
    ap.add_argument("--fmin", type=float, default=50.0)
    ap.add_argument("--fmax", type=float, default=6000.0)
    ap.add_argument("--step", type=float, default=10.0)
    ap.add_argument("--vdiv", type=float, default=0.1)
    ap.add_argument("--out", default="pluto_full_range_1nov.csv")
    a = ap.parse_args()
    out = HERE / a.out
    done = set()
    if out.exists():
        done = {float(r["freq_mhz"]) for r in csv.DictReader(open(out))}
    scope = Scope(a.ch, a.vdiv)

    def get():
        try:
            return scope.read()
        except Exception:
            scope.drop()
            raise

    with open(out, "a", newline="") as fh:
        w = csv.writer(fh)
        if not done:
            w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "in_table", "detector_mean_v", "repeat_sd_v", "rms_v", "tries"])
        try:
            retry(tone_off, "tone off")
            time.sleep(1.0)
            m, sd, r = retry(get, "scope")[0]
            print(f"tone off: {m*1e3:.2f} mV, rms {r*1e3:.2f} mV", flush=True)
            att, want, _ = plan(1105.0)
            retry(lambda: tone_on(1105e6, att, SCALE), "tone on")
            time.sleep(1.0)
            m, sd, r = retry(get, "scope")[0]
            print(f"check 1105 MHz, att {att}: {m*1e3:.2f} mV, rms {r*1e3:.2f} mV (calibration 243.2 mV)", flush=True)
            for f in np.arange(a.fmin, a.fmax + a.step / 2, a.step):
                if float(f) in done:
                    continue
                att, want, inside = plan(f)
                _, t1 = retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                time.sleep(0.3)
                (m, sd, r), t2 = retry(get, f"scope {f:.0f}")
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, round(want, 2), int(inside), m, sd, r, t1 + t2 - 1])
                fh.flush()
                print(f"{f:7.1f} MHz att {att:5.2f} | {m*1e3:8.2f} mV (rms {r*1e3:.2f})", flush=True)
        finally:
            scope.drop()
            try:
                tone_off()
                print("tone off")
            except Exception as e:
                print(f"TONE OFF FAILED, Pluto may still be on: {str(e)[:160]}")


if __name__ == "__main__":
    main()
