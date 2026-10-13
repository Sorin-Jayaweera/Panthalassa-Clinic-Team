"""Deconvolution: divide the drive's edge shape out of the measured step responses.

Input  x(t): drive voltage on Vt (scope CH1), averaged over ~420 edges.
Output y(t): mixer voltage (scope CH2), converted back to "equivalent Vt" with the static
             calibration so that the static nonlinearity of VCO + mixer is removed and what is
             left is a linear system with a DC gain of 1.
H(f) = cross-spectrum(x', y') / power-spectrum(x'), combined over all 20 recorded steps
(the derivatives are used so the signals are pulse-like and can be Fourier transformed).
The deconvolved step response is the running integral of the inverse transform of H(f),
band-limited to where the drive edge actually has energy.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RUN = HERE / "step_response" / "20261010_182707"
OUT = HERE / "deconvolution"
OUT.mkdir(exist_ok=True)


def load(path):
    return np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")


cal = load(HERE / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv")
cal = cal[(cal["direction"] == "up") & (cal["vt_meas_v"] <= 1.2)]
order = np.argsort(cal["mixer_out_v"])


def mixer_to_vt(mv):
    return np.interp(mv / 1e3, cal["mixer_out_v"][order], cal["vt_meas_v"][order])


tr = load(RUN / "mean_traces.csv")
summ = load(RUN / "summary.csv")
t = tr["time_ns"] * 1e-9
dt = t[1] - t[0]
N = len(t)
f = np.fft.rfftfreq(N, dt)
pre = t < -0.2e-6
post = (t > 3e-6) & (t < 4.5e-6)


def smooth5(x):
    """The mixer traces were saved with a 5-point smoothing; give the drive the same so it cancels."""
    w = np.hanning(7)[1:-1]
    return np.convolve(x, w / w.sum(), mode="same")


def normalise(z):
    z0, z1 = np.median(z[pre]), np.median(z[post])
    return (z - z0) / (z1 - z0), z1 - z0


k = 150
ramp = 0.5 * (1 - np.cos(np.pi * np.arange(k) / k))
win = np.ones(N)
win[:k], win[-k:] = ramp, ramp[::-1]

DX, DY, gains = [], [], []
for r in summ:
    tag = f"{r['edge']}_lo{r['v_lo_set']:.2f}_hi{r['v_hi_set']:.2f}".replace(".", "")
    xn, xs = normalise(smooth5(tr[tag + "_drive_V"]))
    yn, ys = normalise(mixer_to_vt(tr[tag + "_mixer_mV"]))
    DX.append(np.fft.rfft(np.gradient(xn) * win))
    DY.append(np.fft.rfft(np.gradient(yn) * win))
    gains.append(ys / xs)
DX, DY = np.array(DX), np.array(DY)
print("static gain check (output step in equivalent Vt / drive step; should be about 1):")
print("  ", np.round(gains, 3))

Sxx = np.mean(np.abs(DX) ** 2, axis=0)
Syy = np.mean(np.abs(DY) ** 2, axis=0)
Sxy = np.mean(np.conj(DX) * DY, axis=0)
H = Sxy / Sxx
coh = np.abs(Sxy) ** 2 / (Sxx * Syy)
mag = 20 * np.log10(np.abs(H))
ph = np.unwrap(np.angle(H))
spread = np.std(20 * np.log10(np.abs(DY / DX)), axis=0)

probe = (1, 2, 5, 10, 15, 20, 30, 40)
print("at MHz:                    ", probe)
print("drive-edge content (dB):   ", np.round([10 * np.log10(np.interp(p * 1e6, f, Sxx) / Sxx[0]) for p in probe], 1))
print("coherence:                 ", np.round([np.interp(p * 1e6, f, coh) for p in probe], 3))
print("|H| (dB):                  ", np.round([np.interp(p * 1e6, f, mag) for p in probe], 2))
print("spread between steps (dB): ", np.round([np.interp(p * 1e6, f, spread) for p in probe], 2))

F_VALID = 7e6  # above this the drive edge has a spectral null (about 10 MHz) and the division blows up
sel = (f > 0) & (f <= F_VALID)
fv, Hv, wv = f[sel], H[sel], coh[sel]


def fit(order_n):
    best = None
    for fc in np.concatenate([np.arange(2e6, 60e6, 0.5e6), np.arange(60e6, 400e6, 10e6)]):
        base = 1.0 / (1 + 1j * fv / fc) ** order_n
        for tau in np.arange(-20e-9, 60e-9, 0.5e-9):
            e = np.sum(wv * np.abs(Hv - base * np.exp(-2j * np.pi * fv * tau)) ** 2) / np.sum(wv)
            if best is None or e < best[0]:
                best = (e, fc, tau)
    return best


e1, fc, tau = fit(1)
e2, fc2, tau2 = fit(2)
print(f"one-pole fit:  corner {fc/1e6:.2f} MHz (time constant {1e9/(2*np.pi*fc):.1f} ns, 10-90 % rise {2.197e9/(2*np.pi*fc):.0f} ns), "
      f"delay {tau*1e9:.1f} ns, residual {e1:.4f}")
print(f"two-pole fit:  corner {fc2/1e6:.2f} MHz each, delay {tau2*1e9:.1f} ns, residual {e2:.4f}")
below = np.nonzero(mag[1:] < mag[1] - 3)[0]
print("measured -3 dB point: %.1f MHz" % (f[1:][below[0]] / 1e6 if len(below) else float("nan")))

lowf = (f > 0) & (f <= 5e6)
group_delay = -np.polyfit(2 * np.pi * f[lowf], ph[lowf], 1)[0]
print(f"delay from the phase slope below 5 MHz: {group_delay*1e9:.1f} ns")
print("|H| at 1, 2, 3, 5, 7 MHz (dB):", np.round([np.interp(p * 1e6, f, mag) for p in (1, 2, 3, 5, 7)], 2))

H_reg = Sxy / (Sxx + 0.02 * Sxx[0])  # Wiener-style: stops the division blowing up where the drive has no energy
results = {}
for fcut in (5e6, 7e6):
    G = np.exp(-0.5 * (f / (fcut / 1.177)) ** 2)  # Gaussian band limit, -3 dB at fcut
    shift = N // 6
    step = np.cumsum(np.roll(np.fft.irfft(H_reg * G, N), shift))
    ref = np.cumsum(np.roll(np.fft.irfft(G.astype(complex), N), shift))
    tt = (np.arange(N) - shift) * dt

    def measure(y):
        y = y / np.median(y[(tt > 1.5e-6) & (tt < 3e-6)])
        ok = tt > -0.4e-6
        t10, t50, t90 = (tt[ok][np.nonzero(y[ok] >= lv)[0][0]] for lv in (0.1, 0.5, 0.9))
        return (t90 - t10) * 1e9, t50 * 1e9, y

    r_sys, t50_sys, ys_ = measure(step)
    r_ref, t50_ref, yr_ = measure(ref)
    results[fcut] = (tt, ys_, yr_)
    print(f"band limit {fcut/1e6:.0f} MHz: deconvolved step 10-90 % = {r_sys:.0f} ns; an instant system through the same band limit "
          f"gives {r_ref:.0f} ns; system alone about {np.sqrt(max(r_sys**2 - r_ref**2, 0)):.0f} ns; "
          f"delay at 50 % = {t50_sys - t50_ref:.0f} ns; overshoot {100*(ys_.max()-1):.1f} %")

tt, ys_, yr_ = results[7e6]
tm = np.arange(-0.2e-6, 1.0e-6, 1e-9)
model = np.where(tm > tau, 1 - np.exp(-(tm - tau) * 2 * np.pi * fc), 0)

fig, ax = plt.subplots(2, 2, figsize=(14, 9.5))
a = ax[0, 0]
a.fill_between(f / 1e6, mag - spread, mag + spread, color="tab:blue", alpha=0.2, label="spread of the 20 individual steps")
a.plot(f / 1e6, mag, color="tab:blue", label="measured, all steps combined")
a.plot(f / 1e6, -20 * np.log10(np.abs(1 + 1j * f / fc)), "k--", label=f"one-pole fit, {fc/1e6:.1f} MHz corner")
a.axvspan(F_VALID / 1e6, 40, color="gray", alpha=0.15, label="not trusted: drive edge has a null near 10 MHz")
a.set(xlim=(0, 40), ylim=(-25, 15), xlabel="Modulation frequency (MHz)", ylabel="|H| (dB)",
      title="Transfer function magnitude: drive on Vt -> frequency read by the mixer")
a.legend(fontsize=8)
a = ax[0, 1]
a.plot(f / 1e6, np.degrees(ph), color="tab:blue", label="measured")
a.plot(f / 1e6, np.degrees(np.unwrap(np.angle(np.exp(-2j * np.pi * f * tau) / (1 + 1j * f / fc)))), "k--",
       label=f"fit: {tau*1e9:.0f} ns delay + {fc/1e6:.1f} MHz pole")
a.axvspan(F_VALID / 1e6, 40, color="gray", alpha=0.15)
a.set(xlim=(0, 40), ylim=(-400, 30), xlabel="Modulation frequency (MHz)", ylabel="Phase (degrees)", title="Transfer function phase")
a.legend(fontsize=8)
a = ax[1, 0]
a.plot(f / 1e6, coh, color="tab:green", label="coherence between drive and output (1 = fully explained)")
a.plot(f / 1e6, np.sqrt(Sxx / Sxx[0]), color="tab:orange", label="how much of the drive edge is at this frequency (relative)")
a.axvspan(F_VALID / 1e6, 40, color="gray", alpha=0.15)
a.set(xlim=(0, 40), ylim=(0, 1.05), xlabel="Modulation frequency (MHz)", title="Where the estimate can be trusted")
a.legend(fontsize=8)
a = ax[1, 1]
tag = "rise_lo020_hi100"
a.plot(t * 1e9, normalise(smooth5(tr[tag + "_drive_V"]))[0], color="gray", lw=1, label="measured drive edge (0.2 -> 1.0 V)")
a.plot(t * 1e9, normalise(mixer_to_vt(tr[tag + "_mixer_mV"]))[0], color="tab:blue", lw=1, label="measured output for that drive")
a.plot(tt * 1e9, yr_, ":", color="k", lw=1, label="ideal step through the 7 MHz analysis band (resolution limit)")
a.plot(tt * 1e9, ys_, color="tab:red", lw=1.8, label="DECONVOLVED: output for an ideal step at t = 0")
a.plot(tm * 1e9, model, "--", color="tab:purple", lw=1, label=f"one-pole model: {tau*1e9:.0f} ns delay, {1e9/(2*np.pi*fc):.0f} ns time constant")
a.set(xlim=(-150, 500), ylim=(-0.15, 1.25), xlabel="Time (ns)", ylabel="Normalised step (0 = start, 1 = final)",
      title="Step response with the drive's edge shape divided out")
a.legend(fontsize=7.5, loc="lower right")
for a in ax.ravel():
    a.grid(alpha=0.3)
fig.suptitle("Deconvolution: transfer function and step response of VCO + phase detector (GOOD setup, 20 steps combined)", fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "deconvolution_result.png", dpi=125)

with open(OUT / "transfer_function.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["freq_hz", "H_mag_db", "H_phase_deg", "spread_between_steps_db", "coherence", "drive_content_rel_db"])
    for i in range(1, len(f)):
        if f[i] <= 40e6:
            w.writerow([round(f[i]), round(mag[i], 3), round(np.degrees(ph[i]), 2), round(spread[i], 3), round(coh[i], 4),
                        round(10 * np.log10(Sxx[i] / Sxx[0]), 2)])
m = (tt > -0.3e-6) & (tt < 1.5e-6)
np.savetxt(OUT / "deconvolved_step_response.csv", np.column_stack([tt * 1e9, ys_, yr_])[m], delimiter=",",
           header="time_ns,deconvolved_step,ideal_step_through_7MHz_band", comments="", fmt="%.5g")
print("saved to", OUT)
