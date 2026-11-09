"""ADCMP604 comparator tests with the CGR-201: DC levels, slow triangle, trip-point sweep.

Commands (run them from this folder):

    python cmp_cgr.py calibrate            # Step 0: map generator code -> volts. BOARD DISCONNECTED.
    python cmp_cgr.py dc 0.60              # DC level, waveform off (the clean way to get DC)
    python cmp_cgr.py triangle --center 1.24 --pkpk 0.10 --freq 1    # Test 3
    python cmp_cgr.py sweep --vn 1.162     # Test 2: find the trip point around IN- = 1.162 V
    python cmp_cgr.py off                  # park the output at 0 V DC

Add --port COM5 (Windows) or --port /dev/cu.usbserial-XXXX if the port is not found
automatically. Close the CircuitGear software and any GNU Radio flowgraph first: the
CGR-201 serial port can only be open in one program.

How it works
- Generator: the commands in ../vco_rise_time/cgr201.py (WA amplitude, WO offset, WW
  waveform, WF frequency). DC = amplitude 0 + waveform OFF + offset code. With a waveform
  selected the output carries ~100 mV pk-pk even at amplitude 0 (run_noise.py, and the
  error log on the website), so this script always switches the waveform off for DC.
- Scope: the capture protocol from ed_sweep.py (115200 baud, RTS/CTS; 'c' + 'M' returns
  'D' + 4096 x (A, B) 16-bit big-endian samples; volts = (511 - sample) * step).
  Input A watches IN+. Input B watches OUT+ (J7) to tell high from low.
- The offset code -> volts map is measured in `calibrate` and stored in
  data/cgr201_offset_cal.json. Every other command refuses to run without it, and refuses
  any level outside SAFE_V.

Why `sweep` asks for the DMM: the CGR-201 scope resolves 5.05 mV per count on this unit
(data/ed_sweep_1.10GHz_20261026_220822.csv header), as large as the whole +/-5 mV offset
spec. The DMM across IN+ and IN- reads the difference directly to 0.1 mV, at the pins,
so the 1 kOhm series resistor and input loading drop out.
"""

import argparse
import csv
import glob
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vco_rise_time"))
from cgr201 import CGR201  # noqa: E402  (team driver: generator commands)

DATA = os.path.join(HERE, "data")
CAL_FILE = os.path.join(DATA, "cgr201_offset_cal.json")

# Comparator at VCC = 3.3 V: abs max input -0.5 to 3.8 V (ADCMP604 Table 3, p. 6);
# working range -0.2 to 3.5 V (Table 1, p. 3). Stay well inside both.
SAFE_V = (0.0, 3.0)

# Prior for the generator map before calibration: 1.875 mV/code measured on 10 Oct
# (phase_detector_calibration/run_log_step_response.txt); nominal 0 V at code 2047.5
# (vendor formula in cgr201.set_offset). Only used to choose the calibration points.
PRIOR_V_PER_CODE = 1.875e-3
PRIOR_ZERO_CODE = 2047.5
AMP_V_PER_CODE_PKPK = 1.400e-3  # square-wave amplitude, same log. Triangle assumed the same: check on the scope.

# CGR-201 scope front end (from ed_sweep.py / Yelloscope CGRMK2.tcl)
_K8_HIGH = (90.9e3 / (909e3 + 90.9e3)) * (1.87e3 / 7.5e3)
_K8_LOW = _K8_HIGH * (1 + 4.64e3 / 510)
STEP_LOW_DEFAULT = 1 / 1023.0 * 1.24 / _K8_LOW  # ~5.3 mV/count, low range (about +/-2.7 V)
EEPROM_OFFSETS = 0
EEPROM_VERTICAL = 128
EEPROM_STEP_A_LOW = 160


# --------------------------------------------------------------------------- instrument

