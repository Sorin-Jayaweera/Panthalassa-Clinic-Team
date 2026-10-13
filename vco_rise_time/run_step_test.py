"""VCO step-response test: CGR-201 square wave -> VCO Vt, scope records drive + RF.

Usage:  python run_step_test.py [--rf-ch 2] [--lo 0.5] [--hi 0.75:3.0:0.25]
                                [--n 8] [--sq-hz 50000] [--tdiv 2e-4]

For each high level: set the square wave (closed loop on scope CH1), take N deep
single-shot records (each holds many edges), and save every raw record. The RF is
aliased and weak, so the frequency-vs-time trace is built by stacking all rising
edges of a level (see analysis.py). Results go to data/<timestamp>/.
"""
import argparse
import csv
import datetime as dt
import time
from pathlib import Path

import numpy as np

import analysis as an
from cgr201 import CGR201
from sds import SDS

V_FLOOR, V_CEIL = 0.2, 3.3  # abort if the measured drive leaves this window
DRIVE_CH = 1
GRID = np.arange(-2e-6, 6e-6, 2e-9)  # time relative to the drive's 50 % crossing
N_GROUPS = 4  # captures are split into groups to estimate the scatter of the result
STATIC_FILE = Path(__file__).parent / "data" / "static_tuning_20261010.csv"


def parse_hi(text):
    if ":" in text:
        a, b, step = (float(x) for x in text.split(":"))
        return [round(x, 4) for x in np.arange(a, b + step / 2, step)]
    return [float(x) for x in text.split(",")]


def static_freq_hz(vt):
    """Today's static tuning curve measured on the scope (falls back to the SA table)."""
    if not STATIC_FILE.exists():
        return an.expected_freq_hz(vt)
    d = np.genfromtxt(STATIC_FILE, delimiter=",", names=True)
    return float(np.interp(vt, d["vt_meas"], d["f_meas_hz"]))


class Drive:
    """Sets square-wave low/high levels using gains measured on the scope."""

    def __init__(self, gen, scope, sq_hz):
        self.g, self.s, self.sq_hz = gen, scope, sq_hz
        self.off_v_per_code = None
        self.off_zero_code = None
        self.amp_v_per_code = None

    def _view(self):
        self.s.write(f"TDIV {0.2 / self.sq_hz:.3E}S")
        self.s.write("TRMD AUTO", 1.5)

    def _read_levels(self):
        t, v = self.s.waveform(DRIVE_CH)
        return an.levels(v) if np.ptp(v) > 0.1 else (float(np.median(v)),) * 2

    def calibrate(self):
        g = self.g
        g.set_amplitude_raw(0)
        g.set_frequency(self.sq_hz)
        g.set_waveform("square")
        self._view()
        pts = []
        for nominal in (0.5, 1.5):
            code = round(4095.0 * (nominal + 4.0) / 8.0)
            g.set_offset_raw(code)
            time.sleep(1.5)
            pts.append((code, self._read_levels()[0]))
        (c0, v0), (c1, v1) = pts
        if abs(v1 - v0) < 0.2:
            raise RuntimeError("Scope CH1 does not follow the generator offset - check the BNC connection.")
        self.off_v_per_code = (v1 - v0) / (c1 - c0)
        self.off_zero_code = c0 - v0 / self.off_v_per_code
        g.set_amplitude_raw(300)  # small swing centred on ~1.2 V
        time.sleep(1.5)
        lo, hi = self._read_levels()
        if hi - lo < 0.02:
            raise RuntimeError("No square wave seen on CH1 at amplitude code 300.")
        self.amp_v_per_code = (hi - lo) / 300.0
        print(f"  offset {self.off_v_per_code*1e3:.3f} mV/code, amplitude {self.amp_v_per_code*1e3:.3f} mV/code (pk-pk)")
        g.set_amplitude_raw(0)

    def set_levels(self, lo, hi):
        """Go to DC at the new midpoint first, then open up the swing."""
        if not (V_FLOOR <= lo < hi <= V_CEIL):
            raise ValueError(f"levels {lo}..{hi} V outside allowed window")
        g = self.g
        self._view()
        mid, pp = 0.5 * (lo + hi), hi - lo
        off_code, amp_code = self.off_zero_code + mid / self.off_v_per_code, pp / self.amp_v_per_code
        for _ in range(4):
            g.set_amplitude_raw(0)
            g.set_offset_raw(off_code)
            g.set_amplitude_raw(amp_code)
            time.sleep(1.5)
            mlo, mhi = self._read_levels()
            if mlo < V_FLOOR - 0.15 or mhi > V_CEIL + 0.15:
                g.set_amplitude_raw(0)
                raise RuntimeError(f"Drive measured {mlo:.2f}..{mhi:.2f} V, outside safe window; stopped.")
            if abs(mlo - lo) < 0.02 and abs(mhi - hi) < 0.02:
                break
            off_code += (mid - 0.5 * (mlo + mhi)) / self.off_v_per_code
            amp_code *= pp / (mhi - mlo)
        return mlo, mhi

    def park(self, volts=0.5):
        """Leave a steady DC level on the output."""
        self.g.set_amplitude_raw(0)
        if self.off_zero_code is not None:
            self.g.set_offset_raw(self.off_zero_code + volts / self.off_v_per_code)


