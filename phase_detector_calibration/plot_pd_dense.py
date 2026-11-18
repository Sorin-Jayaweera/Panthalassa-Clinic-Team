"""Dense sweep with pads at the mixer (cable E): voltage, slope, and the frequency error a 1 mV reading error gives.
Also every power-level pass present in the file. Saves pd_dense_E_pads.png."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, chain, fv, rows

R = rows("pd_cable_13nov_E_pads.csv")
K = [r for r in rows("pd_kitty_13nov_E_pads.csv") if float(r["freq_mhz"]) > 0]
RISE = (1228, 1440)
PASSES = [("power-60", "-60 dBm", "#1b9e77"), ("power-55", "-55 dBm", "#66a61e"), ("power-45", "-45 dBm", "#e6ab02"), ("power-40", "-40 dBm", "#a6761d")]


def get(name):
    return fv([r for r in R if r["pass"] == name])


def main():
    fig, ax = wiring.figure(3, [chain("level per curve", sm="20 dB of pads\nthen SM200B")], size=(14, 13),
                            titles=["Wiring, 13 Nov (D and B are the same length, so the length difference is cable E, about 8 cm)"])
    f, v = get("dense2")
    for name, lab, col in PASSES:
        d = get(name)
        if d.size:
            ax[0].plot(*d, color=col, lw=1, label=lab)
    ax[0].plot(f, v, "-", color="#d95f02", lw=1.6, marker="o", ms=2.5, label="-50 dBm, 2 MHz steps")
    kf, kv = fv(K, x="freq_mhz") if False else (np.array([float(r["freq_mhz"]) for r in K]), np.array([float(r["detector_mean_v"]) * 1e3 for r in K]))
    sel = (kf >= 1100) & (kf <= 1600)
    ax[0].plot(kf[sel], kv[sel], "s", color="k", ms=5, mfc="none", label="-50 dBm, 25 MHz steps, 15 min earlier")
    rise = (f >= RISE[0]) & (f <= RISE[1])
    s = np.gradient(v, f)
    err = np.where(s[rise] > 0.05, 1.0 / np.maximum(s[rise], 1e-9), np.nan)
    ax[0].set(ylabel="detector output (mV), raw", title=f"Detector output: rises the whole way from 1228 to 1440 MHz (shaded, {RISE[1] - RISE[0]:.0f} MHz), {v[rise].min():.0f} to {v[rise].max():.0f} mV")
    ax[0].legend(fontsize=8, loc="upper left")
    ax[1].plot(f, s, color="#d95f02", lw=1.2)
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set(ylabel="slope (mV per MHz)", title=f"Slope between neighbouring 2 MHz points: median {np.median(s[rise]):.2f}, from {s[rise].min():.2f} to {s[rise].max():.2f} mV/MHz in the shaded range")
    ax[2].semilogy(f[rise], err, color="#d95f02", lw=1.2)
    ax[2].axhline(2, color="#b30000", ls="--", lw=1, label="2 MHz")
    ax[2].set(ylabel="MHz per 1 mV of reading error", title="Frequency error from a 1 mV error in the reading (1 / slope); points with slope under 0.05 mV/MHz left out", ylim=(0.2, 50))
    ax[2].legend(fontsize=8)
    for a in ax[:2]:
        a.axvspan(*RISE, color="#d95f02", alpha=0.07)
    for a in ax[:3]:
        a.grid(alpha=0.3, which="both")
        a.set(xlabel="Pluto frequency (MHz)", xlim=(1145, 1555))
    fig.tight_layout()
    fig.savefig(HERE / "pd_dense_E_pads.png", dpi=100)
    print(HERE / "pd_dense_E_pads.png")


if __name__ == "__main__":
    main()
