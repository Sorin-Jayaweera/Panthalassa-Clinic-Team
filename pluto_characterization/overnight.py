"""Overnight characterisation of the Pluto TX output. Wiring: Pluto TX straight into the spectrum analyzer
(Siglent SSA3021X). Nothing else connected, so the Pluto may be set to any level (its maximum, about +7 dBm,
is far below the analyzer's +30 dBm limit).

Every reading is appended to overnight_readings.csv as it is taken. Traces go to traces/. Finished blocks are
listed in overnight_done.txt, and a restart skips them and skips readings already saved in an unfinished block.
A reference check (three frequencies, two levels, tone frequency, Pluto temperature) runs every 10 minutes
between other readings. The run stops itself at STOP_AT.
"""
import csv
import ctypes
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pyvisa

HERE = Path(__file__).resolve().parent
OUT = HERE / "overnight_readings.csv"
DONEF = HERE / "overnight_done.txt"
TR = HERE / "traces"
TR.mkdir(exist_ok=True)
IIO_ATTR = r"C:\Users\Sorin\radioconda\Library\bin\iio_attr.exe"
IIO_INFO = r"C:\Users\Sorin\radioconda\Library\bin\iio_info.exe"
URI = "ip:192.168.2.1"
VISA = "USB0::0xF4EC::0x1300::SSA3XLBC3R0429::INSTR"
STOP_AT = dt.datetime(2026, 10, 13, 7, 20)
FIELDS = ["time", "block", "freq_set_hz", "att_db", "scale", "offset_hz", "ref_level_dbm", "rbw_hz", "span_hz", "preamp",
          "read_centre_hz", "freq_meas_hz", "level_dbm", "pluto_temp_c", "note"]


class Stop(Exception):
    pass


