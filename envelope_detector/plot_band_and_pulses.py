"""Test A Steps 5-6: band edges (1.0 / 1.1 / 1.2 GHz CW sweeps) and pulse response (100 / 10 us).

    ~/miniforge3/envs/gr/bin/python plot_band_and_pulses.py data/ed_sweep_1.10GHz_<t>.csv data/ed_sweep_1.00GHz_<t>.csv \
        data/ed_sweep_1.20GHz_<t>.csv data/ed_pulse100us_1.10GHz_<t>.csv data/ed_pulse10us_1.10GHz_<t>.csv

Writes data/ed_band_edges_<date>.png and data/ed_pulses_<date>.png and prints the tables.
Rises use each sweep's floor rows (TX <= -50 dB) as the zero, not the single pre-RF reading.
VRMS from CGR-201 Input B is divided by 0.986 (its gain error against the DMM, 1 Nov).
"""

import csv
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

GAIN_VENV, GAIN_VRMS, B_GAIN = 1.47, 1.91, 0.986
FLOOR_DB, FIT_FROM_DB = -50, -10
COLORS = {1.0: "#2a78d6", 1.1: "#eb6834", 1.2: "#1baf7a"}  # validated categorical slots 1-3
PULSE_COLORS = {100.0: "#2a78d6", 10.0: "#eb6834"}
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def load(path):
    rows = list(csv.DictReader(line for line in open(path) if not line.startswith("#")))
    num = lambda v: float(v) if v not in ("", None) else None
    return [{k: (v if k == "time" else num(v)) for k, v in r.items()} for r in rows]


def dbm(v):
    return 10 * math.log10(v * v / 50 / 1e-3) if v > 0 else float("nan")


