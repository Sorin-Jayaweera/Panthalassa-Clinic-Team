"""15 Nov night, pads removed: high-density sweep 600-1600 MHz at -36, -50 and -57 dBm, one reading per point (no dither),
100 mV/div. Filled coarse to fine: 900-1200 and 1300-1500 MHz first (5, 2.5, 1.25, 0.625 MHz), the rest at 10, 5, 2.5 MHz.
Raw readings, nothing subtracted. Saves pd_hd_night_15nov.png."""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
L3 = (-36.0, -50.0, -57.0)
WIRING = [["Pluto TX\n-36, -50, -57 dBm", "4 x ZX60-P162LN+\n4.03 V", "ZFRSC-42-S+\nsplitter",
           ["right arm (LO): cable D\nno pad", "left arm (RF): cable B + E\nno pad"],
           "ZX05-30W-S+\nLO and RF in, IF out", ["SDS1104X-E CH1, 1 Mohm\n100 mV/div, one reading per point", "20 dB of pads\nthen SM200B (not read)"]]]


def main(tag="hdr"):
    """tag hdr = long IF cable (15 Nov 20:03-20:31), ifs = short IF cable (15 Nov 20:33-21:43)."""
    R = [r for r in csv.DictReader(open(HERE / "pd_dither_14nov.csv")) if r["stage"] in (f"{tag}_pri", f"{tag}_rest")]
    lo_rep, hi_rep = (81, 91) if tag == "hdr" else (91, 200)
    off = [float(r["detector_mean_v"]) * 1e3 for r in csv.DictReader(open(HERE / "pd_dither_14nov.csv")) if r["stage"] == "off" and lo_rep <= int(r["rep"]) < hi_rep]
    ifc = "long IF cable" if tag == "hdr" else "short IF cable (~16 cm SMA + SMA-BNC)"
    wiring_ = [WIRING[0][:5] + ["IF: " + ifc.replace(" (", "\n("), WIRING[0][5][0]]]
    pts = {w: {} for w in L3}
    for r in R:
        pts[float(r["pluto_want_dbm"])].setdefault(float(r["freq_mhz"]), float(r["detector_mean_v"]) * 1e3)
    col = dict(zip(L3, ("#440154", "#21918c", "#5ec962")))
    fig, ax = wiring.figure(3, wiring_, size=(14, 16), titles=[f"Wiring, 15 Nov night: cable E, NO pads, {ifc}"])
    for k, (lo, hi, t) in enumerate(((595, 1605, "600-1600 MHz"), (895, 1205, "zoom 900-1200 MHz"), (1295, 1505, "zoom 1300-1500 MHz"))):
        for w in L3:
            a = np.array(sorted(pts[w].items()))
            if not len(a):
                continue
            m = (a[:, 0] >= lo) & (a[:, 0] <= hi)
            ax[k].plot(a[m, 0], a[m, 1], "-o", ms=2.5 if k else 1.8, lw=1.1, color=col[w], label=f"{w:.0f} dBm ({m.sum()} points)")
        if k == 0:
            for a_, b_ in ((900, 1200), (1300, 1500)):
                ax[k].axvspan(a_, b_, color="#999999", alpha=0.08)
        ax[k].set(xlim=(lo, hi), xlabel="Pluto frequency (MHz)", ylabel="detector (mV, raw)", title=f"Pads removed, {ifc}, {t}")
        ax[k].grid(alpha=0.3)
        ax[k].legend(fontsize=8)
    ts = sorted(r["timestamp"][11:16] for r in R)
    ax[0].set_title(f"Pads removed, {ifc}, 600-1600 MHz, three Pluto levels, one reading per point, 15 Nov {ts[0]}-{ts[-1]} "
                    f"(tone-off {np.median(off):.1f} mV; grey = priority regions, filled first)")
    fig.tight_layout()
    name = "pd_hd_night_15nov.png" if tag == "hdr" else "pd_ifs_night_15nov.png"
    fig.savefig(HERE / name, dpi=95)
    print(name, {w: len(p) for w, p in pts.items()})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hdr")
