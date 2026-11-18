"""14 Nov evening, after the PC crashes: five Pluto levels (-36 = Pluto top, -43, -50, -57, -64 dBm), 1150-1550 MHz, filled in
coarse to fine by halving (ends, middle, quarters, ... 6.25 MHz over the whole span, then 3.125 and 1.5625 MHz on the rise).
All five levels are read back to back at each frequency; each halving depth starts by re-reading 1350 MHz (drift check).
Thin lines: the 2 MHz sweep from before the crash (stage sweep5, 15:50-17:59). Saves pd_bisect_14nov.png and prints statistics."""
import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring
from pdlib import HERE, L5, chain, colours, fv, mv, rows, zero

ALL = rows("pd_dither_14nov.csv")
REF, RISE = -50.0, (1240.0, 1430.0)
WIRING = [chain("-36 to -64 dBm", "4.03 V, 0.22-0.26 A", scope=", 1 Mohm\n50 mV/div, 4 offsets 1 mV apart", sm="20 dB of pads\nthen SM200B (not read)")]
WT = ["Wiring, 14 Nov evening (unchanged; PC restarted several times 18:00-18:48, instruments replugged 19:10)"]


def main():
    zb, zs = zero(ALL, ("31", "32", "33"), default=0.0), zero(ALL, ("21",), default=0.0)
    depth_of, pts, chk = {}, {w: {} for w in L5}, {w: [] for w in L5}
    for r in (r for r in ALL if r["stage"] in ("bisect5", "bisect5s")):
        f, w, d, t = float(r["freq_mhz"]), float(r["pluto_want_dbm"]), int(r["rep"]), r["timestamp"]
        if f == 1350.0 and d >= 2:
            chk[w].append((int(t[11:13]) + int(t[14:16]) / 60 + (24 if t[8:10] == "15" else 0), mv(r) - zb))
            if f in pts[w]:
                continue
        pts[w][f] = mv(r) - zb
        depth_of.setdefault(f, d)
    C = {w: np.array(sorted(p.items())).T for w, p in pts.items() if p}
    S = {w: fv([r for r in ALL if r["stage"] == "sweep5" and float(r["pluto_want_dbm"]) == w]) - [[0], [zs]] for w in L5}
    col = colours(L5)
    maxd = max(depth_of.values()) if depth_of else 0

    fig, ax = wiring.figure(4, WIRING, size=(14, 20), titles=WT)
    for w in L5:
        if S[w].size:
            ax[0].plot(*S[w], "-", color=col[w], lw=0.7, alpha=0.45)
        if w in C:
            ax[0].plot(*C[w], "-o", color=col[w], ms=3.5, lw=1.4, label=f"{w:.0f} dBm" + (" (Pluto top)" if w == -36 else ""))
    ax[0].set(xlim=(1145, 1555), ylabel="detector minus tone-off (mV)",
              title=f"Five Pluto levels, halving down to {400.0 / 2 ** maxd:g} MHz so far (circles, {len(depth_of)} frequencies); thin lines = 2 MHz sweep before the crash")
    ax[0].legend(fontsize=8, ncol=5)
    if REF in C and C[REF].shape[1] >= 5:
        rf, rv = C[REF]
        sl = np.gradient(rv, rf)
        at = lambda c, f: c[1][c[0] == f][0]
        for w in L5:
            if w == REF or w not in C:
                continue
            f = C[w][0][np.isin(C[w][0], rf)]
            d = np.array([at(C[w], x) - at(C[REF], x) for x in f])
            s = np.interp(f, rf, sl)
            ax[1].plot(f, d, "-o", color=col[w], ms=3, lw=1.1, label=f"{w:.0f} dBm")
            ax[2].plot(f, np.where(s > 0.15, d / s, np.nan), "-o", color=col[w], ms=3, lw=1.1, label=f"{w:.0f} dBm")
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
            M = np.array([[(at(C[w], f) - rv[i]) / sl[i] if np.any(C[w][0] == f) else np.nan for i, f in enumerate(rf) if g[i]] for w in sel if w in C])
            if M.size:
                span = np.nanmax(M, axis=0) - np.nanmin(M, axis=0)
                print(f"levels {sel}: peak-to-peak error in {RISE}: best {np.nanmin(span):.2f}, worst {np.nanmax(span):.2f} at {rf[g][np.nanargmax(span)]:.1f}, "
                      f"median {np.nanmedian(span):.2f} MHz, {np.mean(span <= 4) * 100:.0f}% of points within +/-2 MHz")
    for w in L5:
        if chk[w]:
            ax[3].plot(*np.array(chk[w]).T, "-o", color=col[w], ms=5, lw=1.2, label=f"{w:.0f} dBm")
    ax[3].set(xlabel="clock time on 14 Nov (hours; 24 = midnight), one check at the start of each step", ylabel="1350 MHz reading (mV)",
              title="Drift check: 1350 MHz at the five levels, re-read at the start of every step")
    ax[3].legend(fontsize=8, ncol=5)
    for a in ax[:3]:
        a.set_xlabel("Pluto frequency (MHz)")
    for a in ax[:4]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "pd_bisect_14nov.png", dpi=95)
    print(HERE / "pd_bisect_14nov.png", f"depth {maxd}, {len(depth_of)} frequencies, tone-off {zb:.2f} mV (before the crash {zs:.2f})")


if __name__ == "__main__":
    main()