class CGR(CGR201):
    """Team generator driver + the scope capture from ed_sweep.py, on one serial port."""

    def __init__(self, port):
        super().__init__(port)
        self.ser.rtscts = True  # ed_sweep.py captures with RTS/CTS flow control
        self.step_a = STEP_LOW_DEFAULT
        self.step_b = STEP_LOW_DEFAULT  # channel B calibration is not read; B is only used for high/low

    # --- serial helpers
    def _read(self, n, timeout):
        buf = bytearray()
        deadline = time.monotonic() + timeout
        while len(buf) < n and time.monotonic() < deadline:
            self.ser.timeout = max(0.01, min(0.5, deadline - time.monotonic()))
            buf += self.ser.read(n - len(buf))
        return bytes(buf)

    def _drain(self, wait=0.3):
        time.sleep(wait)
        self.ser.reset_input_buffer()

    # --- identity and scope setup (same command sequence as ed_sweep.py)
    def identify(self):
        for c in ("", "k", "X", "d 0"):  # stop captures, strip chart, digital reports
            self.cmd(c)
        self._drain()
        self.cmd("i")
        return self._read(64, 1.5).decode("ascii", "replace").strip()

    def _eeprom(self, address):
        self.cmd(f"e {address}")
        r = self._read(2, 1.0)
        if len(r) != 2 or r[0:1] != b"e":
            raise IOError(f"bad EEPROM response at {address}: {r!r}")
        return r[1]

    def _eeprom_string(self, address):
        return "".join(chr(c) for c in (self._eeprom(address + i) for i in range(16)) if c != 0)

    def setup_scope(self):
        """Channel A and B: DC, low range (+/-2.7 V), 156 kHz sampling (26 ms per capture)."""
        if self._eeprom_string(EEPROM_VERTICAL) == "1":
            try:
                self.step_a = float(self._eeprom_string(EEPROM_STEP_A_LOW))
            except ValueError:
                pass
        hi, lo = self._eeprom(EEPROM_OFFSETS), self._eeprom(EEPROM_OFFSETS + 1)
        offset = 0 if hi == 255 else 2047 - (hi * 256 + lo)
        for c in ("D A", "P a", f"o A {2047 + offset}", "D B", "P b", "o B 2047",
                  "B8", "S", "R", "a 100"):
            self.cmd(c)
        self._drain()

    def capture(self):
        """One 4096-sample capture: (A volts array, B volts array)."""
        self.ser.reset_input_buffer()
        self.cmd("c")
        self.cmd("M")
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if self._read(1, 0.5) == b"D":
                break
        else:
            raise IOError("no capture data from the CGR-201")
        data = self._read(16384, 5.0)
        if len(data) != 16384:
            raise IOError(f"short capture: {len(data)} of 16384 bytes")
        raw = np.frombuffer(data, dtype=">u2").reshape(-1, 2).astype(float)
        return (511 - raw[:, 0]) * self.step_a, (511 - raw[:, 1]) * self.step_b

    # --- generator, always through the calibration and the safety window
    def dc_code(self, code):
        self.set_amplitude_raw(0)
        self.set_waveform("off")
        self.set_offset_raw(min(max(int(round(code)), 0), 4095))


class Cal:
    def __init__(self, v_per_code, zero_code, method, when):
        self.v_per_code, self.zero_code, self.method, self.when = v_per_code, zero_code, method, when

    def code(self, volts):
        if not SAFE_V[0] <= volts <= SAFE_V[1]:
            raise ValueError(f"{volts:.3f} V is outside the allowed window {SAFE_V} V")
        return self.zero_code + volts / self.v_per_code

    def volts(self, code):
        return (code - self.zero_code) * self.v_per_code

    @staticmethod
    def load():
        if not os.path.exists(CAL_FILE):
            sys.exit("No generator calibration. Run `python cmp_cgr.py calibrate` first (board disconnected).")
        with open(CAL_FILE) as f:
            d = json.load(f)
        if not d["time"].startswith(datetime.now().strftime("%Y-%m-%d")):
            print(f"NOTE: calibration is from {d['time']}. Re-run `calibrate` if anything was re-plugged.")
        return Cal(d["v_per_code"], d["zero_code"], d["method"], d["time"])


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbserial-*") + glob.glob("/dev/ttyUSB*"))
    if not ports:
        sys.exit("CGR-201 not found. Plug it in, or give --port (Windows: --port COM5).")
    return ports[0]


