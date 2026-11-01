"""Time and frequency from the detector I/Q captures. Levels are referred to before the 23 dB pads."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
D = HERE / "furuno_detector_1nov_pll_on"
CASES = [("baseband_21MHz", "Detector output, centre 21 MHz"), ("if_1p105GHz", "Detector output, centre 1.105 GHz")]
C = "#1f5fa8"
fig, axes = plt.subplots(2, 2, figsize=(12, 7))
for row, (name, title) in zip(axes, CASES):
    z = np.load(D / f"iq_{name}.npz")
    iq, fs, center, pad = z["iq"], float(z["fs"]), float(z["center"]), float(z["pad_db"])
    db = 10 * np.log10(iq.real ** 2 + iq.imag ** 2 + 1e-20) + pad
    k = int(db.argmax())
    above = db > db.max() - 10
    edges = np.flatnonzero(np.diff(above.astype(int)) == 1)
    edges = edges[np.insert(np.diff(edges) > 25, 0, True)]
    pri = np.diff(edges) / fs * 1e6
    width = np.sum(above[max(0, k - 150):k + 150]) / fs * 1e6
    n = 1024
    a = max(0, k - 100)
    seg = iq[a:a + n] * np.hanning(n)
    sp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(seg))) / np.sum(np.hanning(n)) + 1e-20) + pad
    fr = (center + np.fft.fftshift(np.fft.fftfreq(n, 1 / fs))) / 1e6
    pk = fr[int(sp.argmax())]
    print(f"{name}: peak {db.max():.2f} dBm, median {np.median(db):.2f} dBm, pulses within 10 dB {len(edges)}, "
          f"median PRI {np.median(pri) if len(pri) else float('nan'):.1f} us, width within 10 dB {width:.2f} us, spectrum peak {pk:.2f} MHz")
    t = (np.arange(len(db)) - k) / fs * 1e6
    w = abs(t) < 3
    row[0].plot(t[w], db[w], lw=1, color=C)
    row[0].set_xlabel("Time from strongest sample (µs)")
    row[0].set_ylabel("dBm before pads")
    row[0].set_title(title + ": time")
    row[0].grid(alpha=0.3)
    row[1].plot(fr, sp, lw=1, color=C)
    row[1].set_xlabel("Frequency (MHz)")
    row[1].set_ylabel("dB, strongest pulse, before pads")
    row[1].set_title(title + ": frequency")
    row[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / "furuno_detector_1nov_iq.png", dpi=130)
