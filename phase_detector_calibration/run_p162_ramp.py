"""Four ZX60-P162LN+ chain: Pluto power ramp at several frequencies, scope and SM200B at each point.

Starts at the Pluto minimum and steps up. Stops with the tone off if the detector passes STOP_MV or the SM200B line,
referred to before the 23 dB pads, passes STOP_DBM. Run from clinic/claude/signal_hound. Saves p162x4_ramp_1nov.csv.
Usage: python run_p162_ramp.py [top_dbm]
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
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from run_pluto_full_range import SCALE, Scope, _MAP, retry, tone_off, tone_on  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

TOP_DBM = float(sys.argv[1]) if len(sys.argv) > 1 else -50.0
FREQS = (1054.0, 1000.0, 1090.0, 950.0, 1150.0)
LEVELS = np.arange(-89.0, TOP_DBM + 0.5, 3.0)
PAD_DB = 23.0
STOP_MV = 450.0
STOP_DBM = -10.0
OUT = HERE / "p162x4_ramp_1nov.csv"


def line(h, f):
    sm_set_IQ_center_freq(h, f * 1e6)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    iq = sm_get_IQ(h, 262_144, 0, SM_TRUE)["iq_buf"]
    sm_abort(h)
    win = np.hanning(len(iq))
    sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq * win))) / win.sum() + 1e-20) + PAD_DB
    fr = (f * 1e6 + np.fft.fftshift(np.fft.fftfreq(len(iq), 1 / fs))) / 1e6
    m = abs(fr - f) < 2.0
    return float(sp[m].max()), float(np.median(sp))


def main():
    new = not OUT.exists()
    scope = Scope(1, 0.2)
    h = sm_open_device()["device"]
    stopped = False
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        sm_set_ref_level(h, 0.0)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, 1)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        with open(OUT, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v", "line_dbm", "median_dbm"])
            for f in FREQS:
                full_scale = float(np.interp(f, _MAP[:, 0], _MAP[:, 1]))
                for want in LEVELS:
                    att = min(89.75, round((full_scale - want) * 4) / 4)
                    retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                    time.sleep(0.3)
                    m, sd, r = scope.read()
                    ld, md = line(h, f)
                    w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, float(want), m, sd, r, round(ld, 2), round(md, 2)])
                    fh.flush()
                    print(f"{f:.0f} MHz {want:6.1f} dBm att {att:5.2f} | {m*1e3:7.1f} mV rms {r*1e3:5.1f} | line {ld:6.1f} dBm", flush=True)
                    if abs(m) * 1e3 > STOP_MV or ld > STOP_DBM:
                        print(f"STOP RULE at {f:.0f} MHz {want} dBm", flush=True)
                        stopped = True
                        break
                tone_off()
                if stopped:
                    break
    finally:
        scope.drop()
        sm_close_device(h)
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
