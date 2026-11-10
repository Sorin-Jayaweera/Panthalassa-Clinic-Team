"""One figure per idea, every recording with racon replies pooled (run after racon_stats.py; reads its CSVs).

    python racon_figs.py           # all figures (re-reads the 250 MS/s captures for the edge figure, about a minute)
    python racon_figs.py --no-edges

Writes plots/racon_fig1_durations.png, _fig2_edges, _fig3_frequency, _fig4_levels, _fig5_short_block, and
data/racon_short_blocks.csv (one row per block of short R replies).
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import racon_stats as R  # noqa: E402

A, PLOTS, DATA = R.A, R.PLOTS, R.DATA
VCOL, SHORT = R.VCOL, R.SHORT
RECS = [r for r in R.RECS if r in SHORT]
REC_COL = dict(zip(RECS, ["#1b9e77", "#7570b3", "#e7298a", "#66a61e", "#1f6fb4", "#a6761d"]))
ROT_S = 2.5885          # Furuno rotation period measured 25 Oct
PRI_US = 1656.0         # mean pulse spacing (604 Hz)


def load(rec):
    f = DATA / f"stats_{rec}_replies.csv"
    if not f.exists():
        return []
    out = []
    for r in csv.DictReader(open(f)):
        d = {k: (r[k] if k == "variant" else float(r[k])) for k in r}
        d["rec"] = rec
        out.append(d)
    return out


ROWS = {rec: load(rec) for rec in RECS}
ALL = [r for rec in RECS for r in ROWS[rec]]


def by(v, k, rows=None):
    x = np.array([r[k] for r in (rows or ALL) if r["variant"] == v and k in r], float)
    return x[np.isfinite(x)]


def save(fig, name, title, note=None):
    fig.suptitle(title, fontsize=12, y=0.985)
    if note:
        fig.text(0.07, 0.955, note, fontsize=9)
    out = PLOTS / f"racon_{name}.png"
    fig.savefig(out, dpi=100)
    plt.close(fig)
    print(out)
    return out


def hist1(ax, x, color, label, unit, scale=1.0, bins=60):
    """Histogram of one population, title = median, sd, 5-95 %."""
    x = np.asarray(x) * scale
    if len(x) < 3:
        ax.set_title(f"{label}: none", fontsize=9)
        return
    lo, hi = np.percentile(x, 0.5), np.percentile(x, 99.5)
    if hi <= lo:
        lo, hi = lo - 1e-3, hi + 1e-3
    ax.hist(x, bins=np.linspace(lo, hi, bins), color=color, alpha=0.9)
    md, sd = np.median(x), np.std(x, ddof=1)
    ax.axvline(md, color="k", lw=1)
    nd = 3 if unit in ("us", "ratio") else 2
    ax.set_title(f"{label}\nmedian {md:.{nd}f}, sd {sd:.{nd}f}, 5-95 % {np.percentile(x, 5):.{nd}f} to {np.percentile(x, 95):.{nd}f} {unit} (N {len(x)})",
                 fontsize=8.5)
    ax.set_xlabel({"us": "microseconds", "ratio": "dash / dot"}.get(unit, unit))
    ax.set_ylabel("replies")
    ax.grid(alpha=0.25)


# --------------------------------------------------------------------------------------------- 0. racon frequency relative to the Furuno
def fstats(x, bw=0.1):
    """peak (mode of a 0.1 MHz histogram smoothed over 0.5 MHz), median, mean, sd, 5 %, 95 %, N."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    edges = np.arange(np.floor(x.min()), np.ceil(x.max()) + bw, bw)
    h, _ = np.histogram(x, edges)
    hs = np.convolve(h, np.ones(5) / 5, mode="same")
    k = int(np.argmax(hs))
    return dict(n=len(x), peak=float(0.5 * (edges[k] + edges[k + 1])), median=float(np.median(x)), mean=float(np.mean(x)),
                sd=float(np.std(x, ddof=1)), p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)))


