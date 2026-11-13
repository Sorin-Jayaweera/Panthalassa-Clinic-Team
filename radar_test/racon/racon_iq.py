"""I and Q of single racon replies against time, from the 250 MS/s horn recording (seg_horn_racon_250M).

Writes plots/racon_fig6_iq_time.png and data/racon_iq_examples.csv (the plotted samples).
Run:  python racon_iq.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import racon_figs as F  # noqa: E402

R, A, VCOL = F.R, F.A, F.VCOL
REC = "seg_horn_racon_250M"
CI, CQ = "#1f6fb4", "#d1495b"     # I blue, Q red


def pick(rows, v):
    """Strongest reply of variant v whose timing is within 2 % of that variant's median and whose dash frequency is within
    0.5 MHz of the median (a typical reply, clean)."""
    rr = [r for r in rows if r["variant"] == v]
    med = {k: np.median([r[k] for r in rr]) for k in ("dot1_us", "dash_us", "dot2_us")}
    fo = np.median([r["dash_off_mhz"] for r in rr])
    ok = [r for r in rr if all(abs(r[k] / med[k] - 1) < 0.02 for k in med) and abs(r["dash_off_mhz"] - fo) < 0.5]
    return max(ok or rr, key=lambda r: r["dash_dbm"])


def clip(ax, lim, pk):
    """y range set by the racon; the Furuno pulse goes off the top, so say how big it is."""
    ax.set_ylim(-lim, lim)
    ax.text(0.012, 0.96, f"Furuno pulse at 0 us is off scale (peak {pk:.0f}); full scale in the row below",
            transform=ax.transAxes, fontsize=8, va="top", color="0.2", bbox=dict(fc="white", ec="0.7", alpha=0.9))


def iq(ax, t, y, lw=0.6, alpha=0.75, marker=None):
    kw = dict(marker=marker, ms=3, mew=0) if marker else {}
    ax.plot(t, y.real, color=CI, lw=lw, alpha=alpha, label="I", **kw)
    ax.plot(t, y.imag, color=CQ, lw=lw, alpha=alpha, label="Q", **kw)


XL = "time from the Furuno pulse's rising edge (us)"


def main():
    R.combined_strip()
    D = R.process(REC)
    fs, fc = D["R"]["fs"], D["R"]["fc"]
    ms = {m["k"]: m for m in D["ms"]}
    fig, gs = A.fig_with_strip([1, 1, 1, 1, 1], (19, 25))
    sub = gs[:5].subgridspec(5, 2, hspace=0.6, wspace=0.12)
    dump = []
    for c, v in enumerate(("long", "short")):
        row = pick(D["rows"], v)
        m = ms[row["snip"]]
        x = D["R"]["snips"][row["snip"]].astype(complex) * 1e3        # uW^0.5
        u = "uW^0.5"
        r0 = m["radar"]["i0"]
        t = (np.arange(len(x)) - r0) / fs * 1e6                      # us from the radar pulse's half-power rise
        sel = (t > -3) & (t < row["end_us"] + 4)
        f_r = m["radar"]["f_bb"]                                       # Furuno frequency relative to the SM200B centre
        xr = x * np.exp(-2j * np.pi * f_r * np.arange(len(x)) / fs)    # mixed down by the Furuno frequency
        nlp = round(0.1e-6 * fs)                                       # 0.1 us boxcar, about 9 MHz wide
        xl = np.convolve(xr, np.ones(nlp) / nlp, mode="same")
        da = m["els"][1]
        a_el = np.median(np.abs(xl[int(da["i0"]):int(da["i1"])]))
        lim = 2.4 * a_el
        pk = np.abs(x[sel]).max()
        tit = (f"{v} R, reply {row['snip']:.0f} at t = {row['t_s']:.2f} s: dot {row['dot1_us']:.2f} / dash {row['dash_us']:.2f} / "
               f"dot {row['dot2_us']:.2f} us, dash {row['dash_off_mhz']:+.2f} MHz from the Furuno")

        ax = fig.add_subplot(sub[0, c])
        iq(ax, t[sel], x[sel], lw=0.4, alpha=0.6)
        clip(ax, lim, pk)
        ax.set(title=f"Whole reply, every sample as recorded (SM200B centre {fc/1e6:.1f} MHz, 160 MHz wide)\n{tit}", xlabel=XL, ylabel=f"I, Q ({u})")

        ax = fig.add_subplot(sub[1, c])
        iq(ax, t[sel], xl[sel], lw=1.0, alpha=0.9)
        ax.plot(t[sel], np.abs(xl[sel]), color="k", lw=0.8, label="|I + jQ|")
        clip(ax, lim, pk)
        ax.set(title=f"Whole reply, mixed down by the Furuno frequency ({f_r/1e6:+.2f} MHz from centre) and 0.1 us averaged (about 9 MHz wide):\n"
                     f"Furuno at 0 Hz, so I and Q turn at the racon-minus-Furuno offset", xlabel=XL, ylabel=f"I, Q ({u})")

        ax = fig.add_subplot(sub[2, c])
        z = (t > -0.4) & (t < m["radar"]["dur_us"] + 0.4)
        iq(ax, t[z], x[z], lw=0.9, alpha=0.9, marker="o")
        ax.plot(t[z], np.abs(x[z]), color="k", lw=0.8, label="|I + jQ|")
        ax.set(title=f"Whole Furuno pulse that triggered this reply, every sample (4 ns apart), full scale\n"
                     f"{m['radar']['dur_us']:.2f} us at half power, {f_r/1e6:+.2f} MHz from the SM200B centre, {row['radar_dbm']:.1f} dBm at the SM200B",
               xlabel=XL, ylabel=f"I, Q ({u})")

        ax = fig.add_subplot(sub[3, c])
        iq(ax, t[z], xr[z], lw=0.9, alpha=0.9, marker="o")
        ax.plot(t[z], np.abs(xr[z]), color="k", lw=0.8, label="|I + jQ|")
        ph = np.unwrap(np.angle(xr[(t > 0.15) & (t < m["radar"]["dur_us"] - 0.15)]))
        ax.set(title=f"Same Furuno pulse, mixed down by its own frequency (as in row 2), full scale, every sample\n"
                     f"Furuno at 0 Hz: I and Q stay nearly flat; phase moves {np.degrees(ph.max() - ph.min()):.0f} deg across the middle of the pulse",
               xlabel=XL, ylabel=f"I, Q ({u})")

        tm = ((da["i0"] + da["i1"]) / 2 - r0) / fs * 1e6
        z = (t > tm - 0.5) & (t < tm + 0.5)
        ax = fig.add_subplot(sub[4, c])
        iq(ax, t[z], x[z], lw=0.8, alpha=0.9, marker="o")
        f_d = da["f_bb"]
        ax.set(title=f"1 us in the middle of the dash, every sample as recorded (4 ns apart)\n"
                     f"dash at {f_d/1e6:+.2f} MHz from the SM200B centre: one I/Q turn every {1e3/abs(f_d/1e6):.0f} ns", xlabel=XL, ylabel=f"I, Q ({u})")
        for a_ in fig.axes[-5:]:
            a_.title.set_fontsize(9)
            a_.grid(alpha=0.25)
            a_.legend(fontsize=8, loc="upper right")
        for i in np.flatnonzero(sel):
            dump.append(dict(variant=v, snip=int(row["snip"]), t_us=round(t[i], 4), I=x.real[i], Q=x.imag[i], I_furuno_ref=xr.real[i], Q_furuno_ref=xr.imag[i], unit='uW^0.5'))
    with open(F.DATA / "racon_iq_examples.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dump[0]))
        w.writeheader()
        w.writerows(dump)
    return F.save(fig, "fig6_iq_time", "I and Q of one racon reply against time: long R (left) and short R (right), 250 MS/s horn recording",
                  "I^2 + Q^2 = power in uW at the SM200B input. The Furuno pulse is about 45 dB above the reply, so rows 1-2 are scaled to the reply and rows 3-4 "
                  "show the pulse at full scale. CSV of the plotted samples: data/racon_iq_examples.csv")


if __name__ == "__main__":
    main()
