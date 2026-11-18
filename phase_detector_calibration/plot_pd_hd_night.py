"""Detail plot of each high-density phase detector run in pd_runs.RUNS (pads removed): 600-1600 MHz at -36, -50 and -57 dBm,
one reading per point, 100 mV/div, with zooms on 900-1200 and 1300-1500 MHz (the regions filled first, 5 down to 0.625 MHz).
Raw readings, nothing subtracted. One figure per run, saved under the run's "detail" name. Loops over the table: a new run
needs no change here. Usage: python plot_pd_hd_night.py [tag ...] (default: every run with data)."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import pd_runs as R
import wiring

HERE = Path(__file__).resolve().parent
ZOOMS = ((595, 1605, "600-1600 MHz"), (895, 1205, "zoom 900-1200 MHz"), (1295, 1505, "zoom 1300-1500 MHz"))


def detail(D, run):
    P, (t0, t1) = R.load(D, run)
    fig, ax = wiring.figure(len(ZOOMS), [R.wiring_for(run)], size=(14, 16), titles=[f"Wiring, {run['day']}: {run['desc']}, no pads"])
    for k, (lo, hi, t) in enumerate(ZOOMS):
        for w in R.LEVELS:
            a = P[w]
            if not len(a):
                continue
            m = (a[:, 0] >= lo) & (a[:, 0] <= hi)
            ax[k].plot(a[m, 0], a[m, 1], "-o", ms=2.5 if k else 1.8, lw=1.1, color=R.LEVEL_COLOURS[w], label=f"{w:.0f} dBm ({m.sum()} points)")
        if k == 0:
            for a_, b_ in ((900, 1200), (1300, 1500)):
                ax[k].axvspan(a_, b_, color="#999999", alpha=0.08)
        ax[k].set(xlim=(lo, hi), xlabel="Pluto frequency (MHz)", ylabel="detector (mV, raw)", title=f"{run['day']}: {run['desc']}, {t}")
        ax[k].grid(alpha=0.3)
        ax[k].legend(fontsize=8)
    ax[0].set_title(f"{run['day']} {t0}-{t1}: {run['desc']}, no pads, 600-1600 MHz, three Pluto levels, one reading per point "
                    f"(tone-off {R.tone_off(D, run):.1f} mV; grey = priority regions, filled first)")
    fig.tight_layout()
    fig.savefig(HERE / run["detail"], dpi=95)
    print(run["detail"], {w: len(p) for w, p in P.items()})


def main(tags):
    D = R.rows()
    for run in R.present(D):
        if not tags or run["tag"] in tags:
            detail(D, run)


if __name__ == "__main__":
    main(sys.argv[1:])
