"""Spectrograms, FFT slices and single-pulse waveforms from the newest raw_*.npz. Writes radar_test/plots/ and the website img folder."""
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
OUT.mkdir(exist_ok=True)
IMG = HERE.parent / "phase_detector_calibration" / "site" / "img"
d = np.load(sorted(glob.glob(str(HERE / "raw_*.npz")))[-1])
iq, fs, fc = d["iq"].astype(np.complex128), float(d["fs"]), float(d["center"])
pw = np.abs(iq) ** 2
dbm = 10 * np.log10(pw + 1e-20)
noise = float(np.median(pw))
R = {"noise_dbm_per_sample": round(10 * np.log10(noise), 2)}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=115)
    shutil.copy2(OUT / f"{name}.png", IMG / f"radar_{name}.png")
    plt.close(fig)


def mark(ax, x, y, text, dx=10, dy=10, color="tab:red"):
    ax.plot([x], [y], "v", color=color, ms=7)
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=8, color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.6))


# find the pulses: rising crossings 15 dB over the noise, at least 20 us apart
above = pw > noise * 10 ** 1.5
edges = np.flatnonzero(np.diff(above.astype(np.int8)) == 1) + 1
starts = []
for e in edges:
    if not starts or e - starts[-1] > 20e-6 * fs:
        starts.append(e)
starts = np.array(starts)
peaks = np.array([pw[s: s + 60].max() for s in starts])
k = int(np.argmax(peaks))
s0 = starts[k]
R["pulses_in_record"] = int(len(starts))
R["strongest_dbm"] = round(10 * np.log10(peaks[k]), 2)

# ---------------------------------------------------------------- A. pulse train, 60 ms
t = np.arange(len(pw)) / fs * 1e3
fig, ax = plt.subplots(2, 1, figsize=(14, 8))
dec = 50
env = dbm[: len(dbm) // dec * dec].reshape(-1, dec).max(axis=1)
ax[0].plot(t[::dec][: len(env)], env, lw=0.6)
for i in range(min(len(starts) - 1, 40)):
    a, b = starts[i], starts[i + 1]
    ax[0].annotate(f"{(b - a) / fs * 1e6:.1f}", ((a + b) / 2 / fs * 1e3, 10 * np.log10(max(peaks[i], peaks[i + 1])) + 1.5), ha="center", fontsize=6, color="tab:purple")
mark(ax[0], s0 / fs * 1e3, 10 * np.log10(peaks[k]), f"strongest pulse {10*np.log10(peaks[k]):.1f} dBm")
ax[0].set(xlabel="Time (ms)", ylabel="Peak power in each 1 µs (dBm)", ylim=(10 * np.log10(noise) - 3, 10 * np.log10(peaks[k]) + 6),
          title=f"{len(starts)} pulses in {t[-1]:.0f} ms of one beam pass; purple numbers = time between pulses (µs)")
# B. waterfall: one row per pulse, the FFT of that pulse. Shows whether every pulse is at the same frequency.
nf = 4096
fw = (np.arange(nf) - nf // 2) * fs / nf / 1e6
rows = []
for s_ in starts:
    seg_ = iq[max(0, s_ - int(0.5e-6 * fs)): s_ + int(1.5e-6 * fs)]
    rows.append(10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(seg_, nf))) ** 2 / len(seg_) + 1e-20))
W = np.array(rows)
im = ax[1].imshow(W, aspect="auto", origin="lower", extent=[fw[0], fw[-1], 0.5, len(starts) + 0.5], vmin=W.max() - 45, vmax=W.max(), cmap="viridis")
fig.colorbar(im, ax=ax[1], label="dB")
pkf = fw[np.argmax(W, axis=1)]
ax[1].plot(pkf, np.arange(1, len(starts) + 1), "r.", ms=4, label=f"peak of each pulse: {np.mean(pkf):+.3f} MHz mean, {np.std(pkf)*1e3:.0f} kHz std")
ax[1].set(xlabel=f"Offset from {fc/1e9:.4f} GHz (MHz)", ylabel="Pulse number", xlim=(-10, 10), title="Waterfall: the spectrum of each pulse, one row per pulse (2 µs FFT around each pulse)")
ax[1].legend(fontsize=8, loc="upper right")
R["pulse_to_pulse_freq_std_khz"] = round(float(np.std(pkf) * 1e3), 0)
for a in ax:
    a.grid(alpha=0.25)
save(fig, "train_spectrogram")

