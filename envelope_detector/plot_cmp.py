"""Plots for the ADCMP604 comparator tests (COMPARATOR-TEST-RESULTS.md).

Run from this folder, on the computer that has the data/ files:

    python3 plot_cmp.py

Writes four PNGs to plots_cmp/:
  1_trip_band.png      Test 2: OUT+ vs IN+ - IN- at four IN- levels (5 Nov runs)
  2_rfoff_margin.png   Test 4: RF-off edge rate vs threshold margin (8-9 Nov)
  3_osc_vs_pickup.png  Scope: real oscillation (68 mV margin) vs a pickup burst (335 mV)
  4_pulses_0dB.png     Test 4: 100 us pulses at TX 0 dB, 335 mV margin

Each plot is skipped with a message if its data files aren't found.
Needs numpy and matplotlib (python3 -m pip install matplotlib).
"""

import csv
import glob
import os
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "plots_cmp")

# This board's OUT+ levels from Test 1 (DMM): low 1.105 V, high 1.483 V.
OUT_LOW, OUT_HIGH = 1.105, 1.483


def latest(pattern):
    files = sorted(glob.glob(os.path.join(DATA, pattern)))
    return files[-1] if files else None


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


# --------------------------------------------------------------------------- 1. Test 2 band

def read_trip(path):
    meta, rows = {}, []
    with open(path) as f:
        lines = f.read().splitlines()
    body = []
    for ln in lines:
        if ln.startswith("# vn_dmm_v,"):
            meta["vn"] = float(ln.split(",")[1])
        elif ln.startswith("# cal,"):
            parts = ln.split(",")
            meta["v_per_code"] = float(parts[1].split()[0])
            meta["zero"] = float(parts[2].split()[1])
        elif not ln.startswith("#"):
            body.append(ln)
    for r in csv.DictReader(body):
        rows.append(r)
    return meta, rows


def j1_offset_v(steps_name, meta):
    """J1 minus the CGR setting, from the DMM reading the sweep asked for at its 'up' park point
    (data/cmp_trip_summary.csv). Falls back to 0 if the row isn't there."""
    path = os.path.join(DATA, "cmp_trip_summary.csv")
    if not os.path.exists(path):
        return 0.0
    with open(path) as f:
        for r in csv.DictReader(f):
            if r.get("steps_file") == steps_name and r.get("dmm_up_mv") not in ("", None):
                code = float(r["dmm_up_code"])
                set_v = (code - meta["zero"]) * meta["v_per_code"]
                return float(r["dmm_up_mv"]) / 1e3 - (set_v - meta["vn"])
    return 0.0


def plot_trip():
    files = [latest(f"cmp_trip_vn{vn}_20261105_*.csv") for vn in ("1.152", "1.241", "1.343", "1.663")]
    files = [f for f in files if f]
    if not files:
        print("1: no 5 Nov trip files found, skipped")
        return
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for path in files:
        meta, rows = read_trip(path)
        off = j1_offset_v(os.path.basename(path), meta)
        ref = {r["phase"]: float(r["b_mean_v"]) for r in rows if r["phase"] in ("ref_low", "ref_high")}
        lo, hi = ref.get("ref_low"), ref.get("ref_high")
        pts = [r for r in rows if r["phase"] in ("coarse", "fine_up", "fine_down")]
        x = np.array([(float(r["vp_set_v"]) + off - meta["vn"]) * 1e3 for r in pts])
        y = np.array([(float(r["b_mean_v"]) - lo) / (hi - lo) for r in pts])
        order = np.argsort(x)
        line, = ax.plot(x[order], y[order], ".", ms=4, alpha=0.7)
        up = [i for i, r in enumerate(pts) if r["phase"] in ("coarse", "fine_up")]
        upo = sorted(up, key=lambda i: x[i])
        ax.plot(x[upo], y[upo], "-", lw=1, color=line.get_color(),
                label=f"IN− = {meta['vn']:.3f} V (J1 = setting {1e3 * off:+.1f} mV)")
    ax.axvline(0, color="k", lw=0.8)
    ax.axvspan(-5, 5, color="0.85", zorder=0, label="±5 mV offset spec [DS Table 1]")
    ax.set_xlabel("IN+ − IN−  (mV, at the pins; from CGR setting + DMM-measured J1 offset)")
    ax.set_ylabel("OUT+ on CGR Input B\n(0 = low, 1 = high; CGR averages, 5 MHz)")
    ax.set_title("Test 2: OUT+ is undecided over ≈ ±45 mV, centred near 0 mV\n"
                 "(5 Nov, 100 Ω source; in-between = ≈ 27 MHz oscillation averaged by the CGR)")
    ax.set_ylim(-0.1, 1.15)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left")
    save(fig, "1_trip_band.png")


# --------------------------------------------------------------------------- 2. RF-off margin

# Margins as set on the bench (DMM at J3 - 1.14 V, or J3 - J1), where the label rounds them.
MARGIN_BY_LABEL = {"rf_off": 17.2, "rf_off_m50": 54.8, "rf_off_m110": 110.6, "rf_off_m110_ch1": 110.6}
STALE = {"20261108_211314"}  # scope probably not re-armed: discarded in the results sheet
# Runs that never triggered write no summary row; add them by hand (results sheet).
NO_TRIGGER = [(560, "coax; CH1 cable on the tee"), (300, "coax; CH1 cable on the tee")]


