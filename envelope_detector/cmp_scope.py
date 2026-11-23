"""ADCMP604 Tests 3 and 4: count comparator edges on the Siglent SDS1104X-E.

Set the scope up by hand first (channels, scales, trigger, timebase: see
COMPARATOR-TEST-PROCEDURE.md), then:

    python cmp_scope.py --label tri_1Hz --shots 10                  # Test 3: chatter
    python cmp_scope.py --label ed_tx-10_100us --shots 10 --match   # Test 4: one output pulse per RF pulse

Each shot: arm SINGLE, wait for the trigger, download the output channel (OUT+, default CH2)
and the reference channel (IN+ or VENV, default CH1), then
- find OUT+ edges with two thresholds (Schmitt: low < --out-lo, high > --out-hi), so scope
  noise is not counted as edges;
- group edges closer than --gap-us into bursts (one burst = one decision of the comparator,
  plus any chatter);
- with --match: find the reference pulses and check each has exactly one OUT+ rising edge
  within --window-us of its start (missed = none, extra = more than one, or edges with no
  reference pulse nearby).

Saves every shot to data/cmp_scope_<label>_<time>/shot_NN.npz (raw scope codes, same
format as the team's other captures: volts = codes * vdiv / 25 - offset) and appends one
row per shot to data/cmp_scope_summary.csv.

Limits: the scope samples at whatever the timebase gives (7 Mpts over the screen). Chatter
faster than the sample rate or the 100 MHz bandwidth is undercounted; the burst DURATION
is still right. Uses ../vco_rise_time/sds.py (pyvisa).
"""

import argparse
import csv
import os
import sys
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SUMMARY_FIELDS = ["time", "label", "shot", "fs_hz", "record_s", "out_p2_v", "out_p98_v", "out_rising",
                  "out_falling", "bursts", "max_rising_per_burst", "max_burst_us", "median_burst_us",
                  "ref_p2_v", "ref_p98_v", "ref_lo_v", "ref_hi_v", "ref_pulses_found", "ref", "hit", "missed",
                  "extra_in_window", "extra_outside", "expected_from_period"]


# --------------------------------------------------------------------------- analysis (no hardware)

def schmitt_states(v, lo, hi):
    """0/1 state per sample: goes 1 above `hi`, 0 below `lo`, holds in between.
    Samples before the first decisive one take that first state (no edge invented at the start).
    Returns None if the signal never leaves the band."""
    s = np.full(len(v), -1, dtype=np.int8)
    s[v > hi] = 1
    s[v < lo] = 0
    known = s >= 0
    if not known.any():
        return None
    idx = np.where(known, np.arange(len(v)), 0)
    np.maximum.accumulate(idx, out=idx)
    out = s[idx]
    first = int(np.argmax(known))
    out[:first] = s[first]
    return out


def edges(v, lo, hi):
    """(rising sample indices, falling sample indices)."""
    st = schmitt_states(v, lo, hi)
    if st is None:
        return np.array([], int), np.array([], int)
    d = np.diff(st.astype(np.int16))
    return np.flatnonzero(d == 1) + 1, np.flatnonzero(d == -1) + 1


def bursts(rise_t, fall_t, gap):
    """Group all edges into bursts separated by more than `gap` seconds.
    Returns a list of (start, end, n_rising, n_falling)."""
    ev = sorted([(t, 1) for t in rise_t] + [(t, 0) for t in fall_t])
    out = []
    for t, is_rise in ev:
        if out and t - out[-1][1] <= gap:
            s, _, nr, nf = out[-1]
            out[-1] = (s, t, nr + is_rise, nf + (1 - is_rise))
        else:
            out.append((t, t, is_rise, 1 - is_rise))
    return out


def auto_thresholds(v, min_swing):
    """30 % / 70 % of the 2nd-98th percentile span, or None if the span is under min_swing."""
    p2, p98 = np.percentile(v, [2, 98])
    if p98 - p2 < min_swing:
        return None
    return p2 + 0.3 * (p98 - p2), p2 + 0.7 * (p98 - p2)


