"""Send 'go to 8.3 GHz on Out B' to the AliExpress ADF5355 box in many candidate formats at one baud rate.
Watch Spike: if the 8.000 GHz line moves to 8.300 GHz, one of the formats worked (then bisect).

    python probe_formats.py COM14 115200
"""
import sys
import time

import serial

from adf5355_regs import registers, write_order

port, baud = sys.argv[1], int(sys.argv[2])
R, _ = registers(8300e6, 100e6, "B")
words = write_order(R)
R25, _ = registers(8300e6, 25e6, "B")
words25 = write_order(R25)

FORMATS = {
    "raw4_msb_ref100": b"".join(w.to_bytes(4, "big") for w in words),
    "raw4_msb_ref25": b"".join(w.to_bytes(4, "big") for w in words25),
    "hex_lines_ref100": b"".join(f"{w:08X}\r\n".encode() for w in words),
    "hex_lines_ref25": b"".join(f"{w:08X}\r\n".encode() for w in words25),
    "0xhex_lines_ref100": b"".join(f"0x{w:08X}\r\n".encode() for w in words),
    "mhz_plain": b"8300\r\n",
    "mhz_dot": b"8300.000\r\n",
    "hz_plain": b"8300000000\r\n",
    "F_mhz": b"F8300\r\n",
    "f_mhz": b"f8300\r\n",
    "FREQ_mhz": b"FREQ 8300MHz\r\n",
    "FREQ_scpi": b":FREQ 8.3GHz\r\n",
    "set_mhz": b"SET 8300\r\n",
}

s = serial.Serial(port, baud, timeout=0.2)
for name, payload in FORMATS.items():
    s.reset_input_buffer()
    s.write(payload)
    time.sleep(0.4)
    reply = s.read(256)
    print(f"{baud:6d} {name:20s} {len(payload):4d} bytes  reply: {reply[:60] if reply else '-'}")
s.close()
