"""Fake recording in the segmented-capture format, to check racon_analyze.py before the bench. NOT real data: files are named synthetic_*.

Furuno-like pulse (0.66 us, random start phase, 74 kHz pulse-to-pulse frequency scatter, beam pattern over a rotation) and a racon
reply 'R' (. - .) with a 1.8 us unit starting 1.2 us after the pulse, 0.3 MHz above it, phase-continuous between elements.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
fs, fc, pre, L = 250e6, 9.4026e9, int(3e-6 * 250e6), int(40e-6 * 250e6)
rng = np.random.default_rng(1)


def burst(x, t0, dur, f, p_dbm, ph, edge=40e-9):
    t = np.arange(len(x)) / fs
    env = np.clip((t - t0) / edge, 0, 1) * np.clip((t0 + dur - t) / edge, 0, 1)
    x += np.sqrt(10 ** (p_dbm / 10)) * env * np.exp(1j * (2 * np.pi * f * (t - t0) + ph))


def main(n=200):
    snips, times = [], []
    for k in range(n):
        x = (rng.normal(size=L) + 1j * rng.normal(size=L)) * np.sqrt(10 ** (-72 / 10) / 2)
        t_abs = k * 1.6565e-3 + 1000.0
        beam = -26 - 12 * (1 - np.cos(2 * np.pi * k / n)) if k % 7 else -60
        f_r = 0.15e6 + rng.normal(0, 74e3)
        t0 = pre / fs
        if beam > -55:
            burst(x, t0, 0.66e-6, f_r, beam, rng.uniform(0, 2 * np.pi), 80e-9)
        u, ph, f_c = 1.8e-6, rng.uniform(0, 2 * np.pi), f_r + 0.3e6
        t = t0 + 1.2e-6
        for m in (1, 3, 1):
            burst(x, t, m * u, f_c, -36 + rng.normal(0, 0.3), ph + 2 * np.pi * f_c * (t - t0 - 1.2e-6))
            t += (m + 1) * u
        snips.append(x.astype(np.complex64))
        times.append(t_abs)
    meta = dict(kind="SYNTHETIC test data, not a measurement", chain_gain_db=-17.8)
    out = HERE / "data" / "synthetic_seg.npz"
    np.savez(out, snippets=np.array(snips), t_abs_s=np.array(times), pre=pre, fs=fs, center=fc, meta=json.dumps(meta))
    print(out)


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
