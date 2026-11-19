"""Repeatability of a phase detector run in pd_runs.RUNS: every later repeat minus repeat 1, per Pluto level, against frequency,
with the spread also in MHz (divided by the curve's slope). Usage: python plot_pd_repeats.py [tag ...] (default pad10z).
Saves pd_<tag>_repeats_<day>.png."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import wiring

HERE = Path(__file__).resolve().parent


def by_rep(D, run):
    """{level: {rep: {MHz: mV}}} over the run's stages."""
    want, out = {f"{run['tag']}_{s}" for s in run.get("stages", ("pri", "rest"))}, {}
    for r in D:
        if r["stage"] in want:
            out.setdefault(float(r["pluto_want_dbm"]), {}).setdefault(int(r["rep"]), {})[float(r["freq_mhz"])] = float(r["detector_mean_v"]) * 1e3
    return out


def plot(D, run, lo=720.0):
    V = by_rep(D, run)
    L = [w for w in R.levels(run) if w in V]
    fig, ax = wiring.figure(len(L), [R.wiring_for(run)], size=(14, 3.2 * len(L) + 2.5), strip=0.45, titles=[f"Wiring, {run['day']}: {run['desc']}, {run.get('pads', 'no pads')}"])
    for a, w in zip(ax, L):
        base = V[w][1]
        f1 = np.array(sorted(base))
        slope = np.polyfit(f1[f1 >= lo], [base[x] for x in f1[f1 >= lo]], 1)[0]
        for n in sorted(V[w])[1:]:
            f = np.array(sorted(set(base) & set(V[w][n])))
            d = np.array([V[w][n][x] - base[x] for x in f])
            s = d[f >= lo]
            a.plot(f, d, "-", lw=0.8, color=R.colour(run, w) if n == 2 else "0.55",
                   label=f"repeat {n} - repeat 1: {len(f)} freqs, mean {d.mean():+.2f} mV, sd {s.std():.2f} mV above {lo:g} MHz "
                         f"= {s.std() / abs(slope):.1f} MHz at {slope:.3f} mV/MHz")
        a.axhline(0, color="k", lw=0.6)
        if f1[0] < lo:
            a.axvspan(f1[0], lo, color="0.5", alpha=0.08)
        a.set(xlim=(f1[0] - 5, f1[-1] + 5), ylabel="mV", title=f"{w:.0f} dBm: difference between repeats (raw detector readings; grey = below {lo:g} MHz, the dip, left out of the sd)")
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper right")
    ax[-1].set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    out = HERE / f"pd_{run['tag']}_repeats_{run['day'].split()[0].replace('-', '_')}nov.png"
    fig.savefig(out, dpi=90)
    print(out.name)


if __name__ == "__main__":
    D, tags = R.rows(), sys.argv[1:] or ["pad10z"]
    for run in R.RUNS:
        if run["tag"] in tags:
            plot(D, run)
