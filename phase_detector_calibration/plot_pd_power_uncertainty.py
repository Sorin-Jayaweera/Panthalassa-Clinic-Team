"""Frequency error when the input power is unknown (Sorin, 19 Nov): calibrate with the median over the power levels above a cut,
then read a voltage that lies exactly on one level's curve. Deviation from the median in mV, and the frequency error in MHz:
look the reading up in the median curve (made monotonic with a running maximum, as worst_error in plot_pd_resolution.py) minus the
true frequency. Every sweep is kept, so the spread also holds the repeat scatter; the thick line per level is its median over sweeps.
One figure per row of CASES (a new data set = a new row). Saves pd_power_uncertainty_<name>.png and prints the table."""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import wiring
from plot_pd_resolution import longest

warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN medians outside the band

HERE = Path(__file__).resolve().parent
CUTS = (-60.0, -50.0)       # reference = median over the levels above each cut (dBm)
WIN = 200                   # Sorin's requirement: one continuous 200 MHz stretch read to within 2 MHz
CASES = [dict(name="900_1200MHz_19nov", tags=("pad10z", "pad10z40n", "pad10zn"), lo=900, hi=1200, band=(900, 1200), title="900-1200 MHz, every zoomed sweep with pads (18 Nov night + 19 Nov)"),
         dict(name="cable_E_600_1600MHz_19nov", tags=("pad10d",), lo=600, hi=1600, band=(600, 1600), title="600-1600 MHz, pads + cable E on the RF arm (19 Nov afternoon)"),
         dict(name="600_1600MHz_18nov", tags=("pad10z",), lo=600, hi=1600, band=(720, 1600), title="600-1600 MHz, overnight zoomed run with pads (18-19 Nov); stats above 720 MHz (the dip below is left out)")]


def sweeps(D, tags, lo, hi):
    """{level: (f grid, array sweeps x f)} for every (run, level, rep), mean of duplicate readings, NaN where a sweep has no point."""
    S = {}
    for r in D:
        t = r["stage"].rsplit("_", 1)[0]
        f = float(r["freq_mhz"])
        if t in tags and r["stage"].endswith("mhz") and lo <= f <= hi:
            S.setdefault(float(r["pluto_want_dbm"]), {}).setdefault((t, r["rep"]), {}).setdefault(f, []).append(float(r["detector_mean_v"]) * 1e3)
    f = np.array(sorted(set.intersection(*[set().union(*d.values()) for d in S.values()])))    # frequencies every level has (grid grows as the sweep refines)
    return f, {w: np.array([[np.mean(s[x]) if x in s else np.nan for x in f] for s in d.values()]) for w, d in sorted(S.items(), reverse=True)}


def lookup(f, ref, v, m):
    """Frequency read from v through the lookup table ref on mask m (made monotonic in its overall direction), minus the true f; NaN off m."""
    sg = np.sign(ref[m][-1] - ref[m][0]) or 1.0
    cs = np.maximum.accumulate(sg * ref[m]) + 1e-9 * np.arange(m.sum())
    return np.where(m, np.interp(sg * v, cs, f[m]) - f, np.nan)


def errors(f, V, cut, inb):
    """Reference = median over the level medians above cut; per level, every sweep's deviation (mV) and lookup error (MHz, in band)."""
    ref = np.nanmedian([np.nanmedian(v, 0) for w, v in V.items() if w > cut], 0)
    return ref, {w: v - ref for w, v in V.items()}, {w: lookup(f, ref, v, inb) for w, v in V.items()}


def best_window(f, V, ref, cut, inb):
    """Sorin's requirement: the WIN MHz stretch whose own lookup table gives the smallest worst error; returns (start, worst-error curve)."""
    best = (np.inf, np.nan, np.full(len(f), np.nan))    # stays so until the data spans WIN MHz
    for f0 in f[inb & (f + WIN <= f[inb].max())]:
        m = inb & (f >= f0) & (f <= f0 + WIN)
        e = np.nanmax(abs(np.concatenate([lookup(f, ref, v, m) for w, v in V.items() if w > cut])), 0)
        best = min(best, (np.nanmax(e), f0, e), key=lambda t: t[0])
    return best


