"""Test A automated: step the Pluto level, read VENV (Input A) and VRMS (Input B) on the CGR-201, save a CSV.

Run with the Homebrew GNU Radio Python (it has the Soapy Pluto driver):

    PY=/usr/local/Cellar/gnuradio/3.10.12.0_12/libexec/venv/bin/python
    $PY ed_sweep.py                          # Step 4: CW sweep at 1.1 GHz
    $PY ed_sweep.py --freq 1.0e9 --levels=-20,-10,0   # Step 5: band edge
    $PY ed_sweep.py --pulse-us 100           # Step 6: CW then pulsed at each level
    $PY ed_sweep.py --scope-only             # read both inputs once, no RF

Close the CircuitGear software and any running GNU Radio flowgraph first:
both need exclusive access to the CGR-201 and the Pluto.

CGR-201 protocol from Syscomp's command list and the Yelloscope source
(github.com/johnpeck/yelloscope): 115200 baud, RTS/CTS, ASCII commands ending
in newline. 'c' returns 'D' + 4096 x (A, B) 16-bit big-endian samples, and
volts = (511 - sample) * step.
"""

import argparse
import csv
import glob
import os
import select
import statistics
import sys
import termios
import time
from datetime import datetime

LEVELS_DB = [-89, -80, -70, -60, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0]
PULSE_LEVELS_DB = [-20, -10, -5, 0]

# CGR-201 front-end resistor values (Yelloscope CGRMK2.tcl), used when the unit
# has no stored vertical calibration.
_K8_HIGH = (90.9e3 / (909e3 + 90.9e3)) * (1.87e3 / 7.5e3)
_K8_LOW = _K8_HIGH * (1 + 4.64e3 / 510)
STEP_LOW_DEFAULT = 1 / 1023.0 * 1.24 / _K8_LOW  # V per count, low range (about +/-2.6 V)

# EEPROM layout (Yelloscope main.tcl, CGRMK2.tcl, calibration.tcl)
EEPROM_OFFSET_LOW = {"A": 0, "B": 4}  # low-range offsets, 2 bytes each, stored as 2047 - offset
EEPROM_VERTICAL = 128  # "1" if a custom vertical calibration is stored
EEPROM_STEP_LOW = {"A": 160, "B": 192}  # low-range step sizes, 16 ASCII chars each

# timebase command code -> sampling rate (CGR-201 command list, "Select timebase")
SAMPLE_RATE = {0: 40e6, 1: 20e6, 2: 10e6, 3: 5e6, 4: 2.5e6, 5: 1.25e6, 6: 625e3, 7: 312.5e3, 8: 156.25e3}
CW_TIMEBASE = 8  # 26 ms per capture: long averages for steady levels


