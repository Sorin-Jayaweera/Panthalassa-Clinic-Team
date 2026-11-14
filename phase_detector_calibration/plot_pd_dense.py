"""Dense sweep with pads at the mixer (cable E): voltage, slope, and the frequency error a 1 mV reading error gives.
Also every power-level pass present in the file. Saves pd_dense_E_pads.png."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
R = list(csv.DictReader(open(HERE / "pd_cable_13nov_E_pads.csv")))
K = [r for r in csv.DictReader(open(HERE / "pd_kitty_13nov_E_pads.csv")) if float(r["freq_mhz"]) > 0]


def get(name):
    rr = sorted((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in R if r["pass"] == name)
    return np.array(rr).T if rr else None


def main():
    fig, ax = wiring.figure(3, [["Pluto TX\nlevel per curve", "4 x ZX60-P162LN+\n4.03 V, 0.23 A", "ZFRSC-42-S+\nsplitter",
                                 ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
                                 "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "20 dB of pads\nthen SM200B"]]],
                           size=(14, 13), titles=["Wiring, 13 Nov (D and B are the same length, so the length difference is cable E, about 8 cm)"])
    f, v = get("dense2")
    passes = [("power-60", "-60 dBm", "#1b9e77"), ("power-55", "-55 dBm", "#66a61e"), ("power-45", "-45 dBm", "#e6ab02"), ("power-40", "-40 dBm", "#a6761d")]
    for name, lab, col in passes:
        d = get(name)
        if d is not None:
            ax[0].plot(d[0], d[1], color=col, lw=1, label=lab)
    ax[0].plot(f, v, "-", color="#d95f02", lw=1.6, marker="o", ms=2.5, label="-50 dBm, 2 MHz steps")
    kf = np.array([float(r["freq_mhz"]) for r in K]); kv = np.array([float(r["detector_mean_v"]) * 1e3 for r in K])
    sel = (kf >= 1100) & (kf <= 1600)
    ax[0].plot(kf[sel], kv[sel], "s", color="k", ms=5, mfc="none", label="-50 dBm, 25 MHz steps, 15 min earlier")
    rise = (f >= 1228) & (f <= 1440)
    ax[0].axvspan(1228, 1440, color="#d95f02", alpha=0.07)
    ax[0].set(ylabel="detector output (mV), raw", title=f"Detector output: rises the whole way from 1228 to 1440 MHz (shaded, {1440-1228:.0f} MHz), {v[rise].min():.0f} to {v[rise].max():.0f} mV")
    ax[0].legend(fontsize=8, loc="upper left")
    s = np.gradient(v, f)
    ax[1].plot(f, s, color="#d95f02", lw=1.2)
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].axvspan(1228, 1440, color="#d95f02", alpha=0.07)
    ax[1].set(ylabel="slope (mV per MHz)", title=f"Slope between neighbouring 2 MHz points: median {np.median(s[rise]):.2f}, from {s[rise].min():.2f} to {s[rise].max():.2f} mV/MHz in the shaded range")
    err = np.where(s[rise] > 0.05, 1.0 / np.maximum(s[rise], 1e-9), np.nan)
    ax[2].semilogy(f[rise], err, color="#d95f02", lw=1.2)
    ax[2].axhline(2, color="#b30000", ls="--", lw=1, label="2 MHz")
    ax[2].set(ylabel="MHz per 1 mV of reading error", title="Frequency error from a 1 mV error in the reading (1 / slope); points with slope under 0.05 mV/MHz left out", ylim=(0.2, 50))
    ax[2].legend(fontsize=8)
    for a in ax[:3]:
        a.grid(alpha=0.3, which="both")
        a.set_xlabel("Pluto frequency (MHz)")
        a.set_xlim(1145, 1555)
    fig.tight_layout()
    out = HERE / "pd_dense_E_pads.png"
    fig.savefig(out, dpi=100)
    print(out)


if __name__ == "__main__":
    main()
