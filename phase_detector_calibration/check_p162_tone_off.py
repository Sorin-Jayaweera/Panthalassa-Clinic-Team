"""Tone off check of the amp chain: scope reading, then an SM200B search 420 to 3000 MHz for lines and noise.

Pluto off the whole time. Levels are before the 23 dB pads on the SM200B. Run from clinic/claude/signal_hound.
Usage: python check_p162_tone_off.py <label>
"""
import csv
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from run_pluto_full_range import Scope, tone_off  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

LABEL = sys.argv[1]
PAD_DB = 23.0
tone_off()
print("Pluto tone off", flush=True)
for vdiv in (0.2, 0.05):
    scope = Scope(1, vdiv)
    m, sd, r = scope.read()
    scope.drop()
    print(f"scope {vdiv*1e3:.0f} mV/div: mean {m*1e3:.2f} mV, repeat {sd*1e3:.2f} mV, rms {r*1e3:.2f} mV", flush=True)

h = sm_open_device()["device"]
rows = []
try:
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, -10.0)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    for c in np.arange(420.0, 3001.0, 40.0):
        sm_set_IQ_center_freq(h, c * 1e6)
        sm_configure(h, SM_MODE_IQ_STREAMING)
        fs = sm_get_IQ_parameters(h)["sample_rate"]
        iq = sm_get_IQ(h, 262_144, 0, SM_TRUE)["iq_buf"]
        sm_abort(h)
        win = np.hanning(len(iq))
        sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq * win))) / win.sum() + 1e-20) + PAD_DB
        fr = (c * 1e6 + np.fft.fftshift(np.fft.fftfreq(len(iq), 1 / fs))) / 1e6
        keep = abs(fr - c) < 19
        k = np.flatnonzero(keep)[int(sp[keep].argmax())]
        p = iq.real ** 2 + iq.imag ** 2
        rows.append([c, round(float(fr[k]), 3), round(float(sp[k]), 2), round(float(np.median(sp[keep])), 2), round(float(10 * np.log10(p.mean()) + PAD_DB), 2)])
finally:
    sm_close_device(h)
rows = np.array(rows)
with open(HERE / f"tone_off_{LABEL}.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["center_mhz", "strongest_mhz", "strongest_dbm", "median_bin_dbm", "window_total_dbm"])
    w.writerows(rows.tolist())
print(f"strongest line {rows[:,2].max():.1f} dBm at {rows[rows[:,2].argmax(),1]:.2f} MHz; window total {rows[:,4].min():.1f} to {rows[:,4].max():.1f} dBm, most at {rows[rows[:,4].argmax(),0]:.0f} MHz")
o = np.argsort(rows[:, 2])[::-1][:8]
print("top lines:", [(float(rows[i, 1]), float(rows[i, 2])) for i in sorted(o, key=lambda i: rows[i, 1])])
print("window total every 400 MHz:", [(float(c), float(t)) for c, t in zip(rows[::10, 0], rows[::10, 4])])
