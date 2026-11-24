"""Two display presets for the Siglent SDS1104X-E on the comparator test (×10 probes).

    .venv-scope/bin/python scope_preset.py overview   # 0.5 V/div, 0 V one division above the bottom
    .venv-scope/bin/python scope_preset.py detail     # 50 / 100 mV/div around the working levels

Overview: every node on screen, ground visible; good for power-up checks.
Detail: about 8x finer vertical steps (the scope digitises 8 bits over the
8 divisions on screen), for the trip point and the 27 MHz oscillation.
Offsets only move the trace on the screen; the scope still measures absolute volts.
"""

import sys
import time
import warnings

warnings.filterwarnings("ignore")
import pyvisa  # noqa: E402

RESOURCE = "USB0::62700::60984::SDSMMFCQ5R6888::0::INSTR"

PRESETS = {  # channel: (V/div, screen centre in V)
    "overview": {1: (0.5, 1.5), 2: (0.5, 1.5), 3: (0.5, 1.5), 4: (0.5, 1.5)},
    "detail": {1: (0.05, 1.20), 2: (0.05, 1.20), 3: (0.1, 1.25), 4: (0.1, 1.25)},
}


def main(name):
    s = pyvisa.ResourceManager("@py").open_resource(RESOURCE)
    s.timeout = 5000
    try:
        for ch, (vdiv, centre) in PRESETS[name].items():
            for c in (f"C{ch}:ATTN 10", f"C{ch}:VDIV {vdiv}V", f"C{ch}:OFST {-centre}V"):
                s.write(c)
                time.sleep(0.15)
        for ch in (1, 2, 3, 4):
            vdiv = float(s.query(f"C{ch}:VDIV?").split()[-1].rstrip("V"))
            ofst = float(s.query(f"C{ch}:OFST?").split()[-1].rstrip("V"))
            lo, hi = -ofst - 4 * vdiv, -ofst + 4 * vdiv
            print(f"C{ch}: {vdiv * 1e3:.0f} mV/div, screen {lo:+.2f} to {hi:+.2f} V, "
                  f"step about {(hi - lo) / 256 * 1e3:.1f} mV")
    finally:
        s.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "overview")
