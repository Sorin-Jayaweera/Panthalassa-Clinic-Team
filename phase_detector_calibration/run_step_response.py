"""Step response of the whole chain: Syscomp square wave -> VCO -> splitter/delay/mixer -> scope CH2.

The mixer output is a baseband voltage, so the scope sees it directly. Each deep capture
holds ~140 rising and ~140 falling edges; they are stacked on the drive's 50 % crossing.
Mixer voltage is converted to frequency with the static calibration (valid only where the
mixer curve is single-valued, below about 788 MHz / Vt 1.2 V).

Usage: python run_step_response.py [--n 3] [--sq-hz 50000]
"""
import argparse
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vco_rise_time"))
import analysis as an  # noqa: E402
from cgr201 import CGR201  # noqa: E402
from run_step_test import Drive, crossing_times  # noqa: E402
from sds import SDS  # noqa: E402

GRID = np.arange(-1e-6, 5e-6, 2e-9)
STEPS = [(0.2, 0.4), (0.2, 0.6), (0.2, 0.8), (0.2, 1.0), (0.2, 1.15),
         (0.3, 0.4), (0.5, 0.6), (0.7, 0.8), (0.9, 1.0), (1.0, 1.1)]
CAL = HERE / "phase_detector_calibration_run2_0p02V_steps.csv"


def mixer_to_freq():
    d = np.genfromtxt(CAL, delimiter=",", names=True, dtype=None, encoding="utf-8")
    m = d["vt_meas_v"] <= 1.2  # single-valued part of the mixer curve
    v, f = d["mixer_out_v"][m], d["vco_freq_hz"][m]
    order = np.argsort(v)
    return lambda x: np.interp(x, v[order], f[order]), d


