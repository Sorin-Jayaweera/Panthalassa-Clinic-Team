"""Continuous watch of 9.0-10.8 GHz on the SM200B while the radar is on. Run from clinic/claude/signal_hound.

    python ../radar_test/sm200b_monitor.py [minutes]

Each line is one 3 s max-hold (longer than one antenna rotation, 2.0-2.5 s): the largest level, where, and the
margin to the +20 dBm limit. Every line is saved to radar_test/monitor_<time>.csv and the last max-hold trace to
radar_test/scans/monitor_last.csv.

RBW is 10 MHz, the widest, so a radar pulse reads close to its true peak. For a 0.8 us pulse the reading is within
about 1 dB of the peak; for a 0.08 us pulse it can read 2 to 6 dB low. The "margin" printed assumes the worse case
and subtracts 6 dB.

Internal attenuator 30 dB, ref level +20 dBm. This watch cannot protect the instrument by itself: the damage would
be done by the first pulse. It tells you how much room there is before you move the antenna or the radar.
"""
import csv
import datetime as dt
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from smdevice.sm_api import *  # noqa: E402,F403

PULSE_ALLOWANCE_DB = 6.0
LIMIT = 20.0


def main():
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 30
    h = sm_open_device()["device"]
    out = HERE / f"monitor_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"
    try:
        sm_set_attenuator(h, SM_MAX_ATTEN)
        sm_set_ref_level(h, 20.0)
        sm_set_sweep_start_stop(h, 9.0e9, 10.8e9)
        sm_set_sweep_coupling(h, 10e6, 10e6, 0.001)
        sm_set_sweep_detector(h, SM_DETECTOR_MIN_MAX, SM_VIDEO_LOG)
        sm_set_sweep_scale(h, SM_SCALE_LOG)
        sm_set_sweep_window(h, SM_WINDOW_FLAT_TOP)
        sm_set_sweep_spur_reject(h, SM_FALSE)
        sm_configure(h, SM_MODE_SWEEPING)
        q = sm_get_sweep_parameters(h)
        f = q["actual_start_freq"] + q["bin_size"] * np.arange(q["sweep_size"])
        with open(out, "w", newline="") as fh:
            csv.writer(fh).writerow(["time", "peak_dbm", "peak_freq_ghz", "margin_db_after_pulse_allowance", "sweeps"])
        print(f"watching 9.0-10.8 GHz, RBW 10 MHz, attenuator 30 dB; log {out.name}", flush=True)
        t_end = time.time() + 60 * minutes
        while time.time() < t_end:
            hold = np.full(q["sweep_size"], -200.0)
            n, t0 = 0, time.time()
            while time.time() - t0 < 3.0:
                hold = np.maximum(hold, np.asarray(sm_get_sweep(h)["sweep_max"], float))
                n += 1
            i = int(np.argmax(hold))
            margin = LIMIT - (hold[i] + PULSE_ALLOWANCE_DB)
            flag = "  <-- LESS THAN 15 dB MARGIN: do not move closer" if margin < 15 else ""
            flag = "  <-- UNDER 6 dB MARGIN: SET THE RADAR TO STANDBY NOW" if margin < 6 else flag
            now = dt.datetime.now().strftime("%H:%M:%S")
            print(f"{now}  peak {hold[i]:+6.1f} dBm at {f[i]/1e9:.4f} GHz  margin {margin:5.1f} dB  ({n} sweeps){flag}", flush=True)
            with open(out, "a", newline="") as fh:
                csv.writer(fh).writerow([now, f"{hold[i]:.2f}", f"{f[i]/1e9:.5f}", f"{margin:.1f}", n])
            np.savetxt(HERE / "scans" / "monitor_last.csv", np.column_stack([f, hold]), delimiter=",", header="freq_hz,maxhold_dbm", comments="", fmt=["%.0f", "%.2f"])
    finally:
        sm_abort(h)
        sm_close_device(h)


if __name__ == "__main__":
    main()