def say(*a):
    print(dt.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------ Pluto
pl = {}          # what the Pluto is currently set to


def attr(*args):
    """One iio_attr call. If the Pluto does not answer, wait and retry until it does (it has dropped off USB before)."""
    n = 0
    while True:
        try:
            r = subprocess.run([IIO_ATTR, "-u", URI, *args], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                if n:
                    say("Pluto answering again after", n, "tries")
                    pl.clear()
                    raise ConnectionResetError
                return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            err = (r.stderr.strip() or r.stdout.strip())[:100]
        except subprocess.TimeoutExpired:
            err = "timeout"
        n += 1
        if n in (1, 10) or n % 60 == 0:
            say("Pluto not answering:", err, "(try", n, ")")
        if dt.datetime.now() > STOP_AT:
            raise Stop
        time.sleep(20)


DDS = "cf-ad9361-dds-core-lpc"


def pluto(freq, att, scale=0.5, offset=1e6, scale2=0.0, offset2=2e6):
    """Tone at freq = LO + offset. Optional second tone at LO + offset2. A negative offset puts the tone below the LO."""
    want = dict(lo=int(round(freq - offset)), att=min(89.75, round(att * 4) / 4), scale=scale, offset=int(offset), scale2=scale2, offset2=int(offset2))
    for _ in range(5):
        try:
            changed = False
            if pl.get("lo") != want["lo"]:
                attr("-c", "ad9361-phy", "altvoltage1", "frequency", str(want["lo"]))
                changed = True
            if (pl.get("offset"), pl.get("scale")) != (want["offset"], want["scale"]):
                neg = want["offset"] < 0
                for ch, phase in (("altvoltage0", 0 if neg else 90000), ("altvoltage2", 90000 if neg else 0)):      # I and Q of tone 1
                    attr("-c", DDS, ch, "frequency", str(abs(want["offset"])))
                    attr("-c", DDS, ch, "phase", str(phase))
                    attr("-c", DDS, ch, "scale", str(want["scale"]))
                    attr("-c", DDS, ch, "raw", "1")
                changed = True
            if (pl.get("offset2"), pl.get("scale2")) != (want["offset2"], want["scale2"]):
                for ch, phase in (("altvoltage1", 90000), ("altvoltage3", 0)):                                         # I and Q of tone 2
                    attr("-c", DDS, ch, "frequency", str(abs(want["offset2"])))
                    attr("-c", DDS, ch, "phase", str(phase))
                    attr("-c", DDS, ch, "scale", str(want["scale2"]))
                changed = True
            if pl.get("att") != want["att"]:
                attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain", f"{-want['att']}")
                time.sleep(0.15)
            pl.update(want)
            if changed:
                time.sleep(0.35)
            return
        except ConnectionResetError:
            continue
    raise RuntimeError("could not set the Pluto")


def temp():
    try:
        return float(attr("-c", "ad9361-phy", "temp0", "input").split()[0]) / 1000
    except Exception:
        return float("nan")


# ------------------------------------------------------------------ spectrum analyzer
an = {}
A = None


def an_open():
    global A
    A = pyvisa.ResourceManager().open_resource(VISA)
    A.timeout = 60000
    an.clear()
    A.write(":INIT:CONT OFF")


def an_do(fn):
    for n in range(40):
        try:
            return fn()
        except Exception as e:                       # analyzer USB hiccup: reopen and retry
            say("analyzer error:", str(e)[:80])
            time.sleep(15)
            try:
                A.close()
            except Exception:
                pass
            try:
                an_open()
            except Exception as e2:
                say("reopen failed:", str(e2)[:80])
    raise RuntimeError("analyzer not answering")


def an_set(centre=None, span=None, rl=None, rbw=None, preamp=None, start=None, stop=None):
    if rl is not None and an.get("rl") != rl:
        A.write(f":DISP:WIND:TRAC:Y:RLEV {rl}")
        an["rl"] = rl
        time.sleep(0.3)
    if preamp is not None and an.get("preamp") != preamp:
        A.write(f":POW:GAIN {'ON' if preamp else 'OFF'}")
        an["preamp"] = preamp
        time.sleep(0.3)
    if start is not None:
        A.write(f":FREQ:STAR {start:.0f}")
        A.write(f":FREQ:STOP {stop:.0f}")
        an["centre"], an["span"] = (start + stop) / 2, stop - start
    else:
        # The analyzer stops at 2.1 GHz. A span that would run past it gets shortened by the analyzer without saying so
        # (this spoiled the first tone-scale-1.0 map), so keep the whole span inside the range and always send both values.
        if centre + span / 2 > 2.1e9:
            centre = 2.1e9 - span / 2
        A.write(f":FREQ:CENT {centre:.0f}")
        A.write(f":FREQ:SPAN {span:.0f}")
        A.write(f":FREQ:CENT {centre:.0f}")
        an["centre"], an["span"] = centre, span
    if an.get("rbw", "x") != rbw:
        A.write(":BWID:AUTO ON" if rbw is None else f":BWID {rbw:.0f}")
        an["rbw"] = rbw
    time.sleep(0.12)


def sweep():
    sw = float(A.query(":SWE:TIME?"))
    A.write(":INIT:IMM")
    time.sleep(1.3 * sw + 0.2)
    A.query("*OPC?")


def peak():
    A.write(":CALC:MARK1:STAT ON")
    A.write(":CALC:MARK1:MAX")
    time.sleep(0.1)
    return float(A.query(":CALC:MARK1:X?")), float(A.query(":CALC:MARK1:Y?"))


def trace():
    y = np.array([float(x) for x in A.query(":TRAC:DATA? 1").strip().strip(",").split(",")])
    f = an["centre"] + an["span"] * (np.arange(len(y)) / (len(y) - 1) - 0.5)
    return f, y


def save_trace(name, f, y):
    np.savetxt(TR / f"{name}.csv", np.column_stack([f, y]), delimiter=",", header="freq_hz,level_dbm", comments="", fmt=["%.0f", "%.3f"])


# ------------------------------------------------------------------ logging and resume
SAVED = set()
BLOCKS_DONE = set()
last_ref = [0.0]
in_ref = [False]
last_temp = [float("nan"), 0.0]


def key(block, f, att, scale, offset, note):
    return (block, f"{float(f):.0f}", f"{float(att):.2f}", f"{float(scale):.3f}", f"{float(offset):.0f}", note)


def log(block, f, att, scale, offset, read_centre, fm, lv, note=""):
    if time.time() - last_temp[1] > 60:
        last_temp[0], last_temp[1] = temp(), time.time()
    with open(OUT, "a", newline="") as fh:
        csv.DictWriter(fh, fieldnames=FIELDS).writerow(dict(
            time=dt.datetime.now().isoformat(timespec="seconds"), block=block, freq_set_hz=f"{f:.0f}", att_db=att, scale=scale, offset_hz=f"{offset:.0f}",
            ref_level_dbm=an.get("rl"), rbw_hz="auto" if an.get("rbw") is None else an.get("rbw"), span_hz=f"{an.get('span'):.0f}", preamp=int(bool(an.get("preamp"))),
            read_centre_hz=f"{read_centre:.0f}", freq_meas_hz=f"{fm:.0f}", level_dbm=f"{lv:.3f}", pluto_temp_c=f"{last_temp[0]:.2f}", note=note))
    SAVED.add(key(block, f, att, scale, offset, note))


def measure(block, f, att, scale=0.5, offset=1e6, span=2e6, rl=10, rbw=None, preamp=False, read_at=None, note="", scale2=0.0, offset2=2e6, resume=True):
    """Set the Pluto, sweep, read the peak near read_at (default: the tone), save. Returns (frequency, level)."""
    if resume and key(block, f, att, scale, offset, note) in SAVED:
        return None
    if dt.datetime.now() > STOP_AT:
        raise Stop
    maybe_ref()
    pluto(f, att, scale, offset, scale2, offset2)
    c = f if read_at is None else read_at

    def go():
        an_set(c, span, rl, rbw, preamp)
        sweep()
        return peak()
    fm, lv = an_do(go)
    log(block, f, att, scale, offset, c, fm, lv, note)
    return fm, lv


def tone_freq(f, att=20, block="ref_freq", note=""):
    """Tone frequency: find the peak in 200 kHz, then read it in a 10 kHz span."""
    pluto(f, att)

    def go():
        an_set(f, 200e3, 10, None, False)
        sweep()
        f1, _ = peak()
        an_set(f1, 10e3, 10, None, False)
        sweep()
        return peak()
    fm, lv = an_do(go)
    if lv < -70 + (0 if att <= 40 else -40):        # no tone found: wait and try once more
        time.sleep(2)
        fm, lv = an_do(go)
        note = (note + " retried").strip()
    log(block, f, att, 0.5, 1e6, f, fm, lv, note)
    return fm, lv


def maybe_ref(force=False):
    """Every 10 minutes: the same six readings, so drift of the Pluto or the analyzer through the night is on record."""
    if in_ref[0] or (not force and time.time() - last_ref[0] < 600):
        return
    in_ref[0] = True
    try:
        last_temp[1] = 0
        for f in (1.0e9, 1.1e9, 1.2e9):
            for att in (20, 0):
                measure("ref", f, att, span=200e3, rbw=3e3, resume=False)
        tone_freq(1.1e9)
        last_ref[0] = time.time()
    finally:
        in_ref[0] = False


def block(name):
    def deco(fn):
        def run():
            if name in BLOCKS_DONE:
                return
            say("start", name)
            t0 = time.time()
            fn()
            with open(DONEF, "a") as fh:
                fh.write(name + "\n")
            BLOCKS_DONE.add(name)
            say("done", name, f"{(time.time()-t0)/60:.1f} min")
        run.__name__ = name
        return run
    return deco


# ------------------------------------------------------------------ blocks
@block("state_dump")
def b_state():
    r = subprocess.run([IIO_INFO, "-u", URI], capture_output=True, text=True, timeout=120)
    (HERE / "pluto_iio_info.txt").write_text(r.stdout, encoding="utf-8")


@block("analyzer_floor")
def b_floor():
    """Analyzer reading with the Pluto at maximum attenuation and no tone, for each analyzer setting used tonight."""
    pluto(1.1e9, 89.75, scale=0.0)
    for rl, pre, rbw, span in ((10, False, None, 2e6), (10, False, 3e3, 200e3), (10, False, None, 10e6), (-10, False, 1e3, 100e3), (-30, True, 1e3, 100e3), (-30, True, 100, 10e3)):
        for f in (0.4e9, 1.0e9, 1.1e9, 1.2e9, 2.0e9):
            def go():
                an_set(f, span, rl, rbw, pre)
                sweep()
                fr, y = trace()
                return fr[np.argmax(y)], float(np.median(y)), float(y.max())
            fm, med, mx = an_do(go)
            log("analyzer_floor", f, 89.75, 0.0, 1e6, f, fm, med, "median of trace, tone off")
            log("analyzer_floor", f, 89.75, 0.0, 1e6, f, fm, mx, "maximum of trace, tone off")


@block("map_scale0p5")
def b_map():
    """Output at every 10 MHz from 350 to 2100 MHz, at nine attenuation settings."""
    for f in np.arange(350e6, 2100e6 + 1, 10e6):
        for att in (40, 35, 30, 25, 20, 15, 10, 5, 0):
            measure("map", float(f), att)


@block("fine_steps")
def b_fine():
    """0.25 dB attenuation steps from 0 to 12 dB, down then up, narrow bandwidth for low scatter."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        steps = list(np.arange(12, -0.01, -0.25))
        for d, seq in (("down", steps), ("up", steps[::-1])):
            for att in seq:
                measure("fine_steps", f, float(att), span=200e3, rbw=3e3, note=d)
    for att in np.arange(20, 30.01, 0.25):
        measure("fine_steps", 1.1e9, float(att), span=200e3, rbw=3e3, note="20to30")


@block("low_level")
def b_low():
    """Extend the level table down to the lowest settings, using a lower reference level, the preamp and a narrow bandwidth.
    Each analyzer setting overlaps the one before, so the readings can be tied together."""
    for f in (1.1e9, 1.0e9, 1.2e9, 0.4e9, 2.0e9):
        for att in range(0, 51, 5):
            measure("low_level", f, att, span=100e3, rbw=1e3, rl=10, note="rl+10")
        for att in range(20, 71, 5):
            measure("low_level", f, att, span=100e3, rbw=1e3, rl=-10, note="rl-10")
        for att in list(np.arange(40, 89.76, 2.5)) + [89.75]:
            measure("low_level", f, float(att), span=100e3, rbw=1e3, rl=-30, preamp=True, note="rl-30 preamp")
        for att in list(np.arange(60, 89.76, 2.5)) + [89.75]:
            fm = measure("low_level", f, 40, span=100e3, rbw=1e3, rl=-30, preamp=True, note=f"find tone for {att}", resume=False)
            measure("low_level", f, float(att), span=10e3, rbw=100, rl=-30, preamp=True, read_at=fm[0], note="rl-30 preamp rbw100")
    an_do(lambda: an_set(1.1e9, 2e6, 10, None, False))


@block("tone_scale")
def b_scale():
    scales = (0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0)
    for f in (1.1e9, 1.0e9, 1.2e9, 0.4e9, 2.0e9):
        for att in (20, 0):
            for s in scales:
                measure("tone_scale", f, att, scale=s, span=200e3, rbw=3e3)
    for att in (20, 0):                      # spectrum close to the tone at each scale: distortion made by the digital side
        for s in scales:
            if key("tone_scale_trace", 1.1e9, att, s, 1e6, "") in SAVED:
                continue
            measure("tone_scale_trace", 1.1e9, att, scale=s, span=12e6, rbw=30e3)
            fr, y = an_do(trace)
            save_trace(f"scale_{s:.2f}_att{att}_1100MHz", fr, y)


@block("harmonics")
def b_harm():
    for f in np.arange(350e6, 1050e6 + 1, 50e6):
        for s in (0.5, 1.0):
            for att in (20, 10, 0):
                measure("harmonics", float(f), att, scale=s, note="fundamental")
                measure("harmonics", float(f), att, scale=s, read_at=2 * f, note="2f")
                if 3 * f <= 2.1e9:
                    measure("harmonics", float(f), att, scale=s, read_at=3 * f, note="3f")
                if 3 * (f - 1e6) - 2e6 <= 2.1e9:     # third harmonic of the LO mixes the tone to 3 LO - offset
                    measure("harmonics", float(f), att, scale=s, read_at=3 * (f - 1e6) - 1e6, span=6e6, note="near 3 LO")


@block("close_lines")
def b_close():
    """Lines close to the tone at every 50 MHz: LO leakage (1 MHz below), other sideband (2 MHz below), and others."""
    for f in np.arange(350e6, 2100e6 + 1, 50e6):
        for att in (20, 0):
            if key("close_lines", f, att, 0.5, 1e6, "tone") in SAVED:
                continue
            pluto(float(f), att)
            maybe_ref()
            pluto(float(f), att)

            def go():
                an_set(float(f) - 1e6, 12e6, 10, 30e3, False)
                sweep()
                return trace()
            fr, y = an_do(go)
            save_trace(f"close_{f/1e6:.0f}MHz_att{att}", fr, y)
            for lab, off in (("LO, 1 MHz below", -1e6), ("other sideband, 2 MHz below", -2e6), ("1 MHz above", 1e6), ("2 MHz above", 2e6),
                             ("3 MHz below", -3e6), ("4 MHz below", -4e6), ("tone", 0.0)):
                m = np.abs(fr - (f + off)) < 0.2e6
                k = np.argmax(np.where(m, y, -999))
                log("close_lines", float(f), att, 0.5, 1e6, f + off, fr[k], y[k], lab)


@block("tone_offset")
def b_offset():
    """Move the tone away from the LO (LO fixed at 1100 MHz): output level, LO leakage and the other sideband against offset."""
    lo = 1.1e9
    for att in (20, 0):
        for off in (0.1e6, 0.2e6, 0.5e6, 1e6, 2e6, 3e6, 4e6, 5e6, 6e6, 7e6, 8e6, 9e6, 10e6, 12e6, 14e6, -0.5e6, -1e6, -2e6, -5e6, -9e6):
            sp, rb = (200e3, 3e3) if abs(off) >= 0.5e6 else (50e3, 1e3)
            measure("tone_offset", lo + off, att, offset=off, span=sp, rbw=rb, note="tone")
            measure("tone_offset", lo + off, att, offset=off, span=sp, rbw=rb, read_at=lo - off, note="other sideband")
            measure("tone_offset", lo + off, att, offset=off, span=sp, rbw=rb, read_at=lo, note="LO")
    pluto(1.1e9, 20)


@block("two_tone")
def b_two():
    """Two tones 1 MHz apart (2 and 3 MHz above the LO). The third-order products fall 1 and 4 MHz above the LO."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        lo = f - 2e6
        for s in (0.1, 0.25, 0.4, 0.5):
            for att in (20, 10, 5, 0):
                for lab, off in (("tone 1", 2e6), ("tone 2", 3e6), ("third-order low", 1e6), ("third-order high", 4e6), ("LO", 0.0)):
                    measure("two_tone", f, att, scale=s, offset=2e6, scale2=s, offset2=3e6, span=100e3, rbw=1e3, read_at=lo + off, note=lab)
    pluto(1.1e9, 20)


@block("retune_repeat")
def b_retune():
    rng = np.random.default_rng(1)
    for i in range(30):
        other = float(rng.choice(np.arange(400e6, 2000e6, 100e6)))
        measure("retune_repeat", other, 20, span=200e3, rbw=3e3, note=f"away {i}", resume=False)
        measure("retune_repeat", 1.1e9, 20, span=200e3, rbw=3e3, note=f"back {i}", resume=False)
    for i in range(30):
        measure("retune_repeat", 1.1e9, 0, span=200e3, rbw=3e3, note=f"att0 {i}", resume=False)
        measure("retune_repeat", 1.1e9, 40, span=200e3, rbw=3e3, note=f"att40 {i}", resume=False)
        measure("retune_repeat", 1.1e9, 20, span=200e3, rbw=3e3, note=f"att20 {i}", resume=False)


@block("settling")
def b_settle():
    """Level against time at one frequency (zero span) while the Pluto is retuned or its attenuation changed."""
    for kind in ("retune", "att"):
        for i in range(6):
            if kind == "retune":
                pluto(0.9e9, 20)
            else:
                pluto(1.1e9, 40)
            time.sleep(1.0)

            def go():
                an_set(1.1e9 - 13e3, 0, 10, 300e3, False)
                A.write(":SWE:TIME 4")
                time.sleep(0.3)
                A.write(":INIT:IMM")
                time.sleep(1.0)
                pluto(1.1e9, 20)
                time.sleep(3.6)
                A.query("*OPC?")
                y = np.array([float(x) for x in A.query(":TRAC:DATA? 1").strip().strip(",").split(",")])
                return y
            y = an_do(go)
            save_trace(f"settle_{kind}_{i}", np.linspace(0, 4, len(y)) * 1e6, y)       # first column is time in microseconds
            log("settling", 1.1e9, 20, 0.5, 1e6, 1.1e9, 1.1e9, float(np.median(y[-50:])), f"{kind} {i}: final level; trace saved, time axis in microseconds")
    an_do(lambda: (A.write(":SWE:TIME:AUTO ON"), an.clear(), A.write(":INIT:CONT OFF")))


@block("wide_search")
def b_wide():
    """0 to 2.1 GHz with the tone at each 100 MHz: the five largest lines other than the tone."""
    for att in (0, 20):
        for f in np.arange(400e6, 2000e6 + 1, 100e6):
            if key("wide_search", f, att, 0.5, 1e6, "tone") in SAVED:
                continue
            pluto(float(f), att)
            maybe_ref()
            pluto(float(f), att)

            def go():
                an_set(start=1e6, stop=2.1e9, rl=10, rbw=100e3, preamp=False)
                sweep()
                return trace()
            fr, y = an_do(go)
            save_trace(f"wide_{f/1e6:.0f}MHz_att{att}", fr, y)
            k0 = np.argmax(np.where(np.abs(fr - f) < 20e6, y, -999))
            yy = np.where((np.abs(fr - f) < 20e6) | (fr < 20e6), -999, y)
            for j in range(5):
                k = int(np.argmax(yy))
                log("wide_search", float(f), att, 0.5, 1e6, fr[k], fr[k], y[k], f"line {j+1}")
                yy[np.abs(fr - fr[k]) < 15e6] = -999
            log("wide_search", float(f), att, 0.5, 1e6, f, fr[k0], y[k0], "tone")
    pluto(1.1e9, 89.75, scale=0.0)
    fr, y = an_do(lambda: (an_set(start=1e6, stop=2.1e9, rl=10, rbw=100e3, preamp=False), sweep(), trace())[2])
    save_trace("wide_tone_off", fr, y)


@block("map_scale1p0_redo")
def b_map1():
    """The first attempt (block name map_scale1 in the readings) was taken with a wrong analyzer span and is not used."""
    for f in np.arange(350e6, 2100e6 + 1, 25e6):
        for att in (20, 10, 0):
            measure("map_s1", float(f), att, scale=1.0)
    for f in (2090e6, 2100e6):
        for att in (40, 35, 30, 25, 20, 15, 10, 5, 0):
            measure("map_edge", f, att)


# ------------------------------------------------------------------ second set of blocks (added 22:30 on 12 Oct)
def an_for(level):
    """Analyzer reference level and preamp for a tone of about this level (dBm)."""
    if level > -12:
        return 10, False
    if level > -32:
        return -10, False
    return -30, True


@block("leak_vs_level")
def b_leak():
    """LO leakage and other sideband against attenuation setting and tone scale, with a 300 Hz bandwidth."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        lo = f - 1e6
        for att in (0, 10, 20, 30, 40, 50, 60):
            for s in (1.0, 0.5, 0.2, 0.1, 0.05, 0.02):
                rl, pre = an_for(6 - att + 20 * np.log10(s))
                for lab, c in (("tone", f), ("LO", lo), ("other sideband", lo - 1e6)):
                    measure("leak_vs_level", f, att, scale=s, span=50e3, rbw=300, rl=rl, preamp=pre, read_at=c * (1 - 12.8e-6), note=lab)


@block("close_in")
def b_closein():
    """Spectrum close to the tone at four spans, and the same spans with the tone off."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        for att in (0, 20):
            if key("close_in", f, att, 0.5, 1e6, "span 1000") in SAVED:
                continue
            maybe_ref()
            fm, _ = tone_freq(f, att, block="close_in_find")
            for span, rbw in ((1e6, 3e3), (100e3, 300), (10e3, 30), (1e3, 10)):
                def go():
                    an_set(fm, span, 10, rbw, False)
                    sweep()
                    return trace()
                fr, y = an_do(go)
                save_trace(f"closein_{f/1e6:.0f}MHz_att{att}_span{span:.0f}", fr, y)
                log("close_in", f, att, 0.5, 1e6, fm, fr[np.argmax(y)], y.max(), f"span {span:.0f}")
    pluto(1.1e9, 89.75, scale=0.0)
    for span, rbw in ((1e6, 3e3), (100e3, 300), (10e3, 30), (1e3, 10)):
        fr, y = an_do(lambda: (an_set(1.1e9, span, 10, rbw, False), sweep(), trace())[2])
        save_trace(f"closein_tone_off_span{span:.0f}", fr, y)


@block("offset_more")
def b_offset2():
    """Tone offset test at four more LO frequencies."""
    for lo in (1.0e9, 1.2e9, 0.4e9, 2.0e9):
        for off in (0.5e6, 1e6, 2e6, 5e6, 8e6, 10e6, -1e6, -5e6):
            for lab, c in (("tone", lo + off), ("other sideband", lo - off), ("LO", lo)):
                measure("offset_more", lo + off, 0, offset=off, span=100e3, rbw=1e3, read_at=c * (1 - 12.8e-6), note=lab)
    pluto(1.1e9, 20)


@block("low_more")
def b_low2():
    """Low-level readings at every 100 MHz, fewer settings than the first low-level block."""
    for f in np.arange(500e6, 1900e6 + 1, 100e6):
        if f in (1.0e9, 1.1e9, 1.2e9):
            continue
        for att in (0, 10, 20, 30, 40):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=10, note="rl+10")
        for att in (20, 30, 40, 50, 60):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=-10, note="rl-10")
        for att in (40, 50, 60, 70, 80, 89.75):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=-30, preamp=True, note="rl-30 preamp")
    an_do(lambda: an_set(1.1e9, 2e6, 10, None, False))


