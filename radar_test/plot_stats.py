"""Rotation, beam pattern, pulse-spacing and pulse-statistics plots from the 30 s pulse captures."""
import glob
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "plots"
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"
dirs = sorted(glob.glob(str(HERE / "pulses_*")))
SLOW = [d for d in dirs if d.endswith("_dec8") and json.load(open(Path(d) / "summary.json"))["center_hz"] < 1e10][-1]
FAST = [d for d in dirs if not d.endswith("_dec8") and (Path(d) / "pulses.csv").exists() and np.genfromtxt(Path(d) / "pulses.csv", delimiter=",", skip_header=1).shape[1] == 7][-1]
R = {}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=115)
    shutil.copy2(OUT / f"{name}.png", IMG / f"radar_{name}.png")
    plt.close(fig)


P = np.genfromtxt(Path(SLOW) / "pulses.csv", delimiter=",", skip_header=1)
t, pk = P[:, 0], P[:, 1]
g = 1e-3
m = np.full(int(t.max() / g) + 1, -80.0)
np.maximum.at(m, (t / g).astype(int), pk)
x = 10 ** (m / 10)
x -= x.mean()
ac = np.correlate(x, x, "full")[len(x) - 1:]
lag = np.arange(len(ac)) * g
s = (lag > 1.5) & (lag < 3.5)
T1 = lag[s][np.argmax(ac[s])]
s4 = (lag > 4 * T1 - 0.1) & (lag < 4 * T1 + 0.1)
T = lag[s4][np.argmax(ac[s4])] / 4
R.update(rotation_s=round(float(T), 4), rpm=round(60 / T, 2))

fig, ax = plt.subplots(2, 1, figsize=(13, 7.5))
ax[0].plot(t, pk, ".", ms=1.2)
mains = [i for i in range(len(pk)) if pk[i] > pk.max() - 3]
ax[0].set(xlabel="Time (s)", ylabel="Pulse peak (dBm)", title=f"Every pulse for {t.max():.0f} s (6.25 MS/s, no samples lost): one strong pass per rotation")
ax[1].plot(lag, ac / ac[0], lw=0.8)
for n in range(1, 5):
    ax[1].axvline(n * T, color="tab:red", ls="--", lw=0.8)
ax[1].annotate(f"rotation {T:.4f} s = {60/T:.2f} rpm", (T, 0.6), xytext=(15, 0), textcoords="offset points", color="tab:red", fontsize=9)
ax[1].set(xlabel="Lag (s)", ylabel="Autocorrelation of received power", xlim=(0, 11), title="The received power repeats every rotation; the red lines are 1 to 4 rotations")
for a in ax:
    a.grid(alpha=0.3)
save(fig, "timeline")

ang = (t % T) / T * 360
k = int(np.argmax(pk))
ang = (ang - ang[k] + 180) % 360 - 180
bins = np.arange(-180, 181, 1.0)
idx = np.digitize(ang, bins) - 1
prof = np.array([np.percentile(pk[idx == i], 90) if np.sum(idx == i) > 3 else np.nan for i in range(len(bins) - 1)])
c = bins[:-1] + 0.5
top = np.nanmax(prof)
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ax[0].plot(ang, pk, ".", ms=1, alpha=0.3, label="each pulse")
ax[0].plot(c, prof, "k", lw=1, label="90th percentile in each degree")
for a0, lab in ((0, "main beam"), (180, "half a turn later")):
    j = int(np.argmin(np.abs(c - a0 if a0 == 0 else np.abs(c) - 180)))
ax[0].annotate(f"main beam {top:.1f} dBm", (0, top), xytext=(20, 5), textcoords="offset points", fontsize=8, color="tab:red", arrowprops=dict(arrowstyle="->", color="tab:red"))
back = np.abs(c) > 150
jb = int(np.nanargmax(np.where(back, prof, -200)))
ax[0].annotate(f"{prof[jb]:.1f} dBm at {c[jb]:.0f}°\n({prof[jb]-top:.1f} dB)", (c[jb], prof[jb]), xytext=(25, 10), textcoords="offset points", fontsize=8, color="tab:red", arrowprops=dict(arrowstyle="->", color="tab:red"))
ax[0].set(xlabel="Radar antenna angle from the direction of the Vivaldi (deg)", ylabel="Pulse peak at the SM200B (dBm)", title="Received pulse peak against radar antenna angle, all rotations folded")
ax[0].legend(fontsize=8, loc="lower left")
ax[1].plot(c, prof - top, "k", lw=1)
ax[1].axhline(-3, color="tab:red", ls="--", lw=1)
w = c[prof > top - 3]
ax[1].annotate(f"-3 dB from {w.min():.0f}° to {w.max():.0f}°", (w.max(), -3), xytext=(10, -25), textcoords="offset points", fontsize=8, color="tab:red", arrowprops=dict(arrowstyle="->", color="tab:red"))
ax[1].set(xlabel="Radar antenna angle (deg)", ylabel="Relative to the strongest (dB)", xlim=(-40, 40), ylim=(-25, 2), title="Main lobe zoomed (11.3 m away, room reflections included)")
for a in ax:
    a.grid(alpha=0.3)
