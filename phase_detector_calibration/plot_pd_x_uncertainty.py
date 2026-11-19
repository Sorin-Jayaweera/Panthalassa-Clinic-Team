"""Frequency (x) uncertainty from power (y) uncertainty, Sorin's method (19 Nov), for every phase detector run.
At each frequency: median of every reading (every pass, every power level in the set) -> one median curve, any shape.
Y bar at each frequency: lowest to highest reading there. Each end is read back through the median curve to a frequency;
the x bar is [f(low) - f, f(high) - f] (sorted). The lookup is only defined inside a monotonic stretch of the median curve
(stretches split wherever the median curve turns); a bar end outside its stretch's voltage range has no unique frequency
and is left blank. Two level sets per run: every level ('could be measuring anything') and levels >= -50 dBm
('every pulse we respond to is at least -50 dBm'). The one number reported is Sorin's requirement: the longest
continuous stretch where the total x width (f(high) - f(low)) is <= 4 MHz (Sorin: +/-2 MHz = 4 MHz total).
Usage: python plot_pd_x_uncertainty.py [tag ...]. Saves pd_x_uncertainty_<tag>.png per run."""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import wiring
from plot_pd_resolution import longest, rd, setup_wiring

HERE = Path(__file__).resolve().parent
LIMIT, FLOOR = 2.0, -50.0


def grid(rows, levels):
    """rows (MHz, dBm, pass key, mV) -> f, array (all passes of the given levels) x f, NaN where a pass has no point.
    Only frequencies that every level in the set has."""
    S = {}
    for f, w, k, v in rows:
        if w in levels:
            S.setdefault((w, k), {}).setdefault(f, []).append(v)
    f = np.array(sorted(set.intersection(*[set().union(*[d for (w, k), d in S.items() if w == L]) for L in levels])))
    return f, np.array([[np.mean(d[x]) if x in d else np.nan for x in f] for d in S.values()])


def stretches(med):
    """Index ranges [i, j] where the median curve keeps one direction."""
    s = np.sign(np.diff(med))
    cut = np.flatnonzero(s[1:] != s[:-1]) + 1
    return [(a, b) for a, b in zip(np.r_[0, cut], np.r_[cut, len(s)]) if b > a]


def xbar(f, X):
    """Median curve, y bar (low, high) and x bar (lower, upper) in MHz relative to the true frequency."""
    med, lo, hi = np.nanmedian(X, 0), np.nanmin(X, 0), np.nanmax(X, 0)
    xl, xu = np.full(len(f), np.nan), np.full(len(f), np.nan)
    for a, b in stretches(med):
        sl = slice(a, b + 1)
        g, fs = (med[sl], f[sl]) if med[b] > med[a] else (med[sl][::-1], f[sl][::-1])
        inv = lambda v: np.where((v >= g[0]) & (v <= g[-1]), np.interp(v, g, fs), np.nan)
        e = np.sort([inv(lo[sl]) - f[sl], inv(hi[sl]) - f[sl]], 0)
        xl[sl], xu[sl] = e
    return med, lo, hi, xl, xu


def plot(name, rows, levels, wiring_stages, col, out):
    sets = [("every level", tuple(levels)), (f"levels >= {FLOOR:.0f} dBm", tuple(w for w in levels if w >= FLOOR))]
    fig, ax = wiring.figure(3, [wiring_stages], size=(20, 15), strip=0.3, titles=[f"Wiring: {name}"])
    print(name)
    res, short = [], name.split(":")[0]
    for k, (lab, L) in enumerate(sets):
        f, X = grid(rows, L)
        med, lo, hi, xl, xu = xbar(f, X)
        width = xu - xl                       # total x bar width: Sorin's +/-2 MHz means width <= 4 MHz
        n, a, b = longest(f, width <= 2 * LIMIT)
        txt = f"longest continuous stretch with x width <= {2 * LIMIT:g} MHz: " + (f"{a:g}-{b:g} MHz ({n:g} MHz wide)" if n > 0 else "none")
        print(f"  {lab:22s} ({', '.join(f'{w:.0f}' for w in L)} dBm, {len(X)} passes): {txt}")
        c = ("k", "#d95f02")[k]
        if k == 0:
            for w in levels:
                fw, Xw = grid(rows, (w,))
                ax[0].plot(np.tile(fw, len(Xw)), Xw.ravel(), ".", ms=2, color=R.matplotlib.colormaps["viridis"](0.9 * sorted(levels, reverse=True).index(w) / max(len(levels) - 1, 1)), label=f"{w:.0f} dBm, every pass")
        ax[0].plot(f, med, "-", color=c, lw=1.4, label=f"median of every reading, {lab}")
        ax[0].fill_between(f, lo, hi, color=c, alpha=0.15, label=f"y bar: lowest to highest reading, {lab}")
        q = ax[1 + k]
        q.plot(f, width, "-o", ms=2, color=c, lw=1.2, label=f"x width: lowest and highest reading read back through the median curve\n{txt}")
        q.plot(f, np.where(np.isnan(width) & ~np.isnan(med), 0, np.nan), "x", color="r", ms=4, label="no unique frequency: a bar end lies past a turn of the median curve")
        q.axhline(2 * LIMIT, color="#d95f02", ls="--", lw=1, label=f"{2 * LIMIT:g} MHz total (+/-{LIMIT:g} MHz)")
        q.set(ylim=(0, 15), ylabel="x width (MHz)", title=f"{short}, {lab} ({', '.join(f'{w:.0f}' for w in L)} dBm, {len(X)} passes): total frequency width against frequency")
        res.append((lab, L, len(X), f, width, txt))
    ax[0].set(ylabel="detector (mV)", title=f"{short}: every reading, the median curves and the y bars (wiring and description below)")
    for a in ax:
        a.set_xlim(min(r[3].min() for r in res) - 5, max(r[3].max() for r in res) + 5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
        a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=75)
    return res


