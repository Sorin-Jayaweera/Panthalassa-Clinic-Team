"""Raw phase detector voltage vs frequency for each cable pair, -50 dBm from the Pluto. Saves pd_cable_compare.png."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, fv, mv, rows

WIRING = ["Pluto TX\n-50 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.23 A", "ZFRSC-42-S+\nsplitter",
          ["right arm (LO): cable D\n(pads run: 3 dB pad at LO)", "left arm (RF): B + C (1 Nov) or B + E\n(13 Nov; pads run: 6 dB pad at RF)"],
          "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "29 dB of pads (20 dB in\nthe pads run), then SM200B"]]


def med(rr, cond):
    v = [mv(r) for r in rr if cond(r)]
    return np.median(v) if v else np.nan


def main():
    fine1, map1, e, ek, base, ep = map(rows, ("p162x4_fine_1nov.csv", "p162x4_map_1nov.csv", "pd_cable_13nov_cableE.csv", "pd_kitty_13nov_cableE.csv",
                                              "pd_cable_13nov_baseline.csv", "pd_kitty_13nov_E_pads.csv"))
    zp, z1 = med(ep, lambda r: float(r["freq_mhz"]) == 0), med(map1, lambda r: r["pass"] in ("off", "start_off"))
    zb, ze = med(base, lambda r: r["pass"] == "off"), med(e, lambda r: r["pass"].endswith("_off"))
    at50 = lambda r: float(r["pluto_want_dbm"]) == -50
    series = [
        ("1 Nov, left B + C (C about 12 cm), 5 MHz steps", fv([r for r in map1 if r["pass"] == "map" and at50(r)]), "#7570b3", "-", z1),
        ("1 Nov, left B + C, 1 MHz steps", fv(filter(at50, fine1)), "#b3b0de", "-", z1),
        ("13 Nov, left B + C, before the scope jammed", fv([r for r in base if r["pass"] == "check" or (r["pass"] == "fine" and float(r["freq_mhz"]) > 0)]), "#7570b3", "none", zb),
        ("13 Nov, left B + E (E with adapter ~9 cm), 25 MHz steps", fv([r for r in e if r["pass"] == "coarse"]), "#d95f02", "-", ze),
        ("13 Nov, left B + E, repeat with the SM200B reading", fv(ek), "#1b9e77", "--", ze),
        ("13 Nov, left B + E, 3 dB pad on LO, 6 dB on RF, 25 MHz steps", fv([r for r in ep if float(r["freq_mhz"]) > 0]), "#e7298a", "-", zp)]
    fig, axes = wiring.figure(2, [WIRING], size=(14, 11), titles=["Wiring (right arm cable D throughout; left arm B + C on 1 Nov, B + E on 13 Nov)"])
    for ax, sub in zip(axes, (False, True)):
        for lab, (f, v), col, ls, z in series:
            if len(f):
                ax.plot(f, v - z if sub else v, "o" if ls == "none" else ls, color=col, lw=1.5, ms=7 if ls == "none" else 4,
                        marker="o" if ls == "none" or "25 MHz" in lab else None, label=lab)
        ax.grid(alpha=0.3)
        ax.set(xlabel="Pluto frequency (MHz)", xlim=(590, 1710))
    axes[0].set(ylabel="detector output (mV), raw", title=f"Raw scope reading, Pluto -50 dBm. Tone-off reading: 1 Nov {z1:.1f} mV, 13 Nov before the jam {zb:.1f} mV, 13 Nov with E {ze:.1f} mV, with pads {zp:.1f} mV")
    axes[1].set(ylabel="detector output minus tone-off reading (mV)", title="Same data with each run's tone-off reading subtracted")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(HERE / "pd_cable_compare.png", dpi=100)
    print(HERE / "pd_cable_compare.png")


if __name__ == "__main__":
    main()