def metrics(y, prefix):
    y0, y1 = float(np.median(y[GRID < -0.2e-6])), float(np.median(y[GRID > 3e-6]))
    t10, t50, t90 = crossing_times(GRID, (y - y0) / (y1 - y0))
    return {f"{prefix}_start": y0, f"{prefix}_end": y1, f"{prefix}_t10_s": t10, f"{prefix}_t50_s": t50,
            f"{prefix}_t90_s": t90, f"{prefix}_rise_10_90_s": t90 - t10,
            f"{prefix}_settle_5pct_s": an.settle_time(GRID, y, y0, y1, 0.05)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--sq-hz", type=float, default=50000.0)
    a = ap.parse_args()
    to_freq, _ = mixer_to_freq()
    out = HERE / "step_response" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    (out / "raw").mkdir(parents=True)
    s, g = SDS(), CGR201("COM12")
    drive = Drive(g, s, a.sq_hz)
    rows, traces = [], {"time_ns": GRID * 1e9}
    try:
        for c in ("C1:TRA ON", "C1:ATTN 1", "C1:CPL D1M", "C1:VDIV 0.5V", "C1:OFST -1.75V", "BWL C1,OFF",
                  "C2:TRA ON", "C2:ATTN 1", "C2:CPL D1M", "BWL C2,OFF", "C2:VDIV 2.00E-02V", "C2:OFST -0.09V",
                  "C3:TRA OFF", "C4:TRA OFF", "TRSE EDGE,SR,C1,HT,OFF", "C1:TRSL POS", "TRDL 0S", "ACQW SAMPLING"):
            s.write(c)
        drive.calibrate()
        for lo, hi in STEPS:
            # scale CH1 to the step so small steps are not lost in the 8-bit resolution
            vdiv = next(x for x in (0.05, 0.1, 0.2, 0.5) if x >= (hi - lo) / 4)
            s.write(f"C1:VDIV {vdiv}V")
            s.write(f"C1:OFST {-0.5*(lo+hi):.3f}V")
            mlo, mhi = drive.set_levels(lo, hi)
            s.write(f"C1:TRLV {0.5*(mlo+mhi):.3f}V")
            s.write("TDIV 2.00E-04S", 2.0)
            s.write("TRMD NORM", 3.0)
            acc = {k: np.zeros(len(GRID)) for k in ("rise_drive", "rise_mixer", "fall_drive", "fall_mixer")}
            cnt = {"rise": 0, "fall": 0}
            for i in range(a.n):
                try:
                    ok = s.single(20)
                except Exception as e:  # the scope occasionally stalls after a timebase change
                    print("  scope query failed, retrying:", type(e).__name__)
                    time.sleep(3)
                    s._drain()
                    ok = s.single(20)
                if not ok:
                    print("  capture timed out")
                    continue
                dcode, dvdiv, dofst, fs, t_first = s.waveform_raw(1)
                mcode, mvdiv, mofst, _, _ = s.waveform_raw(2)
                np.savez_compressed(out / "raw" / f"lo{lo:.2f}_hi{hi:.2f}_{i:02d}.npz", drive_codes=dcode, mixer_codes=mcode,
                                    drive_vdiv=dvdiv, drive_offset=dofst, mixer_vdiv=mvdiv, mixer_offset=mofst,
                                    fs=fs, t_first=t_first, v_lo_set=lo, v_hi_set=hi, sq_hz=a.sq_hz,
                                    note="volts = codes*vdiv/25 - offset; t = t_first + n/fs")
                t = t_first + np.arange(len(dcode)) / fs
                vd = dcode * (dvdiv / 25.0) - dofst
                vm = mcode * (mvdiv / 25.0) - mofst
                dlo, dhi = an.levels(vd)
                for name, edges in (("rise", an.rising_edges(t, vd, dlo, dhi)),
                                    ("fall", an.rising_edges(t, -vd, -dhi, -dlo))):
                    for key, y in (("drive", vd), ("mixer", vm)):
                        ssum, ne = an.stack_edges(t, y.astype(complex), edges, GRID)
                        acc[f"{name}_{key}"] += ssum.real
                    cnt[name] += ne
            for name in ("rise", "fall"):
                if cnt[name] == 0:
                    continue
                dmean, mmean = acc[f"{name}_drive"] / cnt[name], an.smooth(acc[f"{name}_mixer"] / cnt[name], 5)
                fmean = to_freq(mmean)
                r = dict(timestamp=dt.datetime.now().isoformat(timespec="seconds"), edge=name, square_wave_hz=a.sq_hz,
                         v_lo_set=lo, v_hi_set=hi, n_edges=cnt[name])
                r.update(metrics(dmean, "drive_v"))
                r.update(metrics(mmean, "mixer_v"))
                r.update(metrics(fmean, "freq_hz"))
                rows.append(r)
                tag = f"{name}_lo{lo:.2f}_hi{hi:.2f}"
                traces[f"{tag}_drive_V"], traces[f"{tag}_mixer_mV"], traces[f"{tag}_freq_MHz"] = dmean, mmean * 1e3, fmean / 1e6
                print(f"{lo:.2f}<->{hi:.2f} V {name}: mixer {r['mixer_v_start']*1e3:.1f}->{r['mixer_v_end']*1e3:.1f} mV, "
                      f"f {r['freq_hz_start']/1e6:.1f}->{r['freq_hz_end']/1e6:.1f} MHz | rise 10-90: drive {r['drive_v_rise_10_90_s']*1e9:.0f} ns, "
                      f"mixer {r['mixer_v_rise_10_90_s']*1e9:.0f} ns, freq {r['freq_hz_rise_10_90_s']*1e9:.0f} ns | "
                      f"t50 lag {(r['mixer_v_t50_s']-r['drive_v_t50_s'])*1e9:.0f} ns | {cnt[name]} edges", flush=True)
            with open(out / "summary.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            np.savetxt(out / "mean_traces.csv", np.column_stack(list(traces.values())), delimiter=",",
                       header=",".join(traces.keys()), comments="", fmt="%.6g")
    finally:
        try:
            drive.park(0.5)
        finally:
            g.close()
            s.write("TDIV 1.00E-03S")
            s.write("TRMD AUTO")
            s.close()
    print("Saved", out)


if __name__ == "__main__":
    main()
