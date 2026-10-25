"""Record raw I/Q of the radar's strongest beam pass: 50 MS/s, 41.5 MHz bandwidth, centred 9.4026 GHz.
Streams for 4 s (more than one 2.59 s rotation) and keeps 60 ms around the strongest pulse.
Saves radar_test/raw_<time>.npz (iq, fs, center, t0). Run from clinic/claude/signal_hound."""
import datetime as dt
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from smdevice.sm_api import *  # noqa: E402,F403

CENTER = 9.4026e9
BLOCK = 500_000            # 10 ms


def main():
    h = sm_open_device()["device"]
    try:
        temp0 = sm_get_device_diagnostics(h)["temperature"]
        sm_set_attenuator(h, SM_MAX_ATTEN)
        sm_set_ref_level(h, 20.0)
        sm_set_IQ_center_freq(h, CENTER)
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
        temp1 = sm_get_device_diagnostics(h)["temperature"]
    finally:
        sm_abort(h)
        sm_close_device(h)
    a, b = max(0, best_i - 3), min(len(ring), best_i + 3)
    iq = np.concatenate(ring[a:b])
    out = HERE / f"raw_{dt.datetime.now():%Y%m%d_%H%M%S}.npz"
    np.savez_compressed(out, iq=iq, fs=fs, center=CENTER, t0=a * BLOCK / fs, temp=[temp0, temp1], lost=lost)
    print(f"saved {out.name}: {len(iq)/fs*1e3:.0f} ms, strongest {10*np.log10(best):.2f} dBm, samples lost {lost}, SM200B {temp0:.1f} -> {temp1:.1f} C")


if __name__ == "__main__":
    main()
