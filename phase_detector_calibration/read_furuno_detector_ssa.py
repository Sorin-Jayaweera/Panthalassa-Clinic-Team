"""SSA3021X view of the phase detector output with the Furuno as source and PLL on. Max Hold, saved as CSV and screen."""
import csv
import io
import time
from pathlib import Path

import pyvisa
from PIL import Image

OUT = Path(__file__).resolve().parent / "furuno_detector_1nov_pll_on"
a = pyvisa.ResourceManager().open_resource("USB0::0xF4EC::0x1300::SSA3XLBC3R0429::INSTR")
a.timeout = 20000
a.write(":DISP:WIND:TRAC:Y:RLEV 10")
a.write(":POW:ATT:AUTO ON")
a.write(":BWID 1e6")
a.write(":DET POS")
a.write(":SWE:TIME 1")
a.write(":INIT:CONT ON")


def hold(name, start, stop, wait):
    a.write(f":FREQ:STAR {start}")
    a.write(f":FREQ:STOP {stop}")
    a.write(":TRAC1:MODE WRIT")
    time.sleep(0.5)
    a.write(":TRAC1:MODE MAXH")
    time.sleep(wait)
    tr = [float(x) for x in a.query(":TRAC:DATA? 1").strip().strip(",").split(",")]
    n = len(tr)
    fr = [start + i / (n - 1) * (stop - start) for i in range(n)]
    top = sorted(range(n), key=lambda i: tr[i], reverse=True)[:4]
    print(name, "RBW", a.query(":BWID?").strip(), "att", a.query(":POW:ATT?").strip(), "median", round(sorted(tr)[n // 2], 1),
          "top", [(round(fr[i] / 1e6, 2), round(tr[i], 1)) for i in top], flush=True)
    with open(OUT / f"ssa_{name}.csv", "w", newline="") as f:
        csv.writer(f).writerows([["freq_hz", "dbm"], *zip(fr, tr)])
    a.write(":HCOP:SDUM:DATA?")
    raw = a.read_raw()
    Image.open(io.BytesIO(raw[raw.find(b"BM"):])).save(OUT / f"ssa_{name}_screen.png")


hold("0p1_to_50MHz", 100e3, 50e6, 40)
hold("0p1_to_2100MHz", 100e3, 2100e6, 40)
a.write(":TRAC1:MODE WRIT")
a.close()
