"""Minimal driver for the Syscomp CircuitGear MKII (CGR-201) waveform generator.

Protocol from Syscomp's "CGR-201 Command List" and their open-source Tcl GUI
(waveform.tcl): 115200 8N1, ASCII commands terminated with a newline.

The generator output is bipolar, so `set_square` refuses levels outside
[V_MIN, V_MAX] to protect whatever is on the output (here: a VCO tuning port).
"""
import time

import serial

DDS_HZ_PER_COUNT = 0.04656613
V_MIN, V_MAX = 0.0, 3.2  # allowed output window, volts

WAVEFORMS = {"sine": "0", "square": "1", "triangle": "2", "sawtooth": "3", "off": "D"}


class CGR201:
    def __init__(self, port="COM12"):
        self.ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def close(self):
        self.ser.close()

    def cmd(self, text):
        self.ser.write((text + "\n").encode("ascii"))
        self.ser.flush()
        time.sleep(0.05)

    def identify(self):
        self.ser.reset_input_buffer()
        self.cmd("i")
        time.sleep(0.2)
        return self.ser.read(self.ser.in_waiting or 64).decode("ascii", "replace").strip()

    # --- raw generator settings -------------------------------------------
    def set_frequency(self, hz):
        n = round(hz / DDS_HZ_PER_COUNT)
        b = [(n >> s) & 0xFF for s in (24, 16, 8, 0)]
        self.cmd("WF%d %d %d %d" % tuple(b))

    def set_amplitude_raw(self, code):
        """0..4095 -> 0..100 % of full-scale amplitude."""
        code = int(round(code))
        if not 0 <= code <= 4095:
            raise ValueError(f"amplitude code {code} out of range")
        self.cmd(f"WA{code}")

    def set_offset_raw(self, code):
        code = int(round(code))
        if not 0 <= code <= 4095:
            raise ValueError(f"offset code {code} out of range")
        self.cmd(f"WO{code}")

    def set_offset(self, volts):
        """Nominal (uncalibrated) offset, from the vendor GUI's MKII formula."""
        self.set_offset_raw(4095.0 * (volts + 4.0) / 8.0)

    def set_waveform(self, name):
        self.cmd("WW" + WAVEFORMS[name])
