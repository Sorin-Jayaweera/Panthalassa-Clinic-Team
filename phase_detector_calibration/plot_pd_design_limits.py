"""What limits the phase detector, and what to change to read frequency to +/-2 MHz over 200 MHz (19 Nov). Four questions:
1. How weak may the weakest pulse be? Longest stretch with total width <= 4 MHz (Sorin's method, plot_pd_x_uncertainty.measure)
   against the threshold level, every run with two or more levels.
2. What does the power dependence look like? pad10hf: each level's reading minus the railed median curve M, every frequency.
3. Is it power or drift? Every pass of every padded run fitted against M over the whole band: d = a (M - mean M) - s M' + c,
   a = gain change (%), s = shift of the curve along frequency (MHz), c = DC offset (mV). Vectorised least squares, all passes
   at once. Passes at the same level that agree mean a systematic power effect, not drift.
4. What would another cable do? Gain, shift and offset errors all become frequency errors divided by the slope, which scales
   with tau, while the monotonic half-cycle shrinks as 1/tau. With r = tau_new / tau_now: width_new(phase) = width_now(phase) / r
   and span(r) = longest(width_now <= 4 r) / r, read off pad10hf's measured width (the only run with a clean half-cycle);
   plotted against the arm difference r x 24.7 cm, with every padded run's measured span as a dot. Assumes the level
   dependence stays the same in phase (set by the amplifiers and mixer, not the cable) and the pads keep reflections down.
Saves pd_design_limits_19nov.png."""
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import pdlib
import wiring
from plot_pd_resolution import longest
from plot_pd_x_uncertainty import LIMIT, RAILED, grid, measure, runs

HERE = Path(__file__).resolve().parent
CABLES = dict(B=15.2, D=16.6, E=9.0, F=16.5, G=15.5, H=7.0)          # cm (Sorin, 18-19 Nov; E with its adapter)
PADDED, BASE = ("pad10z", "pad10zn", "pad10d", "pad10hf"), "pad10hf"
run = lambda tag: R.RUNS[[r["tag"] for r in R.RUNS].index(tag)]


def fit_passes(rows, levels):
    """Every pass against the railed median M over every frequency all passes share: level per pass, (gain %, shift MHz, offset mV) per pass, tau (ns)."""
    f, ws, X = grid(rows, levels)
    M = np.nanmedian(X[ws >= RAILED], 0)
    ok = ~np.isnan(X).any(0)
    k = np.linalg.lstsq(np.c_[M - M.mean(), -np.gradient(M, f), np.ones_like(f)][ok], (X - M)[:, ok].T, rcond=None)[0]
    return ws, np.c_[100 * k[0], k[1], k[2]], pdlib.delay(f, M, deg=0, taus=np.arange(0.02, 2.5, 0.002))[0]