def setup_scope(s, rf_ch, tdiv):
    for c in (f"C{DRIVE_CH}:TRA ON", f"C{DRIVE_CH}:ATTN 1", f"C{DRIVE_CH}:CPL D1M",
              f"C{DRIVE_CH}:VDIV 0.5V", f"C{DRIVE_CH}:OFST -1.75V", f"BWL C{DRIVE_CH},OFF",
              f"C{rf_ch}:TRA ON", f"C{rf_ch}:ATTN 1", f"C{rf_ch}:CPL A1M", f"BWL C{rf_ch},OFF",
              f"C{rf_ch}:OFST 0V", f"C{rf_ch}:VDIV 5.00E-03V",
              f"TRSE EDGE,SR,C{DRIVE_CH},HT,OFF", f"C{DRIVE_CH}:TRSL POS", "TRDL 0S",
              "ACQW SAMPLING", f"TDIV {tdiv:.3E}S"):
        s.write(c)
    for ch in (2, 3, 4):
        if ch != rf_ch:
            s.write(f"C{ch}:TRA OFF")


def crossing_times(t, s):
    """t10, t50, t90 of a normalised 0->1 transition, searched outward from the 50 % point."""
    ok = t > -60e-9
    i50 = np.nonzero(ok[:-1] & (s[:-1] < 0.5) & (s[1:] >= 0.5))[0]
    if len(i50) == 0:
        return np.nan, np.nan, np.nan
    i50 = i50[0]

    def interp(i, level):
        return t[i] + (level - s[i]) * (t[i + 1] - t[i]) / (s[i + 1] - s[i])

    below = np.nonzero(s[:i50 + 1] < 0.1)[0]
    above = np.nonzero(s[i50:] >= 0.9)[0]
    t10 = interp(below[-1], 0.1) if len(below) else np.nan
    t90 = interp(i50 + above[0] - 1, 0.9) if len(above) and above[0] > 0 else np.nan
    return t10, interp(i50, 0.5), t90


def step_metrics(f):
    pre, post = GRID < -0.2e-6, GRID > 4e-6
    f0, f1 = float(np.median(f[pre])), float(np.median(f[post]))
    t10, t50, t90 = crossing_times(GRID, (f - f0) / (f1 - f0))
    return dict(f_lo_meas_hz=f0, f_hi_meas_hz=f1, f_t10_s=t10, f_t50_s=t50, f_t90_s=t90,
                f_rise_10_90_s=t90 - t10, f_settle_5pct_s=an.settle_time(GRID, f, f0, f1, 0.05),
                f_pre_scatter_hz=float(np.std(f[pre])), f_post_scatter_hz=float(np.std(f[post])))


