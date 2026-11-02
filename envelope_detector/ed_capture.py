"""Save raw CGR-201 captures of VENV (Input A) and VRMS (Input B), with and without the Pluto on.

    PY=/usr/local/Cellar/gnuradio/3.10.12.0_12/libexec/venv/bin/python
    $PY ed_capture.py --ripple                 # CW at TX 0 dB: where does the VENV ripple come from?
    $PY ed_capture.py --pulse-us 10            # raw pulse shapes (10 us on, 10 us off)

Each run first captures with the Pluto idle (the reference), then with RF on, at
each sampling rate. Saves data/ed_capture_<kind>_<freq>_<time>.csv and prints the
strongest spectral lines of VENV. Plot with plot_capture.py.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import numpy as np

import ed_sweep as E

RIPPLE_CODES = (5, 2)  # 1.25 MS/s (sees 100-600 kHz) and 10 MS/s (up to the CGR-201's 5 MHz)


def lines(v, fs, n=5):
    """Strongest spectral lines of a capture (Hann window, mean removed): [(Hz, mV peak)]."""
    x = np.asarray(v) - np.mean(v)
    w = np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x * w)) * 2 / w.sum()
    freqs = np.fft.rfftfreq(len(x), 1 / fs)
    spec[:3] = 0  # ignore DC leakage
    peaks = [i for i in range(1, len(spec) - 1) if spec[i] >= spec[i - 1] and spec[i] >= spec[i + 1]]
    peaks.sort(key=lambda i: spec[i], reverse=True)
    return [(freqs[i], spec[i] * 1e3) for i in peaks[:n]]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    kind = p.add_mutually_exclusive_group(required=True)
    kind.add_argument("--ripple", action="store_true", help="CW: capture VENV ripple at two sampling rates")
    kind.add_argument("--pulse-us", type=float, help="pulses this long (same gap): capture their shape")
    p.add_argument("--freq", type=float, default=1.1e9, help="RF frequency in Hz (default 1.1e9)")
    p.add_argument("--level", type=float, default=0.0, help="Pluto TX level in dB (default 0 = full)")
    p.add_argument("--captures", type=int, default=2, help="captures saved per sampling rate")
    p.add_argument("--yes", action="store_true", help="don't ask before turning RF on")
    args = p.parse_args()

    if args.ripple:
        codes, label = RIPPLE_CODES, "ripple"
    else:
        codes, label = (E.pulse_timebase(args.pulse_us), 0), f"pulse{args.pulse_us:g}us"  # and 40 MS/s for edges

    scope = E.CGR201(E.find_port())
    rows, pluto = [], None
    try:
        ident = scope.identify()
        if "CircuitGear" not in ident:
            sys.exit(f"Unexpected identity from the CGR-201: {ident!r}")
        scope.load_calibration()
        scope.setup()
        serial = E.pluto_serial()
        print(f"{ident} | Pluto serial: {serial}")

        def grab(state):
            for code in codes:
                scope.set_timebase(code)
                fs = E.SAMPLE_RATE[code]
                for k in range(args.captures):
                    a, b, clipped = scope.capture()
                    rows.extend({"state": state, "fs_hz": fs, "capture": k, "i": i, "t_s": i / fs,
                                 "venv_v": round(va, 5), "vrms_v": round(vb, 5)} for i, (va, vb) in enumerate(zip(a, b)))
                    top = ", ".join(f"{f / 1e3:.1f} kHz {m:.2f} mV" for f, m in lines(a, fs, 4))
                    print(f"  {state:5} {fs / 1e6:5.2f} MS/s #{k}: VENV mean {np.mean(a):.4f} V, sd {1e3 * np.std(a):.1f} mV"
                          f"{'  CLIPPED' if clipped else ''} | strongest lines: {top}")

        print("Pluto idle (reference):")
        grab("no RF")
        what = "CW" if args.ripple else f"{args.pulse_us:g} us pulses"
        if not args.yes:
            input(f"RF on: {what} at {args.freq / 1e9:.3f} GHz, TX {args.level:g} dB. Enter to start, Ctrl-C to abort: ")
        pluto = E.PlutoTone(args.freq)
        pluto.set_pulsed(None if args.ripple else args.pulse_us)
        pluto.start()
        pluto.set_level(args.level)
        time.sleep(1.0)
        print(f"RF on ({what}, TX {args.level:g} dB):")
        grab("RF")
    finally:
        if pluto is not None:
            pluto.stop()
            print("RF off (Pluto stopped).")
        scope.close()

    os.makedirs(os.path.join(here, "data"), exist_ok=True)
    out = os.path.join(here, "data", f"ed_capture_{label}_{args.freq / 1e9:.2f}GHz_{datetime.now():%Y%m%d_%H%M%S}.csv")
    with open(out, "w", newline="") as f:
        f.write(f"# pluto_serial,{serial}\n# tx_level_db,{args.level:g}\n# pulse_us,{args.pulse_us or ''}\n")
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
