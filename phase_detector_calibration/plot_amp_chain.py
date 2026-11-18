"""Amplifier chain alone (run_amp_chain_iq.py, 18 Nov): output tone, instantaneous power from raw IQ, harmonics, and the ripple
left after a smooth trend, against frequency for every Pluto level. Marks the phase detector's peaks so a shared ~360 MHz
pattern shows at once. Saves amp_chain_18nov.png."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
OUT, RAW = HERE / "amp_chain_18nov.csv", HERE / "amp_chain"
PD_PEAKS = (770, 1160, 1510)
WIRING = ["Pluto TX\n-36 to -71 dBm", "7 cm", "4 x ZX60-P162LN+, 4.03 V\n7 cm cables between", "10 + 10 + 3 + 6 dB\npads (29 dB)",
          "SM200B, raw IQ\n50 MS/s, 16384 samples"]


def table():
    D = list(csv.DictReader(open(OUT)))
    lv = sorted({float(r["pluto_want_dbm"]) for r in D}, reverse=True)
    k = ["freq_mhz", "tone_dbm", "p01_dbm", "p50_dbm", "p99_dbm", "h2_dbm", "h3_dbm"]
    return {w: np.array(sorted({float(r["freq_mhz"]): [float(r[c]) for c in k] for r in D if float(r["pluto_want_dbm"]) == w}.values())) for w in lv}


def delay(f, y):
    """Strongest single delay (ns) and amplitude in the trend-removed ripple."""
    taus = np.arange(0.3, 4, 0.01)
    amp = 2 * np.abs(np.exp(-2j * np.pi * np.outer(taus, f * 1e-3)) @ y) / len(y)
    return taus[amp.argmax()], amp.max()


def main():
    if not OUT.exists():
        return print("no amp chain data yet")
    T = table()
    col = dict(zip(T, matplotlib.colormaps["viridis"](np.linspace(0, 0.9, len(T)))))
    fig, ax = wiring.figure(5, [WIRING], size=(14, 24), titles=["Wiring, 18 Nov: amplifier chain alone into the SM200B (no splitter, arms or mixer)"])
    for w, a in T.items():
        f, c = a[:, 0], col[w]
        ax[0].plot(f, a[:, 1], "-o", ms=2, color=c, label=f"{w:.0f} dBm in ({len(f)} points)")
        ax[1].fill_between(f, a[:, 2], a[:, 4], color=c, alpha=0.15)
        ax[1].plot(f, a[:, 3], color=c, lw=1)
        ax[2].plot(f, a[:, 5], "-", color=c, lw=1)
        ax[2].plot(f, a[:, 6], "--", color=c, lw=1)
        if len(f) > 8:
            r = a[:, 1] - np.polyval(np.polyfit(f, a[:, 1], 2), f)
            tau, A = delay(f, r)
            ax[3].plot(f, r, "-o", ms=2, color=c, label=f"{w:.0f} dBm: rms {r.std():.2f} dB, strongest delay {tau:.2f} ns ({1e3 / tau:.0f} MHz period), {A:.2f} dB")
    x = sorted(RAW.glob("1160_-50.npy")) or sorted(RAW.glob("*_-50.npy"))[:1]
    if x:
        iq = np.load(x[0])
        p = 10 * np.log10(np.abs(iq) ** 2 + 1e-20) + 29.0
        ax[4].plot(np.arange(len(p)) / 50.0, p, lw=0.4, color="#21918c")
        ax[4].set(xlabel="time (us)", ylabel="instantaneous power at amp output (dBm)",
                  title=f"Raw IQ, {x[0].stem.replace('_', ' MHz, ')} dBm in: every sample |I+jQ|^2 (+29 dB pads); mean {10 * np.log10(np.mean(np.abs(iq) ** 2)) + 29:.2f} dBm")
    for a in ax[:4]:
        for pk in PD_PEAKS:
            a.axvline(pk, color="#b30000", lw=0.8, ls=":")
        a.set_xlabel("Pluto frequency (MHz)")
        a.grid(alpha=0.3)
    ax[0].set(ylabel="tone at amp output (dBm)", title="Tone at the amplifier output (FFT line, pads added back). Red dotted: phase detector peaks 770, 1160, 1510 MHz")
    ax[1].set(ylabel="instantaneous power (dBm)", title="Instantaneous power over each 328 us capture: median (line), 1st to 99th percentile (band)")
    ax[2].set(ylabel="harmonic at amp output (dBm)", title="2nd harmonic (solid) and 3rd harmonic (dashed) at the amplifier output")
    ax[3].set(ylabel="tone minus quadratic trend (dB)", title="Ripple left after a smooth trend: a ~2.75 ns (~360 MHz) delay here would mean the amplifiers cause the detector pattern")
    for a in ax[:4:3]:
        a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(HERE / "amp_chain_18nov.png", dpi=90)
    print("amp_chain_18nov.png", {w: len(a) for w, a in T.items()})


if __name__ == "__main__":
    main()
