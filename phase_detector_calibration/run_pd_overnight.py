"""Overnight phase detector program, 13-14 Nov 2026. Same wiring as the evening runs:
Pluto TX -> 4 x ZX60-P162LN+ (4.03 V, 0.23 A) -> ZFRSC-42-S+ -> right arm cable D + 3 dB pad at LO, left arm cable B + E + 6 dB pad at RF
-> ZX05-30W-S+ -> IF to SDS1104X-E CH1 (1 Mohm, DC) and, through 20 dB of pads, the SM200B. D and B are the same length.

Stages, coarse before fine, so a crash at any time still leaves useful data. Every point is saved as taken in
pd_overnight_13nov.csv; rerunning carries on where it stopped. A stage marked kitty=True also reads the tone, 2x and 3x
the tone at the IF port on the SM200B (referred to before the 20 dB). If the SM200B fails, the stage carries on with the scope.

Limits: Pluto level never above -36 dBm (TOP_DBM). Inside the measured level table (350-2090 MHz) the attenuation comes
from the table; outside it the level is unknown, so attenuation is at least 47 dB, which holds -36 dBm even at the
+11 dBm worst-case full scale. Never below the pluto_cw floor. Stops with the tone off if the detector passes 700 mV or a
line at the IF passes +5 dBm. The PC is kept awake by SetThreadExecutionState while it runs (no setting is changed).
Run from clinic/claude/signal_hound:  python ../phase_detector_calibration/run_pd_overnight.py
"""
import csv
import ctypes
import datetime as dt
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_p162_sm200b as K  # noqa: E402  (also puts signal_hound on the path)
import run_pd_cable as P  # noqa: E402
import run_pluto_full_range as full  # noqa: E402
from run_pluto_full_range import SCALE, _MAP, retry, tone_off, tone_on  # noqa: E402
from smdevice.sm_api import *  # noqa: E402,F403

full.RETRY_S = 900.0
K.PAD_DB = 20.0
TOP_DBM = -36.0
WORST_DBM = 11.0
STOP_MV = 700.0
STOP_IF_DBM = 5.0
DEADLINE = dt.datetime(2099, 1, 1)   # runs until Sorin says stop
OUT = HERE / "pd_dither_14nov.csv"
STOP_FILE = HERE / "STOP_PD_RUN"   # create this file to end the run cleanly between points
VDIV = 0.05                        # 50 mV/div: ADC step 2 mV (0.2 V/div gave 8 mV steps = the staircase)
OFST = -0.06                       # screen centre +60 mV, so the screen covers about -140 to +260 mV
CLIP_MV = 250.0
DITHER = 4                         # read at 4 offsets 1 mV apart (half an ADC step) and average: smooths the 2 mV steps
BAND = (1150.0, 1550.0)
COLS = ["timestamp", "stage", "rep", "freq_mhz", "pluto_att_db", "pluto_want_dbm", "level_known", "detector_mean_v", "repeat_sd_v", "rms_v",
        "if_tone_dbm", "if_double_dbm", "if_triple_dbm"]


def att_for(f, want):
    if want > TOP_DBM:
        raise ValueError(f"refusing {want} dBm")
    inside = _MAP[0, 0] <= f <= _MAP[-1, 0]
    if inside:
        att = float(np.interp(f, _MAP[:, 0], _MAP[:, 1])) - want
    else:
        att = WORST_DBM - want              # safe even at the worst-case full scale
    att = max(att, full.ATT_MIN_DB)
    return min(89.75, round(att * 4) / 4), inside


def rng(a, b, s):
    return [round(float(x), 3) for x in np.arange(a, b + s / 2, s)]


def stages():
    """(stage, rep, list of (freq, want_dbm), kitty, label). Order = coarse first."""
    lo, hi = BAND
    yield "off", 0, [(0.0, -999.0)] * 12, False, "tone off, 1 min, 50 mV/div, 4-offset dither"
    yield "band1", 1, [(f, -50.0) for f in rng(lo, hi, 1)], False, "band 1150-1550 MHz, 1 MHz, -50 dBm, 50 mV/div"
    yield "levels", 0, [(f, w) for w in (-60.0, -56.0, -52.0, -48.0, -44.0, -40.0, -36.0) for f in rng(1220, 1452, 4)], False, "power levels -60 to -36 dBm (Pluto top), 1220-1452 MHz every 4 MHz, dithered"
    yield "off", 1, [(0.0, -999.0)] * 12, False, "tone off at the end, 1 min"


def keep_awake(on):
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x00000001 if on else 0))
    except Exception:
        pass


