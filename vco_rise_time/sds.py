"""Small helper for the Siglent SDS1104X-E over VISA (legacy SCPI command set)."""
import re
import time

import numpy as np
import pyvisa

RESOURCE = "USB0::0xF4EC::0xEE38::SDSMMFCQ5R6888::INSTR"
HDIV = 14  # horizontal divisions on the X-E series


def _num(s):
    return float(re.search(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?", s.split(",")[-1] if "," in s else s.split(" ", 1)[-1]).group())


class SDS:
    def __init__(self, resource=RESOURCE):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource)
        self.inst.chunk_size = 1024 * 1024
        self._drain()

    def _drain(self):
        """Drop anything left over from an interrupted transfer."""
        self.inst.timeout = 1500
        try:
            while True:
                self.inst.read_raw()
        except pyvisa.errors.VisaIOError:
            pass
        self.inst.timeout = 30000

    def close(self):
        self.inst.close()

    def write(self, cmd, wait=0.2):
        self.inst.write(cmd)
        time.sleep(wait)

    def query(self, cmd):
        return self.inst.query(cmd).strip()

    def num(self, cmd):
        return _num(self.query(cmd))

    def measure(self, ch, param):
        """Built-in measurement; returns None when the scope reports '****'."""
        r = self.query(f"C{ch}:PAVA? {param}")
        val = r.split(",")[-1]
        if "*" in val:
            return None
        return _num(val)

    def single(self, timeout=10.0):
        """Arm a single acquisition and wait until it has triggered and stopped."""
        self.write("TRMD SINGLE", 0.1)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if "Stop" in self.query("SAST?"):
                return True
            time.sleep(0.05)
        return False

    def waveform_raw(self, ch):
        """Return (codes int8, vdiv, offset, fs, t_first) for the channel's record."""
        vdiv = self.num(f"C{ch}:VDIV?")
        ofst = self.num(f"C{ch}:OFST?")
        tdiv = self.num("TDIV?")
        trdl = self.num("TRDL?")
        sara = self.query("SARA?").split(" ", 1)[-1]
        m = re.match(r"([\d.Ee+-]+)\s*([GMk]?)Sa/s", sara)
        fs = float(m.group(1)) * {"G": 1e9, "M": 1e6, "k": 1e3, "": 1}[m.group(2)]
        self.inst.write(f"C{ch}:WF? DAT2")
        raw = self.inst.read_raw()
        i = raw.index(b"#")
        nd = int(raw[i + 1:i + 2])
        n = int(raw[i + 2:i + 2 + nd])
        while len(raw) < i + 2 + nd + n + 2:  # block + trailing newlines may span several reads
            raw += self.inst.read_raw()
        if n == 0:
            raise RuntimeError(f"Scope returned no data for C{ch} (not triggered?)")
        codes = np.frombuffer(raw[i + 2 + nd:i + 2 + nd + n], dtype=np.int8).copy()
        return codes, vdiv, ofst, fs, -tdiv * HDIV / 2.0 - trdl

    def waveform(self, ch):
        """Return (t, v) arrays for the channel's on-screen record."""
        codes, vdiv, ofst, fs, t0 = self.waveform_raw(ch)
        return t0 + np.arange(len(codes)) / fs, codes * (vdiv / 25.0) - ofst
