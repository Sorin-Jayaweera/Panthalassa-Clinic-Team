"""Max-hold spectra of the radar at several spans and bandwidths. Run from clinic/claude/signal_hound.
Same protection as the other scripts (internal attenuator 30 dB, ref +20 dBm). Saves CSVs and one plot in radar_test/spectra_<time>/."""
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sm200b_scan as S  # noqa: E402

# name, start, stop, RBW, seconds of max hold (at least 4 rotations of 2.59 s)
SCANS = [("full_0-20GHz_rbw3M", 100e3, 20e9, 3e6, 30), ("xband_9-10.8GHz_rbw3M", 9.0e9, 10.8e9, 3e6, 15),
         ("pulse_9.37-9.44_rbw3M", 9.37e9, 9.44e9, 3e6, 12), ("pulse_9.37-9.44_rbw300k", 9.37e9, 9.44e9, 300e3, 12),
         ("pulse_9.37-9.44_rbw30k", 9.37e9, 9.44e9, 30e3, 12), ("harmonic2_18.7-18.9GHz_rbw3M", 18.7e9, 18.9e9, 3e6, 15),
         ("below_band_5-9GHz_rbw3M", 5e9, 9e9, 3e6, 12), ("above_band_10.8-13GHz_rbw3M", 10.8e9, 13e9, 3e6, 12)]


def main():
    out = HERE / f"spectra_{dt.datetime.now():%Y%m%d_%H%M%S}"
    out.mkdir()
    h = S.sm_open_device()["device"]
    res = {"temp_start_c": round(S.sm_get_device_diagnostics(h)["temperature"], 2)}
    fig, ax = plt.subplots(len(SCANS), 1, figsize=(12, 3.1 * len(SCANS)))
    try:
        S.sm_set_attenuator(h, S.SM_MAX_ATTEN)
        S.sm_set_ref_level(h, 20.0)
        for k, (name, a, b, rbw, sec) in enumerate(SCANS):
            f, y, n = S.scan(h, a, b, rbw, sec)
            np.savetxt(out / f"{name}.csv", np.column_stack([f, y]), delimiter=",", header="freq_hz,maxhold_dbm", comments="", fmt=["%.0f", "%.2f"])
            i = int(np.argmax(y))
            res[name] = dict(peak_dbm=round(float(y[i]), 2), peak_ghz=round(float(f[i] / 1e9), 6), median_dbm=round(float(np.median(y)), 2), sweeps=n)
            print(name, res[name], flush=True)
            ax[k].plot(f / 1e9, y, lw=0.7)
            ax[k].set(xlabel="Frequency (GHz)", ylabel="dBm", title=f"{name}: RBW {rbw/1e3:g} kHz, max hold {sec} s")
            ax[k].grid(alpha=0.3)
        res["temp_end_c"] = round(S.sm_get_device_diagnostics(h)["temperature"], 2)
    finally:
        S.sm_abort(h)
        S.sm_close_device(h)
    fig.tight_layout()
    fig.savefig(out / "spectra.png", dpi=100)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
