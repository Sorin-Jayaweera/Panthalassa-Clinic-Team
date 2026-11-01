"""Does a Pluto tone leak through the phase detector at 1.105 GHz? SM200B I/Q through 23 dB of pads, Spike closed.

Setup: Pluto -> 3 x ZX60-P103LN+ -> ZFRSC-42-S+ -> 4.5 in delay -> ZX05-30W-S+ -> IF -> pads -> SM200B.
Pluto level is limited by run_pluto_calibration.attenuation_for. Tone off, then on, 0.2 s at each centre.
Run from clinic/claude/signal_hound. Saves pluto_leak_1nov.npz.
"""
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from smdevice.sm_api import *  # noqa: E402,F403
from run_pluto_calibration import SCALE, attenuation_for, level_dbm, tone_off, tone_on  # noqa: E402

PAD_DB = 23.0
TONE_HZ = 1.105e9
TONE_DBM = -36.0
CENTERS = {"near_dc": 21e6, "if_1p105GHz": 1.105e9}
REF_DBM = -10.0
BLOCK = 500_000


def capture(h, center):
    sm_set_ref_level(h, REF_DBM)
    sm_set_IQ_center_freq(h, center)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_IQ_queue_size(h, 100.0)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    iq = np.concatenate([sm_get_IQ(h, BLOCK, 0, SM_TRUE if b == 0 else SM_FALSE)["iq_buf"].copy() for b in range(20)])
    sm_abort(h)
    return iq, fs


def report(name, state, iq, fs, center):
    p = iq.real ** 2 + iq.imag ** 2
    n = 65536
    win = np.hanning(n)
    sp = np.abs(np.fft.fftshift(np.fft.fft(iq[:n] * win))) / win.sum()
    fr = (center + np.fft.fftshift(np.fft.fftfreq(n, 1 / fs))) / 1e6
    k = int(sp.argmax())
    print(f"{state:8s} {name:12s}: mean {10*np.log10(p.mean())+PAD_DB:7.2f} dBm, peak {10*np.log10(p.max())+PAD_DB:7.2f} dBm, "
          f"spectrum peak {20*np.log10(sp[k])+PAD_DB:7.2f} dBm at {fr[k]:.3f} MHz (before pads)", flush=True)


def main():
    att = attenuation_for(TONE_HZ, TONE_DBM)
    print(f"Pluto {TONE_HZ/1e6:.0f} MHz, att {att} dB, table {level_dbm(TONE_HZ, att):.2f} dBm")
    saved = {}
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        for state in ("tone_off", "tone_on"):
            if state == "tone_on":
                tone_on(TONE_HZ, att, SCALE)
            else:
                tone_off()
            time.sleep(1.0)
            for name, center in CENTERS.items():
                iq, fs = capture(h, center)
                report(name, state, iq, fs, center)
                saved[f"{state}_{name}"] = iq[:200_000]
                saved["fs"] = fs
    finally:
        tone_off()
        sm_close_device(h)
        print("tone off")
    np.savez_compressed(HERE / "pluto_leak_1nov.npz", pad_db=PAD_DB, tone_hz=TONE_HZ, **saved)


if __name__ == "__main__":
    main()
