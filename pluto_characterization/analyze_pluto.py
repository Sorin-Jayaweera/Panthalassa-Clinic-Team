"""Turn readings.csv into tables, plots and a calibration file for this Pluto, and redo the LO buffer
compression calculation with the measured Pluto level in place of the assumed one."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"
LOB = HERE.parent / "lo_buffer_test"

rows = list(csv.DictReader(open(HERE / "readings.csv")))
for r in rows:
    for k in ("freq_set_hz", "att_db", "scale", "freq_meas_hz", "level_dbm", "span_hz", "ref_level_dbm"):
        r[k] = float(r[k])


def sec(name):
    return [r for r in rows if r["section"] == name]


S = {}  # summary numbers for the website

# ---------------------------------------------------------------- A: level vs attenuation
A = sec("A_att_fine")
fineF = sorted({r["freq_set_hz"] for r in A})
cal = {}
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
for f in fineF:
    d = sorted([(r["att_db"], r["level_dbm"]) for r in A if r["freq_set_hz"] == f])
    att, lvl = np.array(d).T
    cal[f] = (att, lvl)
    ax[0].plot(att, lvl, ".-", label=f"{f/1e6:.0f} MHz")
    ref = lvl[att == 20][0] + 20          # level the 20 dB reading predicts for 0 dB
    ax[1].plot(att, lvl - (ref - att), ".-", label=f"{f/1e6:.0f} MHz")
ax[0].set(xlabel="Pluto attenuation setting (dB)", ylabel="Measured output (dBm)", title="Output against attenuation setting, tone scale 0.5")
ax[1].set(xlabel="Pluto attenuation setting (dB)", ylabel="Measured minus straight line through the 20 dB point (dB)",
          title="Departure from 1 dB per dB", ylim=(-4, 2))
for a_ in ax:
    a_.grid(alpha=0.3)
    a_.legend(fontsize=8)
fig.suptitle("Pluto TX straight into the spectrum analyzer, 12 Oct 2026", fontweight="bold")
fig.tight_layout()
for out in (HERE / "pluto_level_vs_attenuation.png", IMG / "pluto_att.png"):
    fig.savefig(out, dpi=125)
plt.close(fig)

S["att_table"] = [[int(a_)] + [round(float(cal[f][1][cal[f][0] == a_][0]), 2) for f in fineF] for a_ in cal[fineF[0]][0]]
S["att_freqs"] = [f / 1e6 for f in fineF]
S["att_dev"] = {f"{f/1e6:.0f}": {str(int(a_)): round(float(cal[f][1][cal[f][0] == a_][0] - (cal[f][1][cal[f][0] == 20][0] + 20 - a_)), 2)
                                 for a_ in (0, 1, 2, 3, 5, 10, 30, 40, 50, 60, 70)} for f in fineF}

Ac = sec("A_att_coarse")
coarseF = sorted({r["freq_set_hz"] for r in Ac})
S["coarse_atts"] = sorted({int(r["att_db"]) for r in Ac})
S["coarse"] = [[f / 1e6] + [round(next(r["level_dbm"] for r in Ac if r["freq_set_hz"] == f and r["att_db"] == a_), 2) for a_ in S["coarse_atts"]] for f in coarseF]

# ---------------------------------------------------------------- B: level vs frequency
B = sec("B_freq")
fig, ax = plt.subplots(figsize=(11, 4.6))
S["freq"] = {}
for att in (0.0, 20.0):
    d = sorted([(r["freq_set_hz"], r["level_dbm"]) for r in B if r["att_db"] == att])
    if not d:
        continue
    f, l = np.array(d).T
    ax.plot(f / 1e6, l + att, ".-", label=f"attenuation {att:.0f} dB (plotted + {att:.0f} dB)")
    S["freq"][str(int(att))] = [[round(x / 1e6), round(float(y), 2)] for x, y in zip(f, l)]
ax.axvspan(1000, 1200, color="tab:green", alpha=0.08, label="IF band 1.0 to 1.2 GHz")
ax.set(xlabel="Tone frequency (MHz)", ylabel="Output referred to 0 dB attenuation (dBm)", title="Pluto output against frequency, tone scale 0.5, 12 Oct 2026")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
for out in (HERE / "pluto_level_vs_frequency.png", IMG / "pluto_freq.png"):
    fig.savefig(out, dpi=125)
plt.close(fig)

# ---------------------------------------------------------------- C: tone scale
Cc = sec("C_scale")
fig, ax = plt.subplots(figsize=(7.5, 4.6))
S["scale"] = []
for att in (20.0, 0.0):
    d = sorted([(r["scale"], r["level_dbm"]) for r in Cc if r["att_db"] == att])
    if not d:
        continue
    s, l = np.array(d).T
    ideal = l[s == 0.5][0] + 20 * np.log10(s / 0.5)
    ax.plot(s, l - ideal, "o-", label=f"attenuation {att:.0f} dB")
    for x, y, i in zip(s, l, ideal):
        S["scale"].append([int(att), float(x), round(float(y), 2), round(float(y - i), 2)])
ax.set(xlabel="Tone scale", ylabel="Measured minus 20 log10(scale / 0.5) (dB)", title="Tone scale: departure from the ideal")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
for out in (HERE / "pluto_tone_scale.png", IMG / "pluto_scale.png"):
    fig.savefig(out, dpi=125)
plt.close(fig)

# ---------------------------------------------------------------- D, F: frequency error and stability
Dd = sec("D_freq_error")
S["freq_err"] = [[r["freq_set_hz"] / 1e6, round(r["freq_meas_hz"] - r["freq_set_hz"]), round((r["freq_meas_hz"] - r["freq_set_hz"]) / r["freq_set_hz"] * 1e6, 2)] for r in Dd]
F = sec("F_stability")
if F:
    lv = np.array([r["level_dbm"] for r in F])
    fr = np.array([r["freq_meas_hz"] for r in F])
    S["stab"] = dict(n=len(F), level_mean=round(float(lv.mean()), 2), level_span=round(float(np.ptp(lv)), 2), level_sd=round(float(lv.std()), 3),
                     freq_mean_err=round(float(fr.mean() - 1.1e9)), freq_span=round(float(np.ptp(fr))), seconds=None)
    import datetime as dt
    t = [dt.datetime.fromisoformat(r["time"]) for r in F]
    S["stab"]["seconds"] = (t[-1] - t[0]).total_seconds()

# ---------------------------------------------------------------- G, H, harmonics
S["ref_level"] = [[r["ref_level_dbm"], round(r["level_dbm"], 2)] for r in sec("G_ref_level")]
S["repeat"] = [[r["att_db"], round(r["level_dbm"], 2)] for r in sec("G_repeat")]
S["tone_off"] = [[r["att_db"], round(r["freq_meas_hz"] / 1e6, 3), round(r["level_dbm"], 2)] for r in sec("H_tone_off")]
S["harm2"] = [[r["att_db"], round(r["level_dbm"], 2)] for r in sec("E_harmonic2")]

# ---------------------------------------------------------------- E: spectra
S["spurs"] = []
fig, ax = plt.subplots(2, 2, figsize=(13, 8))
for j, att in enumerate((20, 0)):
    for i, (name, ttl) in enumerate((("close", "10 MHz span"), ("wide", "0 to 2.1 GHz"))):
        for fset in (1000, 1100, 1200):
            p_ = HERE / f"spectrum_{name}_{fset}MHz_att{att}.csv"
            if not p_.exists():
                continue
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            x = (d[:, 0] - fset * 1e6) / 1e6 if name == "close" else d[:, 0] / 1e6
            ax[j, i].plot(x, d[:, 1], lw=0.9, label=f"tone {fset} MHz")
            if name == "close":
                car = d[:, 1].max()
                fc = d[np.argmax(d[:, 1]), 0]
                for lab, off in (("carrier (LO), 1 MHz below", -1e6), ("other sideband, 2 MHz below", -2e6), ("1 MHz above", 1e6), ("2 MHz above", 2e6), ("3 MHz below", -3e6)):
                    m = np.abs(d[:, 0] - (fc + off)) < 0.15e6
                    S["spurs"].append([fset, att, lab, round(float(d[m, 1].max() - car), 1)])
            else:
                car = d[:, 1].max()
                fc = d[np.argmax(d[:, 1]), 0]
                keep = (np.abs(d[:, 0] - fc) > 30e6) & (d[:, 0] > 30e6)
                k = np.argmax(np.where(keep, d[:, 1], -999))
                S["spurs"].append([fset, att, f"largest line elsewhere, at {d[k,0]/1e6:.0f} MHz", round(float(d[k, 1] - car), 1)])
        ax[j, i].set(xlabel="Offset from the tone (MHz)" if name == "close" else "Frequency (MHz)", ylabel="Level (dBm)", title=f"{ttl}, attenuation {att} dB")
        ax[j, i].grid(alpha=0.3)
        ax[j, i].legend(fontsize=8)
fig.suptitle("Pluto output spectrum, tone scale 0.5, 12 Oct 2026", fontweight="bold")
fig.tight_layout()
for out in (HERE / "pluto_spectra.png", IMG / "pluto_spectra.png"):
    fig.savefig(out, dpi=125)
plt.close(fig)

# ---------------------------------------------------------------- calibration file
calfile = {"note": "ADALM-Pluto TX output into 50 ohm, measured 12 Oct 2026 with the Siglent SSA3021X. Tone scale 0.5, tone 1 MHz above the LO.",
           "level_dbm": {f"{f/1e6:.0f}": {f"{a_:g}": round(float(l), 2) for a_, l in zip(*cal[f])} for f in fineF}}
(HERE / "pluto_tx_calibration.json").write_text(json.dumps(calfile, indent=1))
with open(HERE / "pluto_tx_calibration.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["att_db"] + [f"level_dbm_{f/1e6:.0f}MHz" for f in fineF])
    for row in S["att_table"]:
        w.writerow(row)

# ---------------------------------------------------------------- LO buffer compression, redone
comp = list(csv.DictReader(open(LOB / "compression_20261012.csv")))
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
S["lob"] = []
out_rows = []
for f in fineF:
    att, lvl = cal[f]
    d = [(float(r["att_db"]), float(r["output_dbm"])) for r in comp if float(r["freq_set_hz"]) == f]
    if not d:
        continue
    a_, pout = np.array(sorted(d, reverse=True)).T
    a_ = np.abs(a_)
    pin = np.interp(a_, att, lvl)
    g = pout - pin
    g0 = float(g[pin < -18].mean())
    drop = g0 - g
    p1 = float(np.interp(1.0, drop, pout)) if drop.max() >= 1.0 else None
    S["lob"].append([f / 1e6, round(g0, 2), None if p1 is None else round(p1, 2), round(float(drop.max()), 2), round(float(pout.max()), 2), round(float(pin.max()), 2)])
    ax[0].plot(pin, pout, "o-", label=f"{f/1e6:.0f} MHz")
    ax[1].plot(pout, g, "o-", label=f"{f/1e6:.0f} MHz, low-power gain {g0:.2f} dB")
    for x, y, z, k in zip(a_, pin, pout, g):
        out_rows.append([f, x, round(float(y), 2), round(float(z), 2), round(float(k), 2)])
ax[0].set(xlabel="Input power: Pluto level measured at the same setting (dBm)", ylabel="Output power (dBm)", title="Output against input")
ax[1].set(xlabel="Output power (dBm)", ylabel="Gain (dB)", title="Gain against output power")
ax[1].axvline(11, color="gray", ls="--", lw=1, label="Datasheet typical 1 dB compression, +11 dBm")
ax[1].axvline(9, color="tab:red", ls=":", lw=1.2, label="Datasheet minimum, +9 dBm")
for x in ax:
    x.grid(alpha=0.3)
    x.legend(fontsize=8)
fig.suptitle("LO buffer amp ZX60-14012L-S+ compression, input power from the measured Pluto level", fontweight="bold")
fig.tight_layout()
for out in (LOB / "lo_buffer_compression_corrected.png", IMG / "lobuf_compression2.png"):
    fig.savefig(out, dpi=125)
plt.close(fig)
with open(LOB / "compression_corrected_20261012.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["freq_set_hz", "att_db", "input_dbm_measured_pluto_alone", "output_dbm", "gain_db"])
    w.writerows(out_rows)

(HERE / "summary.json").write_text(json.dumps(S, indent=1))
print(json.dumps({k: v for k, v in S.items() if k not in ("att_table", "freq", "coarse")}, indent=1))
