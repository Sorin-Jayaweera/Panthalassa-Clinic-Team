"""Every phase detector reading of 13-15 Nov, raw: detector volts as read, nothing subtracted, nothing averaged across points.
Cable E without pads (13 Nov 20:38-20:50), then cable E with the 3 dB LO pad and 6 dB RF pad (13 Nov 21:00 to 15 Nov 12:09).
Files: pd_cable_13nov_cableE.csv, pd_kitty_13nov_cableE.csv, pd_kitty_13nov_E_pads.csv, pd_cable_13nov_E_pads.csv,
pd_overnight_13nov.csv, pd_fine_14nov.csv, pd_dither_14nov.csv (14 Nov dithered runs and the 15 Nov coarse repeats).
Saves pd_all_config_raw.png."""
import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
T0 = dt.datetime(2026, 11, 13)


def rows(name):
    return list(csv.DictReader(open(HERE / name)))


def hrs(r):
    return (dt.datetime.fromisoformat(r["timestamp"]) - T0).total_seconds() / 3600


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def fv(rs):
    a = sorted((float(r["freq_mhz"]), mv(r)) for r in rs)
    return np.array(a) if a else np.zeros((0, 2))


KIT = rows("pd_kitty_13nov_E_pads.csv")
CAB = rows("pd_cable_13nov_E_pads.csv")
OVN = rows("pd_overnight_13nov.csv")
FIN = rows("pd_fine_14nov.csv")
DIT = rows("pd_dither_14nov.csv")
DNP = [r for r in DIT if r["stage"] == "coarse_np" or (r["stage"] == "off" and int(r["rep"]) >= 61)]   # 15 Nov 18:51 on: pads removed
DIT = [r for r in DIT if r not in DNP]
NPC = rows("pd_cable_13nov_cableE.csv")
NPK = rows("pd_kitty_13nov_cableE.csv")
for r in CAB + NPC:
    r["stage"] = r["pass"]
for r in KIT:
    r["stage"] = "kitty13"
for r in NPK:
    r["stage"] = "kitty13_np"
WIRING = [["Pluto TX\n-80 to -36 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.22-0.29 A", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n0.2 V/div to 12:51 14 Nov; 50 mV/div after;\ndithered from 13:01", "20 dB of pads\nthen SM200B (read in the 'kitty' runs)"]],
          ["Pluto TX\n-50 dBm", "4 x ZX60-P162LN+\n4.03 V", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\nno pad", "left arm (RF): cable B + E\nno pad"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n0.2 V/div", "SM200B (20:46 run)"]]]
WT = ["Wiring with pads, 13 Nov 21:00 - 15 Nov 12:09 (all panels but the last)",
      "Wiring without pads, 13 Nov 20:38-20:50 (last panel)"]
LV = lambda ws: dict(zip(ws, plt.cm.viridis(np.linspace(0, 0.9, len(ws)))))


def by_level(ax, rs, ws, style="-", ms=2, lw=1.0, suffix=""):
    c = LV(ws)
    for w in ws:
        a = fv([r for r in rs if float(r["pluto_want_dbm"]) == w])
        if len(a):
            ax.plot(a[:, 0], a[:, 1], style, color=c[w], ms=ms, lw=lw, label=f"{w:.0f} dBm{suffix}")