def plot(D, c):
    f, V = sweeps(D, c["tags"], c["lo"], c["hi"])
    run = dict(R.RUNS[[r["tag"] for r in R.RUNS].index(c["tags"][-1])], levels=tuple(V))
    col = lambda w: R.colour(run, w)
    inb = (f >= c["band"][0]) & (f <= c["band"][1])
    fig, ax = wiring.figure(2 + 2 * len(CUTS), [R.wiring_for(run)], size=(22, 34), strip=0.35, titles=[f"Wiring (same for every sweep): {run['desc']}"])
    for w, v in V.items():
        ax[0].plot(f, v.T, color=col(w), lw=0.4, alpha=0.5)
        ax[0].plot([], [], color=col(w), label=f"{w:.0f} dBm: {len(v)} sweeps")
    fig2, bx = wiring.figure(len(CUTS), [R.wiring_for(run)], size=(22, 7 * len(CUTS) + 2), strip=0.3, titles=[f"Wiring (same for every sweep): {run['desc']}"])
    print(f"\n{c['title']}")
    for k, cut in enumerate(CUTS):
        ref, dev, fe = errors(f, V, cut, inb)
        ax[0].plot(f, ref, "k" + "-:"[k], lw=1.4, label=f"median of the levels above {cut:.0f} dBm")
        a, b = ax[2 + 2 * k], ax[3 + 2 * k]
        st = lambda x: (np.sqrt(np.nanmean(x[..., inb] ** 2)), np.nanmax(abs(x[..., inb])))
        for w, d in dev.items():
            for y, x, u in ((a, d, "mV"), (b, fe[w], "MHz")):
                m = np.nanmedian(x, 0)
                y.plot(f, x.T, color=col(w), lw=0.3, alpha=0.35)
                y.plot(f, m, color=col(w), lw=1.6, label=f"{w:.0f} dBm{' (in the median)' if w > cut else ''}\nlevel median: rms %.2f, worst %.2f {u}\nevery sweep: rms %.2f, worst %.2f {u}" % (*st(m), *st(x)))
                print(f"  ref > {cut:.0f}  {w:5.0f} dBm  {u:3}  level median rms %6.2f worst %6.2f   every sweep rms %6.2f worst %6.2f" % (*st(m), *st(x)))
        env = np.nanmax(abs(np.concatenate([fe[w] for w in V if w > cut])), 0)    # worst over every sweep of the levels in the median
        L = [(lambda l: f"{l[1]:g}-{l[2]:g} MHz" if l[0] else "none")(longest(f, inb & (env <= e))) for e in (1, 2)]
        r, wst = st(env)
        bw, f0, benv = best_window(f, V, ref, cut, inb)
        txt = f"rms {r:.2f}, worst {wst:.1f} MHz\n<= 1 MHz at {np.mean(env[inb] <= 1):.0%} of frequencies, longest {L[0]}\n<= 2 MHz at {np.mean(env[inb] <= 2):.0%}, longest {L[1]}\nbest {WIN} MHz window (own lookup): {f0:g}-{f0 + WIN:g} MHz, worst {bw:.1f} MHz"

        print(f"  ref > {cut:.0f}: " + txt.replace("\n", "; "))
        ax[1].plot(f, env, "k" + "-:"[k], lw=1.3, label=f"power unknown, anywhere above {cut:.0f} dBm\n(calibration = median of those levels)\n" + txt)
        q = bx[k]
        q.axvspan(f0, f0 + WIN, color="#7570b3", alpha=0.08)
        q.plot(f, benv, color="#7570b3", lw=2.2, label=f"best {WIN} MHz window, its own lookup table:\nworst over every sweep {bw:.1f} MHz")
        for w in V:
            q.plot(f, abs(np.nanmedian(fe[w], 0)), color=col(w), lw=1.0, label=f"{w:.0f} dBm, level median") if w > cut else None
        q.plot(f, env, "k", lw=1.6, label="worst over every sweep\nof these levels\n" + txt)
        q.set(ylim=(0, 15), ylabel="frequency error (MHz)", title=f"Power unknown, anywhere from {max(V):.0f} dBm down to {min(w for w in V if w > cut):.0f} dBm (levels above {cut:.0f} dBm); calibration = median of those levels; reading exactly on one level's curve")
        a.set(ylabel="mV", title=f"Reading minus the median of the levels above {cut:.0f} dBm (thin: every sweep, thick: level median)")
        b.set(ylabel="MHz", ylim=(-12, 12), title=f"Frequency error, signed, per level (calibration = median of the levels above {cut:.0f} dBm; thin: every sweep, thick: level median)")
    for a in (ax[1], *bx):
        a.axhspan(0, 1, color="#1b9e77", alpha=0.12, label="<= 1 MHz")
        a.axhspan(1, 2, color="#e6ab02", alpha=0.12, label="1-2 MHz")
    ax[1].set(ylim=(0, 15), ylabel="worst frequency error (MHz)", title="Worst frequency error across the span: reading exactly on one level's curve, looked up in the median curve, worst over every sweep of the levels in that median")
    ax[0].set(ylabel="detector mV", title=c["title"])
    for a in (*ax, *bx):
        a.axhline(0, color="k", lw=0.5) if a is not ax[0] else None
        a.axvspan(c["lo"], c["band"][0], color="0.5", alpha=0.1) if c["band"][0] > c["lo"] else None
        a.set_xlim(c["lo"], c["hi"])
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1), labelspacing=0.8)
    for g, a, name, dpi in ((fig, ax, "uncertainty", 80), (fig2, bx, "freq_error", 90)):
        a[-1].set_xlabel("Pluto frequency (MHz)")
        g.tight_layout()
        g.savefig(HERE / f"pd_power_{name}_{c['name']}.png", dpi=dpi)


if __name__ == "__main__":
    D = R.rows()
    for c in CASES:
        plot(D, c)
