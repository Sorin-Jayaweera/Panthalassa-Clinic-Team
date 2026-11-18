"""14 Nov dithered runs (50 mV/div, 4 offsets 1 mV apart): the 1 MHz band sweep, and the band at seven Pluto levels -60 to -36 dBm.
Answers: how far does a change in input power move the reading, in MHz, across the band? Saves pd_levels_14nov.png and prints a summary."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, chain, colours, fv, rows, runs, slope, zero

ALL = rows("pd_dither_14nov.csv")
BREAK = "2026-11-14T15:00"       # run stopped 14:53, Pluto replugged, resumed 15:18: the curve came back about 11 mV higher
R = [r for r in ALL if r["timestamp"] < BREAK]
AFTER = [r for r in ALL if r["timestamp"] >= BREAK and r["stage"] == "levels"]
WIRING = [chain("-60 to -36 dBm", scope=", 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", sm="20 dB of pads\nthen SM200B (not read)")]
WT = ["Wiring, 14 Nov (D and B are the same length, so the length difference is cable E, about 8 cm)"]
GOOD = (1240.0, 1430.0)          # the rise, away from its flat ends


def main():
    z, zo = zero(R, ("0",)), zero(rows("pd_overnight_13nov.csv"))
    bf, bv = fv([r for r in R if r["stage"] == "band1"])
    of, ov = fv([r for r in rows("pd_overnight_13nov.csv") if r["stage"] == "band1"])
    sl = slope(bf, bv, 6)
    lv = sorted({float(r["pluto_want_dbm"]) for r in R if r["stage"] == "levels"})
    L = {w: fv([r for r in R if r["stage"] == "levels" and float(r["pluto_want_dbm"]) == w]) for w in lv}
    fl = max((L[w][0] for w in lv), key=len)
    V = np.array([[v[f == x][0] if np.any(f == x) else np.nan for x in fl] for f, v in L.values()]) - z   # NaN where a level has no point
    s_at = np.interp(fl, bf, sl)
    ref = np.nanmedian(V[[i for i, w in enumerate(lv) if w <= -40]], axis=0)
    err = (V - ref) / np.where(s_at > 0.15, s_at, np.nan)

    fig, ax = wiring.figure(4, WIRING, size=(14, 20), titles=WT)
    ax[0].plot(of, ov - zo, "-", color="#999999", lw=1.6, label="0.2 V/div (8 mV ADC steps), 11:35")
    ax[0].plot(bf, bv - z, "-", color="#d95f02", lw=1.2, label="50 mV/div + dither, 13:03")
    ax[0].set(ylabel="detector minus tone-off (mV)", title="Band sweep, 1 MHz steps, -50 dBm: the dithered reading against the 8 mV-step reading", xlim=(1145, 1555))
    ax[0].legend(fontsize=8)
    ax[1].plot(bf, sl, color="#d95f02", lw=1.2)
    ax[1].axhline(0, color="k", lw=0.8)
    g = (bf >= GOOD[0]) & (bf <= GOOD[1])
    ax[1].set(ylabel="slope (mV per MHz)", xlim=(1145, 1555),
              title=f"Slope of the dithered sweep (line fit over 13 MHz): {sl[g].min():.2f} to {sl[g].max():.2f}, median {np.median(sl[g]):.2f} mV/MHz in {GOOD[0]:.0f}-{GOOD[1]:.0f} MHz")
    col = colours(lv)
    for w, v, e in zip(lv, V, err):
        ax[2].plot(fl, v, "-o", color=col[w], ms=2.5, lw=1.1, label=f"{w:.0f} dBm")
        ax[3].plot(fl, e, "-o", color=col[w], ms=2.5, lw=1.1, label=f"{w:.0f} dBm")
    if AFTER:
        af, av = fv(AFTER)
        ax[2].plot(af, av - z, "--", color="#b30000", lw=1.4, label="-36 dBm after the 15:00 replug (about 11 mV higher)")
    ax[2].set(ylabel="detector minus tone-off (mV)", title="Band at seven Pluto levels, 4 MHz steps, dithered (all before 14:53 except the dashed line)")
    ax[2].legend(fontsize=8, ncol=4)
    ax[3].axhspan(-2, 2, color="#1b9e77", alpha=0.12, label="+/- 2 MHz")
    ax[3].set(ylabel="frequency error (MHz)", ylim=(-15, 15), xlim=(1215, 1457),
              title="Frequency error from input power alone: (reading at this level - median of the -60 to -40 dBm levels) / slope; left out where the slope is under 0.15 mV/MHz")
    ax[3].legend(fontsize=8, ncol=4)
    for a in ax[:4]:
        a.grid(alpha=0.3)
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[2:4]:
        a.axvspan(*GOOD, color="#1b9e77", alpha=0.05)
    fig.tight_layout()
    fig.savefig(HERE / "pd_levels_14nov.png", dpi=95)
    print(HERE / "pd_levels_14nov.png")
    gg = (fl >= GOOD[0]) & (fl <= GOOD[1])
    for lo, hi in ((-60.0, -40.0), (-56.0, -40.0), (-52.0, -40.0), (-60.0, -36.0)):
        k = [i for i, w in enumerate(lv) if lo <= w <= hi]
        if hi == -36.0:
            gg = gg & ~np.isnan(V[-1])
        span = np.nanmax(err[k][:, gg], axis=0) - np.nanmin(err[k][:, gg], axis=0)
        print(f"{lo:.0f} to {hi:.0f} dBm: peak-to-peak error, best {np.nanmin(span):.2f} MHz at {fl[gg][np.nanargmin(span)]:.0f}, worst {np.nanmax(span):.2f} MHz at {fl[gg][np.nanargmax(span)]:.0f}, median {np.nanmedian(span):.2f}; "
              f"share of band within +/-2 MHz (span <= 4): {np.mean(span <= 4) * 100:.0f}%; MHz ranges with span <= 4: "
              + ", ".join(f"{a:.0f}-{b:.0f}" for a, b in runs(fl[gg], span <= 4)))


if __name__ == "__main__":
    main()
