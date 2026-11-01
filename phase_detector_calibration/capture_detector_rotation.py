"""Phase detector output over several radar rotations, SM200B I/Q, Spike closed.

Streams 10 s at 50 MS/s centred 21 MHz and keeps the strongest sample in every 0.2 ms, which is shorter than the
pulse spacing, so each pulse is kept. Run from clinic/claude/signal_hound.
Usage: python capture_detector_rotation.py <label>
"""
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from smdevice.sm_api import *  # noqa: E402,F403

LABEL = sys.argv[1]
PAD_DB = float(sys.argv[2]) if len(sys.argv) > 2 else 23.0
CENTER = 21e6
SECONDS = 10.0
REF_DBM = -10.0
BLOCK = 500_000
BIN = 10_000


h = sm_open_device()["device"]
try:
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, REF_DBM)
    sm_set_IQ_center_freq(h, CENTER)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_IQ_queue_size(h, 100.0)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    env, lost = [], 0
    for b in range(int(SECONDS * fs / BLOCK)):
        r = sm_get_IQ(h, BLOCK, 0, SM_TRUE if b == 0 else SM_FALSE)
        lost += max(0, r["sample_loss"])
        iq = r["iq_buf"]
        p = iq.real ** 2 + iq.imag ** 2
        env.append(p[:len(p) // BIN * BIN].reshape(-1, BIN).max(axis=1))
    sm_abort(h)
finally:
    sm_close_device(h)

env = 10 * np.log10(np.concatenate(env) + 1e-20) + PAD_DB
t = np.arange(len(env)) * BIN / fs
stem = f"furuno_detector_1nov_rotation_{LABEL}"
np.savez_compressed(HERE / f"{stem}.npz", t=t, peak_dbm=env, fs=fs, center=CENTER, pad_db=PAD_DB, lost=lost)
peak_v = np.sqrt(2 * 50 * 10 ** (env / 10) * 1e-3)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(t, peak_v * 1e3, lw=0.8, color="#1f5fa8")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Detector output, peak in each 0.2 ms (mV into 50 Ω, before pads)")
ax.set_title(f"Phase detector output over radar rotation, {LABEL}")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / f"{stem}.png", dpi=130)
print(f"{stem}: {t[-1]:.1f} s, peak {env.max():.2f} dBm = {peak_v.max()*1e3:.0f} mV into 50 ohm, median {np.median(env):.2f} dBm, lost {lost}")