class CGR201:
    """Minimal CGR-201 scope driver: identify, configure both inputs, capture."""

    def __init__(self, port):
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0  # iflag: raw
        attrs[1] = 0  # oflag: raw
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL | termios.CRTSCTS
        attrs[3] = 0  # lflag: raw
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        self.cal = {}

    def close(self):
        os.close(self.fd)

    def send(self, cmd):
        os.write(self.fd, (cmd + "\n").encode("ascii"))

    def read(self, n, timeout=3.0):
        buf = bytearray()
        deadline = time.monotonic() + timeout
        while len(buf) < n:
            left = deadline - time.monotonic()
            if left <= 0:
                break
            ready, _, _ = select.select([self.fd], [], [], left)
            if ready:
                buf += os.read(self.fd, n - len(buf))
        return bytes(buf)

    def drain(self, wait=0.3):
        time.sleep(wait)
        while self.read(4096, timeout=0.05):
            pass

    def identify(self):
        self.send("")
        self.send("k")  # stop any capture in progress
        self.send("X")  # stop strip-chart mode
        self.send("d 0")  # no automatic digital-input reports
        self.drain()
        self.send("i")
        return self.read(64, timeout=1.5).decode("ascii", "replace").strip()

    def eeprom(self, address):
        self.send(f"e {address}")  # read only; 'E' would write
        resp = self.read(2, timeout=1.0)
        if len(resp) != 2 or resp[0:1] != b"e":
            raise IOError(f"bad EEPROM response at {address}: {resp!r}")
        return resp[1]

    def eeprom_string(self, address):
        chars = [self.eeprom(address + i) for i in range(16)]
        return "".join(chr(c) for c in chars if c != 0)

    def load_calibration(self):
        """Store {channel: (step V/count, offset counts)} for the low range of A and B."""
        custom = self.eeprom_string(EEPROM_VERTICAL) == "1"
        for ch in ("A", "B"):
            step = STEP_LOW_DEFAULT
            if custom:
                try:
                    step = float(self.eeprom_string(EEPROM_STEP_LOW[ch]))
                except ValueError:
                    pass
            hi, lo = self.eeprom(EEPROM_OFFSET_LOW[ch]), self.eeprom(EEPROM_OFFSET_LOW[ch] + 1)
            self.cal[ch] = (step, 0 if hi == 255 else 2047 - (hi * 256 + lo))
        return self.cal

    def setup(self):
        for ch in ("A", "B"):
            # DC coupling, low range, 0 V centered
            for cmd in (f"D {ch}", f"P {ch.lower()}", f"o {ch} {2047 + self.cal[ch][1]}"):
                self.send(cmd)
        for cmd in ("S", "R", "a 100"):  # trigger source A, auto-trigger every 3.2 ms
            self.send(cmd)
        self.set_timebase(CW_TIMEBASE)

    def set_timebase(self, code):
        self.send(f"B{code}")
        self.drain()

    def volts(self, ch, counts):
        step = self.cal[ch][0]
        return [(511 - c) * step for c in counts]

    def capture(self):
        """One 4096-sample capture; returns (A volts, B volts)."""
        termios.tcflush(self.fd, termios.TCIFLUSH)
        self.send("c")
        self.send("M")
        # Skip anything before the 'D' that starts the data block.
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            b = self.read(1, timeout=0.5)
            if b == b"D":
                break
        else:
            raise IOError("no capture data from the CGR-201")
        data = self.read(16384, timeout=5.0)
        if len(data) != 16384:
            raise IOError(f"short capture: {len(data)} of 16384 bytes")
        a = [data[i] * 256 + data[i + 1] for i in range(0, 16384, 4)]
        b = [data[i + 2] * 256 + data[i + 3] for i in range(0, 16384, 4)]
        clipped = min(a) <= 2 or max(a) >= 1021 or min(b) <= 2 or max(b) >= 1021
        return self.volts("A", a), self.volts("B", b), clipped


def measure_cw(scope, n_captures):
    """Average n captures. Returns (VENV V, VENV scatter mV, VRMS V, clipped?)."""
    a_all, b_all, clipped = [], [], False
    for _ in range(n_captures):
        a, b, c = scope.capture()
        a_all += a
        b_all += b
        clipped |= c
    return statistics.fmean(a_all), statistics.pstdev(a_all) * 1e3, statistics.fmean(b_all), clipped


def unsteady(std_mv, rise_v):
    """True if a CW step's scatter is far above normal.

    Normal: 2-3 mV with no RF, about 5 % of the rise at the top (Pluto ripple).
    On 1 Nov an intermittent RF connection gave 40-90 % of the rise."""
    return std_mv > 5.0 + 0.08 * abs(rise_v) * 1e3