# ---------------------------------------------------------------- C. one pulse in time
a, b = s0 - int(1.0e-6 * fs), s0 + int(2.5e-6 * fs)
seg = iq[a:b]
tt = (np.arange(len(seg)) - (s0 - a)) / fs * 1e6
p = np.abs(seg) ** 2
amp = np.sqrt(p / p.max())
fig, ax = plt.subplots(2, 2, figsize=(14, 8.5))
ax[0, 0].plot(tt, 10 * np.log10(p + 1e-20), ".-", ms=3, lw=0.8)
m = int(np.argmax(p))
l_ = m
while l_ > 0 and amp[l_ - 1] > 0.1:
    l_ -= 1
r_ = m
while r_ < len(amp) - 1 and amp[r_ + 1] > 0.1:
    r_ += 1
core = np.arange(l_, r_ + 1)                      # the pulse itself, from 10 % up to 10 % down
i707 = core[amp[core] > 0.707]
i90 = core[amp[core] > 0.9]
i10 = core
mark(ax[0, 0], tt[m], 10 * np.log10(p[m]), f"peak {10*np.log10(p[m]):.1f} dBm")
mark(ax[0, 0], tt[i707[0]], 10 * np.log10(p[i707[0]]), f"-3 dB at {tt[i707[0]]:.2f} µs", dx=-110, dy=-18, color="tab:blue")
mark(ax[0, 0], tt[i707[-1]], 10 * np.log10(p[i707[-1]]), f"-3 dB at {tt[i707[-1]]:.2f} µs\nwidth {(i707[-1]-i707[0]+1)/fs*1e9:.0f} ns", dx=8, dy=-30, color="tab:blue")
ax[0, 0].set(xlabel="Time (µs)", ylabel="Power (dBm)", ylim=(-75, -15), title="One pulse, power, one sample every 20 ns")
ax[0, 1].plot(tt, amp, ".-", ms=3, lw=0.8)
for lev, lab in ((0.1, "10 %"), (0.9, "90 %")):
    ax[0, 1].axhline(lev, color="gray", ls=":", lw=1)
rise = (i90[0] - i10[0]) / fs * 1e9
fall = (i10[-1] - i90[-1]) / fs * 1e9
mark(ax[0, 1], tt[i90[0]], 0.9, f"rise 10-90 %: {rise:.0f} ns", dx=-130, dy=8)
mark(ax[0, 1], tt[i90[-1]], 0.9, f"fall 90-10 %: {fall:.0f} ns", dx=10, dy=8)
ax[0, 1].set(xlabel="Time (µs)", ylabel="Amplitude, relative to the peak", title="Same pulse, amplitude (envelope)")
# I and Q after removing the average carrier offset: shows whether it is a clean tone or oscillating
top = seg[(amp > 0.5)]
ph = np.angle(top[1:] * np.conj(top[:-1]))
foff = float(np.mean(ph)) * fs / (2 * np.pi)
base = seg * np.exp(-2j * np.pi * foff * np.arange(len(seg)) / fs)
base /= np.sqrt(p.max())
ax[1, 0].plot(tt, base.real, lw=0.9, label="I (in phase)")
ax[1, 0].plot(tt, base.imag, lw=0.9, label="Q (quadrature)")
ax[1, 0].plot(tt, amp, "k--", lw=0.6, label="envelope")
ax[1, 0].set(xlabel="Time (µs)", ylabel="Relative amplitude", title=f"I and Q, carrier {(fc+foff)/1e6:.3f} MHz removed")
ax[1, 0].legend(fontsize=8)
# instantaneous frequency inside the pulse
inst = np.angle(seg[1:] * np.conj(seg[:-1])) * fs / (2 * np.pi)
ok = amp[1:] > 0.8
ti = tt[1:][ok]
fi = (inst[ok] + fc) / 1e6
ax[1, 1].plot(ti, fi, ".", ms=4)
if len(ti) > 4:
    c1 = np.polyfit(ti, fi, 1)
    ax[1, 1].plot(ti, np.polyval(c1, ti), "r-", lw=1, label=f"straight-line fit: {c1[0]*1e3:+.0f} kHz/µs")
    R["chirp_khz_per_us"] = round(float(c1[0] * 1e3), 0)
ax[1, 1].set(xlabel="Time (µs)", ylabel="Instantaneous frequency (MHz)", title="Frequency inside the pulse (flat top, amplitude > 80 %)")
ax[1, 1].legend(fontsize=8)
for x in ax.flat:
    x.grid(alpha=0.3)
fig.suptitle("The strongest pulse in detail", fontweight="bold")
save(fig, "one_pulse")
R.update(pulse_carrier_mhz=round((fc + foff) / 1e6, 4), width_ns=round((i707[-1] - i707[0] + 1) / fs * 1e9, 0), rise_ns=round(rise, 0), fall_ns=round(fall, 0))

