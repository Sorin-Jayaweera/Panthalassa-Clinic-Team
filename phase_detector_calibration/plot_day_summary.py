"""Master plots of one bench day (default 18 Nov): what each phase detector arrangement showed, from the two run tables
(pd_runs.RUNS for the scope runs, plot_amp_chain.SWEEPS for the SM200B probes). A new arrangement = a new row in DAY.
  pd_day_<day>_detector.png  detector voltage vs frequency per arrangement, tone-off subtracted, stacked, with every wiring
  pd_day_<day>_probes.png    SM200B tone ripple (tone minus quadratic) per probe point, stacked, with every wiring
  pd_day_<day>_delays.png    strongest single delay of every arrangement and level, one row per arrangement"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import plot_amp_chain as A
import wiring
from pdlib import delay

HERE = Path(__file__).resolve().parent
SW = {s["csv"].split("_18nov")[0]: s for s in A.SWEEPS}
# (kind, key, short label, time, what it showed); "ifs" is the 15 Nov reference
DAY = [("det", "ifs", "15 Nov reference: cable E on RF arm, 1 Mohm", "15 Nov 20:33-21:43", "2.77-2.80 ns, about 150 mV"),
       ("det", "sc", "very short cables, 50 ohm IF load", "10:40-12:40", "unchanged: 2.76-2.79 ns"),
       ("sm", "amp_chain", "SM200B: amplifier chain alone", "13:06-13:19", "railed, +-0.5-0.8 dB; strongest 4.4 ns (off this axis)"),
       ("det", "eq", "cables B and D only (RF - LO = -1.4 cm)", "17:02-19:43", "2.28-2.31 ns"),
       ("det", "elo", "cable E moved to LO arm (stopped)", "19:49-19:57", "900-1350 MHz only, no fit"),
       ("sm", "arm_probe_lo", "SM200B: LO arm (D), mixer RF driven", "20:05", "1.9-2.0 ns"),
       ("sm", "arm_probe_rf", "SM200B: RF arm (B), mixer LO driven", "20:16", "2.72 ns, 1.9-2.0 dB rms: the detector's delay"),
       ("sm", "arm_probe_rf_nomixer", "SM200B: RF arm, mixer removed", "evening", "0.6-0.8 dB rms, 2.7 ns gone"),
       ("sm", "arm_probe_rf_padded", "SM200B: RF arm, 10 dB pads at mixer", "evening", "0.56-0.76 dB rms, no clear delay"),
       ("det", "pad10", "10 dB pad at both mixer ports, 1 MHz", "from 20:59 (overnight)", "running; partial data, fit not settled")]
RUNS = {r["tag"]: r for r in R.RUNS}
MIN_SPAN = 700.0   # MHz; a shorter sweep cannot separate a 2-3 ns delay from the trend


def detector(D, tag):
    """{level: (MHz, mV minus tone-off)} for a scope run."""
    run = RUNS[tag]
    P, _ = R.load(D, run)
    off = R.tone_off(D, run)
    return {w: np.c_[a[:, 0], a[:, 1] - (off if np.isfinite(off) else 0)] for w, a in P.items() if len(a)}


def probe(key):
    """{level: (MHz, tone dBm measured + pads)} for an SM200B sweep."""
    s = SW[key]
    return {w: a[:, :2] for w, a in A.table(HERE / s["csv"]).items()} if (HERE / s["csv"]).exists() else {}


def fit(a):
    """(tau ns, amplitude) of the strongest single delay, or None when the sweep is too short."""
    return delay(a[:, 0], a[:, 1], deg=2) if len(a) > 20 and np.ptp(a[:, 0]) >= MIN_SPAN else None


def pick(curves, want=-50.0):
    return min(curves, key=lambda w: abs(w - want)) if curves else None


def wirings(kind):
    rows = [(k, key, lab) for k, key, lab, *_ in DAY if k == kind]
    chains = [(R.wiring_for(RUNS[key]) if k == "det" else c, f"Wiring, {lab}" + (": other splitter output" if j else "")) for k, key, lab in rows
              for j, c in enumerate([None] if k == "det" else SW[key]["wiring"])]
    return [c for c, _ in chains], [t for _, t in chains]


def stacked(kind, load, step, ylab, unit, out):
    D, rows = R.rows(), [r for r in DAY if r[0] == kind]
    chains, titles = wirings(kind)
    fig, ax = wiring.figure(1, chains, size=(15, 9 + 1.6 * len(chains)), titles=titles, strip=0.13)
    a, cm = ax[0], matplotlib.colormaps["tab10"]
    for i, (_, key, lab, when, saw) in enumerate(rows):
        C = load(D, key) if kind == "det" else load(key)
        w, y0 = pick(C), -i * step
        a.axhline(y0, color="0.6", lw=0.5)
        if w is None:
            a.text(605, y0, f"{lab}: no data yet", fontsize=8, va="bottom")
            continue
        f, v = C[w][:, 0], C[w][:, 1]
        if kind == "sm":
            v = v - np.polyval(np.polyfit(f, v, 2), f)
        t = fit(C[w])
        g = np.r_[False, np.diff(f) > 3 * np.median(np.diff(f))]   # no line across a gap in the sweep
        a.plot(np.insert(f, np.flatnonzero(g), np.nan), np.insert(y0 + v, np.flatnonzero(g), np.nan), "-o", ms=1.5, lw=0.9, color=cm(i % 10))
        a.text(1605, y0, f"{lab}\n{when}, {w:.0f} dBm, {len(f)} pts\n"
                         + (f"fit {t[0]:.2f} ns ({1e3 / t[0]:.0f} MHz period), {t[1]:.1f} {unit}" if t else "span too short for a delay fit")
                         + ("" if kind == "det" else f", rms {v.std():.2f} dB") + f"\nseen: {saw}", fontsize=7.5, va="center", color=cm(i % 10))
    a.set(xlim=(595, 1900), xticks=np.arange(600, 1601, 100), yticks=[], xlabel="Pluto frequency (MHz)", ylabel=ylab)
    a.plot([598, 598], [-step / 2, 0], "k-", lw=3)
    a.text(600, -step / 4, f" {step / 2:g} {unit}", fontsize=8, va="center")
    a.grid(alpha=0.3, axis="x")
    a.set_title(f"18 Nov, every arrangement on its own baseline (thin grey line = 0), level nearest -50 dBm; scale bar {step / 2:g} {unit}", fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=90)
    print(out)


def delays(out="pd_day_18nov_delays.png"):
    D = R.rows()
    fig, ax = wiring.figure(1, [["Pluto TX", "4 x ZX60-P162LN+\n4.03 V", "ZFRSC-42-S+\nresistive splitter", ["LO arm", "RF arm"], "ZX05-30W-S+",
                                 ["IF: scope\n(detector rows)", "or one arm into SM200B\n(probe rows)"]]], size=(14, 10),
                            titles=["Wiring, common chain (each arrangement's full wiring is on the two plots above it on the site)"], strip=0.18)
    a = ax[0]
    for i, (kind, key, lab, when, saw) in enumerate(DAY):
        C = detector(D, key) if kind == "det" else probe(key)
        for w, c in C.items():
            t = fit(c)
            if t:
                a.plot(t[0], -i, "o" if kind == "det" else "s", ms=7, mfc="none" if kind == "sm" else "#1b9e77", mec="#1b9e77" if kind == "det" else "#d95f02")
    a.axvspan(2.72, 2.80, color="#d95f02", alpha=0.12, lw=0)
    a.set(yticks=-np.arange(len(DAY)), yticklabels=[f"{lab} ({when})\nseen: {saw}" for _, _, lab, when, saw in DAY], xlim=(1.0, 4.0),
          xlabel="strongest single delay (ns): fit a + b f + c f^2 + A cos(2 pi f tau + phi), 600-1600 MHz, one marker per Pluto level")
    a.plot([], [], "o", mfc="#1b9e77", mec="#1b9e77", label="detector voltage (scope)")
    a.plot([], [], "s", mfc="none", mec="#d95f02", label="tone at the probe point (SM200B)")
    a.legend(fontsize=8, loc="center right")
    a.grid(alpha=0.3)
    a.set_title("18 Nov: strongest delay in each arrangement. Shaded: 2.72-2.80 ns, the detector's delay with cable E", fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=95)
    print(out)


if __name__ == "__main__":
    stacked("det", detector, 400.0, "detector minus tone-off (mV), each arrangement offset", "mV", "pd_day_18nov_detector.png")
    stacked("sm", probe, 8.0, "tone minus quadratic trend (dB), each probe point offset", "dB", "pd_day_18nov_probes.png")
    delays()