def offset_hist(ax, x, color, lab, big=False, xlabel="racon minus the Furuno pulse that triggered it (MHz)"):
    s = fstats(x)
    lo, hi = np.percentile(x, 0.25), np.percentile(x, 99.75)
    bw = 0.1 if big else (0.2 if hi - lo > 5 else 0.01)
    ax.hist(x, bins=np.arange(lo - bw, hi + 2 * bw, bw), color=color, alpha=0.85)
    yl = ax.get_ylim()[1]
    ax.axvspan(s["mean"] - s["sd"], s["mean"] + s["sd"], color="0.5", alpha=0.15, label=f"mean +- 1 sd ({s['sd']:.2f} MHz)")
    if lo < 0 < hi:
        ax.axvline(0, color="k", lw=1.2, ls=":", label="Furuno pulse frequency (0)")
    for key, ls, c in (("peak", "-", "#b30000"), ("median", "--", "k"), ("mean", "-.", "#555555")):
        ax.axvline(s[key], color=c, lw=1.5, ls=ls, label=f"{key} {s[key]:+.2f} MHz")
    ax.text(0.99, 0.97, f"N {s['n']}\npeak {s['peak']:+.2f} MHz\nmedian {s['median']:+.2f} MHz\nmean {s['mean']:+.2f} MHz\n"
                        f"sd {s['sd']:.2f} MHz\n5-95 %: {s['p5']:+.2f} to {s['p95']:+.2f} MHz",
            transform=ax.transAxes, ha="right", va="top", fontsize=10 if big else 8.5, family="monospace",
            bbox=dict(boxstyle="round", fc="white", ec="0.6", alpha=0.95))
    pad = 0.5 if hi - lo > 5 else 0.05
    ax.set(xlim=(lo - pad, hi + pad), xlabel=xlabel, ylabel="replies")
    ax.set_title(lab, fontsize=11 if big else 9.5)
    ax.legend(fontsize=8 if big else 7, loc="upper left")
    ax.grid(alpha=0.25)
    return s