# ---------------------------------------------------------------- D. spectrogram of one pulse
a2, b2 = s0 - int(1.5e-6 * fs), s0 + int(2.5e-6 * fs)
x = iq[a2:b2]
n2 = 16
w2 = np.hanning(n2)
cols = []
for i in range(len(x) - n2):
    X = np.fft.fftshift(np.fft.fft(x[i:i + n2] * w2, 256))
    cols.append(np.abs(X) ** 2)
S2 = 10 * np.log10(np.array(cols) / np.sum(w2 ** 2) + 1e-20)
f2 = (np.arange(256) - 128) * fs / 256 / 1e6
fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(S2.T, aspect="auto", origin="lower", extent=[-1.5 + n2 / 2 / fs * 1e6, 2.5 - n2 / 2 / fs * 1e6, f2[0], f2[-1]], vmin=S2.max() - 50, vmax=S2.max(), cmap="viridis")
fig.colorbar(im, ax=ax, label="dB (0.32 µs window)")
ax.set(xlabel="Time from the pulse start (µs)", ylabel=f"Offset from {fc/1e9:.4f} GHz (MHz)", ylim=(-20, 20), title="Spectrogram inside one pulse (0.32 µs sliding window): one frequency throughout, no second tone, spread only at the switching edges")
save(fig, "pulse_spectrogram")

# ---------------------------------------------------------------- E. FFT slices with markers
nfft = 1 << 16
def spec(seg_):
    X = np.fft.fftshift(np.fft.fft(seg_, nfft))
    return 10 * np.log10(np.abs(X) ** 2 + 1e-30)
ff = (np.arange(nfft) - nfft // 2) * fs / nfft / 1e6
one = spec(iq[s0 - int(0.5e-6 * fs): s0 + int(1.5e-6 * fs)])
one -= one.max()
strong = [s for s, pk_ in zip(starts, peaks) if pk_ > peaks[k] / 2]
avg = np.mean([10 ** (spec(iq[s - int(0.5e-6 * fs): s + int(1.5e-6 * fs)]) / 10) for s in strong], axis=0)
avg = 10 * np.log10(avg)
avg -= avg.max()
tau = R["width_ns"] * 1e-9
ideal = 20 * np.log10(np.abs(np.sinc((ff - ff[int(np.argmax(avg))]) * 1e6 * tau)) + 1e-12)
R["sidelobe_first_db"] = {}
fig, ax = plt.subplots(1, 2, figsize=(14, 5.2))
for a_, lo in ((ax[0], 15), (ax[1], 4)):
    a_.plot(ff, one, lw=0.8, label="strongest pulse")
    a_.plot(ff, avg, lw=1.2, label=f"average of {len(strong)} pulses within 3 dB")
    a_.plot(ff, ideal, "k:", lw=0.8, label=f"ideal rectangle, {tau*1e9:.0f} ns")
    a_.set(xlim=(-lo, lo), ylim=(-60, 3), xlabel=f"Offset from {fc/1e9:.4f} GHz (MHz)", ylabel="Relative power (dB)")
    a_.grid(alpha=0.3)
pk_i = int(np.argmax(avg))
mark(ax[1], ff[pk_i], 0, f"peak {(fc/1e6 + ff[pk_i]):.3f} MHz")
bw = {}
for lev in (3, 10, 20):
    idx = np.flatnonzero(avg > -lev)
    lo_, hi_ = ff[idx[0]], ff[idx[-1]]
    bw[lev] = round(float(hi_ - lo_), 3)
    axx = ax[1] if lev <= 10 else ax[0]
    axx.annotate("", xy=(lo_, -lev), xytext=(hi_, -lev), arrowprops=dict(arrowstyle="<->", color="tab:red", lw=0.8))
    axx.text((lo_ + hi_) / 2, -lev + 1, f"-{lev} dB: {hi_-lo_:.2f} MHz", ha="center", fontsize=8, color="tab:red")
ax[0].set_title("FFT of single pulses, ±15 MHz")
ax[1].set_title("Zoom ±4 MHz with bandwidth markers")
ax[0].legend(fontsize=8)
save(fig, "fft_pulse")
R["bandwidth_mhz_at_minus_db"] = bw
pk0 = ff[pk_i]
for side, sel in (("low", (ff < pk0 - 1.75) & (ff > pk0 - 2.6)), ("high", (ff > pk0 + 1.5) & (ff < pk0 + 2.6))):
    R["sidelobe_first_db"][side] = round(float(avg[sel].max()), 1)
(OUT / "raw_summary.json").write_text(json.dumps(R, indent=1))
print(json.dumps(R, indent=1))
