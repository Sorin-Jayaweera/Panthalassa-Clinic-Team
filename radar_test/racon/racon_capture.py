"""Record the Furuno and the racon with the SM200B (Python API only; Spike must be closed). Run from anywhere.

    python racon_capture.py go              # everything below in order, then the plots. This is the normal call.
    python racon_capture.py check           # 3 s at 9.4026 GHz, max attenuation: peak level, headroom to +20 dBm, noise
    python racon_capture.py survey [-s 10]  # 9.0-10.0 GHz sweeps, max hold and a waterfall: where is the racon replying?
    python racon_capture.py seg [-n 8]      # segmented I/Q, 160 MHz wide, video trigger, 250 snippets per capture
    python racon_capture.py stream [-s 30]  # continuous 50 MS/s I/Q, every event's time and level, snippets of the first 4000
    add --tag load to any of them for the 50 ohm load test (antenna replaced by a load: shows what leaks straight into the SM200B)
    add --center 9.45e9 if the survey shows the racon somewhere else

Every capture is saved in data/<mode>_<tag>_<time>/ as it comes in, so a USB drop loses at most one capture.
Safety: check refuses to go on if anything is within 10 dB of the SM200B's +20 dBm limit.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "signal_hound"))
os.chdir(HERE.parent.parent / "signal_hound")      # sm_api loads its DLL from a path relative to here
from smdevice.sm_api import *  # noqa: E402,F403
import racon_setup as S  # noqa: E402
import racon_analyze as A  # noqa: E402

DATA = HERE / "data"
LAST = DATA / "last_check.json"


def setup_snapshot():
    return dict(chain=[list(c) for c in S.CHAIN], chain_gain_db=S.chain_gain_db(), d_radar_m=S.D_RADAR_M, d_racon_m=S.D_RACON_M,
                d_radar_racon_m=S.D_RADAR_RACON_M, g_rx_dbi=S.G_RX_DBI, radar_foam=S.RADAR_FOAM)


def levels(h, mode):
    """Attenuator and reference level: max attenuation for check, otherwise from the last check."""
    if mode == "check" or not LAST.exists():
        sm_set_attenuator(h, SM_MAX_ATTEN)
        sm_set_ref_level(h, 20.0)
        return dict(atten="max (30 dB)", ref_dbm=20.0)
    c = json.loads(LAST.read_text())
    ref = float(np.clip(c["peak_dbm"] + 6, -30, 20))
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, ref)
    return dict(atten="auto from ref level", ref_dbm=ref)


def stream_cfg(h, center):
    sm_set_IQ_center_freq(h, center)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_IQ_queue_size(h, 100.0)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    return sm_get_IQ_parameters(h)["sample_rate"]


def check(h, a):
    fs = stream_cfg(h, a.center)
    blk, peak, meds = 500_000, -300.0, []
    for b in range(int(3.0 * fs / blk)):
        iq = sm_get_IQ(h, blk, 0, SM_TRUE if b == 0 else SM_FALSE)["iq_buf"]
        p = iq.real ** 2 + iq.imag ** 2
        peak = max(peak, 10 * np.log10(p.max() + 1e-30))
        meds.append(np.median(p))
    noise = 10 * np.log10(np.median(meds) / np.log(2))
    out = dict(time=dt.datetime.now().isoformat(timespec="seconds"), peak_dbm=round(float(peak), 2), noise_dbm=round(float(noise), 2), fs=fs, center=a.center, tag=a.tag)
    LAST.write_text(json.dumps(out, indent=1))
    print(f"CHECK: peak {peak:+.1f} dBm at the SM200B, {S.SM_LIMIT_DBM - peak:.1f} dB below the +20 dBm limit; noise {noise:.1f} dBm per sample at 50 MS/s; "
          f"peak at our antenna port {peak - S.chain_gain_db():+.1f} dBm (chain gain {S.chain_gain_db():+.1f} dB)", flush=True)
    if peak > S.SM_LIMIT_DBM - 10:
        print("STOP: within 10 dB of the SM200B limit. Add pads before the SM200B and run check again.", flush=True)
        return False
    return True


def survey(h, a, folder):
    sm_set_sweep_start_stop(h, a.start, a.stop)
    sm_set_sweep_coupling(h, a.rbw, a.rbw, 0.001)
    sm_set_sweep_detector(h, SM_DETECTOR_MIN_MAX, SM_VIDEO_LOG)
    sm_set_sweep_scale(h, SM_SCALE_LOG)
    sm_set_sweep_window(h, SM_WINDOW_FLAT_TOP)
    sm_set_sweep_spur_reject(h, SM_FALSE)
    sm_configure(h, SM_MODE_SWEEPING)
    q = sm_get_sweep_parameters(h)
    f = q["actual_start_freq"] + q["bin_size"] * np.arange(q["sweep_size"])
    rows, ts, t0 = [], [], time.time()
    try:
        while not rows or time.time() - t0 < a.seconds:
            rows.append(np.asarray(sm_get_sweep(h)["sweep_max"], np.float32))
            ts.append(time.time() - t0)
    except (Exception, SystemExit) as e:                # USB drop (the SM wrapper calls exit()): keep every sweep taken so far
        print(f"SURVEY stopped early at {time.time() - t0:.1f} s: {e}", flush=True)
    W = np.array(rows)
    np.savez(folder / "survey.npz", f=f, W=W, t=np.array(ts), meta=json.dumps(dict(mode="survey", tag=a.tag, rbw=a.rbw, setup=setup_snapshot())))
    hold = W.max(axis=0)
    print(f"SURVEY: {len(rows)} sweeps in {ts[-1]:.1f} s; strongest {hold.max():+.1f} dBm at {f[np.argmax(hold)]/1e6:.2f} MHz", flush=True)
    return folder / "survey.npz"


def seg(h, a, folder):
    c = json.loads(LAST.read_text()) if LAST.exists() else dict(noise_dbm=-60.0, peak_dbm=-20.0)
    trig = a.trigger if a.trigger is not None else c["noise_dbm"] + 7 + 15      # 250 MS/s noise is about 7 dB above the 50 MS/s figure
    sm_set_seg_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_seg_IQ_center_freq(h, a.center)
    sm_set_seg_IQ_video_trigger(h, trig, SM_TRIGGER_EDGE_RISING)
    sm_set_seg_IQ_segment_count(h, a.segments)
    fs_guess = 250e6
    pre, size = int(a.pre_us * 1e-6 * fs_guess), int((a.pre_us + a.win_us) * 1e-6 * fs_guess)
    for i in range(a.segments):
        sm_set_seg_IQ_segment(h, i, SM_TRIGGER_TYPE_VIDEO, pre, size, a.timeout)
    sm_configure(h, SM_MODE_IQ_SEGMENTED_CAPTURE)
    par = sm_get_IQ_parameters(h)
    fs = par["sample_rate"]
    print(f"SEG: {fs/1e6:.0f} MS/s, {par['bandwidth']/1e6:.0f} MHz wide at {a.center/1e6:.1f} MHz; trigger {trig:.1f} dBm; "
          f"{a.segments} x {(a.pre_us + a.win_us):.0f} us per capture; {a.captures} captures", flush=True)
    for cap in range(a.captures):
        sm_seg_IQ_capture_start(h, 0)
        sm_seg_IQ_capture_wait(h, 0)
        snips, t, lost = [], [], 0
        for i in range(a.segments):
            if sm_seg_IQ_capture_timeout(h, 0, i)["timed_out"]:
                lost += 1
                continue
            t.append(sm_seg_IQ_capture_time(h, 0, i)["ns_since_epoch"] / 1e9)
            snips.append(sm_seg_IQ_capture_read(h, 0, i, 0, size)["iq"])
        sm_seg_IQ_capture_finish(h, 0)
        meta = dict(mode="seg", kind=f"segmented I/Q, video trigger {trig:.1f} dBm", tag=a.tag, trigger_dbm=trig, capture=cap, timed_out=lost,
                    bandwidth=par["bandwidth"], levels=a.levels, chain_gain_db=S.chain_gain_db(), setup=setup_snapshot())
        np.savez(folder / f"c{cap:02d}.npz", snippets=np.array(snips, np.complex64).reshape(len(snips), size), t_abs_s=np.array(t),
                 pre=pre if abs(fs - fs_guess) < 1 else int(a.pre_us * 1e-6 * fs), fs=fs, center=a.center, meta=json.dumps(meta, default=float))
        span = (t[-1] - t[0]) if len(t) > 1 else 0
        pk = max((10 * np.log10(np.max(np.abs(s) ** 2)) for s in snips), default=float("nan"))
        print(f"  capture {cap + 1}/{a.captures}: {len(snips)} snippets over {span*1e3:.0f} ms, {lost} timed out, strongest {pk:+.1f} dBm", flush=True)
        if pk > S.SM_LIMIT_DBM - 10:
            print("STOP: within 10 dB of the SM200B limit.", flush=True)
            break
    return folder


def stream(h, a, folder):
    c = json.loads(LAST.read_text()) if LAST.exists() else dict(noise_dbm=-60.0)
    fs = stream_cfg(h, a.center)
    blk = 500_000
    pre, L = int(a.pre_us * 1e-6 * fs), int((a.pre_us + a.win_us) * 1e-6 * fs)
    snips, t_s, all_t, all_pk, lost = [], [], [], [], 0
    prev, prev_i0, last = None, 0, -10 ** 18
    noise = None
    t_wall = time.time()
    nblk = int(a.seconds * fs / blk)
    for b in range(nblk):
        r = sm_get_IQ(h, blk, 0, SM_TRUE if b == 0 else SM_FALSE)
        lost += max(0, r["sample_loss"])
        cur = r["iq_buf"].copy()
        if noise is None:
            noise = float(np.median(cur.real ** 2 + cur.imag ** 2)) / np.log(2)
            thr = noise * 10 ** (a.trig_db / 10)
        if prev is not None:
            buf = np.concatenate([prev, cur])
            p = buf.real ** 2 + buf.imag ** 2
            for s in A.find_starts(p[:len(prev)], thr, L):
                g = prev_i0 + s
                if g - last < L:
                    continue
                last = g
                all_t.append(g / fs)
                all_pk.append(10 * np.log10(p[s:s + L].max()))
                if len(snips) < a.max_snips and s - pre >= 0:
                    snips.append(buf[s - pre:s - pre + L].astype(np.complex64))
                    t_s.append(g / fs)
        prev, prev_i0 = cur, b * blk
        if b and b % int(5 * fs / blk) == 0:
            print(f"  {b*blk/fs:.0f} s: {len(all_t)} events, {len(snips)} snippets kept", flush=True)
    meta = dict(mode="stream", kind=f"streaming I/Q 50 MS/s, events {a.trig_db:g} dB over noise", tag=a.tag, samples_lost=lost, levels=a.levels,
                chain_gain_db=S.chain_gain_db(), setup=setup_snapshot(), wall_start=dt.datetime.fromtimestamp(t_wall).isoformat(timespec="seconds"))
    out = folder / "stream.npz"
    np.savez(out, snippets=np.array(snips, np.complex64).reshape(len(snips), L), t_abs_s=np.array(t_s), pre=pre, fs=fs, center=a.center,
             all_t_s=np.array(all_t), all_peak_dbm=np.array(all_pk), duration_s=nblk * blk / fs, meta=json.dumps(meta, default=float))
    print(f"STREAM: {nblk*blk/fs:.0f} s, {len(all_t)} events, {len(snips)} snippets saved, samples lost {lost}", flush=True)
    return folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["go", "check", "survey", "seg", "stream"])
    ap.add_argument("--tag", default="racon")
    ap.add_argument("--center", type=float, default=S.CENTER_HZ)
    ap.add_argument("-s", "--seconds", type=float, default=None)
    ap.add_argument("-n", "--captures", type=int, default=8)
    ap.add_argument("--segments", type=int, default=250)
    ap.add_argument("--win-us", type=float, default=50.0)
    ap.add_argument("--pre-us", type=float, default=3.0)
    ap.add_argument("--trigger", type=float, default=None, help="video trigger level dBm (default noise + 15 dB)")
    ap.add_argument("--trig-db", type=float, default=15.0)
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--max-snips", type=int, default=4000)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--rbw", type=float, default=100e3, help="survey RBW. 9 Nov: 300 kHz and above gave nonsense levels (median +4 to +24 dBm); 100 kHz reads right")
    ap.add_argument("--start", type=float, default=9.0e9)
    ap.add_argument("--stop", type=float, default=10.0e9)
    a = ap.parse_args()
    modes = ["check", "survey", "seg", "stream"] if a.mode == "go" else [a.mode]
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    made = []
    h = sm_open_device()["device"]
    try:
        t0 = sm_get_device_diagnostics(h)["temperature"]
        print(f"SM200B open, {t0:.1f} C. Chain gain {S.chain_gain_db():+.1f} dB. Tag '{a.tag}'.", flush=True)
        for m in modes:
            a.levels = levels(h, m)
            if m == "check":
                if not check(h, a):
                    return
                continue
            folder = DATA / f"{m}_{a.tag}_{stamp}"
            folder.mkdir(parents=True, exist_ok=True)
            a.seconds = a.seconds if a.seconds is not None and a.mode != "go" else (10.0 if m == "survey" else 30.0)
            made.append((m, {"survey": survey, "seg": seg, "stream": stream}[m](h, a, folder)))
            sm_abort(h)
        t1 = sm_get_device_diagnostics(h)["temperature"]
        print(f"SM200B {t0:.1f} -> {t1:.1f} C", flush=True)
    finally:
        try:
            sm_abort(h)
        finally:
            sm_close_device(h)
    if not a.no_plots:
        for m, path in made:
            figs = A.survey_plot(path) if m == "survey" else A.analyze(path)
            for f in figs or []:
                print("PLOT", f, flush=True)


if __name__ == "__main__":
    main()
