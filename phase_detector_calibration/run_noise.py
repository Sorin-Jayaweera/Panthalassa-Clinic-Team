"""Noise of the mixer output at fixed tuning voltages -> smallest resolvable frequency change.

At each DC Vt the mixer output (scope CH2, AC coupled, 1 mV/div) is recorded and its rms
noise is computed in several bandwidths. CH3 (nothing connected) is recorded with the same
settings as the scope's own noise floor. Frequency noise = voltage noise / local slope of
the static calibration.
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vco_rise_time"))
from cgr201 import CGR201  # noqa: E402
from sds import SDS  # noqa: E402
from run_calibration import set_vt  # noqa: E402

VTS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
CAL = HERE / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv"
OUT = HERE / "noise_cleanDC"


def lowpass_rms(v, fs, cutoff):
    spec = np.fft.rfft(v - v.mean())
    f = np.fft.rfftfreq(len(v), 1 / fs)
    spec[f > cutoff] = 0
    return float(np.fft.irfft(spec, len(v)).std())


def main():
    OUT.mkdir(exist_ok=True)
    cal = np.genfromtxt(CAL, delimiter=",", names=True, dtype=None, encoding="utf-8")
    slope = np.gradient(cal["mixer_out_v"], cal["vco_freq_hz"])  # V per Hz
    s, g = SDS(), CGR201("COM12")
    rows = []
    try:
        g.set_amplitude_raw(0)
        g.set_waveform("off")  # a selected waveform leaks ~100 mV pk-pk even at amplitude 0
        for c in ("MSIZ 7M", "C1:TRA ON", "C1:CPL D1M", "C1:VDIV 0.12V", "C1:OFST 0V", "BWL C1,OFF",
                  "C2:TRA ON", "C2:ATTN 1", "C2:CPL A1M", "C2:VDIV 1.00E-03V", "C2:OFST 0V", "BWL C2,OFF",
                  "C3:TRA ON", "C3:ATTN 1", "C3:CPL A1M", "C3:VDIV 1.00E-03V", "C3:OFST 0V", "BWL C3,OFF",
                  "C4:TRA OFF", "TRMD AUTO"):
            s.write(c)
        code = 2150.0
        for vt_set in VTS:
            s.write("TDIV 1.00E-03S", 1.0)
            vt, code = set_vt(g, s, vt_set, code)
            s.write("TDIV 1.00E-04S", 2.5)  # 1.4 ms record
            time.sleep(1.0)
            codes2, vdiv2, ofst2, fs, _ = s.waveform_raw(2)
            codes3, vdiv3, ofst3, _, _ = s.waveform_raw(3)
            np.savez_compressed(OUT / f"noise_vt{vt_set:.2f}.npz", mixer_codes=codes2, open_ch3_codes=codes3,
                                mixer_vdiv=vdiv2, ch3_vdiv=vdiv3, fs=fs, vt_meas=vt,
                                note="AC coupled; volts = codes*vdiv/25")
            v2, v3 = codes2 * (vdiv2 / 25.0), codes3 * (vdiv3 / 25.0)
            f0 = float(np.interp(vt, cal["vt_meas_v"], cal["vco_freq_hz"]))
            k = float(np.interp(vt, cal["vt_meas_v"], slope))
            r = dict(vt_set_v=vt_set, vt_meas_v=round(vt, 4), freq_hz=f0, slope_mv_per_mhz=k * 1e9,
                     sample_rate_hz=fs, n_samples=len(v2),
                     clip_fraction=float(np.mean(np.abs(codes2) >= 124)))
            for name, bw in (("full", None), ("20MHz", 20e6), ("5MHz", 5e6), ("1MHz", 1e6), ("100kHz", 1e5)):
                n2 = float(v2.std()) if bw is None else lowpass_rms(v2, fs, bw)
                n3 = float(v3.std()) if bw is None else lowpass_rms(v3, fs, bw)
                r[f"mixer_rms_uv_{name}"] = n2 * 1e6
                r[f"scope_floor_rms_uv_{name}"] = n3 * 1e6
                r[f"freq_noise_khz_{name}"] = n2 / k / 1e3
            rows.append(r)
            print(f"Vt {vt:.3f} V ({f0/1e6:.1f} MHz, {k*1e9:.2f} mV/MHz) fs {fs/1e6:.0f}M: mixer rms full {r['mixer_rms_uv_full']:.0f} uV "
                  f"(scope floor {r['scope_floor_rms_uv_full']:.0f}), 1 MHz {r['mixer_rms_uv_1MHz']:.1f} uV (floor {r['scope_floor_rms_uv_1MHz']:.1f}) "
                  f"-> {r['freq_noise_khz_full']:.0f} kHz full, {r['freq_noise_khz_1MHz']:.1f} kHz in 1 MHz", flush=True)
            with open(OUT / "noise_summary.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    finally:
        try:
            for c in ("C3:TRA OFF", "C2:CPL D1M", "C2:VDIV 2.00E-02V", "C2:OFST -0.09V", "TDIV 1.00E-03S"):
                s.write(c)
            set_vt(g, s, 0.5, 2150 + 0.5 / 1.875e-3)
        finally:
            g.close()
            s.close()


if __name__ == "__main__":
    main()
