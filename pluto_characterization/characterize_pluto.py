"""Characterise this ADALM-Pluto's transmit output, with its TX port connected straight to the
Siglent SSA3021X spectrum analyzer. Every reading is appended to readings.csv as it is taken.

Sections: A power vs attenuation, B power vs frequency, C power vs tone scale, D frequency error,
E spectra around the tone and wide, F level and frequency over time, G analyzer reference-level check,
H output with the tone off.
"""
import csv
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pyvisa

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sdr"))
import pluto_cw as P  # noqa: E402

P.ATT_MIN_DB = 0.0  # only the analyzer is connected (safe to +30 dBm); the Pluto cannot exceed about +7 dBm
OUT = HERE / "readings.csv"
FIELDS = ["time", "section", "freq_set_hz", "att_db", "scale", "ref_level_dbm", "span_hz", "freq_meas_hz", "level_dbm", "note"]

a = pyvisa.ResourceManager().open_resource("USB0::0xF4EC::0x1300::SSA3XLBC3R0429::INSTR")
a.timeout = 20000
state = {"rl": None}


def ref_level(rl):
    if state["rl"] != rl:
        a.write(f":DISP:WIND:TRAC:Y:RLEV {rl}")
        state["rl"] = rl
        time.sleep(0.3)


def sweep(centre, span):
    a.write(":INIT:CONT OFF")
    a.write(f":FREQ:CENT {centre:.0f}")
    a.write(f":FREQ:SPAN {span:.0f}")
    time.sleep(0.25)
    sw = float(a.query(":SWE:TIME?"))
    a.write(":INIT:IMM")
    time.sleep(1.5 * sw + 0.3)
    a.query("*OPC?")


def peak(centre, span):
    sweep(centre, span)
    a.write(":CALC:MARK1:STAT ON")
    a.write(":CALC:MARK1:MAX")
    time.sleep(0.15)
    return float(a.query(":CALC:MARK1:X?")), float(a.query(":CALC:MARK1:Y?"))


def trace():
    return np.array([float(x) for x in a.query(":TRAC:DATA? 1").strip().strip(",").split(",")])


def log(section, fset, att, scale, span, f, p, note=""):
    with open(OUT, "a", newline="") as fh:
        csv.DictWriter(fh, fieldnames=FIELDS).writerow(dict(time=dt.datetime.now().isoformat(timespec="seconds"), section=section, freq_set_hz=fset,
                                                           att_db=att, scale=scale, ref_level_dbm=state["rl"], span_hz=span, freq_meas_hz=f, level_dbm=p, note=note))


DONE = set()   # (section, freq, att, scale) already in readings.csv, so a restarted run does not repeat them


def tone(fset, att, scale=0.5):
    """Set the tone. If the Pluto drops off USB, wait up to 2 minutes for it to come back and try again."""
    for attempt in range(12):
        try:
            P.tone_on(fset, att, scale=scale)
            return
        except RuntimeError as e:
            print("Pluto not answering, retry", attempt, str(e)[:80], flush=True)
            time.sleep(10)
    raise RuntimeError("Pluto did not come back")


def read_tone(section, fset, att, scale=0.5, span=2e6, note=""):
    if (section, float(fset), float(att), float(scale)) in DONE:
        return None, None
    tone(fset, att, scale=scale)
    time.sleep(0.5)
    f, p = peak(fset, span)
    log(section, fset, att, scale, span, f, p, note)
    return f, p


