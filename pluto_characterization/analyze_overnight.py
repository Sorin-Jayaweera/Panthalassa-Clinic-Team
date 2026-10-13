"""Plots and summary numbers from overnight_readings.csv. Safe to run while the overnight run is still going:
it uses whatever is saved so far. Writes plots here and into the website's img folder, and overnight_summary.json."""
import collections
import csv
import datetime as dt
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"
TR = HERE / "traces"
NUM = ("freq_set_hz", "att_db", "scale", "offset_hz", "freq_meas_hz", "level_dbm", "read_centre_hz", "pluto_temp_c")

R = list(csv.DictReader(open(HERE / "overnight_readings.csv")))
B = collections.defaultdict(list)
for r in R:
    for k in NUM:
        r[k] = float(r[k])
    r["t"] = dt.datetime.fromisoformat(r["time"])
    B[r["block"]].append(r)
S = {"readings": len(R), "traces": len(list(TR.glob("*.csv"))), "first": R[0]["time"], "last": R[-1]["time"]}


def save(fig, name):
    fig.tight_layout()
    for out in (HERE / f"{name}.png", IMG / f"{name}.png"):
        fig.savefig(out, dpi=120)
    plt.close(fig)


def r2(x, d=2):
    return round(float(x), d)


# ---------------------------------------------------------------- analyzer floor
S["floor"] = [[r["ref_level_dbm"], r["rbw_hz"], r["span_hz"], r["preamp"], r2(np.mean([x["level_dbm"] for x in g]), 1)]
              for key in dict.fromkeys((r["ref_level_dbm"], r["rbw_hz"], r["span_hz"], r["preamp"]) for r in B["analyzer_floor"])
              for g in [[x for x in B["analyzer_floor"] if (x["ref_level_dbm"], x["rbw_hz"], x["span_hz"], x["preamp"]) == key and x["note"].startswith("maximum")]]
              for r in [g[0]]]