def main():
    data = {name.split(" ")[0]: (name, rows, L) for name, rows, L, *_ in runs(R.rows())}
    fig, ax = wiring.figure(5, [["Pluto TX", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", ["LO arm (per run)", "RF arm (per run)"], "10 dB pads\n(padded runs)", "ZX05-30W-S+", "IF -> SDS1104X-E CH1"]],
                            size=(20, 30), strip=0.22, titles=["Wiring common to every run; each run's arms are in pd_runs.py and its own figure"])
    span = lambda tag, T: measure(data[tag][1], tuple(w for w in data[tag][2] if w >= T))
    for tag, (name, rows, L) in data.items():                             # 1: span against the threshold
        if len(L) > 1:
            t = sorted(L, reverse=True)[1:]
            ax[0].plot(t, [span(tag, x)[5][0] for x in t], "o-", ms=4, lw=1.6 if tag in PADDED else 0.7, color=run(tag)["col"] if tag in [r["tag"] for r in R.RUNS] else "0.5", label=name[:115])
    ax[0].axvline(RAILED, color="k", ls="--", lw=0.8, label=f"lowest railed level ({RAILED:.0f} dBm, 18 Nov amplifier ramp)")
    ax[0].set(xlabel="threshold: weakest Pluto level allowed (dBm)", ylabel="longest stretch with\ntotal width <= 4 MHz (MHz)", title="1. How weak may the weakest pulse be? Longest usable stretch against the threshold level, every run (thick = 10 dB pads)")
    name, rows, L = data[BASE]                                            # 2: what the power dependence looks like
    f, ws, X = grid(rows, L)
    M = np.nanmedian(X[ws >= RAILED], 0)
    for w in L:
        ax[1].plot(f, np.nanmedian(X[ws == w], 0) - M, "-", lw=1.1, color=R.matplotlib.colormaps["viridis"](0.9 * L.index(w) / max(len(L) - 1, 1)), label=f"{w:.0f} dBm")
    ax[1].set(ylim=(-25, 25), xlim=(600, 1600), xlabel="Pluto frequency (MHz)", ylabel="reading minus railed\nmedian curve (mV)", title=f"2. What the power dependence looks like, {BASE}: each level minus the railed median curve")
    for tag in PADDED:                                                    # 3: power or drift?
        ws, k, tau = fit_passes(*data[tag][1:])
        for q, y in zip(ax[2:4], k[:, :2].T):
            q.plot(ws + 0.4 * (PADDED.index(tag) - 1.5), y, "o", ms=5, mfc="none", color=run(tag)["col"],
                   label=f"{tag} (RF - LO {run(tag)['dl']:+.1f} cm, tau {tau:.2f} ns): {data[tag][0].split(': ', 1)[1][:70]}; one circle per pass")
    ax[2].set(ylim=(-70, 10), ylabel="gain change against\nthe railed median (%)", title="3a. Power or drift? Gain change of every pass (circles at one level that agree = a systematic power effect)")
    ax[3].set(ylim=(-12, 12), ylabel="curve shift along\nfrequency (MHz)", title="3b. Shift of every pass's curve along frequency against the railed median (an arm phase change; a shift is read directly as a frequency error)")
    for q in ax[2:4]:
        q.axvline(RAILED, color="k", ls="--", lw=0.8)
        q.axhline(0, color="k", lw=0.5)
        q.set_xlabel("Pluto level (dBm), runs offset slightly so circles do not overlap")
    r = np.linspace(0.2, 2.6, 240)                                        # 4: what another cable would give
    for T, ls in ((RAILED, "-"), (-50.0, "--")):
        f, med, o, width, *_ = span(BASE, T)
        ax[4].plot(r * run(BASE)["dl"], [longest(f, width <= 2 * LIMIT * x)[0] / x for x in r], ls, color=run(BASE)["col"], lw=1.6,
                   label=f"predicted from {BASE}'s measured width, threshold {'railed (>= -58 dBm)' if T == RAILED else '-50 dBm'}")
        for tag in PADDED:
            ax[4].plot(abs(run(tag)["dl"]), span(tag, T)[5][0], "o" if T == RAILED else "s", ms=8, mfc=run(tag)["col"] if T == RAILED else "none", color=run(tag)["col"],
                       label=f"measured: {tag}, {'railed' if T == RAILED else '-50 dBm'}" + (" (900-1200 MHz only)" if tag == "pad10zn" else ""))
    pairs = {}
    for lo in CABLES:
        for n in (1, 2):
            for rf in combinations([c for c in CABLES if c != lo], n):
                pairs.setdefault(round(sum(CABLES[c] for c in rf) - CABLES[lo]), f"{' + '.join(rf)} vs {lo}")
    for x, t in sorted(pairs.items()):
        if 15 <= x <= 45:
            ax[4].plot([x, x], [0, 25], color="0.4", lw=0.8)
            ax[4].text(x, 28, t, rotation=90, fontsize=7, ha="center", va="bottom")
    ax[4].axhline(200, color="r", ls=":", lw=1.2, label="200 MHz requirement")
    ax[4].set(xlim=(0, 60), ylim=(0, 600), xlabel="RF arm minus LO arm (cm)", ylabel="longest stretch with\ntotal width <= 4 MHz (MHz)",
              title="4. What another cable would give (ticks = cable pairs on hand, RF cables in series vs one LO cable, 15-45 cm; joints and adapters not counted)")
    ax[0].axhline(200, color="r", ls=":", lw=1.2, label="200 MHz requirement")
    for a in ax:
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
    fig.tight_layout()
    fig.savefig(HERE / "pd_design_limits_19nov.png", dpi=75)


if __name__ == "__main__":
    main()
