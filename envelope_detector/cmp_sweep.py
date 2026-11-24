"""Test B trip-point sweep: step IN+ (CGR-201 C2BJ0VL) up through the threshold and back down,
and at each step read the Siglent: IN+ (CH1), IN- (CH2), OUT+ (CH3), OUT- (CH4).

    python3 cmp_sweep.py --dry-run                 # print the planned codes, touch nothing
    .venv-scope/bin/python cmp_sweep.py            # run (needs pyvisa for the scope)
    .venv-scope/bin/python cmp_sweep.py --start 1.10 --stop 1.32 --fine-lo 1.15 --fine-hi 1.26

Levels are CGR-201 settings by its calibration; the board sees them about 26 mV higher
(19 Nov). The scope gives the board values, and the DMM gives the trusted IN+ - IN-.
Every level goes through cgr_guard (DC only, 0.10-3.00 V). At the end IN+ is put back
to the start level (output low).

Per step the scope is stopped on one acquisition (1 us/div = 14 us, 500 MS/s) and
OUT+ - OUT- is classified sample by sample: low (< -0.2 V), high (> +0.2 V) or in between.
Output: data/cmp_sweep_<time>.csv.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cgr_guard  # noqa: E402

SERIAL_INP = "C2BJ0VL"
SCOPE = "USB0::62700::60984::SDSMMFCQ5R6888::0::INSTR"


def plan(serial, start, stop, fine_lo, fine_hi, coarse):
    c0, c1 = cgr_guard.safe_code(serial, start), cgr_guard.safe_code(serial, stop)
    f0, f1 = cgr_guard.safe_code(serial, fine_lo), cgr_guard.safe_code(serial, fine_hi)
    up, c = [], c0
    while c <= c1:
        up.append(c)
        c += 1 if f0 <= c < f1 else coarse
    if up[-1] != c1:
        up.append(c1)
    return up + up[-2::-1]  # up, then back down


class Scope:
    def __init__(self):
        import warnings
        warnings.filterwarnings("ignore")
        import pyvisa
        self.s = pyvisa.ResourceManager("@py").open_resource(SCOPE)
        self.s.timeout = 20000
        self.s.chunk_size = 4 * 1024 * 1024
        self.s.write("TDIV 1E-6")
        self.s.write("TRMD AUTO")
        time.sleep(0.5)
        self.sara = float(self.s.query("SARA?").split()[-1].replace("Sa/s", ""))
        self.scale = {}
        for ch in (1, 2, 3, 4):
            vdiv = float(self.s.query(f"C{ch}:VDIV?").split()[-1].rstrip("V"))
            ofst = float(self.s.query(f"C{ch}:OFST?").split()[-1].rstrip("V"))
            self.scale[ch] = (vdiv, ofst)
        self.s.write("WFSU SP,1,NP,0,FP,0")

    def wave(self, ch):
        vdiv, ofst = self.scale[ch]
        self.s.write(f"C{ch}:WF? DAT2")
        raw = self.s.read_raw()
        i = raw.index(b"#9")
        n = int(raw[i + 2:i + 11])
        return np.frombuffer(raw[i + 11:i + 11 + n], dtype=np.int8).astype(float) * vdiv / 25.0 - ofst

    def acquire(self):
        self.s.write("TRMD AUTO")  # "RUN" does not restart this scope after STOP: old data was read
        time.sleep(0.3)
        self.s.write("STOP")
        time.sleep(0.15)
        return {ch: self.wave(ch) for ch in (1, 2, 3, 4)}

    def close(self):
        self.s.write("TRMD AUTO")
        self.s.close()


def classify(w, sara):
    d = w[3] - w[4]
    lo, hi = float(np.mean(d < -0.2)), float(np.mean(d > 0.2))
    x = d - d.mean()
    f = np.fft.rfftfreq(len(x), 1 / sara)
    a = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    a[f < 0.5e6] = 0
    return dict(in_p=w[1].mean(), in_m=w[2].mean(), diff_in_mv=1e3 * (w[1].mean() - w[2].mean()),
                out_p=w[3].mean(), out_m=w[4].mean(), out_diff=d.mean(), out_rms_mv=1e3 * d.std(),
                frac_low=lo, frac_mid=1 - lo - hi, frac_high=hi, f_mhz=f[int(a.argmax())] / 1e6)


def state(r):
    if r["frac_low"] > 0.99:
        return "LOW"
    if r["frac_high"] > 0.99:
        return "HIGH"
    return "TOGGLING"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=1.10)
    ap.add_argument("--stop", type=float, default=1.32)
    ap.add_argument("--fine-lo", type=float, default=1.15)
    ap.add_argument("--fine-hi", type=float, default=1.26)
    ap.add_argument("--coarse", type=int, default=4, help="codes per step outside the fine window")
    ap.add_argument("--settle", type=float, default=0.3)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    codes = plan(SERIAL_INP, a.start, a.stop, a.fine_lo, a.fine_hi, a.coarse)
    print(f"{len(codes)} steps, codes {codes[0]}..{max(codes)}..{codes[-1]} "
          f"({cgr_guard.volts_of(SERIAL_INP, codes[0]):.3f} to {cgr_guard.volts_of(SERIAL_INP, max(codes)):.3f} V setting)")
    if a.dry_run:
        print("codes:", codes)
        return

    from ed_sweep import CGR201
    g = CGR201(f"/dev/cu.usbserial-{SERIAL_INP}")
    if "CircuitGear" not in g.identify():
        sys.exit("CGR-201 did not identify. Nothing sent.")
    sc = Scope()
    out = os.path.join(HERE, "data", f"cmp_sweep_{datetime.now():%Y%m%d_%H%M%S}.csv")
    rows = []
    try:
        for i, code in enumerate(codes):
            cgr_guard.send_dc(g, SERIAL_INP, code)
            time.sleep(a.settle)
            r = classify(sc.acquire(), sc.sara)
            r.update(step=i, dir="up" if i < len(codes) // 2 + 1 else "down", code=code,
                     set_v=cgr_guard.volts_of(SERIAL_INP, code), state=state(r), time=datetime.now().isoformat(timespec="seconds"))
            rows.append(r)
            print(f"{i:3d} {r['dir']:4s} code {code} set {r['set_v']:.4f}  IN+-IN- {r['diff_in_mv']:+7.1f} mV (scope)  "
                  f"{r['state']:8s} low {r['frac_low']:.2f} mid {r['frac_mid']:.2f} high {r['frac_high']:.2f}  "
                  f"rms {r['out_rms_mv']:6.1f} mV  f {r['f_mhz']:6.2f} MHz", flush=True)
    finally:
        cgr_guard.send_dc(g, SERIAL_INP, codes[0])  # back to the start: output low
        g.close()
        sc.close()
        if rows:
            with open(out, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
            print("saved", out)


if __name__ == "__main__":
    main()