def main():
    if OUT.exists():
        for r in csv.DictReader(open(OUT)):
            DONE.add((r["section"], float(r["freq_set_hz"]), float(r["att_db"]), float(r["scale"])))
        print("resuming;", len(DONE), "readings already saved", flush=True)
    else:
        with open(OUT, "w", newline="") as fh:
            csv.DictWriter(fh, fieldnames=FIELDS).writeheader()
    try:
        ref_level(10)
        # A. power vs attenuation
        fine = list(range(0, 41)) + [45, 50, 55, 60, 65, 70]
        for fset in (1.0e9, 1.1e9, 1.2e9):
            for att in fine:
                read_tone("A_att_fine", fset, att)
            print("A fine done", fset / 1e6, flush=True)
        coarse = [0, 2, 4, 6, 8, 10, 15, 20, 30, 40]
        for fset in (0.4e9, 0.6e9, 0.8e9, 0.9e9, 1.05e9, 1.15e9, 1.4e9, 1.6e9, 1.8e9, 2.0e9):
            for att in coarse:
                read_tone("A_att_coarse", fset, att)
        print("A coarse done", flush=True)
        # B. power vs frequency at 20 dB and at 0 dB
        freqs = sorted(set(list(np.arange(350e6, 2.1e9 + 1, 25e6)) + list(np.arange(1.0e9, 1.2e9 + 1, 10e6))))
        for att in (20, 0):
            for fset in freqs:
                read_tone("B_freq", float(fset), att)
            print("B done att", att, flush=True)
        # C. power vs tone scale (digital amplitude)
        for sc in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            read_tone("C_scale", 1.1e9, 20, scale=sc)
            read_tone("C_scale", 1.1e9, 0, scale=sc)
        print("C done", flush=True)
        # D. frequency error, narrow span
        for fset in (0.4e9, 0.7e9, 1.0e9, 1.1e9, 1.2e9, 1.5e9, 1.8e9, 2.0e9):
            tone(fset, 20)
            time.sleep(0.5)
            f, _ = peak(fset, 200e3)
            f, p = peak(f, 20e3)
            log("D_freq_error", fset, 20, 0.5, 20e3, f, p)
        print("D done", flush=True)
        # E. spectra
        for fset in (1.0e9, 1.1e9, 1.2e9):
            for att in (20, 0):
                tone(fset, att)
                time.sleep(0.5)
                for span, name in ((10e6, "close"), (200e6, "mid")):
                    sweep(fset, span)
                    tr = trace()
                    fr = fset + span * (np.arange(len(tr)) / (len(tr) - 1) - 0.5)
                    np.savetxt(HERE / f"spectrum_{name}_{fset/1e6:.0f}MHz_att{att}.csv", np.column_stack([fr, tr]), delimiter=",", header="freq_hz,level_dbm", comments="")
                sweep(1.05e9, 2.1e9)
                tr = trace()
                np.savetxt(HERE / f"spectrum_wide_{fset/1e6:.0f}MHz_att{att}.csv", np.column_stack([np.linspace(0, 2.1e9, len(tr)), tr]), delimiter=",", header="freq_hz,level_dbm", comments="")
                if fset == 1.0e9:
                    f2, p2 = peak(2 * fset, 2e6)
                    log("E_harmonic2", fset, att, 0.5, 2e6, f2, p2, "second harmonic of the 1.0 GHz tone")
        print("E done", flush=True)
        # F. stability over about 3 minutes
        tone(1.1e9, 20)
        time.sleep(0.5)
        for i in range(40):
            f, _ = peak(1.1e9, 200e3)
            f, p = peak(f, 20e3)
            log("F_stability", 1.1e9, 20, 0.5, 20e3, f, p)
            time.sleep(2.0)
        print("F done", flush=True)
        # G. the analyzer's own reading against its reference-level setting
        tone(1.1e9, 20)
        time.sleep(0.5)
        for rl in (-10, 0, 10, 20, 10):
            ref_level(rl)
            f, p = peak(1.1e9, 2e6)
            log("G_ref_level", 1.1e9, 20, 0.5, 2e6, f, p)
        # repeat of one setting after everything else
        ref_level(10)
        for att in (40, 20, 0, 20, 40):
            read_tone("G_repeat", 1.1e9, att)
        # H. tone off: what leaks out at the carrier frequency
        for att in (0, 10, 31):
            tone(1.1e9, att, scale=0.0)
            time.sleep(0.5)
            f, p = peak(1.1e9, 10e6)
            log("H_tone_off", 1.1e9, att, 0.0, 10e6, f, p, "tone scale 0, carrier leakage")
        print("all done", flush=True)
    finally:
        P.ATT_MIN_DB = 31.0
        try:
            P.tone_off()
        except RuntimeError as e:
            print("could not turn the tone off:", str(e)[:80], flush=True)
        a.write(":DISP:WIND:TRAC:Y:RLEV 10")
        a.write(":INIT:CONT ON")
        a.close()


if __name__ == "__main__":
    main()