def open_cgr(port):
    g = CGR(port or find_port())
    ident = g.identify()
    if "CircuitGear" not in ident:
        g.close()
        sys.exit(f"Unexpected identity from the CGR-201: {ident!r}")
    return g


def ask_float(prompt):
    """Number typed by the user, or None for Enter."""
    while True:
        s = input(prompt).strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            print("  Type a number, or press Enter to skip.")


# --------------------------------------------------------------------------- calibrate

def cmd_calibrate(args):
    print("CALIBRATION. The CGR-201 Output must go ONLY to Input A (BNC tee) and the DMM.")
    print("The comparator board must NOT be connected: this step drives about 0.4 and 1.9 V.")
    if input("Board disconnected? Type yes: ").strip().lower() != "yes":
        sys.exit("Stopped.")
    g = open_cgr(args.port)
    try:
        g.setup_scope()
        points = []
        for target in (0.4, 1.9):
            code = int(round(PRIOR_ZERO_CODE + target / PRIOR_V_PER_CODE))
            g.dc_code(code)
            time.sleep(0.5)
            a = np.concatenate([g.capture()[0] for _ in range(3)])
            v_a = float(a.mean())
            v_dmm = ask_float(f"  code {code}: Input A reads {v_a:.4f} V. DMM on the Output (V), Enter = use Input A: ")
            points.append((code, v_a, v_dmm))
        use_dmm = all(p[2] is not None for p in points)
        (c0, a0, d0), (c1, a1, d1) = points
        v0, v1 = (d0, d1) if use_dmm else (a0, a1)
        slope = (v1 - v0) / (c1 - c0)
        if not 1.5e-3 < slope < 2.3e-3:
            sys.exit(f"Slope {slope * 1e3:.3f} mV/code is far from the 1.875 measured on 10 Oct. "
                     "Check the Output -> Input A connection. Nothing saved.")
        zero = c0 - v0 / slope
        cal = Cal(slope, zero, "dmm" if use_dmm else "input_a", datetime.now().isoformat(timespec="seconds"))
        # check point: 1.20 V
        g.dc_code(cal.code(1.20))
        time.sleep(0.5)
        v_chk = float(np.concatenate([g.capture()[0] for _ in range(3)]).mean())
        d_chk = ask_float(f"  check at 1.200 V: Input A reads {v_chk:.4f} V. DMM (V), Enter to skip: ")
        g.dc_code(cal.code(0.0))
        os.makedirs(DATA, exist_ok=True)
        with open(CAL_FILE, "w") as f:
            json.dump({"v_per_code": slope, "zero_code": zero, "method": cal.method, "time": cal.when,
                       "points": points, "check_1v2_input_a": v_chk, "check_1v2_dmm": d_chk}, f, indent=1)
        print(f"Saved {CAL_FILE}: {slope * 1e3:.4f} mV/code, 0 V at code {zero:.1f} (from {cal.method}).")
        if d_chk is not None and abs(d_chk - 1.20) > 0.005:
            print(f"WARNING: the check point is {1e3 * (d_chk - 1.2):+.1f} mV off. Re-run, and make sure the DMM "
                  "is on the Output and nothing else is connected.")
        print("Output parked at 0 V DC.")
    finally:
        g.close()


# --------------------------------------------------------------------------- dc / off / triangle

def cmd_dc(args):
    cal = Cal.load()
    code = cal.code(args.volts)
    g = open_cgr(args.port)
    try:
        g.dc_code(code)
        print(f"DC {args.volts:.3f} V (code {round(code)}), waveform off. "
              "At the board this reads a few mV lower (1 kOhm + input loading): measure it there.")
    finally:
        g.close()