def margin_of(label):
    if label in MARGIN_BY_LABEL:
        return MARGIN_BY_LABEL[label]
    m = re.search(r"_(?:m|A|B|d)(\d+)", label)
    return float(m.group(1)) if m else None


def group_of(row):
    if row["time"] < "20261108_211300":
        return "grabber lead + CH1 probe on the IN+ tee"
    if "_B" in row["label"] or row["time"] >= "20261108_215600":  # round B onwards: CH1 cable removed
        return "coax only (tee joins detector and J1)"
    return "coax; CH1 cable on the tee"


def plot_rfoff():
    path = os.path.join(DATA, "cmp_scope_summary.csv")
    if not os.path.exists(path):
        print("2: data/cmp_scope_summary.csv not found, skipped")
        return
    groups = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            lab = r.get("label", "")
            if not lab.startswith("rf_off") or "after" in lab or r["time"] in STALE:
                continue
            mv = margin_of(lab)
            if mv is None:
                continue
            rate = float(r["out_rising"]) / (float(r["record_s"]) * 1e3)  # edges per ms
            groups.setdefault(group_of(r), []).append((mv, rate))
    floor = 0.3
    fig, ax = plt.subplots(figsize=(8, 4.8))
    markers = {"grabber lead + CH1 probe on the IN+ tee": "s", "coax; CH1 cable on the tee": "o",
               "coax only (tee joins detector and J1)": "^"}
    for g, pts in groups.items():
        pts = np.array(pts)
        ax.plot(pts[:, 0], np.maximum(pts[:, 1], floor), markers.get(g, "o"), ms=7, alpha=0.8, label=g)
    for mv, g in NO_TRIGGER:
        ax.plot(mv, floor, markers.get(g, "o"), ms=9, mfc="none", mec="k")
    ax.plot([], [], "o", mfc="none", mec="k", label="no trigger at all in 10 s")
    ax.axvline(20, color="r", ls="--", lw=1)
    ax.text(22, 3e4, "planned\n+20 mV", color="r", fontsize=8, va="top")
    ax.axhline(1, color="0.6", lw=0.8, ls=":")
    ax.text(400, 1.3, "≤ 1 edge: interference blip only (quiet)", fontsize=7, color="0.4")
    ax.set_yscale("log")
    ax.set_ylim(floor * 0.7, 1e5)
    ax.set_xlabel("threshold margin above the detector's resting level (mV)")
    ax.set_ylabel("OUT+ rising edges per ms, RF off\n(plotted at 0.3 when zero)")
    ax.set_title("Test 4: with RF off, the comparator oscillates unless the margin is ≈ 150–300 mV\n"
                 "(8–9 Nov, clip-lead output wiring; 1 ms of oscillation ≈ 27–53 thousand edges)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=7, loc="center right")
    save(fig, "2_rfoff_margin.png")


# --------------------------------------------------------------------------- 3 and 4. scope shots

def load_shot(folder_glob, shot=0):
    folders = sorted(glob.glob(os.path.join(DATA, folder_glob)))
    if not folders:
        return None
    path = os.path.join(folders[-1], f"shot_{shot:02d}.npz")
    if not os.path.exists(path):
        return None
    d = np.load(path)
    v = d["out_codes"].astype(np.float32) * np.float32(float(d["out_vdiv"]) / 25.0) - np.float32(float(d["out_offset"]))
    fs = float(d["fs"])
    t = float(d["t_first"]) + np.arange(len(v)) / fs
    return t, v, fs, os.path.basename(folders[-1])


def plot_osc_vs_pickup():
    osc = load_shot("cmp_scope_rf_off_m68_*")
    pick = load_shot("cmp_scope_rf_off_m335_*")
    if osc is None and pick is None:
        print("3: m68 / m335 captures not found, skipped")
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, shot, title, half in ((axes[0], osc, "68 mV margin: real oscillation", 200e-9),
                                  (axes[1], pick, "335 mV margin: the one 'edge' is a pickup burst", 800e-9)):
        if shot is None:
            ax.set_title(title + "\n(data not found)")
            continue
        t, v, fs, name = shot
        c = int(np.argmax(v)) if "335" in title else len(v) // 2
        n = int(half * fs)
        sl = slice(max(c - n, 0), min(c + n, len(v)))
        ax.plot((t[sl] - t[c]) * 1e9, v[sl], lw=0.8)
        ax.set_title(f"{title}\n{name}", fontsize=9)
        ax.set_xlabel("time (ns)")
        ax.grid(alpha=0.3)
    for ax in axes:
        ax.axhline(OUT_LOW, color="g", lw=0.8, ls="--")
        ax.axhline(OUT_HIGH, color="m", lw=0.8, ls="--")
        ax.axhline(1.40, color="r", lw=0.8, ls=":")
    axes[0].set_ylabel("OUT+ (V)")
    axes[1].text(0.02, 0.97, "green: low 1.105 V   magenta: high 1.483 V   red: trigger 1.40 V\n"
                 "pickup swings above AND below the low level; a real flip steps up to ≈ 1.48 V",
                 transform=axes[1].transAxes, fontsize=7, va="top")
    fig.suptitle("Scope (CH2 on J7, 10× probe), RF off, coax-only IN+", fontsize=10, y=1.06)
    save(fig, "3_osc_vs_pickup.png")


def envelope(t, v, bins=4000):
    n = len(v) // bins * bins
    vv = v[:n].reshape(bins, -1)
    tt = t[:n].reshape(bins, -1)[:, 0]
    return tt, vv.min(axis=1), vv.max(axis=1)


def first_burst(v, fs, level=1.40, window=2e-6, min_samples=50):
    """Sample indices above `level`, starting at the first real chatter burst: at least
    `min_samples` samples above `level` within `window` (a pickup spike has only a few)."""
    idx = np.flatnonzero(v > level)
    n = min_samples
    if len(idx) <= n:
        return idx[:0]
    dense = np.flatnonzero(idx[n:] - idx[:-n] < window * fs)
    return idx[dense[0]:] if len(dense) else idx[:0]


def chatter_bursts(v, fs, level=1.40, gap=1e-6, min_samples=50):
    """(start, end) sample indices of chatter bursts: runs of samples above `level` with gaps
    shorter than `gap`, keeping only runs with at least `min_samples` such samples (drops pickup)."""
    idx = np.flatnonzero(v > level)
    if not len(idx):
        return []
    cuts = np.flatnonzero(np.diff(idx) > gap * fs)
    starts = np.r_[0, cuts + 1]
    ends = np.r_[cuts, len(idx) - 1]
    return [(int(idx[a]), int(idx[b])) for a, b in zip(starts, ends) if b - a + 1 >= min_samples]


def plot_pulses():
    shot = load_shot("cmp_scope_ed_tx0_100us_m335_*")
    if shot is None:
        print("4: ed_tx0_100us_m335 capture not found, skipped")
        return
    t, v, fs, name = shot
    above = first_burst(v, fs)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6))
    tt, lo, hi = envelope(t, v)
    a1.fill_between(tt * 1e3, lo, hi, step="mid", lw=0, label="OUT+ (min–max per screen pixel)")
    if len(above):
        t_first = t[above[0]]
        k = np.arange(np.floor((t[0] - t_first) / 200e-6), np.ceil((t[-1] - t_first) / 200e-6) + 1)
        for tk in t_first + k * 200e-6:
            if t[0] <= tk <= t[-1]:
                a1.axvline(tk * 1e3, color="r", lw=0.4, alpha=0.5)
        a1.plot([], [], color="r", lw=0.8, alpha=0.6, label="expected pulse start (every 200 µs)")
    a1.axhline(1.40, color="k", lw=0.8, ls=":", label="trigger / edge threshold 1.40 V")
    a1.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1), framealpha=0.9)
    a1.set_xlabel("time (ms)")
    a1.set_ylabel("OUT+ (V)")
    a1.set_title(f"Test 4, TX 0 dB, 100 µs on / 100 µs off, 335 mV margin ({name}, shot 0)\n"
                 "red lines: expected pulse starts (every 200 µs, aligned to the first chatter burst). "
                 "About 1/3–1/2 of pulses register.\nThin spikes between bursts: pickup, repeating "
                 "every ≈ 14.5 µs (≈ 69 kHz).", fontsize=9)
    a1.grid(alpha=0.3)
    bursts = chatter_bursts(v, fs)
    if bursts:
        lens = [(b - a) / fs * 1e6 for a, b in bursts]
        a, b = max(bursts, key=lambda ab: ab[1] - ab[0])
        sl = slice(max(a - int(15e-6 * fs), 0), min(a + int(115e-6 * fs), len(v)))
        a2.plot((t[sl] - t[a]) * 1e6, v[sl], lw=0.3, label="OUT+")
        a2.set_title(f"Zoom on the longest burst: ≈ 27 MHz chatter for {(b - a) / fs * 1e6:.0f} µs of the "
                     f"100 µs pulse, not one clean pulse.\nThis shot: {len(bursts)} bursts lasting "
                     f"{min(lens):.0f}–{max(lens):.0f} µs (median {np.median(lens):.0f} µs)", fontsize=9)
    a2.axhline(OUT_HIGH, color="m", lw=0.8, ls="--", label="high level 1.483 V (Test 1)")
    a2.axhline(1.40, color="k", lw=0.8, ls=":", label="edge threshold 1.40 V")
    a2.axhline(OUT_LOW, color="g", lw=0.8, ls="--", label="low level 1.105 V (Test 1)")
    a2.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1), framealpha=0.9)
    a2.set_xlabel("time from the start of the burst (µs)")
    a2.set_ylabel("OUT+ (V)")
    a2.grid(alpha=0.3)
    fig.tight_layout()
    save(fig, "4_pulses_0dB.png")


if __name__ == "__main__":
    plot_trip()
    plot_rfoff()
    plot_osc_vs_pickup()
    plot_pulses()
