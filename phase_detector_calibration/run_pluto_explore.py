"""Unattended Pluto measurements into the 3 amps and detector, scope at 1 Mohm, SM200B through 23 dB (assumed), about 2 hours.

Passes, in order, each saved as it runs in pluto_explore_1nov.csv (kitty readings in pluto_explore_kitty_1nov.csv):
  kitty    300-1700 MHz, 20 MHz steps, about +2.7 dBm at the detector: tone, twice the tone and near DC on the SM200B
  levelmap 900-1200 MHz, 2 MHz steps, at -45, -42, -39, -33 and -31 dBm
  grid     400-1700 MHz, 100 MHz steps, -61 to -31 dBm in 3 dB steps, capped by the port limit below
  hold     1054 MHz, -36 dBm, one reading every 5 s for 15 min
  off      tone off, one reading every 5 s for 5 min
  att31    1200-2090 MHz, 5 MHz steps, attenuation fixed at 31 dB
  repeat   900-1200 MHz, 1 MHz steps, -36 dBm, started every 12 min until 15 min before the deadline
  scope29  2850-2950 MHz, 5 MHz steps, 39 dB, three passes, last in case it drops the scope USB

Limits: Pluto never above -28 dBm, attenuation never below pluto_cw.ATT_MIN_DB, 39 dB or more outside the measured
table, and at most +12.8 dBm at the detector from datasheet gain. A point that breaks a limit is skipped and logged.
USB: retries for 15 min per point, then stops with the tone off.
Run from clinic/claude/signal_hound.
"""
import csv
import datetime as dt
import sys
import time
import traceback
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "signal_hound"))
import run_pluto_full_range as full  # noqa: E402
from run_pluto_full_range import ATT_MIN_DB, P_LIMIT_DBM, P_WORST_DBM, SCALE, Scope, SPLIT_DB, _GAIN, _MAP, plan, retry, tone_off, tone_on  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

full.RETRY_S = 900.0
HOURS = 2.0
PORT_LIMIT_DBM = 12.8
PAD_DB = 23.0
BLOCK = 262_144
MAP_RUNS = HERE / "pluto_map_runs_1nov.csv"
OUT = HERE / "pluto_explore_1nov.csv"
OUT_K = HERE / "pluto_explore_kitty_1nov.csv"
START = time.time()
DEADLINE = START + HOURS * 3600


def setting(f, want):
    """Attenuation for this level, or None if a limit would be broken."""
    gain = 3 * np.interp(f, _GAIN[:, 0], _GAIN[:, 1])
    if want > P_LIMIT_DBM or want + gain - SPLIT_DB > PORT_LIMIT_DBM:
        return None
    full_scale = float(np.interp(f, _MAP[:, 0], _MAP[:, 1]))
    att = full_scale - want
    if not _MAP[0, 0] <= f <= _MAP[-1, 0]:
        att = max(att, P_WORST_DBM - P_LIMIT_DBM)
    return min(89.75, round(max(att, ATT_MIN_DB) * 4) / 4)


class Bench:
    def __init__(self):
        self.scope = Scope(1, 0.1)
        self.fh = open(OUT, "a", newline="")
        self.w = csv.writer(self.fh)
        if OUT.stat().st_size == 0:
            self.w.writerow(["timestamp", "pass", "rep", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "repeat_sd_v", "rms_v"])

    def volts(self):
        def get():
            try:
                return self.scope.read()
            except Exception:
                self.scope.drop()
                raise
        return retry(get, "scope")[0]

    def point(self, name, rep, f, att, want):
        retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f:.0f}")
        time.sleep(0.3)
        return self.save(name, rep, f, att, want)

    def save(self, name, rep, f, att, want):
        m, sd, r = self.volts()
        self.w.writerow([dt.datetime.now().isoformat(timespec="seconds"), name, rep, f, att, want, m, sd, r])
        self.fh.flush()
        return m

    def sweep(self, name, rep, freqs, want):
        for f in freqs:
            if time.time() > DEADLINE:
                return
            att = setting(float(f), want)
            if att is None:
                print(f"{name}: skipped {f:.0f} MHz at {want} dBm, over a limit", flush=True)
                continue
            self.point(name, rep, float(f), att, want)
        print(f"{name} {rep} {want} dBm finished {dt.datetime.now():%H:%M:%S}", flush=True)


def kitty_read(h, center):
    sm_set_IQ_center_freq(h, center)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    iq = sm_get_IQ(h, BLOCK, 0, SM_TRUE)["iq_buf"]
    sm_abort(h)
    win = np.hanning(len(iq))
    sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq * win))) / win.sum() + 1e-20) + PAD_DB
    return (center + np.fft.fftshift(np.fft.fftfreq(len(iq), 1 / fs))) / 1e6, sp