def cmd_off(args):
    args.volts = 0.0
    cmd_dc(args)


def cmd_triangle(args):
    cal = Cal.load()
    # Margin: allow the real amplitude to be 50 % larger than nominal before hitting SAFE_V.
    for edge in (args.center - 0.75 * args.pkpk, args.center + 0.75 * args.pkpk):
        cal.code(edge)  # raises if outside the window
    amp_code = args.pkpk / AMP_V_PER_CODE_PKPK
    if amp_code > 4095:
        sys.exit("pk-pk too large")
    g = open_cgr(args.port)
    try:
        g.set_amplitude_raw(0)
        g.set_waveform("off")
        g.set_offset_raw(int(round(cal.code(args.center))))
        g.set_frequency(args.freq)
        g.set_waveform("triangle")
        g.set_amplitude_raw(amp_code)
        print(f"Triangle {args.freq:g} Hz, {1e3 * args.pkpk:.0f} mV pk-pk (nominal, amplitude code "
              f"{round(amp_code)}), centred on {args.center:.3f} V. Check the real min/max on the scope (CH1).")
        print("Run `python cmp_cgr.py off` when done.")
    finally:
        g.close()


# --------------------------------------------------------------------------- sweep (Test 2)

def classify(b, low, high):
    """Fraction of Input B samples high / in between / low (OUT+ levels low, high)."""
    hi_th, lo_th = low + 0.75 * (high - low), low + 0.25 * (high - low)
    f_hi = float(np.mean(b > hi_th))
    f_lo = float(np.mean(b < lo_th))
    return f_hi, 1.0 - f_hi - f_lo, f_lo


def crossing(codes, fracs, level):
    """First code (interpolated) where fracs crosses `level`, walking in the order given."""
    for (c0, f0), (c1, f1) in zip(zip(codes, fracs), zip(codes[1:], fracs[1:])):
        if (f0 - level) * (f1 - level) <= 0 and f0 != f1:
            return c0 + (level - f0) * (c1 - c0) / (f1 - f0)
    return None


class Bench:
    """What `sweep` needs from the hardware. A simulator with the same methods is used in testing."""

    def __init__(self, g, settle, captures):
        self.g, self.settle, self.captures = g, settle, captures

    def set_code(self, code):
        self.g.dc_code(code)
        time.sleep(self.settle)

    def measure(self):
        a, b = zip(*(self.g.capture() for _ in range(self.captures)))
        return np.concatenate(a), np.concatenate(b)


