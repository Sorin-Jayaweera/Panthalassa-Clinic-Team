"""Set one CGR-201's generator output to a DC level, by its serial number.

    python3 cgr_dc.py C2BKNPC 1.20            # DC at 1.20 V by that unit's calibration
    python3 cgr_dc.py C2BKNPC --code 2834     # raw code (still checked)
    python3 cgr_dc.py C2BKNPC 1.20 --dry-run  # show the code, send nothing
    python3 cgr_dc.py C2BKNPC --limits        # show the allowed code range

Every level goes through cgr_guard.py: only DC, only 0.10 to 3.00 V by the unit's
own DMM calibration (data/cgr_dc_cal.json). A unit without a calibration is refused.
Read the output with the DMM before it touches the board.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cgr_guard  # noqa: E402
from ed_sweep import CGR201  # noqa: E402  (termios serial, RTS/CTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("serial", help="USB serial number, e.g. C2BKNPC")
    ap.add_argument("volts", nargs="?", type=float)
    ap.add_argument("--code", type=int, help="raw offset code instead of volts (still checked)")
    ap.add_argument("--dry-run", action="store_true", help="check and print only; send nothing")
    ap.add_argument("--limits", action="store_true", help="print the allowed range and exit")
    a = ap.parse_args()

    try:
        lo, hi = cgr_guard.limits(a.serial)
        if a.limits:
            print(f"{a.serial}: codes {lo}-{hi} = {cgr_guard.volts_of(a.serial, lo):.3f} to "
                  f"{cgr_guard.volts_of(a.serial, hi):.3f} V")
            return
        code = cgr_guard.safe_code(a.serial, volts=a.volts, code=a.code)
    except cgr_guard.Refused as e:
        sys.exit(f"REFUSED: {e}")
    est = cgr_guard.volts_of(a.serial, code)
    if a.dry_run:
        print(f"{a.serial}: would send DC code {code} = {est:.3f} V. Nothing sent (dry run).")
        return

    port = f"/dev/cu.usbserial-{a.serial}"
    if not os.path.exists(port):
        sys.exit(f"{port} not found. Connected: {[p for p in os.listdir('/dev') if p.startswith('cu.usbserial')]}")
    g = CGR201(port)
    try:
        ident = g.identify()
        if "CircuitGear" not in ident:
            sys.exit(f"Unexpected identity on {port}: {ident!r}. Nothing sent.")
        cgr_guard.send_dc(g, a.serial, code)
        print(f"{a.serial}: DC code {code} = {est:.3f} V by its calibration. Check with the DMM before connecting.")
    finally:
        g.close()


if __name__ == "__main__":
    main()
