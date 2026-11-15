"""14 Nov evening, after the PC crashes: five Pluto levels (-36 = Pluto top, -43, -50, -57, -64 dBm), 1150-1550 MHz, filled in
coarse to fine by halving (ends, middle, quarters, ... 6.25 MHz over the whole span, then 3.125 and 1.5625 MHz on the rise).
All five levels are read back to back at each frequency; each halving depth starts by re-reading 1350 MHz (drift check).
Thin lines: the 2 MHz sweep from before the crash (stage sweep5, 15:50-17:59). Saves pd_bisect_14nov.png and prints statistics."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
ALL = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
REF = -50.0
RISE = (1240.0, 1430.0)
WIRING = [["Pluto TX\n-36 to -64 dBm", "4 x ZX60-P162LN+\n4.03 V, 0.22-0.26 A", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\n3 dB pad at the LO port", "left arm (RF): cable B + E\n6 dB pad at the RF port"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", "20 dB of pads\nthen SM200B (not read)"]]]
WT = ["Wiring, 14 Nov evening (unchanged; PC restarted several times 18:00-18:48, instruments replugged 19:10)"]


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def zero(reps):
    v = [mv(r) for r in ALL if r["stage"] == "off" and r["rep"] in reps]
    return float(np.median(v)) if v else 0.0


def main():
    B = [r for r in ALL if r["stage"] in ("bisect5", "bisect5s")]
    zb = zero(("31", "32", "33"))
    zs = zero(("21",))
    depth_of = {}
    pts = {w: {} for w in L5}
    chk = {w: [] for w in L5}
    for r in B:
        f, w, d = float(r["freq_mhz"]), float(r["pluto_want_dbm"]), int(r["rep"])
        if f == 1350.0 and d >= 2:
            chk[w].append((int(r["timestamp"][11:13]) + int(r["timestamp"][14:16]) / 60 + (24 if r["timestamp"][8:10] == "15" else 0), r["timestamp"][11:16], mv(r) - zb))
            if f in pts[w]:
                continue
        pts[w][f] = mv(r) - zb
        depth_of.setdefault(f, d)
    C = {w: np.array(sorted(p.items())) for w, p in pts.items() if p}
    S = {w: np.array(sorted((float(r["freq_mhz"]), mv(r) - zs) for r in ALL if r["stage"] == "sweep5" and float(r["pluto_want_dbm"]) == w)) for w in L5}
    col = dict(zip(L5, plt.cm.viridis(np.linspace(0, 0.9, len(L5)))))
    maxd = max(depth_of.values()) if depth_of else 0
    step = 400.0 / 2 ** maxd

    fig, ax = wiring.figure(4, WIRING, size=(14, 20), titles=WT)
    for w in L5:
        if len(S[w]):
            ax[0].plot(S[w][:, 0], S[w][:, 1], "-", color=col[w], lw=0.7, alpha=0.45)
        if w in C:
            c = C[w]
            ax[0].plot(c[:, 0], c[:, 1], "-o", color=col[w], ms=3.5, lw=1.4, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else ""))
    ax[0].set(xlim=(1145, 1555), ylabel="detector minus tone-off (mV)",
              title=f"Five Pluto levels, halving down to {step:g} MHz so far (circles, {len(depth_of)} frequencies); thin lines = 2 MHz sweep before the crash")
    ax[0].legend(fontsize=8, ncol=5)

    ref = C.get(REF)
    if ref is not None and len(ref) >= 5:
        rf, rv = ref[:, 0], ref[:, 1]
        sl = np.gradient(rv, rf)
        for w in L5:
            if w == REF or w not in C:
                continue
            c = C[w]
            m = np.isin(c[:, 0], rf)
            d = c[m, 1] - np.array([rv[rf == f][0] for f in c[m, 0]])
            ax[1].plot(c[m, 0], d, "-o", color=col[w], ms=3, lw=1.1, label=f"{w:.0f} dBm")
            s = np.interp(c[m, 0], rf, sl)
            ax[2].plot(c[m, 0], np.where(s > 0.15, d / s, np.nan), "-o", color=col[w], ms=3, lw=1.1, label=f"{w:.0f} dBm")
        ax[1].axhline(0, color="k", lw=0.8)
        ax[1].set(xlim=(1145, 1555), ylabel="minus the -50 dBm reading (mV)", title="Each level minus -50 dBm at the same frequency (read seconds apart)")
        ax[1].legend(fontsize=8, ncol=4)
        ax[2].axhspan(-2, 2, color="#1b9e77", alpha=0.12, label="+/- 2 MHz")
        ax[2].axhline(0, color="k", lw=0.8)
        ax[2].set(xlim=(1215, 1457), ylim=(-15, 15), ylabel="frequency error (MHz)",
                  title="Frequency error from input power alone: (level - -50 dBm) / slope of the -50 dBm curve; left out where the slope is under 0.15 mV/MHz")
        ax[2].legend(fontsize=8, ncol=5)
        ax[2].axvspan(*RISE, color="#1b9e77", alpha=0.05)
        g = (rf >= RISE[0]) & (rf <= RISE[1]) & (sl > 0.15)
        for sel in (L5, L5[:4], L5[1:4]):
            M = []
            for w in sel:
                if w in C:
                    c = C[w]
                    M.append([(c[c[:, 0] == f, 1][0] - rv[i]) / sl[i] if np.any(c[:, 0] == f) else np.nan for i, f in enumerate(rf) if g[i]])
            M = np.array(M)
            if M.size:
                span = np.nanmax(M, axis=0) - np.nanmin(M, axis=0)
                print(f"levels {sel}: peak-to-peak error in {RISE}: best {np.nanmin(span):.2f}, worst {np.nanmax(span):.2f} at {rf[g][np.nanargmax(span)]:.1f}, "
                      f"median {np.nanmedian(span):.2f} MHz, {np.mean(span <= 4) * 100:.0f}% of points within +/-2 MHz")
    for w in L5:
        if chk[w]:
            a = np.array([(d, v) for d, _, v in chk[w]])
            ax[3].plot(a[:, 0], a[:, 1], "-o", color=col[w], ms=5, lw=1.2, label=f"{w:.0f} dBm")
    ax[3].set(xlabel="clock time on 14 Nov (hours; 24 = midnight), one check at the start of each step", ylabel="1350 MHz reading (mV)",
              title="Drift check: 1350 MHz at the five levels, re-read at the start of every step")
    ax[3].legend(fontsize=8, ncol=5)
    for a in ax[:3]:
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[:4]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    out = HERE / "pd_bisect_14nov.png"
    fig.savefig(out, dpi=95)
    print(out, f"depth {maxd}, {len(depth_of)} frequencies, tone-off {zb:.2f} mV (before the crash {zs:.2f})")


if __name__ == "__main__":
    main()
