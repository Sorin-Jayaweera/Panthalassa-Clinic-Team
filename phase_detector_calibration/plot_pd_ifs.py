"""15 Nov night, pads removed, cable E: does the ~360 MHz ripple come from the long IF cable?
Long IF cable (stages hdr_*) against a short IF cable (~16 cm SMA + SMA-BNC adapter into the scope, stages ifs_*).
Same sweep plan (600-1600 MHz, -36/-50/-57 dBm, one reading per point, 100 mV/div). Each run in its own panel; the last
panel overlays the two at -50 dBm because comparing them is the point of that panel. Raw readings, nothing subtracted.
Saves pd_ifs_vs_long_15nov.png."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
L3 = (-36.0, -50.0, -57.0)
COL = dict(zip(L3, ("#440154", "#21918c", "#5ec962")))


def wiring_for(ifc):
    return ["Pluto TX\n-36, -50, -57 dBm", "4 x ZX60-P162LN+\n4.03 V", "ZFRSC-42-S+\nsplitter",
            ["right arm (LO): cable D\nno pad", "left arm (RF): cable B + E\nno pad"],
            "ZX05-30W-S+\nLO and RF in, IF out", f"IF: {ifc}", "SDS1104X-E CH1, 1 Mohm\n100 mV/div, one reading per point"]


def load(D, tag):
    pts = {w: {} for w in L3}
    ts = []
    for r in D:
        if r["stage"] in (f"{tag}_pri", f"{tag}_rest"):
            pts[float(r["pluto_want_dbm"])].setdefault(float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3)
            ts.append(r["timestamp"][11:16])
    return {w: np.array(sorted(p.items())) for w, p in pts.items()}, (min(ts), max(ts)) if ts else ("", "")


def peaks(a):
    f, v = a[:, 0], a[:, 1]
    out = []
    for k in range(2, len(f) - 2):
        if v[k] == v[k - 2:k + 3].max() and v[k] - v[max(0, k - 8):k + 9].min() > 30:
            out.append(f[k])
    return out


def main():
    D = list(csv.DictReader(open(HERE / "pd_dither_14nov.csv")))
    off = {t: np.median([float(r["detector_mean_v"]) * 1e3 for r in D if r["stage"] == "off" and lo <= int(r["rep"]) < hi])
           for t, (lo, hi) in (("hdr", (81, 91)), ("ifs", (91, 200)))}
    runs = [("hdr", "long IF cable to the scope (and SM200B)"), ("ifs", "SHORT IF cable: ~16 cm SMA + SMA-BNC adapter")]
    fig, ax = wiring.figure(3, [wiring_for("long cable"), wiring_for("~16 cm SMA cable\n+ SMA-BNC adapter")], size=(14, 16),
                            titles=["Wiring, panel 1: long IF cable", "Wiring, panels 2 and 3: short IF cable"], strip=0.22)
    data = {}
    for k, (tag, name) in enumerate(runs):
        P, (t0, t1) = load(D, tag)
        data[tag] = P
        for w in L3:
            if len(P[w]):
                ax[k].plot(P[w][:, 0], P[w][:, 1], "-o", ms=1.8, lw=1.0, color=COL[w], label=f"{w:.0f} dBm ({len(P[w])} points)")
        pk = peaks(P[-50.0]) if len(P[-50.0]) > 10 else []
        ax[k].set(title=f"{name}, 15 Nov {t0}-{t1}; tone-off {off[tag]:.1f} mV; -50 dBm peaks near {', '.join(f'{p:.0f}' for p in pk)} MHz")
        print(tag, "peaks -50:", pk, "tone-off", off[tag], {w: len(P[w]) for w in L3})
    for tag, ls, nm in (("hdr", "--", "long IF cable"), ("ifs", "-", "short IF cable")):
        a = data[tag][-50.0]
        ax[2].plot(a[:, 0], a[:, 1], ls, lw=1.3, color="#d95f02" if tag == "ifs" else "#555555", label=f"-50 dBm, {nm}")
    ax[2].set(title="Comparison at -50 dBm: long against short IF cable (two runs overlaid on purpose)")
    for a in ax[:3]:
        a.set(xlim=(595, 1605), xlabel="Pluto frequency (MHz)", ylabel="detector (mV, raw)")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "pd_ifs_vs_long_15nov.png", dpi=95)


if __name__ == "__main__":
    main()
