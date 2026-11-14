"""Raw phase detector voltage vs frequency for each cable pair, -50 dBm from the Pluto. Saves pd_cable_compare.png."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent


def rows(name):
    p = HERE / name
    return list(csv.DictReader(open(p))) if p.exists() else []


def curve(rr, cond):
    pts = sorted((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in rr if cond(r))
    return np.array(pts).T if pts else (np.array([]), np.array([]))


def main():
    fine1, map1 = rows("p162x4_fine_1nov.csv"), rows("p162x4_map_1nov.csv")
    e, ek = rows("pd_cable_13nov_cableE.csv"), rows("pd_kitty_13nov_cableE.csv")
    base = rows("pd_cable_13nov_baseline.csv")
    ep = rows("pd_kitty_13nov_E_pads.csv")
    zp = np.median([float(r["detector_mean_v"]) * 1e3 for r in ep if float(r["freq_mhz"]) == 0]) if ep else np.nan
    z1 = np.median([float(r["detector_mean_v"]) * 1e3 for r in map1 if r["pass"] in ("off", "start_off")])
    zb = np.median([float(r["detector_mean_v"]) * 1e3 for r in base if r["pass"] == "off"]) if base else np.nan
    ze = np.median([float(r["detector_mean_v"]) * 1e3 for r in e if r["pass"].endswith("_off")])
    series = [
        ("1 Nov, left B + C (C about 12 cm), 5 MHz steps", curve(map1, lambda r: r["pass"] == "map" and float(r["pluto_want_dbm"]) == -50), "#7570b3", "-", z1),
        ("1 Nov, left B + C, 1 MHz steps", curve(fine1, lambda r: float(r["pluto_want_dbm"]) == -50), "#b3b0de", "-", z1),
        ("13 Nov, left B + C, before the scope jammed", curve(base, lambda r: r["pass"] == "check" or (r["pass"] == "fine" and float(r["freq_mhz"]) > 0)), "#7570b3", "none", zb),
        ("13 Nov, left B + E (E about 8 cm), 25 MHz steps", curve(e, lambda r: r["pass"] == "coarse"), "#d95f02", "-", ze),
        ("13 Nov, left B + E, repeat with the SM200B reading", curve(ek, lambda r: True), "#1b9e77", "--", ze),
        ("13 Nov, left B + E, 3 dB pad on LO, 6 dB on RF, 25 MHz steps", curve(ep, lambda r: float(r["freq_mhz"]) > 0), "#e7298a", "-", zp),
    ]
    fig, axes = wiring.figure(2, [["Pluto TX\n-50 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.23 A", "ZFRSC-42-S+\nsplitter",
                                    ["right arm (LO): cable D\n(pads run: 3 dB pad at LO)", "left arm (RF): B + C (1 Nov) or B + E\n(13 Nov; pads run: 6 dB pad at RF)"],
                                    "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "29 dB of pads (20 dB in\nthe pads run), then SM200B"]]],
                              size=(14, 11), titles=["Wiring (right arm cable D throughout; left arm B + C on 1 Nov, B + E on 13 Nov)"])
    for ax, sub in zip(axes, (False, True)):
        for lab, (f, v), col, ls, z in series:
            if not len(f):
                continue
            y = v - z if sub else v
            if ls == "none":
                ax.plot(f, y, "o", color=col, ms=7, label=lab)
            else:
                ax.plot(f, y, ls, color=col, lw=1.5, marker="o" if "25 MHz" in lab else None, ms=4, label=lab)
        ax.grid(alpha=0.3)
        ax.set_xlabel("Pluto frequency (MHz)")
        ax.set_xlim(590, 1710)
    axes[0].set(ylabel="detector output (mV), raw", title=f"Raw scope reading, Pluto -50 dBm. Tone-off reading: 1 Nov {z1:.1f} mV, 13 Nov before the jam {zb:.1f} mV, 13 Nov with E {ze:.1f} mV, with pads {zp:.1f} mV")
    axes[1].set(ylabel="detector output minus tone-off reading (mV)", title="Same data with each run's tone-off reading subtracted")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    out = HERE / "pd_cable_compare.png"
    fig.savefig(out, dpi=100)
    print(out)


if __name__ == "__main__":
    main()