def run_sweep(bench, cal, vn, span, coarse, fine, ask=ask_float, log=print):
    """Find the IN+ level where OUT+ switches, around IN- = vn. Returns (step rows, summary dict)."""
    rows = []

    def go(code):  # every code the sweep sends passes the same safety window
        v = cal.volts(code)
        if not SAFE_V[0] - 1e-9 <= v <= SAFE_V[1] + 1e-9:
            raise ValueError(f"code {code} = {v:.3f} V is outside {SAFE_V} V")
        bench.set_code(code)

    def point(code, phase, low=None, high=None):
        go(code)
        a, b = bench.measure()
        r = {"phase": phase, "code": int(code), "vp_set_v": round(cal.volts(code), 5),
             "vp_input_a_v": round(float(a.mean()), 5), "b_mean_v": round(float(b.mean()), 5)}
        if low is not None:
            r["frac_high"], r["frac_mid"], r["frac_low"] = (round(x, 4) for x in classify(b, low, high))
        rows.append(r)
        return r, b

    # 1. Output levels well below and well above the threshold
    c_lo, c_hi = int(round(cal.code(vn - 0.08))), int(round(cal.code(vn + 0.08)))
    _, b_low = point(c_lo, "ref_low")
    _, b_high = point(c_hi, "ref_high")
    low, high = float(np.median(b_low)), float(np.median(b_high))
    log(f"  OUT+ on Input B: {low:.3f} V with IN+ 80 mV below IN-, {high:.3f} V with IN+ 80 mV above")
    if high - low < -0.2:
        raise RuntimeError("OUT+ goes DOWN when IN+ goes up: Input B is probably on OUT- (J8), not OUT+ (J7).")
    if high - low < 0.2:
        raise RuntimeError(f"OUT+ only changes by {1e3 * (high - low):.0f} mV (expect ~390). Check: 3.3 V on, "
                           "100 Ohm across J7/J8, Input B on J7, IN+ connected through the 1 kOhm, IN- at the pot.")

    # 2. Coarse scan up
    codes = list(range(int(round(cal.code(vn - span))), int(round(cal.code(vn + span))) + 1, coarse))
    c_trip = None
    for c in codes:
        r, _ = point(c, "coarse", low, high)
        if r["frac_high"] >= 0.5:
            c_trip = c
            break
    if c_trip is None:
        raise RuntimeError(f"No switching between IN- -{1e3 * span:.0f} and +{1e3 * span:.0f} mV. "
                           "Check the IN- value you typed (DMM at J3), or widen --span.")

    # 3. Fine scans, each approached from the correct side
    up_codes = list(range(c_trip - fine, c_trip + fine + 1))
    go(up_codes[0] - 8)
    up = [point(c, "fine_up", low, high)[0]["frac_high"] for c in up_codes]
    down_codes = up_codes[::-1]
    go(down_codes[0] + 8)
    down = [point(c, "fine_down", low, high)[0]["frac_high"] for c in down_codes]

    c50_up, c50_down = crossing(up_codes, up, 0.5), crossing(down_codes, down, 0.5)
    c10, c90 = crossing(up_codes, up, 0.1), crossing(up_codes, up, 0.9)
    if c50_up is None or c50_down is None:
        raise RuntimeError("The fine scan did not cross 50 %. Re-run with a larger --fine.")
    mv = cal.v_per_code * 1e3
    s = {"vn_dmm_v": vn, "out_low_v": round(low, 4), "out_high_v": round(high, 4),
         "c50_up": round(c50_up, 2), "c50_down": round(c50_down, 2),
         "vp50_up_set_v": round(cal.volts(c50_up), 5),
         "hysteresis_mv": round((c50_up - c50_down) * mv, 2),
         "width_10_90_mv": round(abs(c90 - c10) * mv, 2) if c10 is not None and c90 is not None else "",
         "max_frac_mid": round(max(r.get("frac_mid", 0) for r in rows), 3)}
    # Coarse, DMM-free estimate: Input A (IN+) at the fine-up step nearest the 50 % point, minus IN-.
    nearest = min((r for r in rows if r["phase"] == "fine_up"), key=lambda r: abs(r["code"] - c50_up))
    s["offset_input_a_mv"] = round(1e3 * (nearest["vp_input_a_v"] - vn), 1)

    # 4. DMM at the 50 % point, each direction: park on the code just below/above, read VP-VN,
    #    then correct by the fraction of a code to the interpolated 50 % point.
    for name, c50, approach in (("up", c50_up, -8), ("down", c50_down, +8)):
        c_park = int(np.floor(c50)) if name == "up" else int(np.ceil(c50))
        go(c_park + approach)
        go(c_park)
        a, b = bench.measure()
        f_hi = classify(b, low, high)[0]
        d = ask(f"  [{name}] parked at code {c_park} (OUT+ high {100 * f_hi:.0f} % of the time). "
                "DMM red on J1 (IN+), black on J3 (IN-), mV. Enter to skip: ")
        s[f"dmm_{name}_code"] = c_park
        s[f"dmm_{name}_mv"] = "" if d is None else d
        s[f"offset_{name}_mv"] = "" if d is None else round(d + (c50 - c_park) * mv, 2)
    off = [s[k] for k in ("offset_up_mv", "offset_down_mv") if s[k] != ""]
    s["offset_mv"] = round(float(np.mean(off)), 2) if off else ""
    s["pass_5mv"] = "" if not off else ("pass" if abs(s["offset_mv"]) <= 5.0 else "FAIL")
    go(cal.code(max(vn - 0.08, SAFE_V[0])))  # leave the output low
    return rows, s


