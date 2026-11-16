"""Key plots for the top of the Phase detector tab (cable E with the 3 dB LO pad and 6 dB RF pad). One data set per plot.
pd_key_dithered.png: the 14 Nov evening halving run (dithered, 50 mV/div): five Pluto levels over 1150-1550 MHz, and the same data
                     zoomed on the one-to-one (linear) region.
pd_key_wide.png:     the 14 Nov 10:51 sweep, 300-4000 MHz every 10 MHz at -50 dBm, not dithered (0.2 V/div).
Raw detector readings, nothing subtracted."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
LIN = (1215.0, 1445.0)


def rows(name):
    return list(csv.DictReader(open(HERE / name)))


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def wiring_for(scope, pluto):
    return [[f"Pluto TX\n{pluto}", "4 x ZX60-P162LN+\n4.03 V, 0.22-0.29 A", "ZFRSC-42-S+\nsplitter",
             ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
             "ZX05-30W-S+\nLO and RF in, IF out", [f"SDS1104X-E CH1, 1 Mohm\n{scope}", "20 dB of pads\nthen SM200B"]]]


def dithered():
    D = rows("pd_dither_14nov.csv")
    B = [r for r in D if r["stage"] in ("bisect5", "bisect5s")]
    pts = {w: {} for w in L5}
    for r in B:                                   # first reading at each frequency (1350 MHz is re-read as a drift check)
        pts[float(r["pluto_want_dbm"])].setdefault(float(r["freq_mhz"]), mv(r))
    t0, t1 = B[0]["timestamp"][11:16], B[-1]["timestamp"][11:16]
    col = dict(zip(L5, plt.cm.viridis(np.linspace(0, 0.9, len(L5)))))
    fig, ax = wiring.figure(2, wiring_for("50 mV/div, dithered\n(4 offsets 1 mV apart)", "-36 to -64 dBm"), size=(14, 12),
                            titles=["Wiring, 14 Nov evening: cable E, 3 dB pad at LO, 6 dB pad at RF"])
    for k, (lo, hi) in enumerate(((1145, 1555), (LIN[0] - 5, LIN[1] + 5))):
        for w in L5:
            a = np.array(sorted(pts[w].items()))
            m = (a[:, 0] >= lo) & (a[:, 0] <= hi)
            faded = w == -64.0
            ax[k].plot(a[m, 0], a[m, 1], "--" if faded else "-o", color=col[w], ms=0 if faded else 3, lw=1.0 if faded else 1.5,
                       alpha=0.45 if faded else 1.0, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else "") + (" (noisy, faded)" if faded else ""))
        ax[k].set(xlim=(lo, hi), xlabel="Pluto frequency (MHz)", ylabel="detector output (mV, raw)")
        ax[k].grid(alpha=0.3)
        ax[k].legend(fontsize=9, ncol=5)
    n = len(pts[-50.0])
    ax[0].axvspan(*LIN, color="#1b9e77", alpha=0.08)
    ax[0].set_title(f"Phase detector output, 1150-1550 MHz, five Pluto levels: 14 Nov {t0}-{t1}, {n} frequencies (6.25 MHz steps, 1.6 MHz on the rise); shaded = one-to-one region")
    ax[1].set_title(f"Same data, the one-to-one region {LIN[0]:.0f}-{LIN[1]:.0f} MHz: one voltage = one frequency; -36 to -57 dBm agree within +/-2 MHz on 90% of 1240-1430 MHz")
    fig.tight_layout()
    fig.savefig(HERE / "pd_key_dithered.png", dpi=95)
    print("pd_key_dithered.png", n, "frequencies per level")


def wide():
    O = [r for r in rows("pd_overnight_13nov.csv") if r["stage"] == "wide10_kitty"]
    a = np.array(sorted((float(r["freq_mhz"]), mv(r)) for r in O if r["level_known"] == "1"))
    u = np.array(sorted((float(r["freq_mhz"]), mv(r)) for r in O if r["level_known"] != "1"))
    fig, ax = wiring.figure(1, wiring_for("0.2 V/div, not dithered", "-50 dBm"), size=(14, 6.5),
                            titles=["Wiring, 14 Nov morning: cable E, 3 dB pad at LO, 6 dB pad at RF"])
    ax = ax[0]
    ax.plot(a[:, 0], a[:, 1], "-o", ms=2.5, lw=1.2, color="#1b9e77", label=f"-50 dBm, {len(a)} points")
    if len(u):
        ax.plot(u[:, 0], u[:, 1], "o", ms=2, color="#999999",
                label=f"{u[0, 0]:.0f}-{u[-1, 0]:.0f} MHz: no Pluto level table, attenuation held at 61 dB (well below -50 dBm), so not a detector reading")
    ax.axvspan(1150, 1550, color="#7570b3", alpha=0.08, label="1150-1550 MHz (the dithered plot above)")
    ax.axvspan(*LIN, color="#1b9e77", alpha=0.10, label="one-to-one region")
    ax.set(xlim=(250, 4050), xlabel="Pluto frequency (MHz)", ylabel="detector output (mV, raw)",
           title=f"Widest sweep, not dithered: 300-4000 MHz every 10 MHz at -50 dBm, 14 Nov {O[0]['timestamp'][11:16]}-{O[-1]['timestamp'][11:16]} (0.2 V/div: 8 mV ADC steps)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "pd_key_wide.png", dpi=95)
    print("pd_key_wide.png", len(a), "points")


if __name__ == "__main__":
    dithered()
    wide()
