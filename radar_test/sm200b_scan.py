"""SM200B scan with the input protected as far as the instrument allows: internal attenuator at maximum (30 dB),
reference level +20 dBm, preamp off. Max-hold over several sweeps so short radar pulses are not missed.

    python sm200b_scan.py baseline         # radar off: 100 kHz-20 GHz and 9-10.8 GHz, saved as the background
    python sm200b_scan.py look 30          # any time: same scans, max-hold for 30 s, compared with the background

Every scan is saved to radar_test/scans/ as CSV and PNG. Prints the largest level seen and how far it is below +20 dBm.
"""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "signal_hound"))
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
from smdevice.sm_api import *  # noqa: E402,F403

OUT = HERE / "scans"
OUT.mkdir(exist_ok=True)
LIMIT_DBM = 20.0
SPANS = (("wide", 100e3, 20e9, 1e6), ("xband", 9.0e9, 10.8e9, 100e3))


def scan(h, start, stop, rbw, seconds):
    sm_set_sweep_start_stop(h, start, stop)
    sm_set_sweep_coupling(h, rbw, rbw, 0.001)
    sm_set_sweep_detector(h, SM_DETECTOR_MIN_MAX, SM_VIDEO_LOG)
    sm_set_sweep_scale(h, SM_SCALE_LOG)
    sm_set_sweep_window(h, SM_WINDOW_FLAT_TOP)
    sm_set_sweep_spur_reject(h, SM_FALSE)
    sm_configure(h, SM_MODE_SWEEPING)
    q = sm_get_sweep_parameters(h)
    f = q["actual_start_freq"] + q["bin_size"] * np.arange(q["sweep_size"])
    hold = np.full(q["sweep_size"], -200.0)
    n, t0 = 0, time.time()
    while n == 0 or time.time() - t0 < seconds:
        s = sm_get_sweep(h)
        hold = np.maximum(hold, np.asarray(s["sweep_max"], float))
        n += 1
    return f, hold, n


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "look"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else (10 if mode == "baseline" else 30)
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_MAX_ATTEN)          # 6 x 5 dB = 30 dB inside the instrument
        sm_set_ref_level(h, 20.0)
        try:
            sm_set_preamp(h, SM_FALSE)
        except Exception:
            pass
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        fig, ax = plt.subplots(2, 1, figsize=(12, 8))
        for k, (name, a, b, rbw) in enumerate(SPANS):
            f, y, n = scan(h, a, b, rbw, seconds)
            tag = f"{mode}_{name}_{stamp}"
            np.savetxt(OUT / f"{tag}.csv", np.column_stack([f, y]), delimiter=",", header="freq_hz,maxhold_dbm", comments="", fmt=["%.0f", "%.2f"])
            bg = sorted(OUT.glob(f"baseline_{name}_*.csv"))
            ax[k].plot(f / 1e9, y, lw=0.7, label=f"{mode}, max hold {n} sweeps")
            if mode != "baseline" and bg:
                d = np.genfromtxt(bg[-1], delimiter=",", skip_header=1)
                ax[k].plot(d[:, 0] / 1e9, d[:, 1], lw=0.7, color="gray", label="baseline, radar off")
            i = int(np.argmax(y))
            print(f"{name}: {a/1e9:.4f}-{b/1e9:.4f} GHz, RBW {rbw/1e3:.0f} kHz, {n} sweeps; largest {y[i]:+.1f} dBm at {f[i]/1e9:.4f} GHz; "
                  f"{LIMIT_DBM - y[i]:.1f} dB below the +20 dBm limit", flush=True)
            ax[k].axhline(LIMIT_DBM, color="red", ls="--", lw=1, label="+20 dBm damage limit")
            ax[k].set(xlabel="Frequency (GHz)", ylabel="Level at the SM200B input (dBm)", title=f"SM200B {name}, RBW {rbw/1e3:.0f} kHz, attenuator 30 dB, ref +20 dBm")
            ax[k].grid(alpha=0.3)
            ax[k].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT / f"{mode}_{stamp}.png", dpi=110)
        print("saved", OUT / f"{mode}_{stamp}.png")
    finally:
        sm_abort(h) if "sm_abort" in globals() else None
        sm_close_device(h)


if __name__ == "__main__":
    main()
