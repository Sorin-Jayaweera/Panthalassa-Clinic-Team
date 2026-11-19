"""Frequency uncertainty when the input power is unknown, Sorin's method (19 Nov), for every phase detector run.
Level set = the Pluto levels from the highest down to a lower threshold. Lookup = the median curve of the set: at each
frequency, the median of every reading of every level in the set. At each true frequency f, take the reading at the
highest level and the reading at the threshold level (each the median over that level's passes), read both back through
the median curve, and plot each read frequency minus f. Total width = the distance between the two (Sorin: +/-2 MHz =
4 MHz total). The lookup must be single valued, so it is split wherever the median curve turns; a reading past a turn
has no unique frequency (marked x). Thresholds: every level, -60 dBm, the lowest railed level, -50 dBm.
Two plots per run: voltage read against frequency (one line per Pluto level, every pass, every reading) with the median
curves; then the frequency offsets. Usage: python plot_pd_x_uncertainty.py [tag ...].
Saves pd_x_uncertainty_<tag>.png per run, pd_x_uncertainty_all_runs.png and pd_x_uncertainty_table.json (the site's table)."""
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
# RAILED: lowest Pluto level where the 4 x ZX60-P162LN+ chain is within 1 dB of its saturated output at every frequency
# 950-1600 MHz (amp_ramp_18nov.csv: -58 dBm within 0.7 dB, -60 dBm up to 1.1 dB down, -63 2-3 dB, -72 up to 10 dB)
LIMIT, RAILED = 2.0, -58.0
FLOORS = {-1e9: "every level", -60.0: ">= -60 dBm", RAILED: "amplifiers railed, >= -58 dBm", -50.0: ">= -50 dBm"}
COLS = ("k", "#e7298a", "#d95f02", "#8c510a")


def grid(rows, levels):
    """rows (MHz, dBm, pass key, mV) -> f, level of each pass, array passes x f (NaN where a pass has no point).
    Only frequencies that every level in the set has."""
    S = {}
    for f, w, k, v in rows:
        if w in levels:
            S.setdefault((w, k), {}).setdefault(f, []).append(v)
    f = np.array(sorted(set.intersection(*[set().union(*[d for (w, k), d in S.items() if w == L]) for L in levels])))
    return f, np.array([w for w, k in S]), np.array([[np.mean(d[x]) if x in d else np.nan for x in f] for d in S.values()])


def stretches(med):
    """Index ranges [i, j] where the median curve keeps one direction."""
    s = np.sign(np.diff(med))
    cut = np.flatnonzero(s[1:] != s[:-1]) + 1
    return [(a, b) for a, b in zip(np.r_[0, cut], np.r_[cut, len(s)]) if b > a]


def offsets(f, med, *V):
    """Each reading curve in V read back through the median curve, minus the true frequency (MHz). The lookup is the
    monotonic stretch of the median curve that holds f; a reading outside that stretch's range has no unique frequency (NaN)."""
    out = np.full((len(V), len(f)), np.nan)
    for a, b in stretches(med):
        sl = slice(a, b + 1)
        g, fs = (med[sl], f[sl]) if med[b] > med[a] else (med[sl][::-1], f[sl][::-1])
        for o, v in zip(out, V):
            o[sl] = np.where((v[sl] >= g[0]) & (v[sl] <= g[-1]), np.interp(v[sl], g, fs), np.nan) - f[sl]
    return out


def measure(rows, L):
    """Level set L -> f, median curve, offsets (top level, threshold level; MHz), total width, passes, longest stretch (n, a, b) with width <= 4 MHz."""
    f, ws, X = grid(rows, L)
    med = np.nanmedian(X, 0)
    o = offsets(f, med, *(np.nanmedian(X[ws == w], 0) for w in (max(L), min(L))))
    width = abs(o[0] - o[1])
    return f, med, o, width, len(X), longest(f, width <= 2 * LIMIT) if len(L) > 1 else (0, 0, 0)


