"""Log the tone leak on the SM200B while run_pluto_explore.py sweeps the Pluto. It does not control the Pluto.

Follows the newest line of pluto_explore_1nov.csv and tunes between that frequency and the next one, 41.5 MHz wide, so
the tone is in the window whichever it is on. Saves the strongest line. A loop in the shell restarts this if the USB drops,
since the driver ends the process. Levels are before the 23 dB pads, assumed in place.
"""
import csv
import datetime as dt
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
from smdevice.sm_api import *  # noqa: E402,F403

CAL = Path(__file__).resolve().parent.parent / "phase_detector_calibration"
SRC = CAL / "pluto_explore_1nov.csv"
OUT = CAL / "pluto_leak_during_map_1nov.csv"
PAD_DB = 23.0
BLOCK = 65_536


def newest():
    with open(SRC, "rb") as fh:
        fh.seek(-400, 2)
        return fh.read().decode().strip().splitlines()[-1].split(",")


h = sm_open_device()["device"]
new = not OUT.exists()
try:
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, -10.0)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    with open(OUT, "a", newline="") as fo:
        w = csv.writer(fo)
        if new:
            w.writerow(["timestamp", "pass", "last_freq_mhz", "pluto_want_dbm", "line_mhz", "line_dbm", "median_dbm"])
        last = None
        while True:
            row = newest()
            if row[1] != "map2d":
                if last is not None:
                    break
                time.sleep(2)
                continue
            if row[3] == last:
                time.sleep(0.05)
                continue
            last = row[3]
            f = float(row[3])
            center = (f + 5.0) * 1e6
            sm_set_IQ_center_freq(h, center)
            sm_configure(h, SM_MODE_IQ_STREAMING)
            fs = sm_get_IQ_parameters(h)["sample_rate"]
            iq = sm_get_IQ(h, BLOCK, 0, SM_TRUE)["iq_buf"]
            sm_abort(h)
            win = np.hanning(len(iq))
            sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq * win))) / win.sum() + 1e-20) + PAD_DB
            fr = (center + np.fft.fftshift(np.fft.fftfreq(len(iq), 1 / fs))) / 1e6
            k = int(sp.argmax())
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), row[1], f, row[5], round(float(fr[k]), 3), round(float(sp[k]), 2), round(float(np.median(sp)), 2)])
            fo.flush()
finally:
    sm_close_device(h)
