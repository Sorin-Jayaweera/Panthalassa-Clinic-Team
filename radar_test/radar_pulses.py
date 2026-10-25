"""Capture the Furuno radar's pulses with the SM200B (I/Q streaming, 50 MS/s, 41.5 MHz bandwidth) and measure:
pulse spacing, pulse width, rise and fall time, peak power, the beam pass profile and the rotation period.
Run from clinic/claude/signal_hound:   python ../radar_test/radar_pulses.py [seconds]

Input protection is the same as the other scripts: internal attenuator 30 dB, reference level +20 dBm.
I/Q samples are the corrected 32-bit float type, so |I + jQ|^2 is power in mW at the SM200B input.
Saved in radar_test/pulses_<time>/: every pulse found (pulses.csv), the envelope at 10 us resolution for the
whole capture (envelope_10us.csv), 40 us of raw I/Q around the 20 strongest pulses (snippets.npz), plots, summary.json.
"""
import csv
import datetime as dt
import json
import sys
import time
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

CENTER = float(sys.argv[3]) if len(sys.argv) > 3 else 9.4036e9
BLOCK = 1_000_000              # 20 ms at 50 MS/s
THRESH_DB_OVER_NOISE = 15.0


def diag(h):
    d = sm_get_device_diagnostics(h)
    return round(d["temperature"], 2), round(d["voltage"], 2), round(d["current"], 3)


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    decim = int(sys.argv[2]) if len(sys.argv) > 2 else 1     # 1: 50 MS/s for pulse shape; 8: 6.25 MS/s keeps up for long timing captures
    out = HERE / f"pulses_{dt.datetime.now():%Y%m%d_%H%M%S}_dec{decim}"
    out.mkdir()
    h = sm_open_device()["device"]
    S = {"center_hz": CENTER}
    try:
        S["temp_start_c"], S["supply_v"], S["supply_a"] = diag(h)
        sm_set_attenuator(h, SM_MAX_ATTEN)
        sm_set_ref_level(h, 20.0)
        sm_set_IQ_center_freq(h, CENTER)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, decim)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6 / decim)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        sm_configure(h, SM_MODE_IQ_STREAMING)
        p = sm_get_IQ_parameters(h)
        fs, bw = p["sample_rate"], p["bandwidth"]
        S["sample_rate"], S["bandwidth"], S["decimation"] = fs, bw, decim
        nblocks = int(np.ceil(seconds * fs / BLOCK))
        env10 = []                                   # max power in each 10 us
        dec = int(round(10e-6 * fs))
        pulses, snippets = [], []
        lost = 0
        noise_mw = None
        tail = np.zeros(0, np.complex64)
        t0 = time.time()
        for b in range(nblocks):
            r = sm_get_IQ(h, BLOCK, 0, SM_TRUE if b == 0 else SM_FALSE)
            lost += max(0, r["sample_loss"])
            iq = r["iq_buf"]
            pw = (iq.real.astype(np.float64) ** 2 + iq.imag.astype(np.float64) ** 2)
            if noise_mw is None:
                noise_mw = float(np.median(pw))
                S["noise_dbm_per_sample"] = 10 * np.log10(noise_mw)
            env10.append(pw[: len(pw) // dec * dec].reshape(-1, dec).max(axis=1))
            thr = noise_mw * 10 ** (THRESH_DB_OVER_NOISE / 10)
            above = pw > thr
            edges = np.flatnonzero(np.diff(above.astype(np.int8)) == 1) + 1
            for e in edges:
                if e < 50 or e + 2000 // decim > len(pw):
                    continue
                t_abs = (b * BLOCK + e) / fs
                if pulses and t_abs - pulses[-1][0] < 20e-6:          # same pulse: noise made the threshold cross twice
                    continue
                seg = pw[e - 50: e + 2000 // decim]
                sq = iq[e - 50: e + 2000 // decim]
                m = int(np.argmax(seg[:50 + 350 // decim]))
                pk = float(seg[m])
                a_ = np.sqrt(seg / pk)
                l = m
                while l > 0 and a_[l - 1] > 0.1:
                    l -= 1
                r = m
                while r < len(a_) - 1 and a_[r + 1] > 0.1:
                    r += 1
                core = a_[l:r + 1]
                i90 = np.flatnonzero(core > 0.9)
                i707 = np.flatnonzero(core > 0.707)
                if len(i90) == 0:
                    continue
                width = (i707[-1] - i707[0] + 1) / fs
                rise = i90[0] / fs
                fall = (len(core) - 1 - i90[-1]) / fs
                top = sq[l + i90[0]: l + i90[-1] + 1]
                if len(top) > 6:
                    ph = np.angle(top[1:] * np.conj(top[:-1]))
                    f_off = float(np.mean(ph)) * fs / (2 * np.pi)
                    hlf = len(ph) // 2
                    chirp = (float(np.mean(ph[hlf:])) - float(np.mean(ph[:hlf]))) * fs / (2 * np.pi)
                else:
                    f_off, chirp = np.nan, np.nan
                pulses.append([t_abs, 10 * np.log10(pk), width * 1e9, rise * 1e9, fall * 1e9, (CENTER + f_off) / 1e6, chirp / 1e3])
                snippets.append((10 * np.log10(pk), t_abs, iq[e - 100: e + 1900].copy()))
            if len(snippets) > 60:
                snippets.sort(key=lambda s: -s[0])
                snippets = snippets[:20]
        S["capture_s"] = round(time.time() - t0, 2)
        S["temp_end_c"] = diag(h)[0]
        S["samples_lost"] = lost
    finally:
        sm_abort(h)
        sm_close_device(h)

    env = 10 * np.log10(np.concatenate(env10) + 1e-30)
    te = np.arange(len(env)) * 10e-6
    np.savetxt(out / "envelope_10us.csv", np.column_stack([te, env]), delimiter=",", header="time_s,max_power_dbm_in_10us", comments="", fmt=["%.5f", "%.2f"])
    P = np.array(pulses) if pulses else np.zeros((0, 7))
    with open(out / "pulses.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["time_s", "peak_dbm", "width_ns_half_power", "rise_ns_10_90_amplitude", "fall_ns_90_10_amplitude", "freq_mhz", "chirp_khz_second_half_minus_first"])
        w.writerows([[f"{a:.7f}", f"{b:.2f}", f"{c:.0f}", f"{d:.0f}", f"{e:.0f}", f"{f_:.4f}", f"{g_:.1f}"] for a, b, c, d, e, f_, g_ in P])
    snippets.sort(key=lambda s: -s[0])
    snippets = snippets[:20]
    np.savez(out / "snippets.npz", iq=np.array([s[2] for s in snippets]), peak_dbm=np.array([s[0] for s in snippets]), t=np.array([s[1] for s in snippets]), fs=fs)

    S["pulses_found"] = len(P)
    if len(P) > 2:
        t = P[:, 0]
        gaps = np.diff(t)
        g = gaps[gaps < 5e-3]
        S["pri_us_median"] = round(float(np.median(g)) * 1e6, 2)
        S["pri_us_spread"] = [round(float(np.percentile(g, 5)) * 1e6, 2), round(float(np.percentile(g, 95)) * 1e6, 2)]
        S["prf_hz"] = round(1 / float(np.median(g)), 1)
        # beam passes: gaps longer than 0.3 s separate passes
        cuts = np.flatnonzero(gaps > 0.3)
        starts = np.r_[0, cuts + 1]
        ends = np.r_[cuts, len(t) - 1]
        passes = []
        for a, b in zip(starts, ends):
            seg = P[a: b + 1]
            k = int(np.argmax(seg[:, 1]))
            passes.append(dict(t_peak=round(float(seg[k, 0]), 4), peak_dbm=round(float(seg[k, 1]), 2), pulses=int(len(seg)),
                               dur_ms=round(float(seg[-1, 0] - seg[0, 0]) * 1e3, 1),
                               dur_3db_ms=round(float(np.ptp(seg[seg[:, 1] > seg[k, 1] - 3, 0])) * 1e3, 1)))
        S["passes"] = passes
        top_pk = max(x["peak_dbm"] for x in passes)
        main = [x for x in passes if x["peak_dbm"] > top_pk - 4]
        if len(main) > 1:
            tp = [x["t_peak"] for x in main]
            S["rotation_s"] = round(float(np.median(np.diff(tp))), 3)
            S["rpm"] = round(60 / S["rotation_s"], 2)
        strong = P[P[:, 1] > P[:, 1].max() - 3]
        S["peak_dbm_max"] = round(float(P[:, 1].max()), 2)
        S["strong_pulses"] = int(len(strong))
        S["freq_mhz_strong"] = [round(float(np.nanmedian(strong[:, 5])), 4), round(float(np.nanpercentile(strong[:, 5], 5)), 4), round(float(np.nanpercentile(strong[:, 5], 95)), 4)]
        S["chirp_khz_strong"] = [round(float(np.nanmedian(strong[:, 6])), 0), round(float(np.nanpercentile(strong[:, 6], 5)), 0), round(float(np.nanpercentile(strong[:, 6], 95)), 0)]
        vals, cnt = np.unique(np.round(g * 1e6), return_counts=True)
        o = np.argsort(-cnt)[:10]
        S["pri_us_commonest"] = [[float(vals[i]), int(cnt[i])] for i in o]
        for k, name in ((2, "width_ns"), (3, "rise_ns"), (4, "fall_ns")):
            S[name] = [round(float(np.median(strong[:, k])), 0), round(float(np.min(strong[:, k])), 0), round(float(np.max(strong[:, k])), 0)]

    # plots
    fig, ax = plt.subplots(3, 1, figsize=(12, 11))
    ax[0].plot(te, env, lw=0.5)
    ax[0].set(xlabel="Time (s)", ylabel="Max power in each 10 us (dBm)", title=f"Whole capture at {CENTER/1e9:.4f} GHz: one burst per beam pass")
    if len(P):
        k = int(np.argmax(P[:, 1]))
        tk = P[k, 0]
        m = np.abs(P[:, 0] - tk) < 0.06
        ax[1].plot((P[m, 0] - tk) * 1e3, P[m, 1], ".", ms=3)
        ax[1].set(xlabel="Time from the strongest pulse (ms)", ylabel="Pulse peak (dBm)", title="Pulses in the strongest beam pass")
        for s_ in snippets[:5]:
            pw = 10 * np.log10(np.abs(s_[2]) ** 2 + 1e-30)
            ax[2].plot((np.arange(len(pw)) - 100) / fs * 1e6, pw, lw=0.8, label=f"{s_[0]:.1f} dBm")
        ax[2].set(xlabel="Time from the threshold crossing (us)", ylabel="Power (dBm)", title="The five strongest pulses, one sample every 20 ns", xlim=(-1, 3))
        ax[2].legend(fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("Furuno radar received by the Vivaldi, SM200B I/Q at 50 MS/s", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "pulses.png", dpi=110)
    (out / "summary.json").write_text(json.dumps(S, indent=1))
    print(json.dumps(S, indent=1))
    print("saved", out)


if __name__ == "__main__":
    main()