def main():
    fig, AX = wiring.figure(13, WIRING, size=(14, 68), titles=WT, strip=0.3)
    ax = [AX[0]] + AX[2:11]
    W5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
    WALL = sorted({float(r["pluto_want_dbm"]) for r in CAB + OVN + FIN + DIT if -900 < float(r["pluto_want_dbm"])}, reverse=True)
    call = LV(WALL)

    # 0: every reading against time
    groups = [("13 Nov evening (scope 0.2 V/div)", KIT + CAB, "#7570b3"), ("14 Nov 10:51-12:51 (0.2 V/div)", OVN, "#999999"),
              ("14 Nov 12:52-13:00 (50 mV/div)", FIN, "#e7298a"), ("14-15 Nov dithered, 50 mV/div", DIT, "#1b9e77"), ("15 Nov 18:51, pads removed (own plot)", DNP, "#e6ab02"),
              ("13 Nov 20:38, before the pads", NPC + NPK, "#a6761d")]
    for lab, rs, c in groups:
        on = [r for r in rs if float(r["pluto_want_dbm"]) > -900]
        off = [r for r in rs if float(r["pluto_want_dbm"]) <= -900]
        ax[0].plot([hrs(r) for r in on], [mv(r) for r in on], ".", color=c, ms=2, label=lab + ", tone on")
        ax[0].plot([hrs(r) for r in off], [mv(r) for r in off], "x", color="k", ms=4)
    ax[0].plot([], [], "x", color="k", label="tone off")
    for t, txt in ((24 + 14 + 53 / 60, "stop/replug"), (24 + 17 + 21 / 60, "PC sleep"), (24 + 17 + 59 / 60, "PC crashes"), (24 + 19 + 38 / 60, "Pluto drop"), (24 + 21 + 51 / 60, "Pluto drop"), (48 + 2 + 1 / 60, "Windows Update restart"), (48 + 11 + 40 / 60, "15 Nov coarse repeats")):
        ax[0].axvline(t, color="#d95f02", lw=0.8, ls="--")
        ax[0].text(t, ax[0].get_ylim()[1] if False else 175, txt, rotation=90, fontsize=7, color="#d95f02", va="top")
    ax[0].set(xlabel="hours from 13 Nov 00:00 (24 = midnight)", ylabel="detector (mV, raw)",
              title=f"All {sum(len(g[1]) for g in groups)} readings against time (every frequency and level; tone-off readings as x)")
    ax[0].legend(fontsize=7, ncol=3)

    # overview: every tone-on reading against frequency, colour = Pluto level
    for w in WALL:
        a = fv([r for r in CAB + OVN + FIN + DIT if float(r["pluto_want_dbm"]) == w and float(r["freq_mhz"]) > 0])
        if len(a):
            AX[1].plot(a[:, 0], a[:, 1], ".", color=call[w], ms=2.5, label=f"{w:.0f} dBm ({len(a)})")
    AX[1].set(ylabel="detector (mV, raw)", xlim=(1140, 1560),
              title="Everything with the pads, 13-15 Nov: every tone-on reading against frequency (all runs, all sessions), colour = Pluto level")
    AX[1].legend(fontsize=7, ncol=6)

    # 15 Nov coarse repeats
    by_level(AX[11], [r for r in DIT if r["stage"] == "coarse" and r["rep"] == "1"], W5, "-o", 3, suffix=", sweep 1 (11:42)")
    by_level(AX[11], [r for r in DIT if r["stage"] == "coarse" and r["rep"] == "2"], W5, "--s", 3, suffix=", sweep 2 (11:56)")
    AX[11].set(xlim=(1140, 1560), ylabel="detector (mV, raw)",
               title="15 Nov 11:42-12:09: two coarse sweeps (25 MHz, five levels, dithered), each a fresh launch after the 02:01 restart")
    AX[11].legend(fontsize=7, ncol=5)

    # before the pads
    a = fv([r for r in NPC if r["stage"] == "coarse"])
    AX[12].plot(a[:, 0], a[:, 1], "-o", ms=3, lw=1, color="#a6761d", label="scope only, 20:38")
    a = fv(NPK)
    AX[12].plot(a[:, 0], a[:, 1], "-s", ms=3, lw=1, color="#7570b3", label="with SM200B on the IF, 20:46")
    AX[12].axvspan(1150, 1550, color="#1b9e77", alpha=0.08)
    AX[12].set(ylabel="detector (mV, raw)", title="13 Nov 20:38-20:50, BEFORE the pads (cable E, no pads), -50 dBm, 600-1700 MHz, 0.2 V/div; shaded = 1150-1550 MHz")
    AX[12].legend(fontsize=7)

    # 1: 13 Nov evening sweeps
    for st, c in (("dense2", "#1b9e77"), ("power-60", "#d95f02"), ("power-55", "#7570b3")):
        a = fv([r for r in CAB if r["stage"] == st])
        ax[1].plot(a[:, 0], a[:, 1], "-o", ms=2, lw=1, color=c, label={"dense2": "-50 dBm", "power-60": "-60 dBm", "power-55": "-55 dBm"}[st] + f" ({st}, {[r for r in CAB if r['stage'] == st][0]['timestamp'][11:16]})")
    a = fv([r for r in KIT if float(r["pluto_want_dbm"]) > -900])
    ax[1].plot(a[:, 0], a[:, 1], "s", ms=4, color="k", label="-50 dBm, SM200B run (21:01)")
    ax[1].set(xlim=(1140, 1560), ylabel="detector (mV, raw)", title="13 Nov 21:01-22:05: first sweeps after fitting the pads, 2 MHz steps, 0.2 V/div (8 mV ADC steps)")
    ax[1].legend(fontsize=7)

    # 2: wide sweeps
    for st, c in (("wide10_kitty", "#1b9e77"), ("wide5", "#d95f02")):
        rs = [r for r in OVN if r["stage"] == st]
        a = fv(rs)
        ax[2].plot(a[:, 0], a[:, 1], "-", lw=1, color=c, label=f"{st}: {a[0, 0]:.0f}-{a[-1, 0]:.0f} MHz, {rs[0]['timestamp'][11:16]}, -50 dBm")
    ax[2].axvspan(1215, 1445, color="#1b9e77", alpha=0.08)
    ax[2].set(ylabel="detector (mV, raw)", title="14 Nov wide sweeps at -50 dBm (10 and 5 MHz steps, 0.2 V/div); shaded = the one-to-one rise")
    ax[2].legend(fontsize=7)

    # 3: SM200B readings
    for rs, lab, m in ((KIT, "13 Nov 21:01", "s"), ([r for r in OVN if r["stage"] == "wide10_kitty"], "14 Nov 10:51", ".")):
        for col, c in (("if_tone_dbm", "#1b9e77"), ("if_double_dbm", "#d95f02"), ("if_triple_dbm", "#7570b3")):
            a = sorted((float(r["freq_mhz"]), float(r[col])) for r in rs if r.get(col) not in (None, ""))
            if a:
                a = np.array(a)
                ax[3].plot(a[:, 0], a[:, 1], m + ("-" if m == "." else ""), ms=3, lw=0.8, color=c, label=f"{col.replace('if_', '').replace('_dbm', '')} ({lab})")
    ax[3].set(ylabel="SM200B (dBm, after 20 dB of pads)", title="SM200B at the IF port (through 20 dB of pads): tone, 2nd and 3rd harmonic of the Pluto frequency")
    ax[3].legend(fontsize=7, ncol=2)

    # 4: every -50 dBm band sweep, raw
    sweeps = [(CAB, "dense2", None, "13 Nov 21:19, 0.2 V/div"), (OVN, "band1", None, "14 Nov 11:35, 0.2 V/div"), (FIN, "band1", None, "14 Nov 12:53, 50 mV/div"),
              (DIT, "band1", None, "14 Nov 13:03, dithered"), (DIT, "drift_band", "101", "14 Nov 15:34, dithered"), (DIT, "sweep5", None, "14 Nov 15:50, dithered"),
              (DIT, "bisect5", None, "14 Nov 19:16, dithered"), (DIT, "coarse", "1", "15 Nov 11:42, dithered"), (DIT, "coarse", "2", "15 Nov 11:56, dithered")]
    cs = plt.cm.plasma(np.linspace(0, 0.85, len(sweeps)))
    for (rs, st, rep, lab), c in zip(sweeps, cs):
        a = fv([r for r in rs if r["stage"] == st and (rep is None or r["rep"] == rep) and abs(float(r["pluto_want_dbm"]) + 50) < 0.1])
        ax[4].plot(a[:, 0], a[:, 1], "-", lw=1.1, color=c, label=lab)
    ax[4].set(xlim=(1140, 1560), ylabel="detector (mV, raw)", title="Every -50 dBm sweep of the band, raw (nothing subtracted): the curve moves up and down between sessions")
    ax[4].legend(fontsize=7, ncol=2)

    # 5: power ramp
    rs = [r for r in OVN if r["stage"] == "band_ramp"]
    fs = sorted({float(r["freq_mhz"]) for r in rs})
    cf = plt.cm.viridis(np.linspace(0, 0.9, len(fs)))
    for f, c in zip(fs, cf):
        a = np.array(sorted((float(r["pluto_want_dbm"]), mv(r)) for r in rs if float(r["freq_mhz"]) == f))
        ax[5].plot(a[:, 0], a[:, 1], "-o", ms=3, lw=1, color=c, label=f"{f:.0f} MHz")
    ax[5].set(xlabel="Pluto level (dBm)", ylabel="detector (mV, raw)", title="14 Nov 11:20: Pluto level ramped -80 to -36 dBm at ten frequencies (0.2 V/div)")
    ax[5].legend(fontsize=7, ncol=5)

    # 6: seven levels (14:00) and the recheck (15:29)
    W7 = [-60.0, -56.0, -52.0, -48.0, -44.0, -40.0, -36.0]
    by_level(ax[6], [r for r in DIT if r["stage"] == "levels" and r["rep"] == "0"], W7, "-o", 2.5)
    c7 = LV(W7)
    for w in W7:
        a = fv([r for r in DIT if r["stage"] == "recheck" and float(r["pluto_want_dbm"]) == w])
        ax[6].plot(a[:, 0], a[:, 1], "D", ms=6, mfc="none", color=c7[w])
    ax[6].plot([], [], "D", mfc="none", color="k", label="recheck after the replug (15:29)")
    ax[6].set(xlim=(1215, 1457), ylabel="detector (mV, raw)", title="14 Nov 13:59-15:25: seven Pluto levels, 4 MHz steps, dithered; diamonds = same points re-read at 15:29")
    ax[6].legend(fontsize=7, ncol=4)

    # 7: five levels, 2 MHz, before the crash
    W5 = [-36.0, -43.0, -50.0, -57.0, -64.0]
    by_level(ax[7], [r for r in DIT if r["stage"] == "sweep5"], W5, "-o", 2)
    ax[7].set(xlim=(1140, 1560), ylabel="detector (mV, raw)", title="14 Nov 15:50-17:59: five Pluto levels, 2 MHz steps, dithered (stopped at 1412 MHz by the PC crash)")
    ax[7].legend(fontsize=7, ncol=5)

    # 8: five levels, halving
    by_level(ax[8], [r for r in DIT if r["stage"] in ("bisect5", "bisect5s")], W5, "-o", 2)
    nf = len({r["freq_mhz"] for r in DIT if r["stage"] in ("bisect5", "bisect5s")})
    ax[8].set(xlim=(1140, 1560), ylabel="detector (mV, raw)", title=f"14 Nov 19:16-21:51: five Pluto levels filled in by halving ({nf} frequencies; 1.6 MHz on the rise), dithered")
    ax[8].legend(fontsize=7, ncol=5)

    # 9: hold and tone-off readings
    h = [r for r in OVN if r["stage"] == "hold"]
    t0 = dt.datetime.fromisoformat(h[0]["timestamp"])
    ax[9].plot([(dt.datetime.fromisoformat(r["timestamp"]) - t0).total_seconds() / 60 for r in h], [mv(r) for r in h], ".-", ms=3, lw=0.8, color="#1b9e77", label="1340 MHz, -50 dBm held (12:02-12:22)")
    bq = [r for r in OVN + DIT if r["stage"] == "band_quarter"]
    ax9b = ax[9]
    ax9b.set(xlabel="minutes from 12:02, 14 Nov", ylabel="detector (mV, raw)",
             title=f"14 Nov 12:02: one frequency held for 20 min (0.2 V/div). Spread {np.ptp([mv(r) for r in h]):.1f} mV peak-to-peak; band_quarter run (1220-1230 MHz, 0.25 MHz) is in the time plot")
    ax9b.legend(fontsize=7)
    for a in AX:
        a.grid(alpha=0.3)
        if not a.get_xlabel():
            a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    out = HERE / "pd_all_config_raw.png"
    fig.savefig(out, dpi=90)
    print(out, sum(len(g[1]) for g in groups), "readings")


if __name__ == "__main__":
    main()
