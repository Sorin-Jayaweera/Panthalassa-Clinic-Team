"""The only way our scripts send a level to a CGR-201 generator output.

Guarantee: no command from these scripts can put a negative voltage (or more than
MAX_V) on the output, by that unit's own DMM calibration.

How:
- Every level goes through safe_code(), which needs a calibration for that unit's
  serial number in data/cgr_dc_cal.json. No calibration -> refused. No overrides.
- The lowest code allowed is the code for MIN_V = +0.10 V. The calibration was
  checked to within 5 mV (19 Nov), so even a 20x worse error stays above 0 V.
- Only DC is ever sent: amplitude 0 and waveform off first, then the offset. A
  waveform (sine, triangle, square) is never switched on, because its swing
  below the offset would not be covered by this check. Emmy measured ~100 mV of
  swing even at amplitude 0 with a waveform on.
- The final code is checked again against the unit's floor and ceiling right
  before it is sent, after rounding.

What it cannot control (hardware, not software): the output a CGR-201 has at
power-up or after a USB re-plug, before any command (measured -0.2 to -0.3 V on
19 Nov), and anything another program sends.
"""

import json
import os
import termios
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_FILE = os.path.join(HERE, "data", "cgr_dc_cal.json")

MIN_V = 0.10  # V, lowest level ever sent (positive margin above 0 V)
MAX_V = 3.00  # V, comparator at VCC = 3.3 V: working max 3.5 V, absolute max 3.8 V


class Refused(ValueError):
    pass


def unit_cal(serial):
    if not os.path.exists(CAL_FILE):
        raise Refused(f"No calibration file {CAL_FILE}. Nothing sent.")
    cal = json.load(open(CAL_FILE)).get(serial)
    if not cal or "zero_code" not in cal or "mv_per_code" not in cal:
        raise Refused(f"No calibration for {serial} in {CAL_FILE}. Calibrate it with the DMM first. Nothing sent.")
    if not 1.5 < cal["mv_per_code"] < 2.3:
        raise Refused(f"{serial}: slope {cal['mv_per_code']} mV/code is not plausible. Nothing sent.")
    return cal["zero_code"], cal["mv_per_code"] * 1e-3


def limits(serial):
    """(lowest code, highest code) this unit may ever be sent."""
    zero, slope = unit_cal(serial)
    import math
    return math.ceil(zero + MIN_V / slope), math.floor(zero + MAX_V / slope)


def volts_of(serial, code):
    zero, slope = unit_cal(serial)
    return (code - zero) * slope


def safe_code(serial, volts=None, code=None):
    """Code for `volts` (or check a raw `code`); refuses anything outside MIN_V..MAX_V."""
    zero, slope = unit_cal(serial)
    lo, hi = limits(serial)
    if code is None:
        if volts is None:
            raise Refused("Give a voltage or a code.")
        if not MIN_V <= volts <= MAX_V:
            raise Refused(f"{volts:.3f} V is outside the allowed {MIN_V:.2f}-{MAX_V:.2f} V. Nothing sent.")
        code = round(zero + volts / slope)
    code = int(code)
    if not lo <= code <= hi:
        raise Refused(f"{serial}: code {code} = {volts_of(serial, code):+.3f} V is outside codes {lo}-{hi} "
                      f"({MIN_V:.2f}-{MAX_V:.2f} V). Nothing sent.")
    return code


def send_dc(g, serial, code):
    """Send DC to an open CGR201 `g`. Re-checks the code; only DC commands."""
    lo, hi = limits(serial)
    if not lo <= code <= hi:  # second check, right before sending
        raise Refused(f"{serial}: code {code} outside {lo}-{hi}. Nothing sent.")
    for c in ("WA0", "WWD", f"WO{code}"):  # amplitude 0, waveform off, then the DC offset
        g.send(c)
        time.sleep(0.05)
    termios.tcdrain(g.fd)  # every byte out before the port closes
    time.sleep(0.3)