def plot(name, rows, levels, wiring_stages, col, out):
    fig, ax = wiring.figure(2, [wiring_stages], size=(20, 13), strip=0.3, titles=[f"Wiring: {name}"])
    short, seen, P, sets, res = name.split(":")[0], set(), {}, {}, {}
    for f, w, k, v in sorted(rows):
        P.setdefault((w, k), []).append((f, v))
    allw = sorted({w for w, k in P}, reverse=True)                      # every level taken, also ones outside the sets
    for (w, k), p in sorted(P.items(), key=lambda t: -t[0][0]):          # every reading: one line per level and pass
        ax[0].plot(*np.array(p).T, "-", lw=0.7, color=R.matplotlib.colormaps["viridis"](0.9 * allw.index(w) / max(len(allw) - 1, 1)),
                   label="_" if w in seen else f"Pluto {w:.0f} dBm ({sum(x == w for x, _ in P)} passes, one line each)")
        seen.add(w)
    for c, nm in FLOORS.items():
        sets.setdefault(tuple(w for w in levels if w >= c), []).append(nm)
    print(name)
    for L, names in sets.items():
        f, med, o, width, npass, (n, a, b) = measure(rows, L)
        txt = "one level only, no power range" if len(L) == 1 else f"longest stretch with total width <= {2 * LIMIT:g} MHz: " + (f"{a:g}-{b:g} MHz ({n:g} MHz wide)" if n > 0 else "none")
        lab = f"{max(L):.0f} to {min(L):.0f} dBm ({' = '.join(names)}; median of {npass} passes)"
        print(f"  {lab}: {txt}")
        k = list(FLOORS.values()).index(names[0])
        ax[0].plot(f, med, "--", color=COLS[k], lw=1.6, label=f"median curve (lookup), {max(L):.0f} to {min(L):.0f} dBm")
        ax[1].plot(f, o[0], "-", color=COLS[k], lw=1.3, label=f"{lab}\n   solid: reading at {max(L):.0f} dBm, dashed: reading at {min(L):.0f} dBm\n   {txt}")
        ax[1].plot(f, o[1], "--", color=COLS[k], lw=1.3)
        ax[1].plot(f, np.where(np.isnan(o).any(0) & ~np.isnan(med), -9.5 + 0.5 * k, np.nan), "x", color=COLS[k], ms=4)
        res.update({nm: (nm, L, npass, f, width, txt) for nm in names})
    for y in (LIMIT, -LIMIT):
        ax[1].axhline(y, color="r", ls=":", lw=1.2, label=f"+/-{LIMIT:g} MHz\nx at the bottom: no unique frequency (reading past a turn of that median curve)" if y > 0 else "_")
    ax[0].set(ylabel="voltage read (mV)", title=f"{short}: voltage read against frequency, one line per Pluto level (every pass); dashed = median curve of each level set (wiring below)")
    ax[1].set(ylim=(-10, 10), ylabel="frequency read on the median curve\nminus true frequency (MHz)",
              title=f"{short}: input at the top level (solid) or at the threshold level (dashed): the voltage it gives, looked up on that set's median curve")
    for a in ax:
        a.set_xlim(min(f for f, *_ in rows) - 5, max(f for f, *_ in rows) + 5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
        a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    fig.savefig(HERE / out, dpi=75)
    return [res[nm] for nm in FLOORS.values()]


def summary(results):
    """One row per run (runs with at least two levels): total width against frequency for each level set, same axes."""
    results = [(n, r) for n, r in results if len(r[0][1]) > 1]
    fig, ax = wiring.figure(len(results), [["Pluto TX", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", ["LO arm (per row)", "RF arm (per row)"], "ZX05-30W-S+", "IF -> SDS1104X-E CH1"]],
                            size=(20, 2.6 * len(results) + 2), strip=0.25, titles=["Wiring common to every run; each run's arms and pads are in its row title and in its own detail figure"])
    for a, (name, res) in zip(ax, results):
        for (lab, L, n, f, width, txt), c in zip(res, COLS):
            a.plot(f, width, "-", color=c, lw=1.1, label=f"{max(L):.0f} to {min(L):.0f} dBm ({lab}): {txt.replace('longest stretch with total width', 'longest')}")
        a.axhline(2 * LIMIT, color="r", ls=":", lw=1.2)
        a.set(xlim=(600, 1600), ylim=(0, 15), ylabel="total width (MHz)")
        a.set_title(name, fontsize=9)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
    ax[-1].set_xlabel("Pluto frequency (MHz)")
    fig.suptitle(f"Every run: distance between the frequencies read for the top level and the threshold level (both looked up on the set's median curve); dotted = {2 * LIMIT:g} MHz", y=1.0)
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
