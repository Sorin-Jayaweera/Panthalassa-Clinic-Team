"""Cable C (1 Nov) against cable E with pads (14 Nov) and cable E without pads (13 and 15 Nov), all at -50 dBm at the Pluto.
Each setup in its own panel (different runs), with the local slope underneath. Saves pd_c_vs_e.png and prints the numbers."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent


def rd(name):
    return list(csv.DictReader(open(HERE / name)))


def arr(pts):
    d = {}
    for f, v in pts:
        d.setdefault(f, v)
    return np.array(sorted(d.items()))


def slope(f, v, half=10):
    return np.array([np.polyfit(f[(f >= x - half) & (f <= x + half)], v[(f >= x - half) & (f <= x + half)], 1)[0] for x in f])


def setup(arm, pads, scope):
    lo, rf = ("3 dB pad at the LO port", "6 dB pad at the RF port") if pads else ("no pad", "no pad")
    return ["Pluto TX\n-50 dBm", "4 x ZX60-P162LN+", "ZFRSC-42-S+\nsplitter", [f"right arm (LO): cable D\n{lo}", f"left arm (RF): cable B + {arm}\n{rf}"],
            "ZX05-30W-S+", [f"SDS1104X-E CH1\n{scope}"]]


def main():
    C = arr((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in rd("p162x4_fine_1nov.csv") if r["pluto_want_dbm"] == "-50.0")
    D = rd("pd_dither_14nov.csv")
    EP = arr((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in D if r["stage"] in ("bisect5", "bisect5s") and r["pluto_want_dbm"] == "-50.0")
    EN13 = arr((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in rd("pd_cable_13nov_cableE.csv") if r["pass"] == "coarse")
    EN15 = arr((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in D if r["stage"] == "coarse_np" and r["rep"] == "1" and r["pluto_want_dbm"] == "-50.0")
    runs = [("1 Nov: cable C, no pads, 900-1200 MHz every 1 MHz", C, (905, 1120), "#7570b3"),
            ("14 Nov: cable E WITH pads, 1150-1550 MHz (halving run, 1.6-6.25 MHz steps, dithered)", EP, (1220, 1440), "#1b9e77"),
            ("13 Nov: cable E, no pads, 600-1700 MHz every 25 MHz", EN13, (950, 1150), "#d95f02"),
            ("15 Nov: cable E, no pads, 1150-1550 MHz every 25 MHz, dithered", EN15, (1335, 1500), "#e7298a")]
    fig, ax = wiring.figure(4, [setup("C", False, "0.2 V/div"), setup("E", True, "50 mV/div, dithered"), setup("E", False, "0.2 V/div (13 Nov), 50 mV/div dithered (15 Nov)")],
                            size=(14, 21), titles=["Wiring, panel 1 (1 Nov)", "Wiring, panel 2 (14 Nov)", "Wiring, panels 3 and 4 (13 and 15 Nov)"], strip=0.3)
    for a, (t, d, (lo, hi), c) in zip(ax, runs):
        f, v = d[:, 0], d[:, 1]
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
