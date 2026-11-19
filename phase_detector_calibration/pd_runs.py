"""One table of the phase detector's high-density runs (run_pd_overnight.py with HD_NIGHT=1, HD_TAG=tag), shared by every plot.
A new bench configuration = one more row here; the plot scripts loop over RUNS and need no change.
Data: pd_dither_14nov.csv, stages <tag>_pri, <tag>_rest, <tag>_rep; tone-off readings are stage "off" with rep in OFF_REPS."""
import csv
from pathlib import Path

import matplotlib
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "pd_dither_14nov.csv"
LEVELS = (-36.0, -50.0, -57.0)
LEVEL_COLOURS = dict(zip(LEVELS, ("#440154", "#21918c", "#5ec962")))

# Lengths (Sorin, 18 Nov): B 15.2 cm, D 16.6 cm, E with its adapter about 9 cm (the adapter was on in every run)
ARMS_E = ["right arm (LO): cable D (16.6 cm)\nno pad", "left arm (RF): cable B (15.2 cm) + E with adapter (~9 cm)\nRF - LO = 7.6 cm, no pad"]
ARMS_EQ = ["right arm (LO): cable D (16.6 cm)\nno pad", "left arm (RF): cable B (15.2 cm)\nRF - LO = -1.4 cm, no pad"]
ARMS_ELO = ["right arm (LO, splitter port 2): cable D (16.6 cm)\n+ cable E with adapter (about 9 cm), no pad", "left arm (RF, splitter port 1): cable B (15.2 cm)\nRF - LO = -10.4 cm, no pad"]
ARMS_PAD10 = ["port 2: cable D (16.6 cm)\n+ 10 dB pad -> mixer LO", "port 1: cable B (15.2 cm)\n+ 10 dB pad -> mixer RF"]
ARMS_SHORT = ["right arm (LO): very short cable\nno pad", "left arm (RF): very short cable\nno pad"]

# off: tone-off reps [lo, hi); region: one-to-one stretch for the resolution analysis (None = automatic)
RUNS = [
    dict(tag="hdr", day="15 Nov", desc="cable E arm, long IF cable to the scope (and SM200B)", arms=ARMS_E,
         ifl="long cable", inp="1 Mohm", off=(81, 91), ls="--", col="#555555", detail="pd_hd_night_15nov.png", region=(1340, 1480)),
    dict(tag="ifs", day="15 Nov", desc="cable E arm, short IF cable (~16 cm SMA + SMA-BNC)", arms=ARMS_E,
         ifl="~16 cm SMA cable\n+ SMA-BNC adapter", inp="1 Mohm", off=(91, 141), ls="-", col="#d95f02", detail="pd_ifs_night_15nov.png", region=(1340, 1480)),
    dict(tag="sc", day="18 Nov", desc="very short cables at every mixer connection, 50 ohm IF load", arms=ARMS_SHORT,
         ifl="short cable\n+ 50 ohm load", inp="50 ohm load", off=(141, 200), ls="-", col="#1b9e77", detail="pd_short_cables_detail_18nov.png", region=None),
    dict(tag="eq", day="18 Nov", desc="near-equal arms (cable B 15.2 cm, cable D 16.6 cm), 50 ohm IF load", arms=ARMS_EQ,
         ifl="short cable\n+ 50 ohm load (as sc)", inp="50 ohm load", off=(201, 230), ls="-", col="#7570b3", detail="pd_equal_arms_detail_18nov.png", region=None),
    dict(tag="elo", day="18 Nov", desc="cable E (+ adapter, about 9 cm) moved to the LO arm, 50 ohm IF load", arms=ARMS_ELO,
         ifl="short cable\n+ 50 ohm load (as sc)", inp="50 ohm load", off=(231, 260), ls="-", col="#e7298a", detail="pd_cable_E_on_LO_detail_18nov.png", region=None),
    dict(tag="pad10", day="18-19 Nov", desc="10 dB pad at each mixer port, cables B and D, 50 ohm IF load", arms=ARMS_PAD10, pads="10 dB at LO and RF",
         levels=(-36.0, -45.0, -54.0, -63.0, -72.0), stages=("8mhz", "4mhz", "2mhz", "1mhz"),
         ifl="short cable\n+ 50 ohm load (as sc)", inp="50 ohm load", off=(261, 265), ls="-", col="#66a61e", detail="pd_pads_10dB_1MHz_detail_18nov.png", region=None),
    dict(tag="pad10z", day="18-19 Nov", desc="as pad10, two-round zoomed readings (finest V/div per point)", arms=ARMS_PAD10, pads="10 dB at LO and RF",
         levels=(-36.0, -45.0, -54.0, -63.0, -72.0), stages=("8mhz", "4mhz", "2mhz", "1mhz"), reading="zoom",
         ifl="short cable\n+ 50 ohm load (as sc)", inp="50 ohm load", off=(271, 275), ls="-", col="#1f78b4", detail="pd_pads_10dB_zoomed_detail_18nov.png", region=None),
]


def rows():
    return list(csv.DictReader(open(DATA)))


def wiring_for(run):
    return [f"Pluto TX\n{', '.join(f'{w:.0f}' for w in levels(run))} dBm", "4 x ZX60-P162LN+, 4.03 V\n7 cm cables Pluto-amps-splitter", "ZFRSC-42-S+\nsplitter", run["arms"],
            "ZX05-30W-S+\nLO and RF in, IF out", f"IF: {run['ifl']}", f"SDS1104X-E CH1, {run['inp']}\n" + ("100 mV/div, then finest V/div\ncentred on it (2 rounds per point)" if run.get("reading") == "zoom" else "100 mV/div, one reading per point")]


def load(D, run, stages=("pri", "rest")):
    """{level: array of (MHz, mV)}, first reading per frequency, and (first, last) time."""
    want = {f"{run['tag']}_{s}" for s in run.get("stages", stages)}
    pts = {w: {} for w in levels(run)}
    ts = []
    for r in D:
        if r["stage"] in want:
            pts[float(r["pluto_want_dbm"])].setdefault(float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3)
            ts.append(r["timestamp"][11:16])
    return {w: np.array(sorted(p.items())).reshape(-1, 2) for w, p in pts.items()}, (ts[0], ts[-1]) if ts else ("", "")   # first and last in file order (min/max broke across midnight)


def tone_off(D, run):
    lo, hi = run["off"]
    v = [float(r["detector_mean_v"]) * 1e3 for r in D if r["stage"] == "off" and lo <= int(r["rep"]) < hi]
    return float(np.median(v)) if v else float("nan")


def present(D):
    have = {r["stage"] for r in D}
    return [r for r in RUNS if any(f"{r['tag']}_{s}" in have for s in r.get("stages", ("pri",)))]


def levels(run):
    return run.get("levels", LEVELS)


def colour(run, w):
    L = levels(run)
    return LEVEL_COLOURS[w] if L == LEVELS else matplotlib.colormaps["viridis"](0.9 * L.index(w) / max(len(L) - 1, 1))