def match_pulses(ref_rise_t, out_rise_t, window, t_start, t_end):
    """Each reference pulse start should have exactly one OUT+ rising edge within +/- window.
    Reference pulses within `window` of the record ends are skipped (they may be cut off).
    Returns dict: ref, hit, missed, extra_in_window, extra_outside."""
    ref = [t for t in ref_rise_t if t_start + window <= t <= t_end - window]
    out = np.asarray(out_rise_t)
    used = np.zeros(len(out), bool)
    hit = missed = extra_in = 0
    for t in ref:
        m = (out >= t - window) & (out <= t + window)
        n = int(m.sum())
        used |= m
        if n == 0:
            missed += 1
        else:
            hit += 1
            extra_in += n - 1
    inside = (out >= t_start + window) & (out <= t_end - window)
    return {"ref": len(ref), "hit": hit, "missed": missed,
            "extra_in_window": extra_in, "extra_outside": int((~used & inside).sum())}


def analyse(t0, fs, v_out, v_ref, a):
    """All numbers for one shot. `a` = parsed arguments."""
    n = len(v_out)
    r_i, f_i = edges(v_out, a.out_lo, a.out_hi)
    r_t, f_t = t0 + r_i / fs, t0 + f_i / fs
    b = bursts(r_t, f_t, a.gap_us * 1e-6)
    res = {"fs_hz": fs, "record_s": n / fs,
           "out_p2_v": round(float(np.percentile(v_out, 2)), 4), "out_p98_v": round(float(np.percentile(v_out, 98)), 4),
           "out_rising": len(r_t), "out_falling": len(f_t), "bursts": len(b),
           "max_rising_per_burst": max((x[2] for x in b), default=0),
           "max_burst_us": round(1e6 * max((x[1] - x[0] for x in b), default=0.0), 3),
           "median_burst_us": round(1e6 * float(np.median([x[1] - x[0] for x in b])), 3) if b else 0.0}
    if v_ref is not None:
        th = (a.ref_lo, a.ref_hi) if a.ref_lo is not None else auto_thresholds(v_ref, a.ref_min_swing)
        res["ref_p2_v"], res["ref_p98_v"] = (round(float(x), 4) for x in np.percentile(v_ref, [2, 98]))
        if th is None:
            res["ref_pulses_found"] = 0
        else:
            rr, _ = edges(v_ref, *th)
            rr_t = t0 + rr / fs
            res["ref_lo_v"], res["ref_hi_v"] = round(float(th[0]), 4), round(float(th[1]), 4)
            res["ref_pulses_found"] = len(rr_t)
            if a.match:
                res.update(match_pulses(rr_t, r_t, a.window_us * 1e-6, t0, t0 + n / fs))
    if a.match and a.period_us and not res.get("ref_pulses_found"):
        res["expected_from_period"] = int((n / fs) // (a.period_us * 1e-6))
    return res, b


# --------------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--label", required=True, help="short name for this run, e.g. tri_1Hz or ed_tx-10_100us")
    p.add_argument("--shots", type=int, default=10)
    p.add_argument("--out-ch", type=int, default=2, help="scope channel on OUT+ (J7)")
    p.add_argument("--ref-ch", type=int, default=1, help="scope channel on IN+ / VENV (0 = none)")
    p.add_argument("--out-lo", type=float, default=1.10, help="OUT+ low threshold, V (levels ~1.00 / 1.39 V)")
    p.add_argument("--out-hi", type=float, default=1.30, help="OUT+ high threshold, V")
    p.add_argument("--gap-us", type=float, default=1.0, help="edges closer than this are one burst")
    p.add_argument("--match", action="store_true", help="Test 4: match OUT+ pulses to reference pulses")
    p.add_argument("--ref-lo", type=float, default=None, help="reference low threshold, V (default: auto)")
    p.add_argument("--ref-hi", type=float, default=None, help="reference high threshold, V (default: auto)")
    p.add_argument("--ref-min-swing", type=float, default=0.008, help="auto: smallest reference pulse, V")
    p.add_argument("--window-us", type=float, default=2.0, help="match window around each reference edge")
    p.add_argument("--period-us", type=float, default=None, help="pulse period, if the reference is too small to see")
    p.add_argument("--timeout", type=float, default=20.0, help="s to wait for each trigger")
    p.add_argument("--resource", default=None, help="VISA resource (default: the one in sds.py)")
    a = p.parse_args()
    if (a.ref_lo is None) != (a.ref_hi is None):
        sys.exit("Give both --ref-lo and --ref-hi, or neither.")

    sys.path.insert(0, os.path.join(HERE, "..", "vco_rise_time"))
    import sds  # noqa: E402  (team driver)

    # pyvisa-py (no NI-VISA on the Mac): sds.SDS._drain only catches VisaIOError, but on
    # pyvisa-py an empty read ends in a raw USB timeout / pipe error. Treat those as "drained".
    _orig_drain = sds.SDS._drain

    def _safe_drain(self):
        try:
            _orig_drain(self)
        except Exception:
            self.inst.timeout = 30000

    sds.SDS._drain = _safe_drain
    s = sds.SDS(a.resource or sds.RESOURCE)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(DATA, f"cmp_scope_{a.label}_{stamp}")
    os.makedirs(folder, exist_ok=True)
    summary = os.path.join(DATA, "cmp_scope_summary.csv")
    rows = []
    try:
        for i in range(a.shots):
            if not s.single(a.timeout):
                print(f"shot {i}: no trigger within {a.timeout:g} s, skipped")
                continue
            codes_o, vdiv_o, ofst_o, fs, t0 = s.waveform_raw(a.out_ch)
            v_out = codes_o * np.float32(vdiv_o / 25.0) - np.float32(ofst_o)
            v_ref, extra = None, {}
            if a.ref_ch:
                codes_r, vdiv_r, ofst_r, fs_r, _ = s.waveform_raw(a.ref_ch)
                if fs_r != fs or len(codes_r) != len(codes_o):
                    print(f"shot {i}: channels have different records; reference ignored")
                else:
                    v_ref = codes_r * np.float32(vdiv_r / 25.0) - np.float32(ofst_r)
                    extra = dict(ref_codes=codes_r, ref_vdiv=vdiv_r, ref_offset=ofst_r)
            np.savez_compressed(os.path.join(folder, f"shot_{i:02d}.npz"), out_codes=codes_o, out_vdiv=vdiv_o,
                                out_offset=ofst_o, fs=fs, t_first=t0, out_ch=a.out_ch, ref_ch=a.ref_ch, **extra,
                                note="volts = codes*vdiv/25 - offset; t = t_first + n/fs")
            res, _ = analyse(t0, fs, v_out, v_ref, a)
            if not 0.6 < res["out_p2_v"] < 1.8 or not 0.6 < res["out_p98_v"] < 1.8:
                print(f"  WARNING: OUT+ spans {res['out_p2_v']}..{res['out_p98_v']} V, expected ~1.0..1.4 V. "
                      "Probe attenuation setting (ATTN) wrong, or not on J7?")
            row = {"time": stamp, "label": a.label, "shot": i, **res}
            rows.append(row)
            msg = (f"shot {i}: {res['out_rising']} rising / {res['bursts']} bursts, "
                   f"max {res['max_rising_per_burst']} rising per burst, longest burst {res['max_burst_us']} us")
            if "ref" in res:
                msg += (f" | ref pulses {res['ref']}: hit {res['hit']}, missed {res['missed']}, "
                        f"extra {res['extra_in_window'] + res['extra_outside']}")
            elif "expected_from_period" in res:
                msg += f" | reference not seen; ~{res['expected_from_period']} pulses expected from the period"
            print(msg)
    finally:
        s.close()
    if not rows:
        print("Nothing captured.")
        return
    new = not os.path.exists(summary)
    with open(summary, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, restval="")
        if new:
            w.writeheader()
        w.writerows(rows)
    if a.match and any("ref" in r for r in rows):
        tot = {k: sum(r.get(k, 0) for r in rows) for k in ("ref", "hit", "missed", "extra_in_window", "extra_outside")}
        print(f"\nTOTAL over {len(rows)} shots: {tot['ref']} reference pulses, {tot['hit']} hit, {tot['missed']} missed, "
              f"{tot['extra_in_window'] + tot['extra_outside']} extra edges")
    print(f"Saved {folder}\nAppended {summary}")


if __name__ == "__main__":
    main()