def summary(results):
    """One row per run (runs with at least two levels): total x width against frequency for both level sets, same axes."""
    results = [(n, r) for n, r in results if len(r[0][1]) > 1]
    fig, ax = wiring.figure(len(results), [["Pluto TX", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", ["LO arm (per row)", "RF arm (per row)"], "ZX05-30W-S+", "IF -> SDS1104X-E CH1"]],
                            size=(20, 2.6 * len(results) + 2), strip=0.25, titles=["Wiring common to every run; each run's arms and pads are in its row title and in its own detail figure"])
    for a, (name, res) in zip(ax, results):
        for (lab, L, n, f, width, txt), c in zip(res, ("k", "#d95f02")):
            a.plot(f, width, "-", color=c, lw=1.1, label=f"{lab} ({', '.join(f'{w:.0f}' for w in L)} dBm, {n} passes): {txt.replace('longest continuous stretch with x width', 'longest stretch')}")
        a.axhline(2 * LIMIT, color="#d95f02", ls="--", lw=1)
        a.set(xlim=(600, 1600), ylim=(0, 15), ylabel="x width (MHz)")
        a.set_title(name, fontsize=9)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
    ax[-1].set_xlabel("Pluto frequency (MHz)")
    fig.suptitle(f"Every run: total frequency width (lowest and highest reading read back through the median-of-every-reading curve); dashed = {2 * LIMIT:g} MHz", y=1.0)
    fig.tight_layout()
    fig.savefig(HERE / "pd_x_uncertainty_all_runs.png", dpi=70)


def runs(D):
    """(name, rows, levels, wiring, colour, file) for every run: the two old setups, then pd_runs.RUNS."""
    seen, old = {}, []
    for r in rd("p162x4_fine_1nov.csv"):
        key = (float(r["freq_mhz"]), float(r["pluto_want_dbm"]))
        seen[key] = seen.get(key, 0) + 1
        old.append((*key, seen[key], float(r["detector_mean_v"]) * 1e3))
    yield "Cable C, no pads (1 Nov)", old, (-36.0, -40.0, -50.0, -60.0), setup_wiring("C", False, "0.1-0.2 V/div"), "#7570b3", "pd_x_uncertainty_cable_C_1nov.png"
    ep = [(float(r["freq_mhz"]), float(r["pluto_want_dbm"]), int(r["rep"]), float(r["detector_mean_v"]) * 1e3) for r in D if r["stage"] in ("bisect5", "bisect5s")]
    yield "Cable E, 3 dB LO / 6 dB RF pads (14 Nov)", ep, (-36.0, -43.0, -50.0, -57.0), setup_wiring("E", True, "50 mV/div"), "#1b9e77", "pd_x_uncertainty_cable_E_small_pads_14nov.png"
    for run in R.present(D):
        want = {f"{run['tag']}_{s}" for s in run.get("stages", ("pri", "rest"))}
        rows = [(float(r["freq_mhz"]), float(r["pluto_want_dbm"]), int(r["rep"]), float(r["detector_mean_v"]) * 1e3) for r in D if r["stage"] in want]
        L = tuple(w for w in R.levels(run) if any(x[1] == w for x in rows))
        yield f"{run['tag']} ({run['day']}): {run['desc']}, {run.get('pads', 'no pads')}", rows, L, R.wiring_for(run), run["col"], f"pd_x_uncertainty_{run['tag']}.png"


if __name__ == "__main__":
    D, tags = R.rows(), sys.argv[1:]
    out = [(name, plot(name, rows, L, wst, col, png), png) for name, rows, L, wst, col, png in runs(D) if not tags or any(name.startswith(t + " ") for t in tags)]
    if not tags:
        summary([o[:2] for o in out])
        json.dump([[name, png, *[f"{r[5].split(': ')[-1]} ({len(r[1])} levels, {r[2]} passes)" for r in res]] for name, res, png in out], open(HERE / "pd_x_uncertainty_table.json", "w"))
