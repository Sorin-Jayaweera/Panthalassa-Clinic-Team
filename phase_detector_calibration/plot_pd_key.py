"""Key plots for the top of the Phase detector tab (cable E with the 3 dB LO pad and 6 dB RF pad). One data set per plot.
pd_key_dithered.png: the 14 Nov evening halving run (dithered, 50 mV/div): five Pluto levels over 1150-1550 MHz, and the same data
                     zoomed on the one-to-one (linear) region.
pd_key_wide.png:     the 14 Nov 10:51 sweep, 300-4000 MHz every 10 MHz at -50 dBm, not dithered (0.2 V/div).
Raw detector readings, nothing subtracted."""
import matplotlib

matplotlib.use("Agg")

import wiring
from pdlib import HERE, L5, chain, colours, fv, rows

LIN = (1215.0, 1445.0)


def wiring_for(scope, pluto):
    return [chain(pluto, "4.03 V, 0.22-0.29 A", scope=f", 1 Mohm\n{scope}")]


def dithered():
    B = [r for r in rows("pd_dither_14nov.csv") if r["stage"] in ("bisect5", "bisect5s")]
    C = {w: fv([r for r in B if float(r["pluto_want_dbm"]) == w], first=True) for w in L5}   # 1350 MHz is re-read as a drift check: first reading kept
    col = colours(L5)
    fig, ax = wiring.figure(2, wiring_for("50 mV/div, dithered\n(4 offsets 1 mV apart)", "-36 to -64 dBm"), size=(14, 12),
                            titles=["Wiring, 14 Nov evening: cable E, 3 dB pad at LO, 6 dB pad at RF"])
    for k, (lo, hi) in enumerate(((1145, 1555), (LIN[0] - 5, LIN[1] + 5))):
        for w, (f, v) in C.items():
            m, faded = (f >= lo) & (f <= hi), w == -64.0
            ax[k].plot(f[m], v[m], "--" if faded else "-o", color=col[w], ms=0 if faded else 3, lw=1.0 if faded else 1.5,
                       alpha=0.45 if faded else 1.0, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else "") + (" (noisy, faded)" if faded else ""))
        ax[k].set(xlim=(lo, hi), xlabel="Pluto frequency (MHz)", ylabel="detector output (mV, raw)")
        ax[k].grid(alpha=0.3)
        ax[k].legend(fontsize=9, ncol=5)
    n = C[-50.0].shape[1]
    ax[0].axvspan(*LIN, color="#1b9e77", alpha=0.08)
    ax[0].set_title(f"Phase detector output, 1150-1550 MHz, five Pluto levels: 14 Nov {B[0]['timestamp'][11:16]}-{B[-1]['timestamp'][11:16]}, {n} frequencies (6.25 MHz steps, 1.6 MHz on the rise); shaded = one-to-one region")
    ax[1].set_title(f"Same data, the one-to-one region {LIN[0]:.0f}-{LIN[1]:.0f} MHz: one voltage = one frequency; -36 to -57 dBm agree within +/-2 MHz on 90% of 1240-1430 MHz")
    fig.tight_layout()
    fig.savefig(HERE / "pd_key_dithered.png", dpi=95)
    print("pd_key_dithered.png", n, "frequencies per level")


def wide():
    O = [r for r in rows("pd_overnight_13nov.csv") if r["stage"] == "wide10_kitty"]
    a, u = fv([r for r in O if r["level_known"] == "1"]), fv([r for r in O if r["level_known"] != "1"])
    fig, ax = wiring.figure(1, wiring_for("0.2 V/div, not dithered", "-50 dBm"), size=(14, 6.5), titles=["Wiring, 14 Nov morning: cable E, 3 dB pad at LO, 6 dB pad at RF"])
    ax = ax[0]
    ax.plot(*a, "-o", ms=2.5, lw=1.2, color="#1b9e77", label=f"-50 dBm, {a.shape[1]} points")
    if u.size:
        ax.plot(*u, "o", ms=2, color="#999999", label=f"{u[0, 0]:.0f}-{u[0, -1]:.0f} MHz: no Pluto level table, attenuation held at 61 dB (well below -50 dBm), so not a detector reading")
    ax.axvspan(1150, 1550, color="#7570b3", alpha=0.08, label="1150-1550 MHz (the dithered plot above)")
    ax.axvspan(*LIN, color="#1b9e77", alpha=0.10, label="one-to-one region")
    ax.set(xlim=(250, 4050), xlabel="Pluto frequency (MHz)", ylabel="detector output (mV, raw)",
           title=f"Widest sweep, not dithered: 300-4000 MHz every 10 MHz at -50 dBm, 14 Nov {O[0]['timestamp'][11:16]}-{O[-1]['timestamp'][11:16]} (0.2 V/div: 8 mV ADC steps)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "pd_key_wide.png", dpi=95)
    print("pd_key_wide.png", a.shape[1], "points")


if __name__ == "__main__":
    dithered()
    wide()