save(fig, "beam")
R.update(beam_peak_dbm=round(float(top), 2), beam_3db_deg=[float(w.min()), float(w.max())], back_dbm=round(float(prof[jb]), 2), back_deg=float(c[jb]), back_rel_db=round(float(prof[jb] - top), 1))

d = np.diff(t) * 1e6
d1 = d[(d > 1550) & (d < 1750)]
step = 100 / 15
vals = np.unique(np.round((d1 - 1606.5) / step) * step + 1606.5)
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8))
h_, e_, _ = ax[0].hist(d1, bins=np.arange(1600, 1712, 0.5), color="tab:purple")
for v in vals:
    ax[0].annotate(f"{v:.1f}", (v, h_.max() * 0.95), rotation=90, fontsize=6, ha="center", color="gray")
ax[0].set(xlabel="Time between consecutive pulses (µs)", ylabel="Count", title=f"{len(d1)} intervals: {len(vals)} values, {vals.min():.1f} to {vals.max():.1f} µs, step {step:.2f} µs")
ax[1].plot(d1[:150], "o-", ms=3, lw=0.5)
ax[1].set(xlabel="Interval number (consecutive)", ylabel="Time between pulses (µs)", title="The first 150 intervals in order: the spacing jumps among the 16 values")
for a in ax:
    a.grid(alpha=0.3)
save(fig, "pri")
R.update(pri_values_us=[round(float(v), 1) for v in vals], pri_mean_us=round(float(np.mean(d1)), 1), prf_mean_hz=round(1e6 / float(np.mean(d1)), 1))

F = np.genfromtxt(Path(FAST) / "pulses.csv", delimiter=",", skip_header=1)
st = F[F[:, 1] > F[:, 1].max() - 3]
fig, ax = plt.subplots(1, 4, figsize=(16, 3.8))
for i, (col, lab, rng) in enumerate(((2, "Width at half power (ns)", np.arange(560, 740, 20)), (3, "Rise 10-90 % (ns)", np.arange(0, 260, 20)), (4, "Fall 90-10 % (ns)", np.arange(0, 260, 20)))):
    ax[i].hist(st[:, col], bins=rng, color="tab:blue")
    med = np.median(st[:, col])
    ax[i].axvline(med, color="tab:red", ls="--", lw=1)
    ax[i].set(xlabel=lab, ylabel="Pulses", title=f"median {med:.0f} ns")
fq = F[(F[:, 1] > -30) & np.isfinite(F[:, 5])][:, 5]
ax[3].hist(fq, bins=40, color="tab:green")
ax[3].axvline(np.median(fq), color="tab:red", ls="--", lw=1)
ax[3].set(xlabel="Carrier frequency of each pulse (MHz)", ylabel="Pulses", title=f"median {np.median(fq):.3f} MHz")
for a in ax:
    a.grid(alpha=0.3)
fig.suptitle(f"Pulse statistics, 50 MS/s: {len(st)} pulses within 3 dB of the strongest; frequency from {len(fq)} pulses above -30 dBm. Edges are measured to one 20 ns sample.", fontsize=10)
save(fig, "pulse_stats")
R.update(width_ns=np.percentile(st[:, 2], [5, 50, 95]).round(0).tolist(), rise_ns=np.percentile(st[:, 3], [5, 50, 95]).round(0).tolist(),
         fall_ns=np.percentile(st[:, 4], [5, 50, 95]).round(0).tolist(), freq_mhz=np.percentile(fq, [5, 50, 95]).round(3).tolist(), n_strong=int(len(st)))
(OUT / "stats_summary.json").write_text(json.dumps(R, indent=1))
print(json.dumps(R, indent=1))
