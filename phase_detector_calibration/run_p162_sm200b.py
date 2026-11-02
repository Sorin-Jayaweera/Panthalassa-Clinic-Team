"""Four ZX60-P162LN+ chain: tone, twice and three times the tone, and near DC on the SM200B, with the scope at each point.

700 to 1500 MHz, 20 MHz steps, at -70, -60, -50 and -45 dBm. Levels are before the 23 dB pads. Stops with the tone off if a
line passes STOP_DBM. The driver ends the process if the SM200B USB drops; rerun to carry on. Saves p162x4_sm200b_1nov.csv.
Run from clinic/claude/signal_hound. Also remeasures 1320 MHz at -65 dBm for the map.
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

PAD_DB = 23.0
STOP_DBM = 5.0
LEVELS = (-60.0, -45.0, -70.0, -50.0)
OUT = HERE / "p162x4_sm200b_1nov.csv"
MAP = HERE / "p162x4_map_1nov.csv"


def spectrum(h, center):
    sm_set_IQ_center_freq(h, center)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    iq = sm_get_IQ(h, 131_072, 0, SM_TRUE)["iq_buf"]
    sm_abort(h)
    win = np.hanning(len(iq))
    sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq * win))) / win.sum() + 1e-20) + PAD_DB
    return (center + np.fft.fftshift(np.fft.fftfreq(len(iq), 1 / fs))) / 1e6, sp


def near(h, f):
    fr, sp = spectrum(h, f * 1e6)
    return float(sp[abs(fr - f) <= 2.0].max())


def att_for(f, want):
    return min(89.75, round((float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - want) * 4) / 4)


def main():
    done = set()
    new = not OUT.exists()
    if not new:
        done = {(float(r["freq_mhz"]), float(r["pluto_want_dbm"])) for r in csv.DictReader(open(OUT))}
    scope = Scope(1, 0.2)
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        sm_set_ref_level(h, 0.0)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, 1)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        with open(MAP, "a", newline="") as fm:
            att = att_for(1320.0, -65.0)
            retry(lambda: tone_on(1320e6, att, SCALE), "tone 1320")
            time.sleep(0.3)
            m, sd, r = scope.read()
            csv.writer(fm).writerow([dt.datetime.now().isoformat(timespec="seconds"), "map", 1, 1320.0, att, -65.0, m, sd, r])
            print(f"1320 MHz -65 dBm remeasured: {m*1e3:.1f} mV", flush=True)
        with open(OUT, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "rms_v", "tone_dbm", "double_dbm", "triple_dbm", "low_mhz", "low_dbm"])
            for want in LEVELS:
                for f in np.arange(700.0, 1500.5, 20.0):
                    if (float(f), want) in done:
                        continue
                    att = att_for(f, want)
                    retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
                    time.sleep(0.3)
                    m, sd, r = scope.read()
                    t1, t2, t3 = near(h, f), near(h, 2 * f), near(h, 3 * f)
                    fr, sp = spectrum(h, 21e6)
                    keep = abs(fr) > 0.5
                    k = int(sp[keep].argmax())
                    w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, want, m, r, round(t1, 2), round(t2, 2), round(t3, 2), round(float(fr[keep][k]), 3), round(float(sp[keep][k]), 2)])
                    fh.flush()
                    if max(t1, t2, t3) > STOP_DBM:
                        print(f"STOP RULE at {f} MHz {want} dBm: {t1} {t2} {t3}", flush=True)
                        return
                print(f"sm200b {want} dBm finished {dt.datetime.now():%H:%M:%S}", flush=True)
    finally:
        scope.drop()
        sm_close_device(h)
        tone_off()
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
