"""Every raw reading from the first delay-line setup (right arm cable D, left arm cable B + C, no pads at the mixer), 1 Nov 2026,
plus the 13 Nov check points on the same cables. Nothing averaged or subtracted: each curve is the scope reading as saved.
Saves pd_old_setup_all_raw.png."""
import csv
import datetime as dt
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


MAP, FINE, KS, RAMP = rows("p162x4_map_1nov.csv"), rows("p162x4_fine_1nov.csv"), rows("p162x4_sm200b_1nov.csv"), rows("p162x4_ramp_1nov.csv")
BASE = rows("pd_cable_13nov_baseline.csv")
WIRING = [["Pluto TX\nlevel per curve", "4 x ZX60-P162LN+\nabout 4 V (KUAIQU, then\nAgilent E3630A 3.94 V)", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D", "left arm (RF): cable B + C\n(C about 12 cm), no pads"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "pads, then SM200B\n(SM200B run only)"]]]
WT = ["Wiring, 1 Nov 2026 (the three-cable setup before cable E: D on the right, B + C on the left; D and B are the same length, so the length difference is cable C)"]


def curve(rr, cond, fkey="freq_mhz"):
    a = np.array(sorted((float(r[fkey]), float(r["detector_mean_v"]) * 1e3) for r in rr if cond(r)))
    return (a[:, 0], a[:, 1]) if len(a) else (np.array([]), np.array([]))


def mins(rr, cond):
    t = [(dt.datetime.fromisoformat(r["timestamp"]), float(r["detector_mean_v"]) * 1e3) for r in rr if cond(r)]
    return t


def main():
    fig, ax = wiring.figure(5, WIRING, size=(15, 27), titles=WT)
    levels = sorted({float(r["pluto_want_dbm"]) for r in MAP if r["pass"] == "map"})
    cm = plt.cm.viridis(np.linspace(0, 0.95, len(levels)))
    for c, L in zip(cm, levels):
        f, v = curve(MAP, lambda r: r["pass"] == "map" and float(r["pluto_want_dbm"]) == L)
        ax[0].plot(f, v, "-o", color=c, lw=1, ms=2, label=f"{L:.0f} dBm ({len(f)} pts)")
    ax[0].set(xlim=(690, 1610), ylabel="detector output (mV), raw",
              title="Test 50, power map: 700-1600 MHz in 5 MHz steps at 13 Pluto levels, -85 to -30 dBm (top levels miss points where the Pluto hit its 31 dB attenuation floor)")
    ax[0].legend(fontsize=7.5, ncol=4, loc="upper left")

    flv = sorted({float(r["pluto_want_dbm"]) for r in FINE})
    cf = plt.cm.plasma(np.linspace(0, 0.85, len(flv)))
    for c, L in zip(cf, flv):
        f, v = curve(FINE, lambda r: float(r["pluto_want_dbm"]) == L)
        ax[1].plot(f, v, "-", color=c, lw=1.1, label=f"{L:.0f} dBm, 1 MHz steps")
    f, v = curve(BASE, lambda r: float(r["freq_mhz"]) > 0)
    if len(f):
        ax[1].plot(f, v, "kD", ms=7, mfc="none", label="13 Nov check points, same cables, -50 dBm")
    ax[1].set(xlim=(895, 1205), ylabel="detector output (mV), raw", title="Test 52, 1 MHz sweeps at six Pluto levels, 900-1200 MHz (Agilent supply)")
    ax[1].legend(fontsize=8, ncol=2)

    reps = sorted({int(r["rep"]) for r in MAP if r["pass"] == "repeat"})
    big = [rp for rp in reps if sum(1 for r in MAP if r["pass"] == "repeat" and int(r["rep"]) == rp) > 50]
    cr = plt.cm.cividis(np.linspace(0, 0.9, max(1, len(big))))
    for c, rp in zip(cr, big):
        f, v = curve(MAP, lambda r: r["pass"] == "repeat" and int(r["rep"]) == rp)
        ax[2].plot(f, v, "-", color=c, lw=1, label=f"repeat {rp}, -60 dBm ({len(f)} pts)")
    small = [r for r in MAP if r["pass"] == "repeat" and int(r["rep"]) not in big]
    if small:
        ax[2].plot([float(r["freq_mhz"]) for r in small], [float(r["detector_mean_v"]) * 1e3 for r in small], ".", color="#d95f02", ms=4,
                   label=f"short repeats {min(int(r['rep']) for r in small)}-{max(int(r['rep']) for r in small)}, -60 dBm ({len(small)} pts)")
    f, v = curve(MAP, lambda r: r["pass"] == "bad_amps_off_repeat")
    if len(f):
        ax[2].plot(f, v, "x", color="#b30000", ms=6, label="amplifiers unpowered (bad run), -60 dBm")
    ax[2].set(xlim=(895, 1205), ylabel="detector output (mV), raw", title="Test 51, repeat sweeps at -60 dBm, every repeat as taken")
    ax[2].legend(fontsize=8, ncol=2)

    klv = sorted({float(r["pluto_want_dbm"]) for r in KS})
    ck = plt.cm.viridis(np.linspace(0, 0.9, len(klv)))
    for c, L in zip(ck, klv):
        f, v = curve(KS, lambda r: float(r["pluto_want_dbm"]) == L)
        ax[3].plot(f, v, "-s", color=c, ms=3.5, lw=1.2, label=f"SM200B run, {L:.0f} dBm")
    ax[3].set(ylabel="detector output (mV), raw", title="Scope reading during the SM200B run (IF spectrum taken at each point), four Pluto levels")
    ax[3].legend(fontsize=8)
    if RAMP:
        ins = ax[3].inset_axes([0.62, 0.08, 0.36, 0.42])
        a = np.array(sorted((float(r["pluto_want_dbm"]), float(r["detector_mean_v"]) * 1e3) for r in RAMP))
        ins.plot(a[:, 0], a[:, 1], "o-", color="#7570b3", ms=3)
        ins.set_title(f"power ramp at {float(RAMP[0]['freq_mhz']):.0f} MHz", fontsize=8)
        ins.set_xlabel("Pluto level (dBm)", fontsize=8)
        ins.set_ylabel("mV", fontsize=8)
        ins.tick_params(labelsize=7)
        ins.grid(alpha=0.3)

    groups = [("hold, 1054 MHz -60 dBm", lambda r: r["pass"] == "hold", "#d95f02"),
              ("tone off", lambda r: r["pass"] in ("off", "start_off"), "#1b9e77"),
              ("amplifiers unpowered: hold", lambda r: r["pass"] == "bad_amps_off_hold", "#b30000"),
              ("amplifiers unpowered: tone off", lambda r: r["pass"] == "bad_amps_off_off", "#e7298a")]
    allt = [dt.datetime.fromisoformat(r["timestamp"]) for r in MAP]
    t0 = min(allt)
    for lab, cond, col in groups:
        t = mins(MAP, cond)
        if t:
            ax[4].plot([(a - t0).total_seconds() / 3600 for a, _ in t], [b for _, b in t], "o", color=col, ms=3.5, label=f"{lab} ({len(t)})")
    w = []
    for line in open(HERE / "p162x4_tone_off_watch_1nov.csv"):
        parts = line.strip().split(",")
        try:
            w.append((dt.datetime.fromisoformat(parts[0]), float(parts[1]) * 1e3))
        except (ValueError, IndexError):
            pass
    if w:
        ax[4].plot([(a - t0).total_seconds() / 3600 for a, _ in w], [b for _, b in w], "^", color="#7570b3", ms=5, label=f"tone-off watch after the supply swap ({len(w)})")
    ax[4].set(xlabel=f"hours after {t0:%H:%M} on 1 Nov", ylabel="detector output (mV), raw", title="Held tone and tone-off readings through the evening")
    ax[4].legend(fontsize=8)
    for a in ax[:4]:
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[:5]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    out = HERE / "pd_old_setup_all_raw.png"
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
