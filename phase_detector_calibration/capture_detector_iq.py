"""Record raw I/Q of the phase detector output on the SM200B (through 23 dB of pads), Spike closed.

50 MS/s, 41.5 MHz bandwidth. Streams 4 s (more than one 2.59 s rotation) at each centre and keeps
60 ms around the strongest pulse. Saves furuno_detector_1nov_pll_on/iq_<centre>.npz.
"""
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from smdevice.sm_api import *  # noqa: E402,F403

OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "furuno_detector_1nov_pll_on")
OUT.mkdir(exist_ok=True)
PAD_DB = 23.0
CENTERS = {"baseband_21MHz": 21e6, "if_1p105GHz": 1.105e9}
REF_DBM = -10.0            # expected at most about -25 dBm after the pads; SM200B limit +20 dBm
BLOCK = 500_000            # 10 ms


def capture(h, name, center):
    sm_set_ref_level(h, REF_DBM)
    sm_set_IQ_center_freq(h, center)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_IQ_queue_size(h, 100.0)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    ring, best, best_i, lost = [], -1.0, -1, 0
    for b in range(int(4.0 * fs / BLOCK)):
        r = sm_get_IQ(h, BLOCK, 0, SM_TRUE if b == 0 else SM_FALSE)
        lost += max(0, r["sample_loss"])
        iq = r["iq_buf"].copy()
        pk = float(np.max(iq.real ** 2 + iq.imag ** 2))
        ring.append(iq)
        if pk > best:
            best, best_i = pk, b
    sm_abort(h)
    a, c = max(0, best_i - 3), min(len(ring), best_i + 3)
    iq = np.concatenate(ring[a:c])
    np.savez_compressed(OUT / f"iq_{name}.npz", iq=iq, fs=fs, center=center, pad_db=PAD_DB, lost=lost)
    p = iq.real ** 2 + iq.imag ** 2
    print(f"{name}: fs {fs/1e6:.1f} MS/s, {len(iq)/fs*1e3:.0f} ms kept, strongest {10*np.log10(best):.2f} dBm at the SM200B "
          f"({10*np.log10(best)+PAD_DB:.2f} before pads), median {10*np.log10(np.median(p)):.2f} dBm, samples lost {lost}", flush=True)


def main():
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        for name, center in CENTERS.items():
            capture(h, name, center)
    finally:
        sm_close_device(h)


if __name__ == "__main__":
    main()
