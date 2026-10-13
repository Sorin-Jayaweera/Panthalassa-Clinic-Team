"""1. How mixer voltage is mapped to frequency.  2. Step responses shown as mixer voltage AND frequency,
with a +/-2 MHz band around the final frequency and the first time the trace enters it."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RUN = HERE / "step_response" / "20261010_182707"
TOL = 2.0  # MHz


def load(p):
    return np.genfromtxt(p, delimiter=",", names=True, dtype=None, encoding="utf-8")


cal_all = load(HERE / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv")
up = cal_all[cal_all["direction"] == "up"]
use = up[up["vt_meas_v"] <= 1.2]  # the single-valued part
cf, cv = use["vco_freq_hz"] / 1e6, use["mixer_out_v"] * 1e3
order = np.argsort(cv)


def mv_to_mhz(mv):
    return np.interp(mv, cv[order], cf[order])


def mhz_to_mv(mhz):
    return np.interp(mhz, cf, cv)


tr = load(RUN / "mean_traces.csv")
t = tr["time_ns"]
steps = [(0.2, h) for h in (0.4, 0.6, 0.8, 1.0, 1.15)]

# ---------------------------------------------------------------- mapping figure
fig, ax = plt.subplots(1, 3, figsize=(19, 5.6))
a = ax[0]
a.plot(up["vco_freq_hz"] / 1e6, up["mixer_out_v"] * 1e3, "-", color="lightgray", lw=1, label="rest of the sweep (not usable: folds back)")
a.plot(cf, cv, "o", ms=4, color="tab:green", label=f"calibration points used ({len(cf)} points, Vt 0 to 1.2 V)")
a.plot(cf, cv, "-", color="tab:green", lw=0.8, label="straight lines between points = the lookup")
a.set(xlabel="Frequency read by the spectrum analyzer (MHz)", ylabel="Mixer output read by the scope (mV)",
      title="Step 1: what was measured (frequency in, voltage out)", xlim=(740, 830))
a.legend(fontsize=8)
a = ax[1]
a.plot(cv[order], cf[order], "o-", ms=4, lw=0.8, color="tab:green", label="same points, axes swapped")
ex_mv = 90.0
ex_f = mv_to_mhz(ex_mv)
a.plot([ex_mv, ex_mv, cv.min() - 5], [cf.min() - 2, ex_f, ex_f], "--", color="tab:red", lw=1)
a.plot([ex_mv], [ex_f], "o", color="tab:red")
a.annotate(f"example: {ex_mv:.0f} mV reads as {ex_f:.1f} MHz", (ex_mv, ex_f), (ex_mv - 55, ex_f + 6), color="tab:red", fontsize=9,
           arrowprops=dict(arrowstyle="->", color="tab:red"))
a.set(xlabel="Mixer output (mV)", ylabel="Frequency (MHz)", title="Step 2: the lookup, voltage in, frequency out",
      xlim=(cv.min() - 5, cv.max() + 5), ylim=(cf.min() - 2, cf.max() + 2))
a.legend(fontsize=8, loc="lower right")
a = ax[2]
slope = np.gradient(cv, cf)
a.plot(cf, slope, "o-", ms=3, color="tab:blue")
a.set(xlabel="Frequency (MHz)", ylabel="Slope (mV per MHz)", title="Step 3: how sensitive the lookup is")
a2 = a.twinx()
a2.plot(cf, 2 * TOL * slope, alpha=0)  # same shape; gives the right-hand scale
a2.set_ylabel(f"Width of a +/-{TOL:g} MHz band, in mV")
for x in ax:
    x.grid(alpha=0.3)
fig.suptitle("How mixer voltage is turned into frequency (GOOD setup, clean DC, run 3)", fontweight="bold")
fig.tight_layout()
fig.savefig(HERE / "MAPPING_mixer_voltage_to_frequency.png", dpi=125)
plt.close(fig)
print("usable range: %.1f-%.1f MHz, %.1f-%.1f mV; slope min %.2f max %.2f mV/MHz" % (cf.min(), cf.max(), cv.min(), cv.max(), slope.min(), slope.max()))
# how rough is the lookup: each point against a line through its two neighbours
res = cv[1:-1] - (cv[:-2] + (cv[2:] - cv[:-2]) * (cf[1:-1] - cf[:-2]) / (cf[2:] - cf[:-2]))
print("point-to-point roughness of the lookup: rms %.3f mV = %.0f kHz at the mean slope" % (res.std(), res.std() / np.mean(slope) * 1e3))

# ---------------------------------------------------------------- step responses: voltage and frequency
rows = []
for edge in ("rise", "fall"):
    fig, axes = plt.subplots(len(steps), 2, figsize=(14, 3.2 * len(steps)))
    for (lo, hi), ax in zip(steps, axes):
        tag = f"{edge}_lo{lo:.2f}_hi{hi:.2f}".replace(".", "")
        mv, d = tr[tag + "_mixer_mV"], tr[tag + "_drive_V"]
        fr = mv_to_mhz(mv)
        sel = (t > -150) & (t < 4500)
        pre, post = t < -200, (t > 3000) & (t < 4500)
        f0, f1 = np.median(fr[pre]), np.median(fr[post])
        m0, m1 = np.median(mv[pre]), np.median(mv[post])
        d0, d1 = np.median(d[pre]), np.median(d[post])
        band_mv = sorted((mhz_to_mv(f1 - TOL), mhz_to_mv(min(f1 + TOL, cf.max()))))
        inside = np.abs(fr - f1) <= TOL
        i_first = np.nonzero(sel & inside)[0][0]
        out_after = np.nonzero(sel & ~inside)[0]
        t_first = t[i_first]
        t_stay = t[out_after[-1] + 1] if len(out_after) else t_first
        t_start = t[np.nonzero(sel & (np.abs(d - d0) > 0.05 * abs(d1 - d0)))[0][0]]
        rows.append(dict(edge=edge, v_from=lo if edge == "rise" else hi, v_to=hi if edge == "rise" else lo,
                         mixer_start_mv=round(m0, 2), mixer_final_mv=round(m1, 2), band_low_mv=round(band_mv[0], 2), band_high_mv=round(band_mv[1], 2),
                         freq_start_mhz=round(f0, 2), freq_final_mhz=round(f1, 2), tolerance_mhz=TOL,
                         first_within_ns_after_drive_50pct=round(t_first), stays_within_ns_after_drive_50pct=round(t_stay),
                         first_within_ns_after_drive_start=round(t_first - t_start)))
        a = ax[0]
        a.axhspan(*band_mv, color="tab:green", alpha=0.18, label=f"{band_mv[0]:.1f} to {band_mv[1]:.1f} mV  (= final +/-{TOL:g} MHz)")
        a.plot(t, mv, color="tab:orange", lw=1.4, label="mixer output, as measured")
        a.set_ylabel("Mixer output (mV)")
        a.set_title(f"Vt {rows[-1]['v_from']:.2f} -> {rows[-1]['v_to']:.2f} V: MEASURED mixer voltage, {m0:.1f} -> {m1:.1f} mV", fontsize=10)
        b = ax[1]
        b.axhspan(f1 - TOL, f1 + TOL, color="tab:green", alpha=0.18, label=f"final {f1:.1f} MHz +/-{TOL:g} MHz")
        b.plot(t, fr, color="tab:blue", lw=1.4, label="frequency, from the lookup")
        b.set_ylabel("Frequency (MHz)")
        b.set_title(f"Same trace through the lookup: {f0:.1f} -> {f1:.1f} MHz", fontsize=10)
        sec = b.secondary_yaxis("right", functions=(mhz_to_mv, mv_to_mhz))
        sec.set_ylabel("equivalent mixer mV")
        for x, y in ((a, mv), (b, fr)):
            x.axvline(t_first, color="tab:red", lw=1.2)
            x.plot([t_first], [y[i_first]], "o", color="tab:red")
            x.axvline(t_start, color="gray", lw=0.8, ls=":")
            x.set_xlim(-150, 600)
            x.grid(alpha=0.3)
            x.legend(fontsize=7.5, loc="lower right" if edge == "rise" else "upper right")
        b.annotate(f"inside the band at {t_first:.0f} ns\n({t_first - t_start:.0f} ns after the drive edge starts)", (t_first, fr[i_first]),
                   (t_first + 70, f0 + 0.4 * (f1 - f0)), fontsize=8.5, color="tab:red", arrowprops=dict(arrowstyle="->", color="tab:red"))
    for x in axes[-1]:
        x.set_xlabel("Time after drive 50 % crossing (ns)   [dotted line = drive edge starts]")
    fig.suptitle(f"{'Rising' if edge == 'rise' else 'Falling'} edges: measured mixer voltage (left) and the frequency it maps to (right), "
                 f"with the +/-{TOL:g} MHz band", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(RUN / f"settle_within_2MHz_{edge}.png", dpi=120)
    plt.close(fig)
with open(RUN / "settle_within_2MHz.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    if r["edge"] == "rise":
        print(r["v_from"], "->", r["v_to"], "| mixer", r["mixer_start_mv"], "->", r["mixer_final_mv"], "mV, band", r["band_low_mv"], "-", r["band_high_mv"],
              "| f", r["freq_start_mhz"], "->", r["freq_final_mhz"], "| first within", r["first_within_ns_after_drive_50pct"], "ns")
