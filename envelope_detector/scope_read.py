"""Read all four channels from the Siglent (current settings) and summarise each.

    .venv-scope/bin/python scope_read.py [tdiv]     # optional timebase, e.g. 50e-9 or 1e-3
"""
import sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, pyvisa

RES = "USB0::62700::60984::SDSMMFCQ5R6888::0::INSTR"

def num(s):
    return float(s.strip().split()[-1].rstrip("VSa/s").rstrip("V").rstrip("S"))

def grab(s, ch):
    vdiv = float(s.query(f"C{ch}:VDIV?").split()[-1].rstrip("V"))
    ofst = float(s.query(f"C{ch}:OFST?").split()[-1].rstrip("V"))
    s.write("WFSU SP,1,NP,0,FP,0")
    s.write(f"C{ch}:WF? DAT2")
    raw = s.read_raw()
    i = raw.index(b"#9")
    n = int(raw[i+2:i+11])
    d = np.frombuffer(raw[i+11:i+11+n], dtype=np.int8).astype(float)
    return d * vdiv / 25.0 - ofst

def main():
    s = pyvisa.ResourceManager("@py").open_resource(RES)
    s.timeout = 20000; s.chunk_size = 4 * 1024 * 1024
    if len(sys.argv) > 1:
        s.write(f"TDIV {sys.argv[1]}"); time.sleep(0.5)
    s.write("TRMD AUTO"); time.sleep(0.3)
    s.write("STOP"); time.sleep(0.3)  # freeze one acquisition for all channels
    sara = float(s.query("SARA?").split()[-1].replace("Sa/s", ""))
    tdiv = float(s.query("TDIV?").split()[-1].rstrip("S"))
    print(f"timebase {tdiv:g} s/div, {sara/1e6:g} MS/s")
    for ch in (1, 2, 3, 4):
        v = grab(s, ch)
        x = v - v.mean()
        f = np.fft.rfftfreq(len(x), 1 / sara); a = np.abs(np.fft.rfft(x * np.hanning(len(x))))
        a[f < 2 / (len(x) / sara)] = 0
        k = int(a.argmax())
        print(f"C{ch}: n={len(v)} mean {v.mean():+.4f} V  min {v.min():+.4f}  max {v.max():+.4f}  "
              f"pk-pk {1e3*(v.max()-v.min()):.1f} mV  rms noise {1e3*x.std():.1f} mV  strongest line {f[k]/1e6:.3f} MHz")
    s.write("TRMD AUTO"); s.close()

main()