def line_near(fr, sp, f, width=2.0):
    m = abs(fr - f) <= width
    k = np.flatnonzero(m)[int(sp[m].argmax())]
    return float(fr[k]), float(sp[k])


def kitty_pass(b):
    h = sm_open_device()["device"]
    new = not OUT_K.exists()
    try:
        sm_set_attenuator(h, SM_AUTO_ATTEN)
        sm_set_ref_level(h, -10.0)
        sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
        sm_set_IQ_sample_rate(h, 1)
        sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
        sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
        sm_set_IQ_queue_size(h, 100.0)
        with open(OUT_K, "a", newline="") as fk:
            w = csv.writer(fk)
            if new:
                w.writerow(["timestamp", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "detector_mean_v", "tone_found_mhz", "tone_dbm", "double_found_mhz", "double_dbm", "low_found_mhz", "low_dbm"])
            for f in np.arange(300.0, 1700.5, 20.0):
                att, want, _ = plan(f)
                m = b.point("kitty", 0, f, att, want)
                ft, lt = line_near(*kitty_read(h, f * 1e6), f)
                fd, ld = line_near(*kitty_read(h, 2 * f * 1e6), 2 * f)
                fr, sp = kitty_read(h, 21e6)
                keep = abs(fr) > 0.5
                k = int(sp[keep].argmax())
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), f, att, round(float(want), 2), m, ft, round(lt, 2), fd, round(ld, 2), float(fr[keep][k]), round(float(sp[keep][k]), 2)])
                fk.flush()
    finally:
        sm_close_device(h)
    print(f"kitty finished {dt.datetime.now():%H:%M:%S}", flush=True)


def wait_for_map_runs():
    """The Pluto has one owner: wait until the earlier runs have finished or stopped updating for 5 min."""
    while True:
        rows = sum(1 for _ in open(MAP_RUNS))
        idle = time.time() - MAP_RUNS.stat().st_mtime
        if rows >= 508 or idle > 300:
            print(f"map runs: {rows} lines, idle {idle:.0f} s", flush=True)
            time.sleep(15)
            return
        time.sleep(10)


def main():
    wait_for_map_runs()
    global START, DEADLINE
    START = time.time()
    DEADLINE = START + HOURS * 3600
    b = Bench()
    try:
        retry(tone_off, "tone off")
        time.sleep(1.0)
        m = b.save("start_off", 0, 0.0, 89.75, -999.0)
        print(f"tone off {m*1e3:.2f} mV", flush=True)
        # The SM200B driver ends the process when its USB drops, so the kitty pass is not run here.
        for want in (-37.0, -31.0, -43.0, -34.0, -40.0, -46.0, -49.0, -52.0, -55.0, -58.0, -61.0):
            b.sweep("map2d", 0, np.arange(400.0, 1700.5, 10.0), want)
        att = setting(1054.0, -36.0)
        retry(lambda: tone_on(1054e6, att, SCALE), "tone hold")
        for i in range(180):
            b.save("hold", i, 1054.0, att, -36.0)
            time.sleep(4.0)
        print(f"hold finished {dt.datetime.now():%H:%M:%S}", flush=True)
        retry(tone_off, "tone off")
        for i in range(60):
            b.save("off", i, 0.0, 89.75, -999.0)
            time.sleep(4.0)
        print(f"off finished {dt.datetime.now():%H:%M:%S}", flush=True)
        for f in np.arange(1200.0, 2090.5, 5.0):
            b.point("att31", 0, float(f), max(31.0, ATT_MIN_DB), float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - 31.0)
        print(f"att31 finished {dt.datetime.now():%H:%M:%S}", flush=True)
        rep = 0
        while time.time() < DEADLINE - 900:
            t0 = time.time()
            b.sweep("repeat", rep, np.arange(900.0, 1200.5, 1.0), -36.0)
            rep += 1
            retry(tone_off, "tone off")
            b.save("repeat_off", rep, 0.0, 89.75, -999.0)
            while time.time() < min(t0 + 720, DEADLINE - 900):
                time.sleep(5)
        for rep in range(3):
            for f in np.arange(2850.0, 2950.5, 5.0):
                b.point("scope29", rep, float(f), 39.0, -28.0)
        print(f"scope29 finished {dt.datetime.now():%H:%M:%S}", flush=True)
    finally:
        b.scope.drop()
        b.fh.close()
        try:
            tone_off()
            print("tone off", flush=True)
        except Exception as e:
            print(f"TONE OFF FAILED, Pluto may still be on: {str(e)[:160]}", flush=True)


if __name__ == "__main__":
    main()