def fig_freq_offset():
    R.combined_strip()
    fig, gs = A.fig_with_strip([1.5, 1, 1], (19, 20))
    out = []
    s = offset_hist(fig.add_subplot(gs[0]), [r["dash_off_mhz"] for r in ALL], "#555f6d",
                    f"Dash (the longest element, best estimate): racon minus Furuno, every complete R from {sum(1 for r in RECS if ROWS[r])} recordings", big=True)
    out.append(dict(element="dash", group="all", **s))
    sub = gs[1:3].subgridspec(2, 3, hspace=0.45, wspace=0.22)
    for i, (k, lab) in enumerate((("dot1_off_mhz", "Dot 1"), ("dot2_off_mhz", "Dot 2"))):
        s = offset_hist(fig.add_subplot(sub[0, i]), [r[k] for r in ALL], "#555f6d", f"{lab} minus Furuno, all replies")
        out.append(dict(element=lab.lower(), group="all", **s))
    s = offset_hist(fig.add_subplot(sub[0, 2]), [r["drift_dot1_to_dot2_mhz"] for r in ALL], "#555f6d", "Drift inside one reply: dot 2 minus dot 1",
                       xlabel="dot 2 frequency minus dot 1 frequency, same reply (MHz)")
    out.append(dict(element="drift dot 1 to dot 2", group="all", **s))
    for i, v in enumerate(("long", "short")):
        s = offset_hist(fig.add_subplot(sub[1, i]), by(v, "dash_off_mhz"), VCOL[v], f"Dash minus Furuno, {v} R only")
        out.append(dict(element="dash", group=f"{v} R", **s))
    ax = fig.add_subplot(sub[1, 2])
    for j, rec in enumerate(r for r in RECS if ROWS[r]):
        x = [r["dash_off_mhz"] for r in ROWS[rec]]
        s = fstats(x)
        out.append(dict(element="dash", group=SHORT[rec], **s))
        ax.errorbar(j, s["mean"], yerr=s["sd"], fmt="o", color=REC_COL[rec], capsize=4, ms=6, label="mean +- sd" if j == 0 else None)
        ax.plot(j + 0.18, s["median"], "k_", ms=12, mew=2, label="median" if j == 0 else None)
        ax.plot(j - 0.18, s["peak"], "v", color="#b30000", ms=7, label="peak" if j == 0 else None)
    ax.axhline(0, color="k", lw=1, ls=":")
    recs = [r for r in RECS if ROWS[r]]
    ax.set_xticks(range(len(recs)), [SHORT[r] for r in recs], rotation=30, ha="right", fontsize=8)
    ax.set(ylabel="dash minus Furuno (MHz)", title="Dash minus Furuno, each recording")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.25)
    with open(DATA / "racon_freq_offset.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["element", "group", "n", "peak", "median", "mean", "sd", "p5", "p95"])
        w.writeheader()
        for row in out:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
    return save(fig, "fig0_freq_offset", "Racon reply frequency relative to the Furuno pulse that triggered it",
                "Each element's frequency from the phase slope over its middle 80 %; the Furuno pulse's the same way. "
                "Peak = mode of a 0.1 MHz histogram smoothed over 0.5 MHz. Positive = racon above the Furuno.")


# --------------------------------------------------------------------------------------------- 1. durations
def fig_durations():
    R.combined_strip()
    items = [("delay_us", "Delay: radar pulse start to dot 1 start", "us"), ("dot1_us", "Dot 1", "us"), ("gap1_us", "Gap 1 (dot 1 to dash)", "us"),
             ("dash_us", "Dash", "us"), ("gap2_us", "Gap 2 (dash to dot 2)", "us"), ("dot2_us", "Dot 2", "us"),
             ("total_us", "Whole R: dot 1 start to dot 2 end", "us"), ("dash_over_dot", "Dash / mean dot (Morse says 3)", "ratio"),
             ("radar_dur_us", "Radar pulse length (half power) that triggered it", "us")]
    fig, gs = A.fig_with_strip([1] * 5, (19, 24))
    sub = gs[:-1].subgridspec(5, 4, hspace=0.75, wspace=0.28)
    for i, (k, lab, u) in enumerate(items):
        r, c = i // 2, (i % 2) * 2
        for j, v in enumerate(("long", "short")):
            hist1(fig.add_subplot(sub[r, c + j]), by(v, k), VCOL[v], f"{lab}, {v} R", u)
    ax = fig.add_subplot(sub[4, 2:])
    for v in ("long", "short"):
        ax.scatter(by(v, "delay_us"), by(v, "dash_us"), s=4, alpha=0.35, color=VCOL[v], label=f"{v} R", lw=0)
    ax.set(xlabel="delay, radar start to dot 1 (us)", ylabel="dash length (us)", title="Delay against dash length: the two versions are separate clusters")
    ax.legend(markerscale=4, fontsize=8)
    ax.grid(alpha=0.25)
    return save(fig, "fig1_durations", "Racon Morse R: every duration, long R (blue) and short R (orange), all 9 Nov recordings pooled",
                f"{len(ALL)} complete replies from {sum(1 for r in RECS if ROWS[r])} recordings. Edges at half of each element's own power, interpolated "
                "between samples (20 ns apart at 50 MS/s, 4 ns at 250 MS/s). Black line = median.")


# --------------------------------------------------------------------------------------------- 2. edges
def fig_edges(do_curves=True):
    R.combined_strip()
    try:
        E = json.loads((DATA / "racon_stats_edges.json").read_text())
    except FileNotFoundError:
        E = {}
    edges = [(("radar", "rise"), "radar pulse rising"), (("radar", "fall"), "radar pulse falling"), ((0, "rise"), "dot 1 rising"), ((0, "fall"), "dot 1 falling"),
             ((1, "rise"), "dash rising"), ((1, "fall"), "dash falling"), ((2, "rise"), "dot 2 rising"), ((2, "fall"), "dot 2 falling")]
    fig, gs = A.fig_with_strip([1, 1, 1.1], (19, 17))
    sub = gs[:2].subgridspec(2, 4, hspace=0.45, wspace=0.25)
    if do_curves:
        D = R.process("seg_horn_racon_250M")
        for i, (w, lab) in enumerate(edges):
            t, Y = R.edge_curves(D, w)
            ax = fig.add_subplot(sub[i // 4, i % 4])
            isv = np.array([r["variant"] for r in D["rows"]])
            for v in ("long", "short"):
                if (isv == v).sum() > 3:
                    ax.plot(t, Y[isv == v].mean(0), color=VCOL[v], lw=1.6, label=f"{v} R mean ({(isv == v).sum()})")
            mu, sd = Y.mean(0), Y.std(0)
            ax.fill_between(t, mu - sd, mu + sd, color="0.6", alpha=0.3, label="all, +-1 sd")
            r = R.ten90(t, mu)
            ax.set_title(f"{lab}: 10-90 % {r:.0f} ns" if r > 1 else f"{lab}: not measurable,\nthe radar pulse ends just before it", fontsize=10)
            ax.set(xlabel="ns from the half-power crossing", ylabel="power / element level", ylim=(-0.2, 1.6))
            ax.grid(alpha=0.25)
            if i == 0:
                ax.legend(fontsize=7)
        del D
    ax = fig.add_subplot(gs[2])
    labs = [lab for _, lab in edges]
    recs = [r for r in RECS if r in E]
    w = 0.8 / max(1, len(recs))
    for j, rec in enumerate(recs):
        y = [E[rec].get(lab, np.nan) for lab in labs]
        y = [np.nan if (q is None or q <= 0) else q for q in y]
        is250 = rec.startswith("seg_")
        ax.bar(np.arange(len(labs)) + (j - (len(recs) - 1) / 2) * w, y, w, color=REC_COL[rec], label=SHORT[rec],
               hatch=None if is250 else None, alpha=1.0 if is250 else 0.75, edgecolor="k" if is250 else "none")
    ax.set_xticks(range(len(labs)), labs)
    ax.set(ylabel="10-90 % time (ns)", ylim=(0, 400),
           title="10-90 % of the averaged edge, every recording. Trust the 250 MS/s bars (black outline). At 50 MS/s the radar edges and dot 1 rising are "
                 "blurred by the 41.5 MHz filter and by the radar pulse just before dot 1")
    ax.legend(fontsize=8, ncol=3)
    ax.grid(alpha=0.25, axis="y")
    return save(fig, "fig2_edges", "Rise and fall times: radar pulse and every racon element",
                "Top: 250 MS/s (160 MHz wide). Single replies are too noisy to time an edge, so every reply is lined up on its own half-power crossing, "
                "8x resampled, noise power subtracted and averaged. Blue / orange = long / short R mean, grey = +-1 sd of all.")


# --------------------------------------------------------------------------------------------- 3. frequency
def fig_frequency():
    R.combined_strip()
    fig, gs = A.fig_with_strip([1, 1, 1.2], (19, 17))
    sub = gs[:-1].subgridspec(3, 4, hspace=0.7, wspace=0.28)

    def vh(ax, k, lab, unit):
        xs = [by(v, k) for v in ("long", "short")]
        allv = np.concatenate(xs)
        bins = np.linspace(np.percentile(allv, 0.5), np.percentile(allv, 99.5), 70)
        ax.hist(xs, bins=bins, stacked=True, color=[VCOL["long"], VCOL["short"]], label=[f"long R ({len(xs[0])})", f"short R ({len(xs[1])})"])
        st = fstats(allv, 0.1 if unit == "MHz" else 0.005)
        for key, ls, c in (("peak", "-", "#b30000"), ("median", "--", "k"), ("mean", "-.", "#555555")):
            ax.axvline(st[key], color=c, lw=1.2, ls=ls)
        ax.set_title(f"{lab} ({unit}), all replies:\npeak {st['peak']:+.3f}, median {st['median']:+.3f}, mean {st['mean']:+.3f}, sd {st['sd']:.3f}",
                     fontsize=8.5)
        ax.set(xlabel=unit, ylabel="replies")
        ax.grid(alpha=0.25)

    for i, n in enumerate(R.EL):
        vh(fig.add_subplot(sub[0, i]), f"{n}_off_mhz", f"{['Dot 1', 'Dash', 'Dot 2'][i]} frequency minus the radar pulse's", "MHz")
    vh(fig.add_subplot(sub[0, 3]), "drift_dot1_to_dot2_mhz", "Drift inside one reply: dot 2 minus dot 1", "MHz")
    fig.axes[-1].legend(fontsize=8)
    for i, n in enumerate(R.EL):
        vh(fig.add_subplot(sub[1, i]), f"{n}_chirp_mhz_per_us", f"Chirp (frequency slope) inside {['dot 1', 'the dash', 'dot 2'][i]}", "MHz/us")
    ax = fig.add_subplot(sub[1, 3])
    for rec in RECS:
        x = [r["dash_off_mhz"] for r in ROWS[rec]]
        if x:
            ax.hist(x, bins=70, histtype="step", density=True, lw=1.3, color=REC_COL[rec], label=SHORT[rec])
    ax.set(title="Dash minus radar, each recording", xlabel="MHz", ylabel="fraction of replies (density)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.25)
    ax = fig.add_subplot(sub[2, 0:2])
    X = np.array([r["radar_f_mhz"] for r in ALL])
    Y = np.array([r["dash_f_mhz"] for r in ALL])
    for v in ("long", "short"):
        ax.scatter(by(v, "radar_f_mhz"), by(v, "dash_f_mhz"), s=4, lw=0, alpha=0.35, color=VCOL[v], label=f"{v} R")
    c = np.polyfit(X, Y, 1)
    xx = np.linspace(X.min(), X.max(), 2)
    ax.plot(xx, np.polyval(c, xx), "k-", lw=1.2, label=f"fit slope {c[0]:.2f}")
    ax.plot(xx, xx + np.median(Y - X), "k:", lw=1, label="slope 1 = racon follows the radar")
    ax.set(xlabel="Radar frequency of the triggering pulse (MHz)", ylabel="Racon dash frequency (MHz)",
           title="Does the racon follow the radar pulse to pulse? No: its frequency is picked afresh each reply")
    ax.legend(fontsize=8, markerscale=4)
    ax.grid(alpha=0.25)
    ax = fig.add_subplot(sub[2, 2:])
    for rec in RECS:
        rr = ROWS[rec]
        if rr:
            ax.hist([r["radar_f_mhz"] for r in rr], bins=60, histtype="step", lw=1.3, color=REC_COL[rec], label=SHORT[rec])
    ax.set(title="Radar frequency of the triggering pulses, each recording (the magnetron drifts as it warms)", xlabel="MHz", ylabel="pulses")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.25)
    return save(fig, "fig3_frequency", "Racon frequency: offset from the radar, drift and chirp inside a reply, all recordings pooled",
                "Element frequency from the phase slope over the middle 80 % of each element, chirp from a quadratic phase fit. "
                "Offsets are relative to the radar pulse that triggered that reply.")


# --------------------------------------------------------------------------------------------- 4. levels
def fig_levels():
    R.combined_strip()
    fig, gs = A.fig_with_strip([1, 1], (19, 12))
    sub = gs[:-1].subgridspec(2, 3, hspace=0.55, wspace=0.28)
    ax = fig.add_subplot(sub[0, 0])
    for rec in RECS:
        x = [r["dash_dbm"] for r in ROWS[rec]]
        if x:
            ax.hist(x, bins=60, histtype="step", lw=1.3, color=REC_COL[rec], label=f"{SHORT[rec]}: {np.median(x):.1f}")
    ax.set(title="Dash level at the SM200B, each recording (median in legend)", xlabel="dBm at SM200B", ylabel="replies")
    ax.legend(fontsize=7)
    for i, n in enumerate(("dot1", "dot2")):
        ax = fig.add_subplot(sub[0, 1 + i])
        for v in ("long", "short"):
            x = by(v, f"{n}_dbm") - by(v, "dash_dbm")
            ax.hist(x, bins=np.linspace(-6, 4, 80), alpha=0.7, color=VCOL[v], label=f"{v} R, median {np.median(x):+.2f} dB")
        ax.set(title=f"{'Dot 1' if n == 'dot1' else 'Dot 2'} level minus dash level, same reply", xlabel="dB", ylabel="replies")
        ax.legend(fontsize=8)
    ax = fig.add_subplot(sub[1, 0])
    for v in ("long", "short"):
        ax.hist(by(v, "radar_dbm"), bins=70, alpha=0.7, color=VCOL[v], label=f"{v} R")
    ax.set(title="Radar pulse level at the SM200B for each reply", xlabel="dBm at SM200B", ylabel="replies")
    ax.legend(fontsize=8)
    ax = fig.add_subplot(sub[1, 1:])
    for rec in RECS:
        rr = ROWS[rec]
        if rr:
            ax.plot([r["t_s"] for r in rr], [r["dash_dbm"] for r in rr], ".", ms=2, color=REC_COL[rec], label=SHORT[rec])
    ax.set(title="Dash level through each recording (each burst = one pass of the radar beam)", xlabel="seconds into that recording", ylabel="dBm at SM200B")
    ax.legend(fontsize=7, markerscale=4)
    for a in fig.axes:
        a.grid(alpha=0.25)
    return save(fig, "fig4_levels", "Racon level: per recording, dots against the dash, and the radar pulse that triggered it",
                "Levels are at the SM200B input (chain gain in the wiring strip). Antenna gains are not known, so no EIRP. "
                "Vivaldi recordings are about 15 dB lower than the horn recording.")


# --------------------------------------------------------------------------------------------- 5. short-R blocks
def blocks(rows, min_len=8):
    v = np.array([r["variant"] == "short" for r in rows])
    out, i = [], 0
    while i < len(v):
        if v[i]:
            j = i
            while j < len(v) and v[j]:
                j += 1
            if j - i >= min_len:
                out.append((i, j))
            i = j
        else:
            i += 1
    return v, out


def fig_short_block():
    R.combined_strip()
    fig, gs = A.fig_with_strip([0.8, 1.4, 1, 1], (19, 24))
    # (a) timing diagram
    ax = fig.add_subplot(gs[0])
    for y, v in ((1, "long"), (0, "short")):
        m = {k: np.median(by(v, k)) for k in ("delay_us", "dot1_us", "gap1_us", "dash_us", "gap2_us", "dot2_us")}
        t0 = m["delay_us"]
        ax.broken_barh([(0, 0.66)], (y - 0.35, 0.7), color="0.2")
        x = t0
        for k, on in (("dot1_us", 1), ("gap1_us", 0), ("dash_us", 1), ("gap2_us", 0), ("dot2_us", 1)):
            if on:
                ax.broken_barh([(x, m[k])], (y - 0.35, 0.7), color=VCOL[v])
                ax.text(x + m[k] / 2, y, f"{m[k]:.2f}", ha="center", va="center", color="w", fontsize=9, fontweight="bold")
            else:
                ax.text(x + m[k] / 2, y + 0.42, f"gap {m[k]:.2f}", ha="center", fontsize=8)
            x += m[k]
        ax.text(x + 0.8, y, f"{v} R: ends {x:.2f} us after the radar starts ({len(by(v, 'dash_us'))} replies)", va="center", fontsize=9)
    ax.set(yticks=[0, 1], yticklabels=["short R", "long R"], xlim=(-1, 85), xlabel="microseconds from the radar pulse start (black bar = radar pulse)",
           title="The two versions, medians. The short R is the long one played 0.75x as long: it ends at 45 us where the long R is still in its dash. "
                 "That is the 'drop' in the middle of the stacked plots")
    ax.grid(alpha=0.25, axis="x")
    # (b) raster of every burst, horn recording
    rec = "20261109_215716"
    rows = ROWS[rec]
    t = np.array([r["t_s"] for r in rows])
    groups = [g for g in np.split(np.arange(len(t)), np.flatnonzero(np.diff(t) > 0.5) + 1) if len(g) >= 15]
    ax = fig.add_subplot(gs[1])
    vv = np.array([r["variant"] == "short" for r in rows])
    groups = [g for g in groups if any(j - i >= 8 for i, j in blocks([rows[k] for k in g])[1])]
    for gi, g in enumerate(groups):
        i0 = blocks([rows[k] for k in g])[1][0][0]
        tt = (t[g] - t[g[i0]]) * 1e3
        for v in ("long", "short"):
            sel = np.array([rows[i]["variant"] == v for i in g])
            ax.plot(tt[sel], np.full(sel.sum(), gi), ls="none", marker="o", ms=3.2, mew=0, color=VCOL[v], label=f"{v} R" if gi == 0 else None)
    ax.axvspan(0, 28.1, color=VCOL["short"], alpha=0.08)
    ax.set(xlabel="milliseconds from the first short R of the block (one reply every 1.66 ms)", ylabel="burst number (one radar beam pass each)", xlim=(-250, 250),
           title=f"Every burst of the horn recording ({SHORT[rec]}), one row each: the short R comes as one solid block of about 18 replies "
                 "(about 29 ms) per pass, then a few stray short ones. Rows lined up on the block start", ylim=(-1, len(groups)))
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.25)
    # (c)-(h) numbers
    sub = gs[2:4].subgridspec(2, 3, hspace=0.55, wspace=0.28)
    blk_rows = []
    lens, durs, after = [], [], []
    inside = {k: [] for k in ("radar_dbm", "delay_us", "dash_off_mhz", "dash_dbm")}
    outside = {k: [] for k in inside}
    for rec in RECS:
        rr = ROWS[rec]
        if len(rr) < 50:
            continue
        v, bl = blocks(rr)
        tt = np.array([r["t_s"] for r in rr])
        mask = np.zeros(len(rr), bool)
        for i, j in bl:
            mask[i:j] = True
            lens.append(j - i)
            durs.append((tt[j - 1] - tt[i]) * 1e3)
            nxt = next((k for k in range(j, min(j + 40, len(rr))) if v[k] and tt[k] - tt[j - 1] < 0.1), None)
            after.append(np.nan if nxt is None else nxt - (j - 1))
            blk_rows.append(dict(recording=rec, start_s=round(tt[i], 4), replies=j - i, duration_ms=round((tt[j - 1] - tt[i]) * 1e3, 2),
                                 next_stray_short_after_replies=after[-1]))
        for k in inside:
            x = np.array([r[k] for r in rr])
            inside[k] += list(x[mask])
            outside[k] += list(x[~v])
    with open(DATA / "racon_short_blocks.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(blk_rows[0]))
        w.writeheader()
        w.writerows(blk_rows)
    ax = fig.add_subplot(sub[0, 0])
    ax.hist(lens, bins=np.arange(0.5, 25.5), color=VCOL["short"])
    ax.set(title=f"Replies in each short block: median {np.median(lens):.0f} ({len(lens)} blocks, 6 recordings)", xlabel="short R in a row", ylabel="blocks")
    ax = fig.add_subplot(sub[0, 1])
    ax.hist(durs, bins=40, color=VCOL["short"])
    beam = np.median(durs) / 1e3 / ROT_S * 360
    ax.set(title=f"Block length: median {np.median(durs):.1f} ms = {beam:.1f} deg of the radar's {ROT_S:.2f} s turn", xlabel="ms, first to last short R", ylabel="blocks")
    ax = fig.add_subplot(sub[0, 2])
    a2 = np.array(after, float)
    ax.hist(a2[np.isfinite(a2)], bins=np.arange(0.5, 30.5), color="0.4")
    ax.set(title="Stray short R after the block: how many replies later", xlabel="replies after the block ends", ylabel="blocks")
    for i, (k, lab, unit) in enumerate((("radar_dbm", "Radar level at the SM200B", "dBm"), ("delay_us", "Delay, radar start to dot 1", "us"),
                                        ("dash_off_mhz", "Dash minus radar frequency", "MHz"))):
        ax = fig.add_subplot(sub[1, i])
        a, b = np.array(outside[k]), np.array(inside[k])
        bins = np.linspace(np.percentile(np.r_[a, b], 0.5), np.percentile(np.r_[a, b], 99.5), 60)
        ax.hist(a, bins=bins, density=True, alpha=0.65, color=VCOL["long"], label=f"long R, outside blocks: median {np.median(a):.2f}")
        ax.hist(b, bins=bins, density=True, alpha=0.65, color=VCOL["short"], label=f"short R, in blocks: median {np.median(b):.2f}")
        ax.set(title=f"{lab} ({unit})", xlabel=unit, ylabel="fraction (density)")
        ax.legend(fontsize=8)
    for a in fig.axes[-6:]:
        a.grid(alpha=0.25)
    return save(fig, "fig5_short_block", "The 'drop in the middle': the racon's short R comes in one block per radar beam pass",
                "Long R = blue, short R = orange. Radar level in the bottom-left panel is at the SM200B, not at the racon, so it only hints at where the beam was.")


if __name__ == "__main__":
    outs = [fig_freq_offset(), fig_durations(), fig_frequency(), fig_levels(), fig_short_block()]
    outs.append(fig_edges("--no-edges" not in sys.argv))
