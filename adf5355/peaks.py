"""Quick SM200B sweep (only when Spike is closed): list the strongest lines between two frequencies.

    python peaks.py 7.6e9 8.7e9
"""
import os
import sys
from pathlib import Path

import numpy as np

SH = Path(__file__).resolve().parent.parent / "signal_hound"
os.chdir(SH)                                    # sm_api.dll is loaded relative to the working directory
sys.path.insert(0, str(SH))
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
from smdevice.sm_api import *  # noqa: E402,F403

start, stop = float(sys.argv[1]), float(sys.argv[2])
h = sm_open_device()["device"]
try:
    sm_set_attenuator(h, SM_MAX_ATTEN)
    sm_set_ref_level(h, 20.0)
    sm_set_sweep_start_stop(h, start, stop)
    sm_set_sweep_coupling(h, 300e3, 300e3, 0.001)
    sm_set_sweep_detector(h, SM_DETECTOR_MIN_MAX, SM_VIDEO_LOG)
    sm_set_sweep_scale(h, SM_SCALE_LOG)
    sm_configure(h, SM_MODE_SWEEPING)
    q = sm_get_sweep_parameters(h)
    f = q["actual_start_freq"] + q["bin_size"] * np.arange(q["sweep_size"])
    hold = np.full(q["sweep_size"], -200.0)
    for _ in range(5):
        hold = np.maximum(hold, np.asarray(sm_get_sweep(h)["sweep_max"], float))
finally:
    sm_close_device(h)
idx = []
for i in np.argsort(hold)[::-1]:
    if all(abs(f[i] - f[j]) > 5e6 for j in idx):
        idx.append(i)
    if len(idx) == 5:
        break
for i in idx:
    print(f"{f[i]/1e9:.4f} GHz  {hold[i]:6.1f} dBm")
