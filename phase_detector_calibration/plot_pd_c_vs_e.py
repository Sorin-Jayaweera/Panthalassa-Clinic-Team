"""Cable C (1 Nov) against cable E with pads (14 Nov) and cable E without pads (13 and 15 Nov), all at -50 dBm at the Pluto.
Each setup in its own panel (different runs), with the local slope underneath. Saves pd_c_vs_e.png and prints the numbers."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, PADS, fv, rows, slope


def setup(arm, pads, scope):
    lo, rf = PADS if pads else ("no pad", "no pad")
    return ["Pluto TX\n-50 dBm", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", [f"right arm (LO): cable D\n{lo}", f"left arm (RF): cable B + {arm}\n{rf}"],
            "ZX05-30W-S+", [f"SDS1104X-E CH1\n{scope}"]]


def main():
    D = rows("pd_dither_14nov.csv")
    runs = [("1 Nov: cable C, no pads, 900-1200 MHz every 1 MHz", [r for r in rows("p162x4_fine_1nov.csv") if r["pluto_want_dbm"] == "-50.0"], (905, 1120), "#7570b3"),
            ("14 Nov: cable E WITH pads, 1150-1550 MHz (halving run, 1.6-6.25 MHz steps, dithered)",
             [r for r in D if r["stage"] in ("bisect5", "bisect5s") and r["pluto_want_dbm"] == "-50.0"], (1220, 1440), "#1b9e77"),
            ("13 Nov: cable E, no pads, 600-1700 MHz every 25 MHz", [r for r in rows("pd_cable_13nov_cableE.csv") if r["pass"] == "coarse"], (950, 1150), "#d95f02"),
            ("15 Nov: cable E, no pads, 1150-1550 MHz every 25 MHz, dithered",
             [r for r in D if r["stage"] == "coarse_np" and r["rep"] == "1" and r["pluto_want_dbm"] == "-50.0"], (1335, 1500), "#e7298a")]
    fig, ax = wiring.figure(4, [setup("C", False, "0.2 V/div"), setup("E", True, "50 mV/div, dithered"), setup("E", False, "0.2 V/div (13 Nov), 50 mV/div dithered (15 Nov)")],
                            size=(14, 21), titles=["Wiring, panel 1 (1 Nov)", "Wiring, panel 2 (14 Nov)", "Wiring, panels 3 and 4 (13 and 15 Nov)"], strip=0.3)
    for a, (t, rr, (lo, hi), c) in zip(ax, runs):
        f, v = fv(rr, first=True)
        a.plot(f, v, "-o", ms=2, lw=1.2, color=c)
        a.axvspan(lo, hi, color=c, alpha=0.08)
        m = (f >= lo) & (f <= hi)
        s = slope(f[m], v[m], 10 if np.median(np.diff(f)) < 5 else 25)
        k = np.polyfit(f[m], v[m], 1)
        res = v[m] - np.polyval(k, f[m])
        txt = (f"shaded {lo}-{hi} MHz ({hi - lo} MHz): swing {np.ptp(v[m]):.0f} mV, slope {np.percentile(s, 10):.2f} to {np.percentile(s, 90):.2f} mV/MHz "
               f"(10th-90th percentile, lowest {s.min():.2f}), off a straight line by {res.std():.0f} mV rms = {res.std() / k[0]:.0f} MHz")
        print(t, "|", txt)
        a.set(xlabel="Pluto frequency (MHz)", ylabel="detector (mV, raw)", title=t + "\n" + txt)
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "pd_c_vs_e.png", dpi=95)


if __name__ == "__main__":
    main()
