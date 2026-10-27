"""Second idea for the AliExpress ADF5355 box: the PL2303's modem lines (DTR, RTS) and TXD (via 'break')
may be wired straight to the chip's CLK / DATA / LE, as on some cheap PLL boards, so serial bytes do nothing.

Each trial uses one wiring guess and its own target frequency, so the line on Spike says which trial worked:
trial k -> 8.050 + 0.050*k GHz on Out B (8.05 ... 8.60 GHz).

    python probe_bitbang.py COM14 100e6
"""
import itertools
import sys
import time

import serial

from adf5355_regs import registers, write_order

port, ref = sys.argv[1], float(sys.argv[2])
s = serial.Serial(port, 9600)
LINES = {"DTR": lambda v: setattr(s, "dtr", v), "RTS": lambda v: setattr(s, "rts", v), "TXD": lambda v: setattr(s, "break_condition", v)}

trials = [(perm, inv) for inv in (False, True) for perm in itertools.permutations(LINES, 3)]
for k, ((clk, data, le), inv) in enumerate(trials):
    f = 8.05e9 + 0.05e9 * k
    R, _ = registers(f, ref, "B")
    put = {n: (lambda fn: (lambda v: fn((not v) if inv else v)))(LINES[n]) for n in (clk, data, le)}
    put[clk](0); put[le](1)
    for w in write_order(R):
        put[le](0)
        for i in range(31, -1, -1):
            put[data]((w >> i) & 1)
            put[clk](1); put[clk](0)
        put[le](1)
    print(f"trial {k:2d}: CLK={clk} DATA={data} LE={le} inverted={inv} -> {f/1e9:.2f} GHz", flush=True)
    time.sleep(0.5)
s.close()