class FineScope(full.Scope):
    """The usual scope setup, then a finer V/div and an offset so the in-band readings span many ADC steps."""
    def read(self):
        if self.s is None:
            self.s = full.SDS()
            full.setup_scope(self.s, self.ch, self.vdiv)
            time.sleep(0.5)
        step = self.vdiv / 25.0
        vals, rms = [], []
        for k in range(DITHER):
            self.s.write(f"C{self.ch}:OFST {OFST - k * 0.001:.4E}V")   # offset resolution is 1 mV (half a 2 mV step)
            time.sleep(0.2)
            _, v = self.s.waveform(self.ch)      # scaling uses the offset read back from the scope
            vals.append(v.mean())
            rms.append(v.std())
        return float(np.mean(vals)), float(np.std(vals)), float(np.mean(rms))


class Kitty:
    def __init__(self):
        self.h = None
        self.dead = False

    def open(self):
        if self.h is None and not self.dead:
            self.h = sm_open_device()["device"]
            sm_set_attenuator(self.h, SM_AUTO_ATTEN)
            sm_set_ref_level(self.h, 0.0)
            sm_set_IQ_base_sample_rate(self.h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
            sm_set_IQ_sample_rate(self.h, 1)
            sm_set_IQ_bandwidth(self.h, SM_FALSE, 41.5e6)
            sm_set_IQ_data_type(self.h, SM_DATA_TYPE_32_FC)

    def read(self, f):
        if self.dead:
            return "", "", ""
        try:
            self.open()
            return tuple(round(K.near(self.h, x), 2) for x in (f, 2 * f, 3 * f))
        except Exception as e:
            print(f"SM200B failed, carrying on with the scope only: {str(e)[:120]}", flush=True)
            self.close()
            self.dead = True
            return "", "", ""

    def close(self):
        try:
            if self.h is not None:
                sm_close_device(self.h)
        except Exception:
            pass
        self.h = None


def main():
    keep_awake(True)
    done = set()
    new = not OUT.exists()
    if not new:
        for r in csv.DictReader(open(OUT)):
            done.add((r["stage"], int(r["rep"]), r["_i"] if "_i" in r else None))
    counts = {}
    if not new:
        for r in csv.DictReader(open(OUT)):
            counts[(r["stage"], int(r["rep"]))] = counts.get((r["stage"], int(r["rep"])), 0) + 1
    scope = FineScope(1, VDIV)
    kitty = Kitty()

    def rd():
        try:
            return scope.read()
        except Exception:
            scope.drop()
            time.sleep(3)
            raise

    try:
        with open(OUT, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(COLS)
            for name, rep, pts, use_k, label in stages():
                if dt.datetime.now() > DEADLINE or STOP_FILE.exists():
                    print("deadline reached or stop file", flush=True)
                    break
                start = counts.get((name, rep), 0)
                if start >= len(pts):
                    continue
                print(f"{dt.datetime.now():%H:%M:%S} STAGE {name} rep {rep}: {label}, {len(pts)} points (from {start})", flush=True)
                q = 0
                for i, (f, want) in enumerate(pts):
                    if i < start:
                        continue
                    if dt.datetime.now() > DEADLINE or STOP_FILE.exists():
                        break
                    t0 = time.time()
                    if f <= 0:
                        tone_off()
                        att, inside = 89.75, True
                        time.sleep(0.5)
                    else:
                        att, inside = att_for(f, want)
                        retry(lambda: tone_on(f * 1e6, att, SCALE), f"tone {f}")
                        time.sleep(0.3)
                    m, sd, r = retry(rd, "scope")[0]
                    t1, t2, t3 = kitty.read(f) if (use_k and f > 0) else ("", "", "")
                    w.writerow([dt.datetime.now().isoformat(timespec="seconds"), name, rep, f, att, want, int(inside), m, sd, r, t1, t2, t3])
                    fh.flush()
                    if abs(m) * 1e3 > CLIP_MV or any(isinstance(x, float) and x > STOP_IF_DBM for x in (t1, t2, t3)):
                        print(f"STOP RULE at {f} MHz {want} dBm: {m*1e3:.1f} mV, IF {t1} {t2} {t3}", flush=True)
                        return
                    nq = (i + 1) * 4 // len(pts)
                    if nq != q and nq > 0:
                        print(f"{dt.datetime.now():%H:%M:%S} {name} rep {rep}: {nq*25}%", flush=True)
                    q = nq
                    if name in ("hold", "off"):
                        time.sleep(max(0.0, 5.0 - (time.time() - t0)))
        print(f"{dt.datetime.now():%H:%M:%S} ALL STAGES FINISHED", flush=True)
    except Exception:
        traceback.print_exc()
        raise
    finally:
        scope.drop()
        kitty.close()
        tone_off()
        keep_awake(False)
        print("tone off", flush=True)


if __name__ == "__main__":
    main()
