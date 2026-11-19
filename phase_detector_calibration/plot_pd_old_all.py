"""Every raw reading from the first delay-line setup (right arm cable D, left arm cable B + C, no pads at the mixer), 1 Nov 2026,
plus the 13 Nov check points on the same cables. Nothing averaged or subtracted: each curve is the scope reading as saved.
Saves pd_old_setup_all_raw.png."""
import datetime as dt

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring
from pdlib import HERE, colours, fv, mv, rows

MAP, FINE, KS, RAMP, BASE = map(rows, ("p162x4_map_1nov.csv", "p162x4_fine_1nov.csv", "p162x4_sm200b_1nov.csv", "p162x4_ramp_1nov.csv", "pd_cable_13nov_baseline.csv"))
WIRING = [["Pluto TX\nlevel per curve", "4 x ZX60-P162LN+\nabout 4 V (KUAIQU, then\nAgilent E3630A 3.94 V)", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D", "left arm (RF): cable B + C\n(C about 12 cm), no pads"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "pads, then SM200B\n(SM200B run only)"]]]
WT = ["Wiring, 1 Nov 2026 (the three-cable setup before cable E: D on the right, B + C on the left; D 16.6 cm, B 15.2 cm, C about 12 cm: RF arm longer by about 10.6 cm)"]
GROUPS = [("hold, 1054 MHz -60 dBm", ("hold",), "#d95f02"), ("tone off", ("off", "start_off"), "#1b9e77"),
          ("amplifiers unpowered: hold", ("bad_amps_off_hold",), "#b30000"), ("amplifiers unpowered: tone off", ("bad_amps_off_off",), "#e7298a")]


def at(rr, w):
    return [r for r in rr if float(r["pluto_want_dbm"]) == w]


def main():
    fig, ax = wiring.figure(5, WIRING, size=(15, 27), titles=WT)
    mp = [r for r in MAP if r["pass"] == "map"]
    for L, c in colours(sorted({float(r["pluto_want_dbm"]) for r in mp}), 0.95).items():
        f, v = fv(at(mp, L))
        ax[0].plot(f, v, "-o", color=c, lw=1, ms=2, label=f"{L:.0f} dBm ({len(f)} pts)")
    ax[0].set(xlim=(690, 1610), ylabel="detector output (mV), raw",
              title="Test 50, power map: 700-1600 MHz in 5 MHz steps at 13 Pluto levels, -85 to -30 dBm (top levels miss points where the Pluto hit its 31 dB attenuation floor)")
    ax[0].legend(fontsize=7.5, ncol=4, loc="upper left")
    for L, c in colours(sorted({float(r["pluto_want_dbm"]) for r in FINE}), 0.85, plt.cm.plasma).items():
        ax[1].plot(*fv(at(FINE, L)), "-", color=c, lw=1.1, label=f"{L:.0f} dBm, 1 MHz steps")
    f, v = fv([r for r in BASE if float(r["freq_mhz"]) > 0])
    if len(f):
        ax[1].plot(f, v, "kD", ms=7, mfc="none", label="13 Nov check points, same cables, -50 dBm")
    ax[1].set(xlim=(895, 1205), ylabel="detector output (mV), raw", title="Test 52, 1 MHz sweeps at six Pluto levels, 900-1200 MHz (Agilent supply)")
    ax[1].legend(fontsize=8, ncol=2)
    rep = [r for r in MAP if r["pass"] == "repeat"]
    n = {k: sum(int(r["rep"]) == k for r in rep) for k in {int(r["rep"]) for r in rep}}
    big = sorted(k for k in n if n[k] > 50)
    for rp, c in colours(big, cmap=plt.cm.cividis).items() if big else ():
        f, v = fv([r for r in rep if int(r["rep"]) == rp])
        ax[2].plot(f, v, "-", color=c, lw=1, label=f"repeat {rp}, -60 dBm ({len(f)} pts)")
    small = [r for r in rep if int(r["rep"]) not in big]
    if small:
        ax[2].plot([float(r["freq_mhz"]) for r in small], [mv(r) for r in small], ".", color="#d95f02", ms=4,
                   label=f"short repeats {min(int(r['rep']) for r in small)}-{max(int(r['rep']) for r in small)}, -60 dBm ({len(small)} pts)")
    f, v = fv([r for r in MAP if r["pass"] == "bad_amps_off_repeat"])
    if len(f):
        ax[2].plot(f, v, "x", color="#b30000", ms=6, label="amplifiers unpowered (bad run), -60 dBm")
    ax[2].set(xlim=(895, 1205), ylabel="detector output (mV), raw", title="Test 51, repeat sweeps at -60 dBm, every repeat as taken")
    ax[2].legend(fontsize=8, ncol=2)
    for L, c in colours(sorted({float(r["pluto_want_dbm"]) for r in KS})).items():
        ax[3].plot(*fv(at(KS, L)), "-s", color=c, ms=3.5, lw=1.2, label=f"SM200B run, {L:.0f} dBm")
    ax[3].set(ylabel="detector output (mV), raw", title="Scope reading during the SM200B run (IF spectrum taken at each point), four Pluto levels")
    ax[3].legend(fontsize=8)
    if RAMP:
        ins = ax[3].inset_axes([0.62, 0.08, 0.36, 0.42])
        ins.plot(*fv(RAMP, x="pluto_want_dbm"), "o-", color="#7570b3", ms=3)
        ins.set_title(f"power ramp at {float(RAMP[0]['freq_mhz']):.0f} MHz", fontsize=8)
        ins.set_xlabel("Pluto level (dBm)", fontsize=8)
        ins.set_ylabel("mV", fontsize=8)
        ins.tick_params(labelsize=7)
        ins.grid(alpha=0.3)
    t0 = min(dt.datetime.fromisoformat(r["timestamp"]) for r in MAP)
    hrs = lambda t: (t - t0).total_seconds() / 3600
    for lab, passes, col in GROUPS:
        t = [(hrs(dt.datetime.fromisoformat(r["timestamp"])), mv(r)) for r in MAP if r["pass"] in passes]
        if t:
            ax[4].plot(*np.array(t).T, "o", color=col, ms=3.5, label=f"{lab} ({len(t)})")
    w = []
    for line in open(HERE / "p162x4_tone_off_watch_1nov.csv"):
        p = line.strip().split(",")
        try:
            w.append((hrs(dt.datetime.fromisoformat(p[0])), float(p[1]) * 1e3))
        except (ValueError, IndexError):
            pass
    if w:
        ax[4].plot(*np.array(w).T, "^", color="#7570b3", ms=5, label=f"tone-off watch after the supply swap ({len(w)})")
    ax[4].set(xlabel=f"hours after {t0:%H:%M} on 1 Nov", ylabel="detector output (mV), raw", title="Held tone and tone-off readings through the evening")
    ax[4].legend(fontsize=8)
    for a in ax[:4]:
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[:5]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "pd_old_setup_all_raw.png", dpi=90)
    print(HERE / "pd_old_setup_all_raw.png")


if __name__ == "__main__":
    main()
