"""Time signal of every pulse in one beam pass, stacked by pulse number (a ridgeline / waterfall of wiggly lines).

Data: raw_20261025_130811.npz, 60 ms of SM200B I/Q at 50 MS/s centred on 9402.6 MHz, 11.3 m from the Furuno (the capture behind the
pulse plots on the Radar tab). The SM200B removes the 9.4 GHz carrier, so the raw data is I and Q, one complex sample every 20 ns.
Left panel: the raw I samples. Right panel: the same I/Q moved to a 5 MHz display frequency so the oscillation can be drawn;
the real 9.4 GHz carrier makes about 6,600 cycles in one pulse. Voltage is at the SM200B input, 50 ohm, real-signal peak.
Writes plots/pulse_wiggles.png and pulse_wiggles_raw.csv (every sample of every pulse window).
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phase_detector_calibration"))
import wiring  # noqa: E402

F = HERE / "raw_20261025_130811.npz"
d = np.load(F)
iq, fs, fc = d["iq"].astype(np.complex128), float(d["fs"]), float(d["center"])
p = np.abs(iq) ** 2                                    # mW at the SM200B input
noise = np.median(p)
hot = p > noise * 10 ** 1.5                            # 15 dB over the noise
starts = np.flatnonzero(hot & ~np.r_[False, hot[:-1]])
pulses = []
for s in starts:
    if pulses and s - pulses[-1] < int(100e-6 * fs):
        continue
    seg = p[s:s + int(1.5e-6 * fs)]
    half = s + int(np.argmax(seg >= seg.max() / 2))     # align on the half-power point of the rising edge
    pulses.append(half)
pre, post = int(0.4e-6 * fs), int(1.2e-6 * fs)
pulses = [k for k in pulses if k - pre >= 0 and k + post < len(iq)]
t = np.arange(-pre, post) / fs * 1e6                   # microseconds from the rising edge
K = 2 * 50 * 1e-3                                      # real-signal peak volts = sqrt(2 R P), P in W
volts = lambda z: np.sqrt(K) * z * 1e3                 # complex envelope in mV peak
SHOW_HZ = 5e6
segs = [iq[k - pre:k + post] for k in pulses]
peak = max(np.abs(volts(s)).max() for s in segs)
step = peak * 2.1

fig = plt.figure(figsize=(15, 17))
gs = fig.add_gridspec(2, 2, height_ratios=[11, 1], hspace=0.12, wspace=0.06, left=0.06, right=0.98, top=0.93, bottom=0.02)
a = fig.add_subplot(gs[0, 0])
b = fig.add_subplot(gs[0, 1], sharey=a)
wiring.draw(fig.add_subplot(gs[1, :]), ["Furuno 1722C/NT"+chr(10)+"11.3 m, foam on radome", "Vivaldi R120"+chr(10)+"facing the radar", "long SMA cable",
                                        "JFW manual attenuator"+chr(10)+"at 0 dB", "10 + 2 + 2 dB"+chr(10)+"fixed pads", "SM200B"+chr(10)+"I/Q, 50 MS/s, 9402.6 MHz"], "Wiring, 25 Oct 13:08")
for n, s in enumerate(segs):
    base = n * step
    raw = volts(s).real
    shown = volts(s * np.exp(2j * np.pi * SHOW_HZ * np.arange(len(s)) / fs)).real
    for ax, y in ((a, raw), (b, shown)):
        ax.plot(t, base + y, color=plt.cm.viridis(n / max(len(segs) - 1, 1)), lw=0.9, zorder=2 * n + 2)
        ax.plot(t, base + np.abs(volts(s)), color="0.6", lw=0.5, ls=":", zorder=2 * n + 2)
for ax in (a, b):
    ax.set_xlabel("Time from the rising edge (us)")
    ax.set_xlim(t[0], t[-1])
    ax.grid(alpha=0.25)
    ax.set_yticks([n * step for n in range(0, len(segs), 5)], [str(n + 1) for n in range(0, len(segs), 5)])
a.set_ylabel(f"Pulse number in the beam pass (one row = {step:.1f} mV)")
a.set_title("Raw I samples, one every 20 ns, carrier removed by the SM200B")
b.set_title("Same I/Q drawn at a 5 MHz display frequency\n(the 9.4 GHz carrier itself is about 6,600 cycles per pulse)")
fig.suptitle(f"{len(segs)} pulses of one beam pass, stacked: time signal at the SM200B input, mV peak. Dotted grey: envelope", y=0.985)
fig.savefig(HERE / "plots" / "pulse_wiggles.png", dpi=110)

with open(HERE / "pulse_wiggles_raw.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pulse", "sample_index_in_capture", "time_from_rising_edge_us", "i_sqrt_mw", "q_sqrt_mw"])
    for n, k in enumerate(pulses):
        for j, z in enumerate(segs[n]):
            w.writerow([n + 1, k - pre + j, round(float(t[j]), 3), f"{z.real:.6e}", f"{z.imag:.6e}"])
print(len(segs), "pulses; peak", round(peak, 1), "mV; noise", round(10 * np.log10(noise), 1), "dBm per sample; centre", fc, "fs", fs)
print("start phase of each pulse, degrees:", [int(np.degrees(np.angle(s[pre + 10]))) for s in segs][:12])
