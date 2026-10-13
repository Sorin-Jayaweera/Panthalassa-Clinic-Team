"""Phase detector calibration: VCO + splitter/delay line/mixer measured together.

Setup: Syscomp CGR-201 -> VCO Vt (and scope CH1). VCO RF -> tee -> spectrum analyzer,
and -> splitter -> two cable lengths -> mixer -> scope CH2 (DC).

For each DC tuning voltage this records Vt (scope CH1), the VCO frequency and power
(SSA3021X, narrow span) and the mixer DC output (scope CH2).

Usage: python run_calibration.py [--vmin 0] [--vmax 3.3] [--step 0.05] [--test]
"""
import argparse
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pyvisa

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vco_rise_time"))
from cgr201 import CGR201  # noqa: E402
from sds import SDS  # noqa: E402

SSA = "USB0::0xF4EC::0x1300::SSA3XLBC3R0429::INSTR"
OFFSET_V_PER_CODE = 1.875e-3  # measured on the scope earlier today
V_LIMIT = (-0.1, 3.65)  # refuse to drive Vt outside this window
MIXER_CH = 2


class Analyzer:
    def __init__(self):
        self.a = pyvisa.ResourceManager().open_resource(SSA)
        self.a.timeout = 10000
        self.a.write(":DISP:WIND:TRAC:Y:RLEV 15")  # VCO is about +7 dBm; keeps the input attenuated
        self.a.write(":INIT:CONT ON")
        self.a.write(":CALC:MARK1:STAT ON")

    def _peak(self, centre, span):
        """Peak of one complete single sweep (continuous mode can hand back a half-updated trace)."""
        self.a.write(":INIT:CONT OFF")
        self.a.write(f":FREQ:CENT {centre:.0f}")
        self.a.write(f":FREQ:SPAN {span:.0f}")
        time.sleep(0.3)
        sweep = float(self.a.query(":SWE:TIME?"))
        self.a.write(":INIT:IMM")
        time.sleep(1.5 * sweep + 0.4)
        self.a.query("*OPC?")
        self.a.write(":CALC:MARK1:MAX")
        time.sleep(0.2)
        return float(self.a.query(":CALC:MARK1:X?")), float(self.a.query(":CALC:MARK1:Y?"))

    def measure(self):
        """(frequency Hz, power dBm, rbw Hz): wide search, then a 2 MHz span on the peak."""
        f, _ = self._peak(850e6, 500e6)
        f, p = self._peak(f, 2e6)
        return f, p, float(self.a.query(":BWID?"))

    def close(self):
        self.a.write(":FREQ:CENT 850e6")
        self.a.write(":FREQ:SPAN 500e6")
        self.a.write(":INIT:CONT ON")
        self.a.close()


def scope_mean(s, ch, n=3):
    vals = []
    for _ in range(n):
        time.sleep(0.25)
        _, v = s.waveform(ch)
        vals.append(v.mean())
    return float(np.mean(vals)), float(np.std(vals))


def set_vt(g, s, target, code):
    """Closed-loop DC level on Vt using scope CH1; returns (measured volts, code)."""
    if not V_LIMIT[0] <= target <= V_LIMIT[1]:
        raise ValueError(f"Vt target {target} V outside allowed window")
    s.write(f"C1:OFST {-target:.3f}V")  # keep CH1 centred on the target so it can use a fine scale
    for _ in range(4):
        g.set_offset_raw(min(max(code, 0), 4095))
        time.sleep(0.6)
        v, _ = scope_mean(s, 1, n=2)
        if abs(v - target) < 0.003:
            break
        code += (target - v) / OFFSET_V_PER_CODE
    return v, code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vmin", type=float, default=0.0)
    ap.add_argument("--vmax", type=float, default=3.3)
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--mixer-vdiv", type=float, default=None, help="fix the CH2 scale (V/div)")
    ap.add_argument("--out", default="phase_detector_calibration.csv")
    ap.add_argument("--no-down", action="store_true", help="skip the coarse sweep back down")
    ap.add_argument("--test", action="store_true", help="five coarse points, nothing saved")
    a = ap.parse_args()

    up = np.round(np.arange(a.vmin, a.vmax + a.step / 2, a.step), 4)
    down = np.round(np.arange(a.vmax - 0.05, a.vmin - 0.01, -0.25), 4)
    plan = [("up", v) for v in up] + ([] if a.no_down else [("down", v) for v in down])
    if a.test:
        plan = [("test", v) for v in np.linspace(a.vmin, a.vmax, 5)]

    out = Path(__file__).parent
    s, g, sa = SDS(), CGR201("COM12"), Analyzer()
    rows = []
    try:
        # DC only. The waveform must be switched OFF: with a waveform selected and amplitude 0
        # the CGR-201 still puts ~100 mV pk-pk of it on the output, which frequency-modulates the VCO.
        g.set_amplitude_raw(0)
        g.set_waveform("off")
        for c in ("C1:TRA ON", "C1:ATTN 1", "C1:CPL D1M", "C1:VDIV 0.12V", "C1:OFST 0V", "BWL C1,OFF", "MSIZ 70K",
                  f"C{MIXER_CH}:TRA ON", f"C{MIXER_CH}:ATTN 1", f"C{MIXER_CH}:CPL D1M", f"BWL C{MIXER_CH},ON",
                  f"C{MIXER_CH}:OFST 0V", "C3:TRA OFF", "C4:TRA OFF", "TDIV 1.00E-03S", "TRMD AUTO"):
            s.write(c)
        # 20 mV/div centred on +90 mV covers 10..170 mV. Bandwidth limit off on purpose:
        # the extra noise dithers the 8-bit converter so the mean resolves below one step.
        vdiv = a.mixer_vdiv or 0.02
        s.write(f"C{MIXER_CH}:VDIV {vdiv:.2E}V")
        s.write(f"C{MIXER_CH}:OFST -0.09V")
        s.write(f"BWL C{MIXER_CH},OFF")
        code = 2180.0
        for direction, target in plan:
            vt, code = set_vt(g, s, float(target), code)
            time.sleep(0.5)
            f, p, rbw = sa.measure()
            vm, vm_sd = scope_mean(s, MIXER_CH)
            if not 0.015 < vm < 0.165:
                print("  WARNING: mixer output near the edge of the scope range")
            row = dict(timestamp=dt.datetime.now().isoformat(timespec="seconds"), direction=direction,
                             vt_set_v=float(target), vt_meas_v=round(vt, 4), vco_freq_hz=f, vco_power_at_sa_dbm=round(p, 2),
                             sa_rbw_hz=rbw, mixer_out_v=vm, mixer_out_repeat_sd_v=vm_sd, mixer_scope_vdiv=vdiv)
            rows.append(row)
            if not a.test:  # append as we go so an interrupted run keeps its data
                new = not (out / a.out).exists() or len(rows) == 1
                with open(out / a.out, "w" if new else "a", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(row.keys()))
                    if new:
                        w.writeheader()
                    w.writerow(row)
            print(f"{direction:4s} Vt {vt:6.3f} V | f {f/1e6:9.3f} MHz  {p:6.2f} dBm | mixer {vm*1e3:8.3f} mV (+/- {vm_sd*1e3:.3f})", flush=True)
    finally:
        try:
            set_vt(g, s, 0.5, 2180.0 + 0.5 / OFFSET_V_PER_CODE)  # leave a steady 0.5 V on Vt
        finally:
            g.close()
            sa.close()
            s.close()
        if rows and not a.test:
            print("Saved", out / a.out)


if __name__ == "__main__":
    main()