def summarise(stack, lo, hi, sq_hz, n_caps, tdiv, clip):
    """One summary row plus the mean traces for a finished level."""
    f = stack.freq()
    dmean = stack.drive_mean()
    r = step_metrics(f)
    grp = [step_metrics(stack.freq(k)) for k in range(stack.n_groups) if np.any(stack.acc[k])]
    rises = np.array([x["f_rise_10_90_s"] for x in grp])
    t50s = np.array([x["f_t50_s"] for x in grp])
    dlo, dhi = float(np.median(dmean[GRID < -0.2e-6])), float(np.median(dmean[GRID > 4e-6]))
    d10, d50, d90 = crossing_times(GRID, (dmean - dlo) / (dhi - dlo))
    r.update(timestamp=dt.datetime.now().isoformat(timespec="seconds"), square_wave_hz=sq_hz,
             v_lo_set=lo, v_hi_set=hi, v_lo_meas=dlo, v_hi_meas=dhi,
             f_lo_expected_hz=an.expected_freq_hz(lo), f_hi_expected_hz=an.expected_freq_hz(hi),
             f_hi_datasheet_hz=an.datasheet_freq_hz(hi), f_lo_static_today_hz=stack.f_lo_guess,
             f_hi_static_today_hz=stack.f_hi_guess, f_rise_10_90_group_std_s=float(np.nanstd(rises)),
             f_t50_group_std_s=float(np.nanstd(t50s)), drive_rise_10_90_s=d90 - d10,
             drive_t10_s=d10, drive_t90_s=d90,
             n_edges=stack.n_edges, n_captures=n_caps, sample_rate_hz=stack.fs, tdiv_s=tdiv,
             band_start_hz=stack.band[0], band_stop_hz=stack.band[1], lag_samples=stack.lag,
             rf_clip_fraction=clip)
    return r, (f, dmean, stack.lag_magnitude())


def report(r):
    print(f"V_hi={r['v_hi_set']:.2f} V: drive {r['v_lo_meas']:.3f}->{r['v_hi_meas']:.3f} V (rise {r['drive_rise_10_90_s']*1e9:.0f} ns) | "
          f"f {r['f_lo_meas_hz']/1e6:.1f}->{r['f_hi_meas_hz']/1e6:.1f} MHz (SA table {r['f_lo_expected_hz']/1e6:.1f}->{r['f_hi_expected_hz']/1e6:.1f}) | "
          f"freq rise {r['f_rise_10_90_s']*1e9:.0f} +/- {r['f_rise_10_90_group_std_s']*1e9:.0f} ns, t50 {r['f_t50_s']*1e9:.0f} ns | "
          f"{r['n_edges']} edges, band {r['band_start_hz']/1e6:.0f}-{r['band_stop_hz']/1e6:.0f} MHz lag {r['lag_samples']}", flush=True)


