"""Test A, Step 4 automated: step the Pluto TX level, read VENV on CGR-201 Input A, save a CSV.

Run with the Homebrew GNU Radio Python (it has the Soapy Pluto driver):

    /usr/local/Cellar/gnuradio/3.10.12.0_12/libexec/venv/bin/python ed_sweep.py

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

# CGR-201 front-end resistor values (Yelloscope CGRMK2.tcl), used when the unit
# has no stored vertical calibration.
_K8_HIGH = (90.9e3 / (909e3 + 90.9e3)) * (1.87e3 / 7.5e3)
_K8_LOW = _K8_HIGH * (1 + 4.64e3 / 510)
STEP_LOW_DEFAULT = 1 / 1023.0 * 1.24 / _K8_LOW  # V per count, low range (about +/-2.7 V)

EEPROM_OFFSETS = 0  # channel A low-range offset: 2 bytes
EEPROM_VERTICAL = 128  # "1" if a custom vertical calibration is stored
EEPROM_STEP_A_LOW = 160  # channel A low-range step size, 16 ASCII chars


class CGR201:
    """Minimal CGR-201 scope driver: identify, configure channel A, capture."""

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
        self.send(f"e {address}")
        resp = self.read(2, timeout=1.0)
        if len(resp) != 2 or resp[0:1] != b"e":
            raise IOError(f"bad EEPROM response at {address}: {resp!r}")
        return resp[1]

    def eeprom_string(self, address):
        chars = [self.eeprom(address + i) for i in range(16)]
        return "".join(chr(c) for c in chars if c != 0)

    def load_calibration(self):
        """Return (step V/count, offset counts) for channel A low range."""
        step = STEP_LOW_DEFAULT
        if self.eeprom_string(EEPROM_VERTICAL) == "1":
            try:
                step = float(self.eeprom_string(EEPROM_STEP_A_LOW))
            except ValueError:
                pass
        hi, lo = self.eeprom(EEPROM_OFFSETS), self.eeprom(EEPROM_OFFSETS + 1)
        offset = 0 if hi == 255 else 2047 - (hi * 256 + lo)
        return step, offset

    def setup_channel_a(self, offset):
        for cmd in ("D A", "P a", f"o A {2047 + offset}",  # DC, low range, 0 V centered
                    "D B", "P b", f"o B {2047}",
                    "B8",  # 156.25 kHz sampling: a 26 ms window per capture
                    "S", "R", "a 100"):  # trigger on A, auto-trigger every 3.2 ms
            self.send(cmd)
        self.drain()

    def capture(self):
        """One 4096-sample capture; returns (raw A list, raw B list)."""
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
        return a, b


def measure(scope, step, n_captures):
    """Average n captures. Returns (VENV volts, sample std mV, ch B volts, clipped?)."""
    a_all, b_all = [], []
    for _ in range(n_captures):
        a, b = scope.capture()
        a_all += a
        b_all += b
    a_mean = statistics.fmean(a_all)
    clipped = min(a_all) <= 2 or max(a_all) >= 1021
    return ((511 - a_mean) * step,
            statistics.pstdev(a_all) * step * 1e3,
            (511 - statistics.fmean(b_all)) * step,
            clipped)


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbserial-*"))
    if not ports:
        sys.exit("CGR-201 not found (no /dev/cu.usbserial-*). Is it plugged in?")
    return ports[0]


class PlutoTone:
    """CW tone from the Pluto: same signal as ed_test_pluto_tx_soapy.grc with Pulsed off."""

    def __init__(self, freq_hz, samp_rate=2e6):
        from gnuradio import analog, gr, soapy
        self.tb = gr.top_block()
        tone = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 100e3, 0.7, 0, 0)
        self.sink = soapy.sink("driver=plutosdr", "fc32", 1, "", "", [""], [""])
        self.sink.set_sample_rate(0, samp_rate)
        self.sink.set_bandwidth(0, 20e6)
        self.sink.set_frequency(0, freq_hz - 100e3)
        self.set_level(-89)
        self.tb.connect(tone, self.sink)

    def set_level(self, level_db):
        self.sink.set_gain(0, min(max(89 + level_db, 0.0), 89.0))

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
    p.add_argument("--levels", default=",".join(str(x) for x in LEVELS_DB),
                   help="comma-separated TX levels in dB (-89 = minimum, 0 = full)")
    p.add_argument("--settle", type=float, default=1.0, help="seconds to wait after each level change")
    p.add_argument("--captures", type=int, default=3, help="CGR-201 captures averaged per step")
    p.add_argument("--port", default=None, help="CGR-201 serial port (default: auto)")
    p.add_argument("--scope-only", action="store_true", help="read Input A once, no Pluto, no RF")
    p.add_argument("--yes", action="store_true", help="don't ask before turning RF on")
    p.add_argument("--ask-vrms", action="store_true",
                   help="hold each level and ask for the DMM's VRMS reading (q = stop)")
    args = p.parse_args()

    scope = CGR201(args.port or find_port())
    try:
        ident = scope.identify()
        if "CircuitGear" not in ident:
            sys.exit(f"Unexpected identity from the CGR-201: {ident!r}")
        step, offset = scope.load_calibration()
        scope.setup_channel_a(offset)
        print(f"{ident} | step {step * 1e3:.4f} mV/count, offset {offset} counts")

        venv, std, ch_b, clipped = measure(scope, step, args.captures)
        print(f"No RF (Pluto idle): Input A = {venv:.4f} V (noise {std:.1f} mV)"
              f"{'  CLIPPED' if clipped else ''} | Input B = {ch_b:.4f} V")
        if args.scope_only:
            return
        baseline = venv

        levels = [float(x) for x in args.levels.split(",")]
        if not args.yes:
            input(f"RF will go from the Pluto into the ED at {args.freq / 1e9:.3f} GHz, "
                  f"levels {levels[0]:g} to {levels[-1]:g} dB. Enter to start, Ctrl-C to abort: ")

        pluto = PlutoTone(args.freq)
        rows = []
        pluto.start()
        try:
            for i, level in enumerate(levels, 1):
                pluto.set_level(level)
                print(f"\n>>> Step {i}/{len(levels)}: NOW AT TX {level:g} dB (RF on)"
                      f"  [{datetime.now():%H:%M:%S}]")
                time.sleep(args.settle)
                venv, std, ch_b, clipped = measure(scope, step, args.captures)
                print(f"    VENV {venv:.4f} V | rise {1e3 * (venv - baseline):8.1f} mV"
                      f" | noise {std:5.1f} mV{'  CLIPPED' if clipped else ''}")
                vrms = ""
                if args.ask_vrms:
                    answer = input("    VRMS on the DMM (V), Enter to skip, q to stop: ").strip()
                    if answer.lower() == "q":
                        break
                    vrms = answer
                rows.append({
                    "time": f"{datetime.now():%H:%M:%S}",
                    "tx_level_db": level,
                    "freq_hz": args.freq,
                    "venv_v": round(venv, 5),
                    "venv_rise_v": round(venv - baseline, 5),
                    "venv_noise_mv": round(std, 2),
                    "vrms_dmm_v": vrms,
                    "input_b_v": round(ch_b, 5),
                    "clipped": int(clipped),
                })
        finally:
            pluto.stop()
            print("RF off (Pluto stopped).")

        if not rows:
            print("No steps recorded, nothing saved.")
            return
        os.makedirs(os.path.join(here, "data"), exist_ok=True)
        out = os.path.join(here, "data",
                           f"ed_sweep_{args.freq / 1e9:.2f}GHz_{datetime.now():%Y%m%d_%H%M%S}.csv")
        with open(out, "w", newline="") as f:
            f.write(f"# baseline_no_rf_v,{baseline:.5f}\n# cgr_step_mv,{step * 1e3:.5f}\n")
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {out}")
    finally:
        scope.close()


if __name__ == "__main__":
    main()
