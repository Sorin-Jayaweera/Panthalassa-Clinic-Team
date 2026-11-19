"""Theory against measurement for every phase detector arrangement (Sorin, 19 Nov).
An ideal delay-line phase detector gives V(f) = A cos(2 pi f tau) + C with tau = (RF arm - LO arm) / (VF c). Constants ignored (Sorin):
each panel shows only the cosine, -1 to +1, against frequency.
  theory: cos(2 pi f tau), tau from the measured cable lengths at an assumed VF 0.70 (typical PTFE coax), phase 0;
  measured: the run's strongest level, scaled so its own min..max spans -1..+1 (removes A and C; exaggerates a run that swings less than a full cycle);
  fit (less important): best single cosine, tau scanned 0.02-2.5 ns (pdlib.delay), scaled the same way as the measured data.
Last panel: every theory cosine together. Saves pd_theory_vs_measured.png and prints the table."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import pd_runs as R
import pdlib
import wiring
from plot_pd_resolution import setups

HERE = Path(__file__).resolve().parent
VF, C_CM_NS = 0.70, 29.98
SKIP = ("pad10", "pad10z40", "pad10z40n", "pad10zn")       # same arms as pad10z (subranges / unzoomed): one panel for that arrangement


def cosfit(f, v, tau, free_phase):
    """Least squares v = a cos(2 pi f tau) [+ b sin] + c; returns the fitted curve and rms residual."""
    ph = 2 * np.pi * f * tau / 1e3
    X = np.column_stack([np.cos(ph), np.sin(ph), np.ones_like(f)] if free_phase else [np.cos(ph), np.ones_like(f)])
    y = X @ np.linalg.lstsq(X, v, rcond=None)[0]
    return y, np.sqrt(np.mean((v - y) ** 2))


def arrangements(D):
    """(name, RF-LO cm, f MHz, mV at the strongest level, colour, arms text) for every arrangement with data."""
    old = setups()[:2]
    out = []
    for (name, levels, rows, col, _, _), dl, arms in zip(old, (11.4, 7.6), ("RF: B + C (4.5 in longer), LO: D, no pads", "RF: B + E, LO: D, 3 dB LO / 6 dB RF pads")):
        p = sorted({f: v for f, w, v in rows[::-1] if w == max(levels)}.items())
        out.append((name, dl, *map(np.array, zip(*p)), col, arms))
    for run in R.present(D):
        if run["tag"] not in SKIP:
            L, _ = R.load(D, run)
            w = max(k for k in L if len(L[k]))
            out.append((f"{run['tag']} ({run['day']}): {run['desc']}, {run.get('pads', 'no pads')}", run["dl"], L[w][:, 0], L[w][:, 1], run["col"],
                        " | ".join(a.replace("\n", " ") for a in run["arms"])))
    return out


def main():
    A = arrangements(R.rows())
    fig, ax = wiring.figure(len(A) + 1, [["Pluto TX\nstrongest level per run", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", ["LO arm (per panel)", "RF arm (per panel)"],
                                         "ZX05-30W-S+", "IF -> SDS1104X-E CH1"]], size=(20, 3.6 * (len(A) + 1) + 2), strip=0.25,
                            titles=["Wiring common to every run; each panel's title gives that run's arms and pads"])
    F = np.linspace(600, 1600, 1001)
    for a, (name, dl, f, v, col, arms) in zip(ax, A):
        lo, hi = v.min(), v.max()
        norm = lambda y: 2 * (y - lo) / (hi - lo) - 1
        t0 = abs(dl) / (VF * C_CM_NS) if dl is not None else np.nan
        tf = pdlib.delay(f, v, deg=0, taus=np.arange(0.02, 2.5, 0.002))[0]
        if dl is not None:
            a.plot(F, np.cos(2 * np.pi * F * t0 / 1e3), "--", color="#d95f02", lw=2, label=f"theory: RF - LO = {dl:+.1f} cm, VF {VF}\ntau = {t0:.2f} ns, cos(2 pi f tau)")
        a.plot(f, norm(v), "o-", ms=2.5, lw=0.6, color=col, label=f"measured, scaled to its own range\n({lo:.0f} to {hi:.0f} mV)")
        a.plot(f, norm(cosfit(f, v, tf, True)[0]), "k-", lw=0.9, label=f"fit: tau = {tf:.2f} ns" + (" (at the scan limit)" if tf > 2.49 else ""))
        print(f"{name.split(':')[0]:40s} RF-LO {dl if dl is not None else float('nan'):+6.1f} cm  theory {t0:5.2f} ns  fit {tf:5.2f} ns")
        a.set(ylabel="cos", ylim=(-1.15, 1.15), xlim=(600, 1600), title=f"{name}\n{arms}")
        a.title.set_fontsize(9)
    for name, dl, *_ , col, _ in A:
        ax[-1].plot(F, np.cos(2 * np.pi * F * abs(dl) / (VF * C_CM_NS) / 1e3), color=col, lw=1.4, label=f"{name.split(' (')[0]}: {dl:+.1f} cm") if dl is not None else None
    ax[-1].set(ylabel="cos", ylim=(-1.15, 1.15), xlim=(600, 1600), title=f"Theory only, every arrangement, VF {VF}: cos(2 pi f tau)")
    for a in ax:
        a.axhline(0, color="k", lw=0.5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
        a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    fig.savefig(HERE / "pd_theory_vs_measured.png", dpi=75)


if __name__ == "__main__":
    main()
