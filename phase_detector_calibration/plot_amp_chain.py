"""Amplifier chain alone (run_amp_chain_iq.py, 18 Nov): output tone, instantaneous power from raw IQ, harmonics, and the ripple
left after a smooth trend, against frequency for every Pluto level. Marks the phase detector's peaks so a shared ~360 MHz
pattern shows at once. Saves amp_chain_18nov.png."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import delay

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
            tau, A = delay(f, a[:, 1], deg=2)
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


def ramp():
    """Output against Pluto level (AMP_MODE=ramp): compression curve per frequency, noise share, ripple at fixed input, repeatability, raw IQ."""
    src = HERE / "amp_ramp_18nov.csv"
    if not src.exists():
        return print("no amp ramp data yet")
    d = np.genfromtxt(src, delimiter=",", names=True, dtype=None, encoding="utf-8")
    F, reps = np.unique(d["freq_mhz"]), np.unique(d["rep"])
    one = d[d["rep"] == 1]
    cf = dict(zip(F, matplotlib.colormaps["plasma"](np.linspace(0, 0.9, len(F)))))
    fig, ax = wiring.figure(5, [[WIRING[0].replace("-36 to -71", "-90 to -36"), *WIRING[1:]]], size=(14, 25),
                            titles=["Wiring, 18 Nov: amplifier chain alone into the SM200B; Pluto level stepped 1 dB at fixed frequencies"])
    for f in F:
        m = one["freq_mhz"] == f
        ax[0].plot(one["pluto_want_dbm"][m], one["tone_dbm"][m], "-", color=cf[f], lw=1.2 if f in PD_PEAKS else 0.8, label=f"{f:.0f} MHz" + (" (detector peak)" if f in PD_PEAKS else ""))
        ax[1].plot(one["pluto_want_dbm"][m], one["p_mean_dbm"][m] - one["tone_dbm"][m], "-", color=cf[f], lw=0.8)
    for w, c in zip((-85.0, -75.0, -65.0, -55.0, -45.0, -36.0), matplotlib.colormaps["viridis"](np.linspace(0, 0.9, 6))):
        m = one["pluto_want_dbm"] == w
        ax[2].plot(one["freq_mhz"][m], one["tone_dbm"][m], "-o", ms=3, color=c, label=f"{w:.0f} dBm in")
    if len(reps) > 1:
        for f in F:
            m = d["freq_mhz"] == f
            lv = np.unique(d["pluto_want_dbm"][m])
            sp = [np.ptp(d["tone_dbm"][m & (d["pluto_want_dbm"] == w)]) for w in lv]
            ax[3].plot(lv, sp, "-", color=cf[f], lw=0.8)
    x = sorted((HERE / "amp_ramp").glob("1_1160_*.npy"), key=lambda p: float(p.stem.split("_")[2]))
    for p, c in zip(x[::9], matplotlib.colormaps["viridis"](np.linspace(0, 0.9, len(x[::9])))):
        q = 10 * np.log10(np.abs(np.load(p)) ** 2 + 1e-20) + 29.0
        ax[4].hist(q, bins=150, range=(-20, 30), histtype="step", color=c, density=True, label=f"{p.stem.split('_')[2]} dBm in")
    ax[0].set(xlabel="Pluto level (dBm)", ylabel="tone at amp output (dBm)", title="Compression curve: tone out against Pluto level at each frequency (rep 1)")
    ax[1].set(xlabel="Pluto level (dBm)", ylabel="all power minus tone (dB)", title="Mean instantaneous power in 41.5 MHz minus the tone line: how much of the output is noise and spurs, not the tone")
    ax[2].set(xlabel="Pluto frequency (MHz)", ylabel="tone at amp output (dBm)", title="Tone against frequency at fixed Pluto levels (rep 1). Red dotted: phase detector peaks")
    ax[3].set(xlabel="Pluto level (dBm)", ylabel="spread over reps (dB)", title=f"Repeatability: max minus min tone over {len(reps)} reps, per frequency")
    ax[4].set(xlabel="instantaneous power at amp output (dBm)", ylabel="density", title="Raw IQ at 1160 MHz: distribution of |I+jQ|^2 per sample, rep 1, every 9th level")
    for pk in PD_PEAKS:
        ax[2].axvline(pk, color="#b30000", lw=0.8, ls=":")
    for a in ax[:5]:
        a.grid(alpha=0.3)
    for a in (ax[0], ax[2], ax[4]):
        a.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(HERE / "amp_ramp_18nov.png", dpi=90)
    print("amp_ramp_18nov.png", len(F), "frequencies,", len(reps), "reps")


if __name__ == "__main__":
    main()
    ramp()