@block("tune_step")
def b_tunestep():
    """Ask for small frequency changes and read what the tone does."""
    for base in (1.1e9, 1.0e9):
        for k in (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 0):
            pluto(base + k, 20)

            def go():
                an_set(base * (1 - 12.8e-6), 20e3, 10, None, False)
                sweep()
                f1, _ = peak()
                an_set(f1, 1e3, 10, 10, False)
                sweep()
                return peak()
            fm, lv = an_do(go)
            log("tune_step", base + k, 20, 0.5, 1e6, base, fm, lv, f"asked +{k} Hz")
            maybe_ref()


@block("if_band_map")
def b_ifband():
    """Level table for the IF band: every 1 MHz from 1000 to 1200 MHz, attenuation 0 to 40 dB in 2 dB steps."""
    for f in np.arange(1000e6, 1200e6 + 1, 1e6):
        for att in range(40, -1, -2):
            measure("if_band", float(f), att, span=200e3, rbw=3e3)


@block("if_band_scale")
def b_ifscale():
    """Tone scale 0.1 to 1.0 at every 10 MHz in the IF band, at 0, 10 and 20 dB."""
    for f in np.arange(1000e6, 1200e6 + 1, 10e6):
        for att in (20, 10, 0):
            for s in (0.1, 0.2, 0.3, 0.5, 0.7, 1.0):
                measure("if_band_scale", float(f), att, scale=s, span=200e3, rbw=3e3)