def sweep(path):
    rows = load(path)
    floor = [r for r in rows if r["tx_level_db"] <= FLOOR_DB]
    v0 = sum(r["venv_v"] for r in floor) / len(floor)
    q0 = sum(r["vrms_v"] for r in floor) / len(floor)
    out = []
    for r in rows:
        rise = r["venv_v"] - v0
        qrise = (r["vrms_v"] - q0) / B_GAIN
        out.append({"tx": r["tx_level_db"], "rise_mv": rise * 1e3, "qrise_mv": qrise * 1e3,
                    "p_venv": dbm(rise / GAIN_VENV), "p_vrms": dbm(qrise / GAIN_VRMS),
                    "ratio": rise / qrise if qrise > 0.005 else float("nan"), "unsteady": r.get("unsteady", 0)})
    fit = [p - s["tx"] for s in out if s["tx"] >= FIT_FROM_DB for p in (s["p_venv"], s["p_vrms"])]
    return out, sum(fit) / len(fit), (min(fit), max(fit))


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main(f11, f10, f12, fp100, fp10):
    here = os.path.dirname(os.path.abspath(f11))
    stamp = os.path.basename(f11).split("_")[3]
    plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK_2, "axes.labelcolor": INK_2,
                         "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK})

    # ---------------- band edges
    sw = {}
    for f, path in ((1.0, f10), (1.1, f11), (1.2, f12)):
        sw[f] = sweep(path)
    print("BAND EDGES (rises over each sweep's floor rows; VRMS / 0.986)")
    print("| TX (dB) | " + " | ".join(f"VENV rise {f:g} GHz (mV)" for f in sw) + " | "
          + " | ".join(f"VENV/VRMS {f:g}" for f in sw) + " |")
    for i, tx in enumerate(s["tx"] for s in sw[1.1][0]):
        cells = [f"{sw[f][0][i]['rise_mv']:.1f}" for f in sw] + [
            "-" if math.isnan(sw[f][0][i]["ratio"]) else f"{sw[f][0][i]['ratio']:.3f}" for f in sw]
        print(f"| {tx:g} | " + " | ".join(cells) + " |")
    for f in sw:
        good = [s["ratio"] for s in sw[f][0] if s["tx"] >= -15]
        print(f"{f:g} GHz: Pin = TX level {sw[f][1]:+.2f} dB (spread {sw[f][2][0]:+.2f}..{sw[f][2][1]:+.2f});"
              f" VENV/VRMS at TX >= -15 dB: {min(good):.3f}-{max(good):.3f}, mean {sum(good) / len(good):.3f};"
              f" unsteady steps: {sum(int(s['unsteady'] or 0) for s in sw[f][0])}")
    m = {f: sum(s["ratio"] for s in sw[f][0] if s["tx"] >= -15) / 4 for f in sw}
    print("ED flatness from the ratio, relative to 1.1 GHz: "
          + ", ".join(f"{f:g} GHz {20 * math.log10(m[f] / m[1.1]):+.2f} dB" for f in sw))

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), facecolor=SURFACE)
    for ax in axes:
        style(ax)
    ax = axes[0]
    for f in sw:
        pts = [(s["tx"], s["rise_mv"]) for s in sw[f][0] if s["rise_mv"] > 0.5 and s["tx"] >= -40]
        ax.semilogy([x for x, _ in pts], [y for _, y in pts], "-o", color=COLORS[f], lw=2, ms=6, mec=SURFACE, mew=1.5,
                    label=f"{f:g} GHz")
    ax.set_xlim(-42, 2)
    ax.set_xlabel("Pluto TX level (dB, = -attenuation)")
    ax.set_ylabel("VENV rise (mV)")
    ax.set_title("A. VENV at the IF band edges and centre", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")

    ax = axes[1]
    for f in sw:
        pts = [(s["tx"], s["ratio"]) for s in sw[f][0] if not math.isnan(s["ratio"]) and s["tx"] >= -25]
        ax.plot([x for x, _ in pts], [y for _, y in pts], "-o", color=COLORS[f], lw=2, ms=6, mec=SURFACE, mew=1.5, label=f"{f:g} GHz")
    ax.axhline(GAIN_VENV / GAIN_VRMS, ls="--", color=INK_2, lw=1, label="datasheet 0.77")
    ax.set_ylim(0.6, 1.05)
    ax.set_xlim(-27, 2)
    ax.set_xlabel("Pluto TX level (dB)")
    ax.set_ylabel("VENV rise ÷ VRMS rise")
    ax.set_title("B. ED flatness: ratio of its two outputs", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right")

    ax = axes[2]
    for f in sw:
        pts = [(s["tx"], s["p_vrms"]) for s in sw[f][0] if s["tx"] >= -30 and not math.isnan(s["p_vrms"])]
        ax.plot([x for x, _ in pts], [y for _, y in pts], "-o", color=COLORS[f], lw=2, ms=6, mec=SURFACE, mew=1.5,
                label=f"{f:g} GHz: Pin = TX {sw[f][1]:+.1f} dB".replace("-", "−"))
    ax.plot([-30, 0], [-30, 0], ":", color=INK_2, lw=1, label="Pin = TX level")
    ax.set_xlim(-32, 2)
    ax.set_ylim(-40, 2)
    ax.set_xlabel("Pluto TX level (dB)")
    ax.set_ylabel("Power at ED RFIN from VRMS (dBm)")
    ax.set_title("C. Pluto + long cable, per frequency", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    fig.suptitle("Test A, Step 5: ADL5511 across the IF band, 1 Nov (Pluto …dfdb, long RF cable)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out1 = os.path.join(here, f"ed_band_edges_{stamp}.png")
    fig.savefig(out1, dpi=150, facecolor=SURFACE)

    # ---------------- pulses
    print("\nPULSES at 1.1 GHz (CW and pulsed measured back to back at each level)")
    print("| pulse | TX (dB) | CW rise (mV) | pulse height (mV) | height / CW | between pulses - no-RF (mV) | pulses |"
          " VRMS rise pulsed / CW |")
    pul = {}
    for width, path in ((100.0, fp100), (10.0, fp10)):
        rows = load(path)
        base0 = float(next(l for l in open(path) if l.startswith("# baseline_no_rf_venv_v")).split(",")[1])
        q0 = float(next(l for l in open(path) if l.startswith("# baseline_no_rf_vrms_v")).split(",")[1])
        pul[width] = []
        for r in rows:
            cw = r["venv_rise_v"] * 1e3
            q_ratio = (r["vrms_pulsed_v"] - q0) / (r["vrms_v"] - q0)
            between = (r["pulse_base_v"] - base0) * 1e3
            pul[width].append((r["tx_level_db"], cw, r["pulse_height_v"] * 1e3, r["pulse_vs_cw"], between, r["pulses_seen"], q_ratio))
            print(f"| {width:g} us | {r['tx_level_db']:g} | {cw:.1f} | {r['pulse_height_v'] * 1e3:.1f} | {r['pulse_vs_cw']:.3f} |"
                  f" {between:+.1f} | {int(r['pulses_seen'])} | {q_ratio:.3f} |")
        h = [x[3] for x in pul[width]]
        print(f"{width:g} us: height/CW {min(h):.3f}-{max(h):.3f}, mean {sum(h) / len(h):.3f}")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), facecolor=SURFACE)
    for ax in axes:
        style(ax)
        ax.set_xlabel("Pluto TX level (dB)")
        ax.set_xlim(-22, 2)
    for width in pul:
        xs = [x[0] for x in pul[width]]
        kw = dict(color=PULSE_COLORS[width], lw=2, ms=6, mec=SURFACE, mew=1.5, label=f"{width:g} µs pulses")
        axes[0].plot(xs, [x[3] for x in pul[width]], "-o", **kw)
        axes[1].plot(xs, [x[4] for x in pul[width]], "-o", **kw)
        axes[2].plot(xs, [x[6] for x in pul[width]], "-o", **kw)
    axes[0].axhspan(0.95, 1.05, color=GRID, alpha=0.6, lw=0, label="pass band ±5 %")
    axes[0].axhline(1.0, ls="--", color=INK_2, lw=1)
    axes[0].set_ylim(0.9, 1.06)
    axes[0].set_ylabel("Pulse height ÷ CW rise")
    axes[0].set_title("A. Pulse height matches CW", loc="left", fontweight="bold")
    axes[1].axhline(0, ls="--", color=INK_2, lw=1)
    axes[1].set_ylim(-1, 6)
    axes[1].set_ylabel("VENV between pulses − no-RF (mV)")
    axes[1].set_title("B. Level between pulses", loc="left", fontweight="bold")
    axes[2].axhline(math.sqrt(0.5), ls="--", color=INK_2, lw=1, label="√0.5 = 0.707 (on half the time)")
    axes[2].set_ylim(0.55, 0.8)
    axes[2].set_ylabel("VRMS rise, pulsed ÷ CW")
    axes[2].set_title("C. VRMS sees the average", loc="left", fontweight="bold")
    for ax in axes:
        ax.legend(frameon=False, loc="lower right" if ax is not axes[1] else "upper left")
    fig.suptitle("Test A, Step 6: ADL5511 pulse response at 1.1 GHz, 1 Nov (equal on and off times)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out2 = os.path.join(here, f"ed_pulses_{stamp}.png")
    fig.savefig(out2, dpi=150, facecolor=SURFACE)
    print(f"\nplots: {out1}\n       {out2}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
