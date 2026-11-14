"""Plots of pd_overnight_13nov.csv (run started 14 Nov 10:51). Two figures, each with the wiring:
pd_overnight_wide.png  - wide sweeps: detector mV over 300-4000 MHz and 600-2100 MHz, and the IF lines on the SM200B
pd_overnight_band.png  - the band: 1 MHz sweep vs the evening 2 MHz sweep, power ramp, hold and tone-off drift."""
import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
R = list(csv.DictReader(open(HERE / "pd_overnight_13nov.csv")))
EVE = list(csv.DictReader(open(HERE / "pd_cable_13nov_E_pads.csv")))
WIRING = [["Pluto TX\n-50 dBm unless noted", "4 x ZX60-P162LN+\n4.03 V, 0.23 A", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1\n1 Mohm, reads the mV", "20 dB of pads\nthen SM200B"]]]
WT = ["Wiring, 14 Nov (same as 13 Nov evening; D and B are the same length, so the length difference is cable E, about 8 cm)"]
C = dict(wide10="#7570b3", wide5="#d95f02", band1="#1b9e77", eve="#999999", t1="#1b9e77", t2="#d95f02", t3="#7570b3")


def sel(stage, rep=None):
    return [r for r in R if r["stage"] == stage and (rep is None or r["rep"] == str(rep))]


def fv(rows):
    a = np.array(sorted((float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3) for r in rows))
    return (a[:, 0], a[:, 1]) if len(a) else (np.array([]), np.array([]))


def tm(rows):
    t = [dt.datetime.fromisoformat(r["timestamp"]) for r in rows]
    return np.array([(x - t[0]).total_seconds() / 60 for x in t]), np.array([float(r["detector_mean_v"]) * 1e3 for r in rows])


def wide():
    fig, ax = wiring.figure(3, WIRING, size=(14, 13), titles=WT)
    zero = np.median([float(r["detector_mean_v"]) * 1e3 for r in sel("off")]) if sel("off") else 0.0
    f, v = fv(sel("wide10_kitty"))
    ax[0].plot(f, v, "-o", color=C["wide10"], lw=1, ms=2.5, label="300-4000 MHz, 10 MHz steps (10:51-11:20)")
    f5, v5 = fv(sel("wide5"))
    if len(f5):
        ax[0].plot(f5, v5, "-", color=C["wide5"], lw=1.2, label="600-2100 MHz, 5 MHz steps (12:27-)")
    ax[0].axhline(zero, color="k", lw=0.8, ls=":", label=f"tone off, median {zero:.1f} mV")
    ax[0].axvspan(1228, 1440, color="#1b9e77", alpha=0.08, label="13 Nov clean rise 1228-1440 MHz")
    ax[0].set(ylabel="detector output (mV), raw", title="Detector output over the whole range, Pluto -50 dBm. Outside 350-2090 MHz the Pluto level is not calibrated (attenuation set for the worst case, so the level there is -50 dBm or less)")
    ax[0].legend(fontsize=8, loc="upper right")
    ax[0].set_xlim(280, 4020)
    k = [r for r in sel("wide10_kitty") if r["if_tone_dbm"]]
    kf = np.array([float(r["freq_mhz"]) for r in k])
    for col, key, lab in (("if_tone_dbm", "t1", "tone (f)"), ("if_double_dbm", "t2", "2f"), ("if_triple_dbm", "t3", "3f")):
        ax[1].plot(kf, [float(r[col]) for r in k], "-", color=C[key], lw=1.2, label=f"{lab} at the IF port")
    ax[1].set(ylabel="dBm at the IF port\n(referred to before the 20 dB)", title="IF port on the SM200B during the 10 MHz sweep: the tone, 2x and 3x the tone leaking out of the IF port")
    ax[1].legend(fontsize=8)
    ax[1].set_xlim(280, 4020)
    if len(f5):
        ax[2].plot(f5, v5 - zero, "-o", color=C["wide5"], lw=1.2, ms=2.5, label="5 MHz steps, today")
    fe, ve = fv([r for r in EVE if r["pass"] == "dense2"])
    ze = np.median([float(r["detector_mean_v"]) * 1e3 for r in EVE if r["pass"] == "dense2_off"]) if any(r["pass"] == "dense2_off" for r in EVE) else 0.0
    ax[2].plot(fe, ve - ze, "-", color=C["eve"], lw=1.5, label="2 MHz steps, 13 Nov evening")
    ax[2].axvspan(1228, 1440, color="#1b9e77", alpha=0.08)
    ax[2].set(ylabel="detector minus tone-off (mV)", title="600-2100 MHz in 5 MHz steps, each run's tone-off reading subtracted", xlim=(590, 2110))
    ax[2].legend(fontsize=8)
    for a in ax[:3]:
        a.grid(alpha=0.3)
        a.set_xlabel("Pluto frequency (MHz)")
    fig.tight_layout()
    out = HERE / "pd_overnight_wide.png"
    fig.savefig(out, dpi=100)
    print(out)


def band():
    fig, ax = wiring.figure(4, WIRING, size=(14, 17), titles=WT)
    zero = np.median([float(r["detector_mean_v"]) * 1e3 for r in sel("off")]) if sel("off") else 0.0
    fe, ve = fv([r for r in EVE if r["pass"] == "dense2"])
    ax[0].plot(fe, ve, "-", color=C["eve"], lw=2, label="13 Nov evening, 2 MHz steps")
    reps = sorted({int(r["rep"]) for r in sel("band1")})
    for rp in reps:
        f, v = fv(sel("band1", rp))
        ax[0].plot(f, v, "-", lw=1, label=f"today, 1 MHz steps, repeat {rp}")
    ax[0].axvspan(1228, 1440, color="#1b9e77", alpha=0.08)
    ax[0].set(ylabel="detector output (mV), raw", title="The band, 1150-1550 MHz, Pluto -50 dBm: today against last night", xlim=(1145, 1555))
    ax[0].legend(fontsize=8, loc="upper left")
    f, v = fv(sel("band1", reps[0])) if reps else (np.array([]), np.array([]))
    if len(f):
        s = np.gradient(v, f)
        ax[1].plot(f, s, color="#1b9e77", lw=1)
        ax[1].axhline(0, color="k", lw=0.8)
        rise = (f >= 1228) & (f <= 1440)
        ax[1].set(ylabel="slope (mV per MHz)", title=f"Slope of today's 1 MHz sweep: median {np.median(s[rise]):.2f} mV/MHz in 1228-1440 MHz, from {s[rise].min():.2f} to {s[rise].max():.2f}", xlim=(1145, 1555))
        ax[1].axvspan(1228, 1440, color="#1b9e77", alpha=0.08)
    ramp = sel("band_ramp")
    fr = sorted({float(r["freq_mhz"]) for r in ramp})
    cm = plt.cm.viridis(np.linspace(0, 0.9, len(fr)))
    for c, fq in zip(cm, fr):
        rr = sorted((float(r["pluto_want_dbm"]), float(r["detector_mean_v"]) * 1e3) for r in ramp if float(r["freq_mhz"]) == fq)
        a = np.array(rr)
        ax[2].plot(a[:, 0], a[:, 1] - zero, "-o", color=c, ms=3, lw=1.2, label=f"{fq:.0f} MHz")
    ax[2].axhline(0, color="k", lw=0.8)
    ax[2].set(xlabel="Pluto level (dBm)", ylabel="detector minus tone-off (mV)", title="Power ramp: detector output against Pluto level at each frequency (the spread between lines is what tells frequency)")
    ax[2].legend(fontsize=8, ncol=2)
    th, vh = tm(sel("hold", 0))
    to, vo = tm(sel("off", 0))
    ax[3].plot(th, vh - np.median(vh), "-", color="#d95f02", lw=1, label=f"1340 MHz, -50 dBm, median {np.median(vh):.1f} mV, sd {np.std(vh):.2f} mV")
    if len(to):
        ax[3].plot(to + th[-1] + 0.1, vo - np.median(vo), "-", color="#7570b3", lw=1, label=f"tone off, median {np.median(vo):.1f} mV, sd {np.std(vo):.2f} mV")
    ax[3].set(xlabel="minutes from start of the hold", ylabel="minus its own median (mV)", title="Hold at 1340 MHz for 20 min, then tone off for 5 min: drift and noise in the reading")
    ax[3].legend(fontsize=8)
    for a in ax[:2]:
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[:4]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    out = HERE / "pd_overnight_band.png"
    fig.savefig(out, dpi=100)
    print(out)


if __name__ == "__main__":
    wide()
    band()
