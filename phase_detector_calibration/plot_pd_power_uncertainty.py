"""Frequency error when the input power is unknown (Sorin, 19 Nov): calibrate with the median over the power levels above a cut,
then read a voltage that lies exactly on one level's curve. Deviation from the median in mV, and in MHz (divided by the local slope
of the median). Every sweep is kept, so the spread also holds the repeat scatter; the thick line per level is its median over sweeps.
One figure per row of CASES (a new data set = a new row). Saves pd_power_uncertainty_<name>.png and prints the table."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import wiring
from plot_pd_resolution import local_slope

HERE = Path(__file__).resolve().parent
CUTS = (-60.0, -50.0)       # reference = median over the levels above each cut (dBm)
CASES = [dict(name="900_1200MHz_19nov", tags=("pad10z", "pad10z40n", "pad10zn"), lo=900, hi=1200, band=(900, 1200), title="900-1200 MHz, every zoomed sweep with pads (18 Nov night + 19 Nov)"),
         dict(name="600_1600MHz_18nov", tags=("pad10z",), lo=600, hi=1600, band=(720, 1600), title="600-1600 MHz, overnight zoomed run with pads (18-19 Nov); stats above 720 MHz (the dip below is left out)")]


def sweeps(D, tags, lo, hi):
    """{level: (f grid, array sweeps x f)} for every (run, level, rep), mean of duplicate readings, NaN where a sweep has no point."""
    S = {}
    for r in D:
        t = r["stage"].rsplit("_", 1)[0]
        f = float(r["freq_mhz"])
        if t in tags and r["stage"].endswith("mhz") and lo <= f <= hi:
            S.setdefault(float(r["pluto_want_dbm"]), {}).setdefault((t, r["rep"]), {}).setdefault(f, []).append(float(r["detector_mean_v"]) * 1e3)
    f = np.arange(lo, hi + 1.0)
    return f, {w: np.array([[np.mean(s[x]) if x in s else np.nan for x in f] for s in d.values()]) for w, d in sorted(S.items(), reverse=True)}


def errors(f, V, cut):
    """Reference median over the level medians above cut, its local slope, and per-level deviations (mV) of every sweep."""
    ref = np.nanmedian([np.nanmedian(v, 0) for w, v in V.items() if w > cut], 0)
    return ref, local_slope(f, ref, 15), {w: v - ref for w, v in V.items()}


def plot(D, c):
    f, V = sweeps(D, c["tags"], c["lo"], c["hi"])
    run = dict(R.RUNS[[r["tag"] for r in R.RUNS].index(c["tags"][-1])], levels=tuple(V))
    col = lambda w: R.colour(run, w)
    inb = (f >= c["band"][0]) & (f <= c["band"][1])
    fig, ax = wiring.figure(1 + 2 * len(CUTS), [R.wiring_for(run)], size=(14, 19), strip=0.5, titles=[f"Wiring (same for every sweep): {run['desc'].split(',')[0]}, {run['pads']}"])
    for w, v in V.items():
        ax[0].plot(f, v.T, color=col(w), lw=0.4, alpha=0.5)
        ax[0].plot([], [], color=col(w), label=f"{w:.0f} dBm: {len(v)} sweeps")
    print(f"\n{c['title']}")
    for k, cut in enumerate(CUTS):
        ref, s, dev = errors(f, V, cut)
        ax[0].plot(f, ref, "k" + "-:"[k], lw=1.4, label=f"median of the levels above {cut:.0f} dBm")
        a, b = ax[1 + 2 * k], ax[2 + 2 * k]
        for w, d in dev.items():
            m, e = np.nanmedian(d, 0), d / s
            lab = lambda x, u: f"{w:.0f} dBm{' (in the median)' if w > cut else ''}: level median rms {np.sqrt(np.nanmean(x[inb] ** 2)):.2f}, worst {np.nanmax(abs(x[inb])):.2f} {u}; every sweep worst {np.nanmax(abs((d if u == 'mV' else e)[:, inb])):.2f} {u}"
            for y, x, u in ((a, m, "mV"), (b, m / s, "MHz")):
                y.plot(f, (d if u == "mV" else e).T, color=col(w), lw=0.3, alpha=0.35)
                y.plot(f, x, color=col(w), lw=1.6, label=lab(x, u))
            print(f"  ref > {cut:.0f}  {w:5.0f} dBm  rms {np.sqrt(np.nanmean(m[inb] ** 2)):.2f} mV  worst {np.nanmax(abs(m[inb])):.2f} mV  rms {np.sqrt(np.nanmean((m / s)[inb] ** 2)):.2f} MHz  worst {np.nanmax(abs((m / s)[inb])):.2f} MHz  every sweep worst {np.nanmax(abs(e[:, inb])):.2f} MHz")
        inside = np.concatenate([d[:, inb] / s[inb] for w, d in dev.items() if w > cut])
        a.set(ylabel="mV", title=f"Reading minus the median of the levels above {cut:.0f} dBm (thin: every sweep, thick: level median)")
        b.set(ylabel="MHz", ylim=(-12, 12), title=f"Same, as frequency error (divided by the median's local slope, about {np.nanmedian(s[inb]):.3f} mV/MHz): "
              f"levels in the median, every sweep: rms {np.sqrt(np.nanmean(inside ** 2)):.2f} MHz, worst {np.nanmax(abs(inside)):.2f} MHz")
    ax[0].set(ylabel="detector mV", title=c["title"])
    for a in ax:
        a.axhline(0, color="k", lw=0.5) if a is not ax[0] else None
        a.axvspan(c["lo"], c["band"][0], color="0.5", alpha=0.1) if c["band"][0] > c["lo"] else None
        a.set_xlim(c["lo"], c["hi"])
        a.grid(alpha=0.3)
        a.legend(fontsize=7, loc="upper left", ncol=1 + (a is ax[0]))
    ax[-1].set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    fig.savefig(HERE / f"pd_power_uncertainty_{c['name']}.png", dpi=90)


if __name__ == "__main__":
    D = R.rows()
    for c in CASES:
        plot(D, c)