# ---------------------------------------------------------------- low level: stitch the analyzer settings together
if B["low_level"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    S["low"] = {}
    for f in sorted({r["freq_set_hz"] for r in B["low_level"]}):
        g = [r for r in B["low_level"] if r["freq_set_hz"] == f and not r["note"].startswith("find")]
        sets = {n: {r["att_db"]: r["level_dbm"] for r in g if r["note"] == n} for n in ("rl+10", "rl-10", "rl-30 preamp", "rl-30 preamp rbw100")}
        if not all(sets.values()):
            continue
        # tie each setting to the one before using the settings they share (well above the noise of both)
        off1 = np.mean([sets["rl+10"][a] - sets["rl-10"][a] for a in (20, 25, 30, 35, 40)])
        off2 = np.mean([sets["rl-10"][a] + off1 - sets["rl-30 preamp"][a] for a in (40, 45, 50, 55, 60)])
        off3 = np.mean([sets["rl-30 preamp"][a] + off2 - sets["rl-30 preamp rbw100"][a] for a in (60, 62.5, 65, 67.5, 70)])
        table = {}
        for a in sorted(set().union(*[s.keys() for s in sets.values()])):
            if a <= 40 and a in sets["rl+10"]:
                table[a] = sets["rl+10"][a]
            elif a <= 60 and a in sets["rl-10"]:
                table[a] = sets["rl-10"][a] + off1
            elif a <= 70 and a in sets["rl-30 preamp"]:
                table[a] = sets["rl-30 preamp"][a] + off2
            elif a in sets["rl-30 preamp rbw100"]:
                table[a] = sets["rl-30 preamp rbw100"][a] + off3
            elif a in sets["rl-30 preamp"]:
                table[a] = sets["rl-30 preamp"][a] + off2
        a_ = np.array(sorted(table))
        l_ = np.array([table[x] for x in a_])
        dep = l_ - (table[20.0] + 20 - a_)
        ax[0].plot(a_, l_, ".-", label=f"{f/1e6:.0f} MHz")
        ax[1].plot(a_, dep, ".-", label=f"{f/1e6:.0f} MHz")
        S["low"][f"{f/1e6:.0f}"] = dict(table=[[r2(x), r2(y)] for x, y in zip(a_, l_)], offsets=[r2(off1), r2(off2), r2(off3)],
                                        dep_max_20_to_89=r2(np.abs(dep[a_ >= 20]).max()), lowest=r2(l_[-1]))
    ax[0].set(xlabel="Pluto attenuation setting (dB)", ylabel="Output (dBm)", title="Output against attenuation setting, 0 to 89.75 dB")
    ax[1].set(xlabel="Pluto attenuation setting (dB)", ylabel="Measured minus straight line through the 20 dB point (dB)", title="Departure from 1 dB per dB", ylim=(-2, 2))
    for x in ax:
        x.grid(alpha=0.3)
        x.legend(fontsize=8)
    fig.suptitle("Pluto output down to its lowest setting (tone scale 0.5)", fontweight="bold")
    save(fig, "pluto_low_level")

# ---------------------------------------------------------------- fine steps
if B["fine_steps"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    S["fine"] = {}
    for f in sorted({r["freq_set_hz"] for r in B["fine_steps"]}):
        for d, st in (("down", "-"), ("up", "--")):
            g = sorted([(r["att_db"], r["level_dbm"]) for r in B["fine_steps"] if r["freq_set_hz"] == f and r["note"] == d])
            if len(g) < 10:
                continue
            a_, l_ = np.array(g).T
            step = -(np.diff(l_))
            ax[0].plot(a_[1:], step, st, marker=".", label=f"{f/1e6:.0f} MHz, {d}")
            S["fine"][f"{f/1e6:.0f} {d}"] = dict(mean=r2(step.mean(), 3), sd=r2(step.std(), 3), min=r2(step.min(), 3), max=r2(step.max(), 3))
        up = dict((r["att_db"], r["level_dbm"]) for r in B["fine_steps"] if r["freq_set_hz"] == f and r["note"] == "up")
        dn = dict((r["att_db"], r["level_dbm"]) for r in B["fine_steps"] if r["freq_set_hz"] == f and r["note"] == "down")
        if up and dn:
            k = sorted(set(up) & set(dn))
            dd = np.array([up[x] - dn[x] for x in k])
            ax[1].plot(k, dd, ".-", label=f"{f/1e6:.0f} MHz")
            S["fine"][f"{f/1e6:.0f} updown"] = dict(mean=r2(dd.mean(), 3), maxabs=r2(np.abs(dd).max(), 3))
    ax[0].axhline(0.25, color="gray", ls=":")
    ax[0].set(xlabel="Attenuation setting (dB)", ylabel="Change in output for one 0.25 dB step (dB)", title="Size of each 0.25 dB step")
    ax[1].set(xlabel="Attenuation setting (dB)", ylabel="Level going up minus level going down (dB)", title="Same setting reached from above and from below")
    for x in ax:
        x.grid(alpha=0.3)
        x.legend(fontsize=8)
    save(fig, "pluto_fine_steps")

# ---------------------------------------------------------------- tone scale
if B["tone_scale"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    S["scale"] = {}
    for i, att in enumerate((20.0, 0.0)):
        for f in sorted({r["freq_set_hz"] for r in B["tone_scale"]}):
            g = sorted([(r["scale"], r["level_dbm"]) for r in B["tone_scale"] if r["freq_set_hz"] == f and r["att_db"] == att])
            if not g:
                continue
            s_, l_ = np.array(g).T
            dep = l_ - (l_[s_ == 0.5][0] + 20 * np.log10(s_ / 0.5))
            ax[i].plot(s_, dep, "o-", ms=3, label=f"{f/1e6:.0f} MHz")
            S["scale"][f"{f/1e6:.0f} att{att:.0f}"] = dict(level_at_1=r2(l_[-1]), dep_at_1=r2(dep[-1]), dep_at_0p1=r2(dep[s_ == 0.1][0]), dep_at_0p02=r2(dep[0]))
        ax[i].set(xlabel="Tone scale", title=f"Attenuation {att:.0f} dB", ylim=(-1.5, 1))
        ax[i].grid(alpha=0.3)
        ax[i].legend(fontsize=8)
    ax[0].set_ylabel("Measured minus 20 log10(scale / 0.5) (dB)")
    fig.suptitle("Tone scale: departure from the ideal at five frequencies", fontweight="bold")
    save(fig, "pluto_scale_all")
    # spectra at each scale
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    S["scale_lines"] = []
    for i, att in enumerate((20, 0)):
        for s in (0.1, 0.5, 0.8, 1.0):
            p_ = TR / f"scale_{s:.2f}_att{att}_1100MHz.csv"
            if not p_.exists():
                continue
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            ax[i].plot((d[:, 0] - 1.1e9) / 1e6, d[:, 1], lw=0.9, label=f"scale {s}")
        for s in (0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0):
            p_ = TR / f"scale_{s:.2f}_att{att}_1100MHz.csv"
            if not p_.exists():
                continue
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            car = d[:, 1].max()
            fc = d[np.argmax(d[:, 1]), 0]
            row = [att, s, r2(car)]
            for off in (-1e6, -2e6, -4e6, 1e6, 2e6):
                m = np.abs(d[:, 0] - (fc + off)) < 0.15e6
                row.append(r2(d[m, 1].max() - car, 1))
            row.append(r2(np.median(d[:, 1]) - car, 1))
            S["scale_lines"].append(row)
        ax[i].set(xlabel="Offset from the tone (MHz)", title=f"Attenuation {att} dB, tone at 1100 MHz")
        ax[i].grid(alpha=0.3)
        ax[i].legend(fontsize=8)
    ax[0].set_ylabel("Level (dBm)")
    fig.suptitle("Spectrum near the tone at four tone scales (bandwidth 30 kHz)", fontweight="bold")
    save(fig, "pluto_scale_spectra")

# ---------------------------------------------------------------- tone offset
if B["tone_offset"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    S["offset"] = []
    for att, mk in ((0.0, "o-"), (20.0, "s--")):
        g = [r for r in B["tone_offset"] if r["att_db"] == att]
        offs = sorted({r["offset_hz"] for r in g})
        tone = np.array([next(r["level_dbm"] for r in g if r["offset_hz"] == o and r["note"] == "tone") for o in offs])
        sb = np.array([next(r["level_dbm"] for r in g if r["offset_hz"] == o and r["note"] == "other sideband") for o in offs])
        lo = np.array([next(r["level_dbm"] for r in g if r["offset_hz"] == o and r["note"] == "LO") for o in offs])
        o_ = np.array(offs) / 1e6
        ref = tone[o_ == 1.0][0]
        ax[0].plot(o_, tone - ref, mk, ms=4, label=f"attenuation {att:.0f} dB")
        ax[1].plot(o_, lo - tone, mk, ms=4, label=f"LO leakage, attenuation {att:.0f} dB")
        ax[1].plot(o_, sb - tone, mk, ms=4, label=f"other sideband, attenuation {att:.0f} dB")
        for a, b_, c, d in zip(o_, tone, lo, sb):
            S["offset"].append([att, r2(a, 1), r2(b_), r2(b_ - ref), r2(c - b_, 1), r2(d - b_, 1)])
    ax[0].set(xlabel="Tone offset from the LO (MHz)", ylabel="Tone level relative to the 1 MHz offset (dB)", title="Tone level against offset from the LO (LO at 1100 MHz)")
    ax[1].set(xlabel="Tone offset from the LO (MHz)", ylabel="Level relative to the tone (dB)", title="LO leakage and other sideband")
    for x in ax:
        x.grid(alpha=0.3)
        x.legend(fontsize=8)
    save(fig, "pluto_offset")

# ---------------------------------------------------------------- two tones
if B["two_tone"]:
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    S["two_tone"] = []
    for i, f in enumerate(sorted({r["freq_set_hz"] for r in B["two_tone"]})):
        for s in sorted({r["scale"] for r in B["two_tone"]}):
            xs, ys = [], []
            for att in sorted({r["att_db"] for r in B["two_tone"]}):
                g = {r["note"]: r["level_dbm"] for r in B["two_tone"] if r["freq_set_hz"] == f and r["scale"] == s and r["att_db"] == att}
                if len(g) < 5:
                    continue
                t = (g["tone 1"] + g["tone 2"]) / 2
                im = max(g["third-order low"], g["third-order high"])
                xs.append(att)
                ys.append(im - t)
                S["two_tone"].append([f / 1e6, s, att, r2(t), r2(im - t, 1), r2(t + (t - im) / 2, 1), r2(g["LO"] - t, 1)])
            ax[i].plot(xs, ys, "o-", label=f"each tone at scale {s}")
        ax[i].set(xlabel="Attenuation setting (dB)", title=f"{f/1e6:.0f} MHz")
        ax[i].grid(alpha=0.3)
        ax[i].legend(fontsize=8)
    ax[0].set_ylabel("Larger third-order product relative to one tone (dB)")
    fig.suptitle("Two tones 1 MHz apart: third-order products made by the Pluto itself", fontweight="bold")
    save(fig, "pluto_two_tone")

# ---------------------------------------------------------------- close lines against frequency
if B["close_lines"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    S["close"] = {}
    for i, att in enumerate((0.0, 20.0)):
        g = [r for r in B["close_lines"] if r["att_db"] == att and r["freq_set_hz"] < 2.09e9]      # 2100 MHz is at the edge of the analyzer's range
        fs = sorted({r["freq_set_hz"] for r in g})
        tone = np.array([next(r["level_dbm"] for r in g if r["freq_set_hz"] == f and r["note"] == "tone") for f in fs])
        for lab in ("LO, 1 MHz below", "other sideband, 2 MHz below", "4 MHz below", "1 MHz above", "2 MHz above", "3 MHz below"):
            y = np.array([next(r["level_dbm"] for r in g if r["freq_set_hz"] == f and r["note"] == lab) for f in fs]) - tone
            ax[i].plot(np.array(fs) / 1e6, y, ".-", label=lab)
            S["close"][f"att{att:.0f} {lab}"] = dict(max=r2(y.max(), 1), at=r2(fs[int(np.argmax(y))] / 1e6, 0), median=r2(np.median(y), 1))
        ax[i].set(xlabel="Tone frequency (MHz)", title=f"Attenuation {att:.0f} dB")
        ax[i].grid(alpha=0.3)
        ax[i].legend(fontsize=7)
    ax[0].set_ylabel("Level relative to the tone (dB)")
    fig.suptitle("Lines close to the tone, 350 to 2100 MHz (bandwidth 30 kHz; the flat traces are analyzer noise)", fontweight="bold")
    save(fig, "pluto_close_lines")

# ---------------------------------------------------------------- harmonics
if B["harmonics"]:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    S["harm"] = []
    for i, s in enumerate((0.5, 1.0)):
        for att, st in ((0.0, "-"), (10.0, "--"), (20.0, ":")):
            for lab, col in (("2f", "tab:blue"), ("3f", "tab:red"), ("near 3 LO", "tab:green")):
                xs, ys = [], []
                for f in sorted({r["freq_set_hz"] for r in B["harmonics"]}):
                    g = {r["note"]: r["level_dbm"] for r in B["harmonics"] if r["freq_set_hz"] == f and r["scale"] == s and r["att_db"] == att}
                    edge = {"2f": 2 * f, "3f": 3 * f, "near 3 LO": 3 * f}[lab] > 2.09e9      # at the edge of the analyzer's range
                    if lab in g and "fundamental" in g and not edge and g[lab] > -63:          # under -63 dBm is analyzer noise
                        xs.append(f / 1e6)
                        ys.append(g[lab] - g["fundamental"])
                        S["harm"].append([f / 1e6, s, att, lab, r2(g["fundamental"]), r2(g[lab]), r2(g[lab] - g["fundamental"], 1)])
                if xs:
                    ax[i].plot(xs, ys, st, color=col, marker=".", label=f"{lab}, attenuation {att:.0f} dB")
        ax[i].set(xlabel="Tone frequency (MHz)", title=f"Tone scale {s}")
        ax[i].grid(alpha=0.3)
        ax[i].legend(fontsize=7, ncol=2)
    ax[0].set_ylabel("Level relative to the tone (dB)")
    fig.suptitle("Harmonics of the tone (only those below 2.1 GHz can be seen)", fontweight="bold")
    save(fig, "pluto_harmonics")

# ---------------------------------------------------------------- retune repeat
if B["retune_repeat"]:
    S["retune"] = {}
    for tag in ("back", "att0", "att40", "att20"):
        g = [r for r in B["retune_repeat"] if r["note"].startswith(tag + " ")]
        lv = np.array([r["level_dbm"] for r in g])
        fr = np.array([r["freq_meas_hz"] for r in g])
        S["retune"][tag] = dict(n=len(g), mean=r2(lv.mean(), 3), sd=r2(lv.std(), 3), span=r2(np.ptp(lv), 3), freq_span_hz=r2(np.ptp(fr), 0))

# ---------------------------------------------------------------- settling
st = sorted(TR.glob("settle_*.csv"))
if st:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    S["settle"] = {}
    for i, kind in enumerate(("retune", "att")):
        times = []
        for p_ in sorted(TR.glob(f"settle_{kind}_*.csv")):
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            t, y = d[:, 0] / 1e6, d[:, 1]
            fin = np.median(y[-60:])
            inside = np.abs(y - fin) < 0.5
            S.setdefault("settle_step_ms", r2((t[1] - t[0]) * 1e3, 1))
            # the last moment the level is outside 0.5 dB of its final value, measured from the first moment it left its starting value
            start_lvl = np.median(y[:40])
            moved = np.where(np.abs(y - start_lvl) > 3)[0]
            last_out = np.where(~inside)[0]
            if len(moved) and len(last_out):
                t0 = t[moved[0]]
                times.append(max(0.0, t[last_out[-1]] - t0))
                ax[i].plot((t - t0) * 1e3, y, lw=0.9)
        S["settle"][kind] = dict(n=len(times), ms=[r2(x * 1e3, 0) for x in times])
        ax[i].set(xlabel="Time from the first change (ms)", ylabel="Level at 1100 MHz (dBm)", xlim=(-200, 1500),
                  title="Retune 900 to 1100 MHz" if kind == "retune" else "Attenuation 40 to 20 dB")
        ax[i].grid(alpha=0.3)
    fig.suptitle("Level against time while the Pluto is changed (analyzer zero span, bandwidth 300 kHz)", fontweight="bold")
    save(fig, "pluto_settling")

# ---------------------------------------------------------------- wide search
if B["wide_search"]:
    S["wide"] = []
    for att in (0.0, 20.0):
        for f in sorted({r["freq_set_hz"] for r in B["wide_search"]}):
            g = [r for r in B["wide_search"] if r["freq_set_hz"] == f and r["att_db"] == att]
            tone = [r for r in g if r["note"] == "tone"]
            if not tone:
                continue
            l1 = [r for r in g if r["note"] == "line 1"][0]
            S["wide"].append([att, f / 1e6, r2(tone[0]["level_dbm"]), r2(l1["freq_meas_hz"] / 1e6, 0), r2(l1["level_dbm"], 1), r2(l1["level_dbm"] - tone[0]["level_dbm"], 1)])
    fig, ax = plt.subplots(figsize=(12, 4.8))
    for f in (500, 1000, 1100, 1500, 2000):
        p_ = TR / f"wide_{f}MHz_att0.csv"
        if p_.exists():
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            ax.plot(d[:, 0] / 1e6, d[:, 1], lw=0.8, label=f"tone {f} MHz")
    p_ = TR / "wide_tone_off.csv"
    if p_.exists():
        d = np.genfromtxt(p_, delimiter=",", skip_header=1)
        ax.plot(d[:, 0] / 1e6, d[:, 1], lw=0.8, color="k", label="tone off")
    ax.set(xlabel="Frequency (MHz)", ylabel="Level (dBm)", title="0 to 2.1 GHz at attenuation 0 dB, tone scale 0.5 (bandwidth 100 kHz)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "pluto_wide")

# ---------------------------------------------------------------- full map
for blk, name, sc in (("map", "pluto_map", 0.5), ("map_s1", "pluto_map_scale1", 1.0)):
    g = [r for r in B[blk] if r["freq_set_hz"] < 2.095e9]      # 2100 MHz was read with a wrong span
    if len(g) < 50:
        continue
    atts = sorted({r["att_db"] for r in g})
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    tab = {}
    for att in atts:
        d = sorted([(r["freq_set_hz"], r["level_dbm"]) for r in g if r["att_db"] == att])
        f_, l_ = np.array(d).T
        tab[att] = dict(zip(f_, l_))
        ax[0].plot(f_ / 1e6, l_, lw=1, label=f"{att:.0f} dB")
    fs = sorted(set.intersection(*[set(v) for v in tab.values()]))
    if 20.0 in tab:
        for att in atts:
            if att == 20.0:
                continue
            ax[1].plot(np.array(fs) / 1e6, [tab[att][f] - (tab[20.0][f] + 20 - att) for f in fs], lw=1, label=f"{att:.0f} dB")
    ax[0].set(xlabel="Tone frequency (MHz)", ylabel="Output (dBm)", title=f"Output at each attenuation setting, tone scale {sc}")
    ax[1].set(xlabel="Tone frequency (MHz)", ylabel="Measured minus (20 dB reading + 20 - setting) (dB)", title="Departure from 1 dB per dB, against frequency")
    for x in ax:
        x.grid(alpha=0.3)
        x.legend(fontsize=7, ncol=3)
    save(fig, name)
    l0 = np.array([tab[atts[0]][f] for f in fs])
    S[blk] = dict(n=len(g), freqs=len(fs), att0_max=r2(l0.max()), att0_max_at=r2(fs[int(np.argmax(l0))] / 1e6, 0), att0_min=r2(l0.min()), att0_min_at=r2(fs[int(np.argmin(l0))] / 1e6, 0),
                  band_1000_1200=[r2(min([tab[atts[0]][f] for f in fs if 1.0e9 <= f <= 1.2e9], default=np.nan)), r2(max([tab[atts[0]][f] for f in fs if 1.0e9 <= f <= 1.2e9], default=np.nan))])
    with open(HERE / f"{name}_table.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["freq_mhz"] + [f"level_dbm_att{a:g}" for a in atts])
        for f in fs:
            w.writerow([f"{f/1e6:.0f}"] + [f"{tab[a][f]:.2f}" for a in atts])

# ---------------------------------------------------------------- reference checks and drift through the night
if len(B["ref"]) > 12:
    fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    t0 = B["ref"][0]["t"]
    S["ref"] = {}
    for f in (1.0e9, 1.1e9, 1.2e9):
        for att, st_ in ((20.0, "-"), (0.0, "--")):
            g = [r for r in B["ref"] if r["freq_set_hz"] == f and r["att_db"] == att]
            h_ = np.array([(r["t"] - t0).total_seconds() / 3600 for r in g])
            lv = np.array([r["level_dbm"] for r in g])
            ax[0].plot(h_, lv - lv[0], st_, marker=".", label=f"{f/1e6:.0f} MHz, {att:.0f} dB")
            S["ref"][f"{f/1e6:.0f} att{att:.0f}"] = dict(n=len(g), first=r2(lv[0]), mean=r2(lv.mean()), span=r2(np.ptp(lv), 3), sd=r2(lv.std(), 3), last_minus_first=r2(lv[-1] - lv[0], 3))
    g = B["ref_freq"] + B["drift_freq"]
    g.sort(key=lambda r: r["t"])
    h_ = np.array([(r["t"] - t0).total_seconds() / 3600 for r in g])
    fe = np.array([(r["freq_meas_hz"] - 1.1e9) for r in g])
    ax[1].plot(h_, fe / 1.1e3, ".", ms=3)
    tt = np.array([(r["t"] - t0).total_seconds() / 3600 for r in R])
    tc = np.array([r["pluto_temp_c"] for r in R])
    ax[2].plot(tt[::20], tc[::20], lw=1)
    S["ref"]["freq_ppm"] = dict(n=len(g), first=r2(fe[0] / 1.1e3, 3), last=r2(fe[-1] / 1.1e3, 3), min=r2(fe.min() / 1.1e3, 3), max=r2(fe.max() / 1.1e3, 3))
    S["ref"]["temp_c"] = dict(first=r2(tc[0], 1), last=r2(tc[-1], 1), min=r2(np.nanmin(tc), 1), max=r2(np.nanmax(tc), 1))
    S["ref"]["hours"] = r2(tt[-1], 2)
    ax[0].set(ylabel="Level minus first reading (dB)", title="Reference readings through the night")
    ax[1].set(ylabel="Tone frequency error at 1100 MHz (ppm)")
    ax[2].set(ylabel="Pluto chip temperature (deg C)", xlabel="Hours since the start (21:44 on 12 Oct)")
    ax[0].legend(fontsize=7, ncol=3)
    for x in ax:
        x.grid(alpha=0.3)
    save(fig, "pluto_drift")
if B["drift"]:
    lv = np.array([r["level_dbm"] for r in B["drift"]])
    S["drift"] = dict(n=len(lv), mean=r2(lv.mean(), 3), sd=r2(lv.std(), 4), span=r2(np.ptp(lv), 3))
if B["hourly_att"]:
    tags = sorted({r["note"] for r in B["hourly_att"]})
    S["hourly"] = dict(tags=tags)
    worst = 0
    for f in (1.0e9, 1.1e9, 1.2e9):
        for att in sorted({r["att_db"] for r in B["hourly_att"]}):
            v = [r["level_dbm"] for r in B["hourly_att"] if r["freq_set_hz"] == f and r["att_db"] == att]
            worst = max(worst, np.ptp(v))
    S["hourly"]["att_table_worst_span_db"] = r2(worst, 3)
    worst = 0
    for f in sorted({r["freq_set_hz"] for r in B["hourly_freq"] if r["freq_set_hz"] < 2.095e9}):
        v = [r["level_dbm"] for r in B["hourly_freq"] if r["freq_set_hz"] == f]
        worst = max(worst, np.ptp(v))
    S["hourly"]["freq_sweep_worst_span_db"] = r2(worst, 3)
    S["hourly"]["tonefreq_ppm"] = sorted({r2((r["freq_meas_hz"] - r["freq_set_hz"]) / r["freq_set_hz"] * 1e6, 2) for r in B["hourly_tonefreq"] if r["level_dbm"] > -60})

import analyze_overnight2
analyze_overnight2.run(B, S, TR, HERE, save, r2)
S["blocks"] = {k: len(v) for k, v in B.items()}
(HERE / "overnight_summary.json").write_text(json.dumps(S, indent=1))
show = {k: v for k, v in S.items() if k in ("tune", "tune_drift", "close_in", "low_more", "if_band", "if_scale", "pulse", "pulse_width", "pulse_spectrum", "pulse_check", "map_s1", "blocks")}
print(json.dumps(show, indent=1))