def cmd_sweep(args):
    cal = Cal.load()
    print(f"Trip-point sweep around IN- = {args.vn:.4f} V (type the DMM reading at J3, not the pot setting).")
    print("Needs: comparator at 3.3 V, 100 Ohm across J7/J8, CGR Output -> 1 kOhm -> J1, Input A on J1, "
          "Input B on J7, pot on J3, DMM red J1 / black J3.")
    g = open_cgr(args.port)
    try:
        g.setup_scope()
        rows, s = run_sweep(Bench(g, args.settle, args.captures), cal, args.vn, args.span, args.coarse, args.fine)
    finally:
        g.close()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(DATA, exist_ok=True)
    steps = os.path.join(DATA, f"cmp_trip_vn{args.vn:.3f}_{stamp}.csv")
    keys = ["phase", "code", "vp_set_v", "vp_input_a_v", "b_mean_v", "frac_high", "frac_mid", "frac_low"]
    with open(steps, "w", newline="") as f:
        f.write(f"# vn_dmm_v,{args.vn}\n# cal,{cal.v_per_code:.6e} V/code,zero {cal.zero_code:.2f},{cal.method},{cal.when}\n")
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    summary = os.path.join(DATA, "cmp_trip_summary.csv")
    s = {"time": stamp, **s, "steps_file": os.path.basename(steps)}
    new = not os.path.exists(summary)
    with open(summary, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(s))
        if new:
            w.writeheader()
        w.writerow(s)
    print(f"\nIN- {args.vn:.4f} V | offset (DMM) {s['offset_mv']} mV -> {s['pass_5mv'] or 'no DMM reading'}"
          f" | Input A estimate {s['offset_input_a_mv']} mV (coarse)"
          f" | hysteresis {s['hysteresis_mv']} mV | 10-90 % width {s['width_10_90_mv']} mV"
          f" | most 'in between' samples {100 * s['max_frac_mid']:.0f} %")
    print(f"Saved {steps}\nAppended {summary}\nOutput left at IN- - 80 mV (OUT+ low).")


# --------------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--port", default=None, help="CGR-201 serial port (default: auto on Mac/Linux)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calibrate", help="map offset code -> volts (board disconnected)")
    d = sub.add_parser("dc", help="DC level, waveform off")
    d.add_argument("volts", type=float)
    sub.add_parser("off", help="park at 0 V DC")
    t = sub.add_parser("triangle", help="slow triangle for the chatter test")
    t.add_argument("--center", type=float, required=True, help="centre, V (use the measured IN-)")
    t.add_argument("--pkpk", type=float, default=0.10, help="peak-to-peak, V (default 0.10)")
    t.add_argument("--freq", type=float, default=1.0, help="Hz (default 1)")
    s = sub.add_parser("sweep", help="Test 2: trip point around IN-")
    s.add_argument("--vn", type=float, required=True, help="IN- as read by the DMM at J3, V")
    s.add_argument("--span", type=float, default=0.040, help="coarse search half-width, V (default 0.040)")
    s.add_argument("--coarse", type=int, default=4, help="coarse step, codes (default 4 = ~7.5 mV)")
    s.add_argument("--fine", type=int, default=12, help="fine scan half-width, codes (default 12 = ~22 mV)")
    s.add_argument("--settle", type=float, default=0.15, help="s to wait after each code change")
    s.add_argument("--captures", type=int, default=1, help="captures per point (each ~1.5 s)")
    args = p.parse_args()
    {"calibrate": cmd_calibrate, "dc": cmd_dc, "off": cmd_off,
     "triangle": cmd_triangle, "sweep": cmd_sweep}[args.cmd](args)


if __name__ == "__main__":
    main()
