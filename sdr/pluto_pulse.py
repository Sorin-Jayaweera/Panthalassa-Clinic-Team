"""Make the Pluto transmit a repeating RF pulse. Run with the radioconda Python (it has pyadi-iio):

    C:\\Users\\Sorin\\radioconda\\python.exe pluto_pulse.py --freq 1.1e9 --att 31 --width 1e-6 --period 1e-3

The pulse is a block of constant samples, so the RF is at the LO frequency during the pulse and off between pulses.
Sample rate is left as found (30.72 MS/s on this unit), so the width is a whole number of 32.55 ns samples.
The pulse repeats until the stop file appears or --seconds runs out; then the buffer is removed and the output is
set to maximum attenuation.

The attenuation floor is the same as pluto_cw.py: nothing below ATT_MIN_DB unless --floor is given on purpose.
"""
import argparse
import os
import sys
import time

_BIN = r"C:\Users\Sorin\radioconda\Library\bin"          # where libiio.dll is; it is found through PATH
os.environ["PATH"] = _BIN + os.pathsep + os.environ.get("PATH", "")
os.add_dll_directory(_BIN)
import adi  # noqa: E402
import numpy as np  # noqa: E402

P_WORST_MAX_DBM = 11.0
P_LIMIT_DBM = -20.0
ATT_MIN_DB = max(0.0, P_WORST_MAX_DBM - P_LIMIT_DBM)      # 31 dB

ap = argparse.ArgumentParser()
ap.add_argument("--freq", type=float, required=True)
ap.add_argument("--att", type=float, required=True)
ap.add_argument("--width", type=float, required=True, help="pulse width, seconds")
ap.add_argument("--period", type=float, required=True, help="pulse repetition period, seconds")
ap.add_argument("--amp", type=float, default=0.5, help="0 to 1, same meaning as the tone scale")
ap.add_argument("--seconds", type=float, default=30)
ap.add_argument("--stop-file", default="")
ap.add_argument("--floor", type=float, default=ATT_MIN_DB, help="lowest attenuation allowed, dB")
a = ap.parse_args()
if a.att < a.floor:
    sys.exit(f"refusing {a.att} dB: the floor is {a.floor} dB")
if not 0 < a.amp <= 1:
    sys.exit("amp must be between 0 and 1")

sdr = adi.Pluto("ip:192.168.2.1")
fs = int(sdr.sample_rate)
n_period = int(round(a.period * fs))
n_width = max(1, int(round(a.width * fs)))
if n_period < 2 * n_width or n_period > 2_000_000:
    sys.exit("period must be at least twice the width and under 2 million samples")
iq = np.zeros(n_period, dtype=np.complex64)
iq[:n_width] = a.amp * (2 ** 15 - 1)                    # constant in-phase level: RF at the LO frequency
sdr.tx_hardwaregain_chan0 = -89.75
sdr.tx_lo = int(a.freq)
sdr.tx_cyclic_buffer = True
sdr.tx(iq)
sdr.tx_hardwaregain_chan0 = -min(89.75, round(a.att * 4) / 4)
print(f"PULSING fs={fs} width_samples={n_width} width_s={n_width/fs:.4e} period_samples={n_period} period_s={n_period/fs:.6e}", flush=True)
t0 = time.time()
try:
    while time.time() - t0 < a.seconds and not (a.stop_file and os.path.exists(a.stop_file)):
        time.sleep(0.1)
finally:
    sdr.tx_hardwaregain_chan0 = -89.75
    sdr.tx_destroy_buffer()
    print("STOPPED", flush=True)