def measure_pulsed(scope, n_captures, sample_rate, pulse_us):
    """Pulse top and baseline of VENV, skipping samples near the edges.

    Edges are found on a smoothed copy with hysteresis, so noise on weak pulses
    is not counted as extra edges; the levels are averaged from the raw samples.
    Returns (top V or None, baseline V, rising edges seen, mean VRMS V, clipped?)."""
    win = max(1, int(0.1 * pulse_us * 1e-6 * sample_rate))  # smoothing over a tenth of a pulse
    # skip the Pluto edge (~0.5 us) and the CGR-201's 70 ns, plus the shift the smoothing puts on the found edges
    guard = int(1.5e-6 * sample_rate) + 3 + win
    tops, bases, edges, b_all, clipped = [], [], 0, [], False
    for _ in range(n_captures):
        a, b, c = scope.capture()
        b_all += b
        clipped |= c
        csum = [0.0]
        for v in a:
            csum.append(csum[-1] + v)
        smooth = [(csum[min(len(a), i + win)] - csum[max(0, i - win)]) / (min(len(a), i + win) - max(0, i - win))
                  for i in range(len(a))]
        srt = sorted(smooth)
        lo, hi = srt[len(a) // 20], srt[-len(a) // 20]
        if hi - lo < 0.003:  # no pulses visible above the smoothed noise
            bases += a
            continue
        mid, hyst = (lo + hi) / 2, (hi - lo) / 4
        high, state = [], smooth[0] > mid
        for v in smooth:
            state = v > mid - hyst if state else v > mid + hyst
            high.append(state)
        flips = [i for i in range(1, len(a)) if high[i] != high[i - 1]]
        edges += sum(1 for i in flips if high[i])
        near = set()
        for i in flips:
            near.update(range(max(0, i - guard), min(len(a), i + guard)))
        for i, v in enumerate(a):
            if i not in near:
                (tops if high[i] else bases).append(v)
    top = statistics.fmean(tops) if tops else None
    return top, statistics.fmean(bases), edges, statistics.fmean(b_all), clipped


def pulse_timebase(pulse_us):
    """Fastest sampling that still fits 8 on/off periods (period = 2 x pulse) in one 4096-sample capture."""
    for code in sorted(SAMPLE_RATE):
        if 4096 / SAMPLE_RATE[code] >= 8 * 2 * pulse_us * 1e-6:
            return code
    return max(SAMPLE_RATE)


def ask_volts(prompt):
    """Ask for a DMM reading in volts; Enter skips. Returns the text typed ('' if skipped)."""
    while True:
        answer = input(prompt).strip()
        if not answer:
            return ""
        try:
            float(answer)
            return answer
        except ValueError:
            print("    please type a number in volts, e.g. 1.139, or just Enter to skip")


def pluto_serial():
    """Serial number of the Pluto on USB (macOS), so each CSV says which unit was used."""
    import subprocess
    try:
        out = subprocess.run(["system_profiler", "SPUSBDataType"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if "PlutoSDR (ADALM-PLUTO)" in line:
            for nxt in lines[i + 1:i + 8]:
                if "Serial Number:" in nxt:
                    return nxt.split("Serial Number:")[1].strip()
    return "not found"


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbserial-*"))
    if not ports:
        sys.exit("CGR-201 not found (no /dev/cu.usbserial-*). Is it plugged in?")
    return ports[0]


class PlutoTone:
    """The signal of ed_test_pluto_tx_soapy.grc: 100 kHz tone x on/off gate -> Soapy Pluto sink."""

    def __init__(self, freq_hz, samp_rate=2e6):
        from gnuradio import analog, blocks, gr, soapy
        self.samp_rate = samp_rate
        self.tb = gr.top_block()
        tone = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 100e3, 0.7, 0, 0)
        self.gate = blocks.vector_source_c([1 + 0j], True, 1, [])
        mul = blocks.multiply_cc(1)
        self.sink = soapy.sink("driver=plutosdr", "fc32", 1, "", "", [""], [""])
        self.sink.set_sample_rate(0, samp_rate)
        self.sink.set_bandwidth(0, 20e6)
        self.sink.set_frequency(0, freq_hz - 100e3)
        self.set_level(-89)
        self.tb.connect(tone, (mul, 0))
        self.tb.connect(self.gate, (mul, 1))
        self.tb.connect(mul, self.sink)

    def set_level(self, level_db):
        self.sink.set_gain(0, min(max(89 + level_db, 0.0), 89.0))

    def set_pulsed(self, pulse_us):
        """pulse_us = None for a steady tone; otherwise on for pulse_us, off for the same time."""
        if pulse_us is None:
            self.gate.set_data([1 + 0j], [])
        else:
            n = max(1, round(pulse_us * 1e-6 * self.samp_rate))
            self.gate.set_data([1 + 0j] * n + [0j] * n, [])

    def start(self):
        self.tb.start()

    def stop(self):
        self.set_level(-89)
        self.tb.stop()
        self.tb.wait()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--freq", type=float, default=1.1e9, help="RF frequency in Hz (default 1.1e9)")
    p.add_argument("--levels", default=None,
                   help="comma-separated TX levels in dB (-89 = minimum, 0 = full); "
                        f"default {LEVELS_DB} for CW, {PULSE_LEVELS_DB} with --pulse-us")
    p.add_argument("--pulse-us", type=float, default=None,
                   help="Step 6: at each level measure CW, then pulses this long (same gap)")
    p.add_argument("--settle", type=float, default=1.0, help="seconds to wait after each change")
    p.add_argument("--captures", type=int, default=3, help="CGR-201 captures averaged per measurement")
    p.add_argument("--port", default=None, help="CGR-201 serial port (default: auto)")
    p.add_argument("--scope-only", action="store_true", help="read both inputs once, no Pluto, no RF")
    p.add_argument("--yes", action="store_true", help="don't ask before turning RF on")
    p.add_argument("--ask-vrms", action="store_true",
                   help="also hold each level and ask for a DMM reading of VRMS (q = stop)")
    p.add_argument("--no-eref", action="store_true",
                   help="don't ask for the DMM's EREF reading before and after the run")
    args = p.parse_args()
    levels = [float(x) for x in args.levels.split(",")] if args.levels else (
        PULSE_LEVELS_DB if args.pulse_us else LEVELS_DB)

    scope = CGR201(args.port or find_port())
    try:
        ident = scope.identify()
        if "CircuitGear" not in ident:
            sys.exit(f"Unexpected identity from the CGR-201: {ident!r}")
        cal = scope.load_calibration()
        scope.setup()
        print(f"{ident} | A: {cal['A'][0] * 1e3:.4f} mV/count, offset {cal['A'][1]}"
              f" | B: {cal['B'][0] * 1e3:.4f} mV/count, offset {cal['B'][1]}")
        serial = pluto_serial()
        print(f"Pluto serial: {serial}")

        venv0, std, vrms0, clipped = measure_cw(scope, args.captures)
        print(f"No RF (Pluto idle): VENV (A) = {venv0:.4f} V, noise {std:.1f} mV"
              f" | VRMS (B) = {vrms0:.4f} V{'  CLIPPED' if clipped else ''}")
        if args.scope_only:
            return

        eref_start = eref_end = ""
        if not args.no_eref:
            eref_start = ask_volts("EREF on the DMM now, before RF (V), Enter to skip: ")
            if eref_start:
                print(f"    no-RF VENV - EREF = {1e3 * (venv0 - float(eref_start)):+.1f} mV"
                      f" (CGR-201 vs DMM; expect within about 10 mV)")

        mode = f"{args.pulse_us:g} us pulses (and CW)" if args.pulse_us else "CW"
        if not args.yes:
            input(f"RF will go from the Pluto into the ED at {args.freq / 1e9:.3f} GHz, {mode}, "
                  f"levels {levels[0]:g} to {levels[-1]:g} dB. Enter to start, Ctrl-C to abort: ")

        pulse_code = pulse_timebase(args.pulse_us) if args.pulse_us else None
        pluto = PlutoTone(args.freq)
        rows = []
        pluto.start()
        try:
            for i, level in enumerate(levels, 1):
                pluto.set_pulsed(None)
                pluto.set_level(level)
                scope.set_timebase(CW_TIMEBASE)
                print(f"\n>>> Step {i}/{len(levels)}: NOW AT TX {level:g} dB, CW  [{datetime.now():%H:%M:%S}]")
                time.sleep(args.settle)
                venv, std, vrms, clipped = measure_cw(scope, args.captures)
                tries = 1
                while unsteady(std, venv - venv0) and tries < 3:
                    print(f"    UNSTEADY (noise {std:.1f} mV on a {1e3 * (venv - venv0):.1f} mV rise):"
                          f" RF dropping in and out? Check the RF cable. Re-measuring...")
                    time.sleep(args.settle)
                    venv, std, vrms, clipped = measure_cw(scope, args.captures)
                    tries += 1
                bad = unsteady(std, venv - venv0)
                print(f"    VENV {venv:.4f} V (rise {1e3 * (venv - venv0):7.1f} mV, noise {std:4.1f} mV)"
                      f" | VRMS {vrms:.4f} V (rise {1e3 * (vrms - vrms0):7.1f} mV){'  CLIPPED' if clipped else ''}"
                      f"{'  STILL UNSTEADY: marked in the CSV' if bad else ''}")
                vrms_dmm = ""
                if args.ask_vrms:
                    answer = input("    VRMS on the DMM (V), Enter to skip, q to stop: ").strip()
                    if answer.lower() == "q":
                        break
                    vrms_dmm = answer
                row = {"time": f"{datetime.now():%H:%M:%S}", "tx_level_db": level, "freq_hz": args.freq,
                       "venv_v": round(venv, 5), "venv_rise_v": round(venv - venv0, 5), "venv_noise_mv": round(std, 2),
                       "vrms_v": round(vrms, 5), "vrms_rise_v": round(vrms - vrms0, 5), "vrms_dmm_v": vrms_dmm,
                       "clipped": int(clipped), "unsteady": int(bad), "tries": tries}

                if args.pulse_us:
                    pluto.set_pulsed(args.pulse_us)
                    scope.set_timebase(pulse_code)
                    print(f"    now {args.pulse_us:g} us pulses (CGR-201 at {SAMPLE_RATE[pulse_code] / 1e6:g} MS/s)")
                    time.sleep(args.settle)
                    top, base, edges, vrms_p, clipped_p = measure_pulsed(scope, args.captures, SAMPLE_RATE[pulse_code],
                                                                         args.pulse_us)
                    rise_cw = venv - venv0
                    if top is None:
                        print(f"    no pulses visible | between pulses {base:.4f} V")
                    else:
                        print(f"    pulse top {top:.4f} V, between {base:.4f} V, height {1e3 * (top - base):6.1f} mV"
                              f" = {(top - base) / rise_cw:.3f} x CW rise | {edges} pulses | VRMS {vrms_p:.4f} V")
                    row.update({"pulse_us": args.pulse_us, "pulse_top_v": "" if top is None else round(top, 5),
                                "pulse_base_v": round(base, 5),
                                "pulse_height_v": "" if top is None else round(top - base, 5),
                                "pulse_vs_cw": "" if top is None or rise_cw <= 0 else round((top - base) / rise_cw, 4),
                                "pulses_seen": edges, "vrms_pulsed_v": round(vrms_p, 5), "clipped": int(clipped or clipped_p)})
                rows.append(row)
        finally:
            pluto.stop()
            print("RF off (Pluto stopped).")

        if not args.no_eref:
            eref_end = ask_volts("EREF on the DMM now, after RF (V), Enter to skip: ")
            if eref_start and eref_end:
                print(f"    EREF drift over the run: {1e3 * (float(eref_end) - float(eref_start)):+.1f} mV")

        if not rows:
            print("No steps recorded, nothing saved.")
            return
        os.makedirs(os.path.join(here, "data"), exist_ok=True)
        kind = f"pulse{args.pulse_us:g}us" if args.pulse_us else "sweep"
        out = os.path.join(here, "data", f"ed_{kind}_{args.freq / 1e9:.2f}GHz_{datetime.now():%Y%m%d_%H%M%S}.csv")
        with open(out, "w", newline="") as f:
            f.write(f"# baseline_no_rf_venv_v,{venv0:.5f}\n# baseline_no_rf_vrms_v,{vrms0:.5f}\n"
                    f"# eref_start_dmm_v,{eref_start}\n# eref_end_dmm_v,{eref_end}\n# pluto_serial,{serial}\n"
                    f"# cgr_step_mv_a,{cal['A'][0] * 1e3:.5f}\n# cgr_step_mv_b,{cal['B'][0] * 1e3:.5f}\n")
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {out}")
    finally:
        scope.close()


if __name__ == "__main__":
    main()