def save_results(out, rows, traces):
    with open(out / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    np.savez_compressed(out / "mean_traces.npz", t=GRID,
                        **{f"hi{h:.2f}_freq_hz": tr[0] for h, tr in traces.items()},
                        **{f"hi{h:.2f}_drive_v": tr[1] for h, tr in traces.items()},
                        **{f"hi{h:.2f}_lagmag": tr[2] for h, tr in traces.items()})


def load_raw(path):
    d = np.load(path)
    fs = float(d["fs"])
    vd = d["drive_codes"] * (float(d["drive_vdiv"]) / 25.0) - float(d["drive_offset"])
    vr = d["rf_codes"] * (float(d["rf_vdiv"]) / 25.0) - float(d["rf_offset"])
    t = float(d["t_first"]) + np.arange(len(vd)) / fs
    return t, vd, vr, fs, d


def reprocess(folder):
    """Rebuild summary.csv and mean_traces.npz from the raw captures in a run folder."""
    folder = Path(folder)
    files = sorted((folder / "raw").glob("hi*V_*.npz"))
    rows, traces = [], {}
    for hi in sorted({float(f.name[2:f.name.index("V_")]) for f in files}):
        stack, clip = None, 0.0
        for f in [x for x in files if x.name.startswith(f"hi{hi:.2f}V_")]:
            t, vd, vr, fs, d = load_raw(f)
            lo, sq = float(d["v_lo_set"]), float(d["sq_hz"])
            if stack is None:
                stack = an.LevelStack(GRID, static_freq_hz(lo), static_freq_hz(hi), sq, N_GROUPS)
            clip = max(clip, float(np.mean(np.abs(d["rf_codes"]) >= 124)))
            stack.add(t, vd, vr, fs)
        r, tr = summarise(stack, lo, hi, sq, stack.n_caps, len(vd) / fs / 14, clip)
        rows.append(r)
        traces[hi] = tr
        report(r)
    save_results(folder, rows, traces)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rf-ch", type=int, default=2)
    ap.add_argument("--lo", type=float, default=0.5)
    ap.add_argument("--hi", default="0.75:3.0:0.25")
    ap.add_argument("--n", type=int, default=8, help="deep captures per level")
    ap.add_argument("--sq-hz", type=float, default=50000.0)
    ap.add_argument("--tdiv", type=float, default=2e-4)
    ap.add_argument("--port", default="COM12")
    a = ap.parse_args()
    his = parse_hi(a.hi)

    out = Path(__file__).parent / "data" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    (out / "raw").mkdir(parents=True)
    s, g = SDS(), CGR201(a.port)
    drive = Drive(g, s, a.sq_hz)
    rows, traces = [], {}
    try:
        print("CGR:", g.identify(), "| scope:", s.query("*IDN?"))
        setup_scope(s, a.rf_ch, a.tdiv)
        print("Calibrating drive levels on CH1...")
        drive.calibrate()
        for hi in his:
            t_start = time.time()
            mlo, mhi = drive.set_levels(a.lo, hi)
            s.write(f"C{DRIVE_CH}:TRLV {0.5*(mlo+mhi):.3f}V")
            s.write(f"TDIV {a.tdiv:.3E}S")
            s.write("TRMD NORM", 1.0)
            stack = an.LevelStack(GRID, static_freq_hz(a.lo), static_freq_hz(hi), a.sq_hz, N_GROUPS)
            clip = 0.0
            for i in range(a.n):
                if not s.single():
                    print("  capture timed out (no trigger)")
                    continue
                dcode, dvdiv, dofst, fs, t_first = s.waveform_raw(DRIVE_CH)
                rcode, rvdiv, rofst, _, _ = s.waveform_raw(a.rf_ch)
                np.savez_compressed(out / "raw" / f"hi{hi:.2f}V_{i:02d}.npz", drive_codes=dcode, rf_codes=rcode,
                                    drive_vdiv=dvdiv, drive_offset=dofst, rf_vdiv=rvdiv, rf_offset=rofst,
                                    fs=fs, t_first=t_first, v_lo_set=a.lo, v_hi_set=hi, sq_hz=a.sq_hz,
                                    note="volts = codes*vdiv/25 - offset; t = t_first + n/fs")
                t = t_first + np.arange(len(dcode)) / fs
                clip = max(clip, float(np.mean(np.abs(rcode) >= 124)))
                stack.add(t, dcode * (dvdiv / 25.0) - dofst, rcode * (rvdiv / 25.0) - rofst, fs)
            if stack.n_edges == 0:
                print(f"V_hi={hi:.2f}: no edges captured")
                continue
            r, tr = summarise(stack, a.lo, hi, a.sq_hz, a.n, a.tdiv, clip)
            rows.append(r)
            traces[hi] = tr
            report(r)
    finally:
        try:
            drive.park()
        finally:
            g.close()
            s.write("TDIV 2.00E-05S")
            s.write("TRMD AUTO")
            s.close()
        if rows:
            save_results(out, rows, traces)
            print("Saved:", out)
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--reprocess":
        reprocess(sys.argv[2])
    else:
        main()
