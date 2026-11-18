"""Output of the four ZX60-P162LN+ alone against frequency and drive, from raw SM200B IQ (18 Nov).
Pluto TX -> 4 x ZX60-P162LN+ (7 cm cables) -> 10+10+3+6 = 29 dB of pads -> SM200B. Is the ~360 MHz detector ripple already here?
Coarse to fine: 600-1600 MHz every 25 MHz, then every 5 MHz, each frequency at every level. Per point: 16384 raw IQ samples
(50 MS/s, tone 10 MHz above centre) saved to amp_chain/<freq>_<level>.npy; the CSV holds the tone, the instantaneous power
percentiles and the 2nd and 3rd harmonics, all referred to the amplifier output (pads added back). Resumes where it stopped.
Run from clinic/claude/signal_hound with system Python. Ends cleanly when STOP_AMP_RUN exists; always leaves the tone off."""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "signal_hound"))
from run_p162_sm200b import att_for  # noqa: E402
from run_pluto_full_range import ATT_MIN_DB, SCALE, retry, tone_off, tone_on  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

PAD_DB, TOP_DBM, STOP_DBM, N, OFS = 29.0, -36.0, 5.0, 16384, 10e6
LEVELS = (-36.0, -43.0, -50.0, -57.0, -64.0, -71.0)
# AMP_MODE=ramp: output against Pluto level, -90 to -36 dBm in 1 dB steps at fixed frequencies, repeated (rep 1 keeps 16384 IQ samples, later reps 4096)
MODE = __import__("os").environ.get("AMP_MODE", "sweep")
RAMP_F = sorted({*np.arange(700.0, 1600.1, 50.0), 770.0, 960.0, 1160.0, 1340.0, 1510.0})
RAMP_W, REPS = np.arange(-90.0, TOP_DBM + 0.1, 1.0), 30
NAME = {"sweep": "amp_chain", "ramp": "amp_ramp"}[MODE]
OUT, RAW, STOP, DONE = HERE / f"{NAME}_18nov.csv", HERE / NAME, HERE / "STOP_AMP_RUN", HERE / ("AMP_RUN_DONE" if MODE == "sweep" else "AMP_RAMP_DONE")
COLS = ["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "tone_dbm", "p_mean_dbm", "p01_dbm", "p50_dbm", "p99_dbm", "p_max_dbm", "h2_dbm", "h3_dbm", "sm_in_dbm"] + (["rep"] if MODE == "ramp" else [])
assert max(LEVELS) <= TOP_DBM and max(RAMP_W) <= TOP_DBM


def iq(h, centre, n=N):
    sm_set_IQ_center_freq(h, centre)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    x = np.asarray(sm_get_IQ(h, n, 0, SM_TRUE)["iq_buf"], np.complex64)
    sm_abort(h)
    return x, fs


def line(x, fs, off):
    """Power of the strongest line within 1 MHz of off (Hz from centre), dBm at the SM200B input."""
    w = np.hanning(len(x))
    s = np.abs(np.fft.fft(x * w)) / w.sum()
    fr = np.fft.fftfreq(len(x), 1 / fs)
    return float(20 * np.log10(s[abs(fr - off) <= 1e6].max() + 1e-20))


def plan():
    if MODE == "ramp":
        return [(n, f, round(float(w), 1)) for n in range(1, REPS + 1) for f in RAMP_F for w in RAMP_W]
    return [(1, f, w) for step in (25.0, 5.0) for f in np.arange(600.0, 1600.1, step) for w in LEVELS]


def key(r):
    return int(r.get("rep") or 1), float(r["freq_mhz"]), float(r["pluto_want_dbm"])


def main():
    RAW.mkdir(exist_ok=True)
    new = not OUT.exists()
    done = set() if new else {key(r) for r in csv.DictReader(open(OUT))}
    h = sm_open_device()["device"]
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        sm_set_ref_level(h, 0.0)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, 1)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        with open(OUT, "a", newline="") as fh:
            wr = csv.writer(fh)
            if new:
                wr.writerow(COLS)
                tone_off()
                time.sleep(0.5)
                x, fs = iq(h, 1000e6 - OFS)
                np.save(RAW / "tone_off_1000.npy", x)
                p = 10 * np.log10(np.abs(x) ** 2 + 1e-20) + PAD_DB
                print(f"tone off: mean {10 * np.log10(np.mean(np.abs(x) ** 2)) + PAD_DB:.1f} dBm, max {p.max():.1f} dBm (referred to amp output)", flush=True)
            todo = list(dict.fromkeys(k for k in plan() if k not in done))
            print(f"{dt.datetime.now():%H:%M:%S} {len(todo)} points to go", flush=True)
            for i, (n, f, want) in enumerate(todo):
                if STOP.exists():
                    print("stop file", flush=True)
                    break
                att = max(att_for(f, want), ATT_MIN_DB)   # the Pluto safety floor wins; the CSV keeps the setting actually used
                retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f}")
                time.sleep(0.3)
                x, fs = iq(h, f * 1e6 - OFS, N if n == 1 else 4096)
                np.save(RAW / (f"{f:.0f}_{want:.0f}.npy" if MODE == "sweep" else f"{n}_{f:.0f}_{want:.0f}.npy"), x)
                p = 10 * np.log10(np.abs(x) ** 2 + 1e-20)
                t = line(x, fs, OFS)
                h2, h3 = (line(*iq(h, k * f * 1e6 - OFS, 8192), OFS) + PAD_DB for k in (2, 3))
                if want >= -60 and t + PAD_DB < 0:   # a working chain is railed near +20 dBm here; this means no signal (14:40 on 18 Nov)
                    print(f"NO SIGNAL: {t + PAD_DB:.1f} dBm out at {f} MHz {want} dBm in; stopping, check amp supply and cables", flush=True)
                    STOP.touch()
                    break
                wr.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, want, round(t + PAD_DB, 2), round(10 * np.log10(np.mean(np.abs(x) ** 2)) + PAD_DB, 2),
                             *np.round(np.percentile(p, [1, 50, 99]) + PAD_DB, 2), round(float(p.max()) + PAD_DB, 2), round(h2, 2), round(h3, 2), round(t, 2)] + ([n] if MODE == "ramp" else []))
                fh.flush()
                if t > STOP_DBM:
                    print(f"STOP RULE: {t:.1f} dBm at the SM200B at {f} MHz {want} dBm", flush=True)
                    break
                if i % 60 == 0 or (MODE == "ramp" and i % len(RAMP_W) == 0):
                    print(f"{dt.datetime.now():%H:%M:%S} {f:.0f} MHz {want:.0f} dBm: tone {t + PAD_DB:.1f} dBm out, 2f {h2:.1f}, 3f {h3:.1f}  ({i}/{len(todo)})", flush=True)
            else:
                DONE.touch()
    finally:
        tone_off()
        sm_close_device(h)
        print(f"{dt.datetime.now():%H:%M:%S} tone off, SM200B closed", flush=True)


if __name__ == "__main__":
    main()
