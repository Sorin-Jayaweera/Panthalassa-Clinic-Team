"""Pads removed: every high-density 600-1600 MHz run, one panel each, then their -50 dBm curves together.
  hdr  15 Nov 20:03  cable E arm (B 15.2 cm + E ~9 cm, D 16.6 cm), long IF cable to the scope (and SM200B), 1 Mohm
  ifs  15 Nov 20:33  same, short IF cable (~16 cm SMA + SMA-BNC), 1 Mohm
  sc   18 Nov 10:39  very short cables at every mixer connection, IF into the scope with a 50 ohm load
Same sweep plan for all (run_pd_overnight.py HD_NIGHT, tag = HD_TAG): -36/-50/-57 dBm, one reading per point, 100 mV/div.
A new run is one more row in pd_runs.RUNS. The comparison panel scales each run to its own swing (the 50 ohm load lowers the
voltage), because comparing the shapes is the point of that panel. Raw readings in the other panels.
Saves pd_ifs_vs_long_15nov.png (all runs) and prints the -50 dBm peaks and best single delay of each run."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring

import pd_runs as R
from pdlib import delay

HERE = Path(__file__).resolve().parent


def peaks(a):
    f, v = a[:, 0], a[:, 1]
    out = []
    for k in range(len(f)):
        w = np.abs(f - f[k]) <= 60
        if v[k] == v[w].max() and v[k] - v[w].min() > 0.06 * np.ptp(v) and 0 < k < len(f) - 1:
            out.append(f[k])
    return out


def main():
    D = R.rows()
    runs = R.present(D)
    n = len(runs)
    fig, ax = wiring.figure(n + 1, [R.wiring_for(r) for r in runs], size=(14, 5.2 * (n + 1) + 2),
                            titles=[f"Wiring, panel {k + 1} ({r['day']}): {r['desc']}" for k, r in enumerate(runs)], strip=0.2)
    data = {}
    near50 = lambda P: min(P, key=lambda w: abs(w + 50))   # runs with other level sets (pad10) use their nearest level
    for k, run in enumerate(runs):
        P, (t0, t1) = R.load(D, run)
        data[run["tag"]] = P
        for w in R.levels(run):
            if len(P[w]):
                ax[k].plot(P[w][:, 0], P[w][:, 1], "-o", ms=1.8, lw=1.0, color=R.colour(run, w), label=f"{w:.0f} dBm ({len(P[w])} points)")
        a = P[near50(P)]
        pk = peaks(a) if len(a) > 10 else []
        tau, amp = delay(a[:, 0], a[:, 1]) if len(a) > 20 and np.ptp(a[:, 0]) > 500 else (np.nan, np.nan)
        dl = f"; best single delay {tau:.2f} ns ({1e3 / tau:.0f} MHz cycle)" if tau == tau else "; too little range yet for a delay fit"
        ax[k].set(title=f"{run['day']} {t0}-{t1}: {run['desc']}; tone-off {R.tone_off(D, run):.1f} mV; "
                        f"-50 dBm peaks near {', '.join(f'{p:.0f}' for p in pk) or '-'} MHz{dl}", ylabel="detector (mV, raw)")
        print(run["tag"], run["day"], "peaks -50:", [float(x) for x in pk], "delay ns:", round(tau, 3) if tau == tau else None,
              "amp mV:", round(amp, 1) if amp == amp else None, "tone-off:", round(R.tone_off(D, run), 1), {w: len(P[w]) for w in P})
    for run in runs:
        a = data[run["tag"]][near50(data[run["tag"]])]
        if len(a) > 2:
            ax[n].plot(a[:, 0], (a[:, 1] - np.median(a[:, 1])) / np.ptp(a[:, 1]), run["ls"], lw=1.3, color=run["col"],
                       label=f"{run['day']}: {run['desc']} (swing {np.ptp(a[:, 1]):.0f} mV)")
    ax[n].set(title="All runs at the level nearest -50 dBm, each scaled to its own swing (runs overlaid on purpose: is the ~360 MHz pattern still there?)",
              ylabel="detector / its own swing")
    for a in ax[:n + 1]:
        a.set(xlim=(595, 1605), xlabel="Pluto frequency (MHz)")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "pd_ifs_vs_long_15nov.png", dpi=90)


if __name__ == "__main__":
    main()