def hourly(tag):
    """Repeat of the level table and a coarse frequency sweep, to see how much they move through the night."""
    for att in range(40, -1, -2):
        for f in (1.0e9, 1.1e9, 1.2e9):
            measure("hourly_att", f, att, span=200e3, rbw=3e3, note=tag, resume=False)
    for f in np.arange(350e6, 2100e6 + 1, 50e6):
        measure("hourly_freq", float(f), 20, span=200e3, rbw=3e3, note=tag, resume=False)
    for f in (0.4e9, 0.7e9, 1.0e9, 1.2e9, 1.5e9, 1.8e9, 2.0e9):
        tone_freq(f, block="hourly_tonefreq", note=tag)


def drift():
    """Until the stop time: level and frequency at 1100 MHz every 30 s, with the 10-minute reference checks and an hourly repeat."""
    say("start drift")
    last_hour = 0.0
    n = 0
    while True:
        if dt.datetime.now() > STOP_AT:
            raise Stop
        if time.time() - last_hour > 3600:
            hourly(dt.datetime.now().strftime("%H:%M"))
            last_hour = time.time()
        maybe_ref()
        measure("drift", 1.1e9, 20, span=200e3, rbw=3e3, resume=False)
        tone_freq(1.1e9, block="drift_freq")
        n += 1
        time.sleep(22)


