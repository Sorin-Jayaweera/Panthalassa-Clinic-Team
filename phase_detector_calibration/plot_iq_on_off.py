"""PLL on and PLL off from the saved I/Q, in separate rows: 60 ms of pulses, one pulse, and the spectrum there.

Only 60 ms around the strongest pulse was kept in each 4 s stream, so this does not show a full rotation.
Levels are referred to before the 23 dB pads. The middle and right columns centre on the strongest sample in the
capture, which with the PLL off is not a radar pulse.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import wiring

HERE = Path(__file__).parent
SETS = [("furuno_detector_1nov_pll_on", "PLL ON", "#1f5fa8"), ("furuno_detector_1nov_pll_off_deliberate", "PLL OFF", "#c8691c")]
CASES = [("baseband_21MHz", "near DC"), ("if_1p105GHz", "1.105 GHz")]
fig, axes = plt.subplots(4, 3, figsize=(15, 13))
rows = iter(axes)
for case, title in CASES:
    case_rows = []
    for folder, label, color in SETS:
        row = next(rows)
        case_rows.append(row)
        z = np.load(HERE / folder / f"iq_{case}.npz")
        iq, fs, center, pad = z["iq"], float(z["fs"]), float(z["center"]), float(z["pad_db"])
        db = 10 * np.log10(iq.real ** 2 + iq.imag ** 2 + 1e-20) + pad
        k = int(db.argmax())
        blk = 500
        n0 = len(db) // blk
        env = db[:n0 * blk].reshape(n0, blk).max(axis=1)
        row[0].plot(np.arange(n0) * blk / fs * 1e3, env, lw=0.8, color=color)
        t = (np.arange(len(db)) - k) / fs * 1e6
        w = abs(t) < 3
        row[1].plot(t[w], db[w], lw=1, color=color)
        n = 1024
        a = max(0, k - 100)
        sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq[a:a + n] * np.hanning(n)))) / np.sum(np.hanning(n)) + 1e-20) + pad
        fr = (center + np.fft.fftshift(np.fft.fftfreq(n, 1 / fs))) / 1e6
        row[2].plot(fr, sp, lw=0.8, color=color)
        row[0].set_title(f"{label}, {title}: 60 ms, peak in each 10 µs")
        row[0].set_xlabel("Time (ms)")
        row[1].set_title(f"{label}, {title}: around strongest sample")
        row[1].set_xlabel("Time from strongest sample (µs)")
        row[2].set_title(f"{label}, {title}: spectrum there")
        row[2].set_xlabel("Frequency (MHz)")
        row[0].set_ylabel("dBm before pads")
        row[1].set_ylabel("dBm before pads")
        row[2].set_ylabel("dB before pads")
        for ax in row:
            ax.grid(alpha=0.3)
    for col in range(3):
        lo = min(r[col].get_ylim()[0] for r in case_rows)
        hi = max(r[col].get_ylim()[1] for r in case_rows)
        if col == 1:
            lo = max(lo, -70)
        for r in case_rows:
            r[col].set_ylim(lo, hi)
fig.tight_layout()
wiring.add_strip(fig, wiring.RADAR_P103, "Wiring. LO of the ZX05-14LH-S+: ADF5355 at 8.3 GHz, ZX60-14012L-S+, ZX10-2-1252-S+. PLL OFF rows have the ADF5355 off")
fig.savefig(HERE / "furuno_detector_1nov_iq_on_off.png", dpi=110)