def main():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)      # keep the computer from idle-sleeping while this runs
    if OUT.exists():
        for r in csv.DictReader(open(OUT)):
            SAVED.add(key(r["block"], r["freq_set_hz"], r["att_db"], r["scale"], r["offset_hz"], r["note"]))
    else:
        with open(OUT, "w", newline="") as fh:
            csv.DictWriter(fh, fieldnames=FIELDS).writeheader()
    if DONEF.exists():
        BLOCKS_DONE.update(DONEF.read_text().split())
    say("start; saved readings", len(SAVED), "blocks done", sorted(BLOCKS_DONE))
    an_open()
    try:
        maybe_ref(force=True)
        for b in (b_state, b_floor, b_fine, b_low, b_scale, b_offset, b_two, b_close, b_harm, b_retune, b_settle, b_wide, b_map, b_map1,
                  b_leak, b_closein, b_offset2, b_tunestep, b_low2, b_ifscale, b_ifband):
            try:
                b()
            except Stop:
                raise
            except Exception as e:                      # one failed block must not stop the night
                say("BLOCK FAILED", b.__name__, repr(e)[:200])
                an.clear()
                pl.clear()
                try:
                    A.write(":SWE:TIME:AUTO ON")
                except Exception:
                    pass
        drift()
    except Stop:
        say("stop time reached")
    finally:
        try:
            attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain", "-89.75")
            for ch in ("altvoltage0", "altvoltage1", "altvoltage2", "altvoltage3"):
                attr("-c", DDS, ch, "scale", "0")
        except BaseException as e:
            say("could not turn the tone off:", repr(e)[:80])
        try:
            A.write(":SWE:TIME:AUTO ON")
            A.write(":POW:GAIN OFF")
            A.write(":BWID:AUTO ON")
            A.write(":DISP:WIND:TRAC:Y:RLEV 10")
            A.write(":FREQ:CENT 1.1e9")
            A.write(":FREQ:SPAN 10e6")
            A.write(":INIT:CONT ON")
            A.close()
        except Exception as e:
            say("analyzer restore failed:", repr(e)[:80])
        say("finished")


if __name__ == "__main__":
    main()
