"""Two-round DC reading on the SDS1104X-E with the finest V/div that holds the signal, so the 8-bit ADC adds no quantization
(Sorin, 18 Nov: always the highest resolution; measure, then zoom in on that voltage and measure precisely).
Round 1: coarse V/div gives the level and its noise. Round 2: centre the screen on that level (offset = -level) at the finest
V/div whose +-4 div holds the noise; if any sample clips, step up one range and read again."""
import time

import numpy as np

VDIVS = (0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5)   # SDS1104X-E 1-2-5 ranges, 1 Mohm input
CODES_PER_DIV, CLIP = 25.0, 124   # int8 codes; |code| >= CLIP is at the ADC edge


def grab(s, ch, vdiv, ofst, settle=0.25):
    """Set V/div and offset, wait, return (volts array, clipped?)."""
    s.write(f"C{ch}:VDIV {vdiv:.3E}V")
    s.write(f"C{ch}:OFST {ofst:.4E}V")
    time.sleep(settle)
    codes, vd, of, _, _ = s.waveform_raw(ch)
    return codes * (vd / CODES_PER_DIV) - of, bool(np.abs(codes).max() >= CLIP)


def zoom_read(s, ch, coarse=(0.1, -0.04), span_sd=5.0, log=None):
    """(mean V, fine V/div, coarse mean V, fine sd V, clip retries) from one coarse and one fine record."""
    v0, clip0 = grab(s, ch, *coarse)
    m0, sd0 = v0.mean(), v0.std()
    # half a screen must hold the coarse mean's own error (half a coarse step) plus span_sd x the noise
    k = next((i for i, d in enumerate(VDIVS) if 4 * d >= coarse[0] / CODES_PER_DIV / 2 + span_sd * sd0), len(VDIVS) - 1)
    tries = 0
    while True:
        v, clip = grab(s, ch, VDIVS[k], -m0)
        if not clip or k == len(VDIVS) - 1:
            break
        k, tries = k + 1, tries + 1
    if log:
        log(m0, VDIVS[k], v.mean(), v.std(), tries, clip0)
    return float(v.mean()), VDIVS[k], float(m0), float(v.std()), tries


class Tracker:
    """Zoomed readings along a sweep: per key (Pluto level) keep the last fine V/div and level, and read next time with the
    screen centred on the last level, so only the offset moves (no V/div switch, no coarse round). A clipped record, or no
    history, falls back to zoom_read. The V/div for the next point holds span_sd x the noise plus the last step in level."""
    def __init__(self, coarse=(0.1, -0.04), span_sd=5.0):
        self.coarse, self.span_sd, self.last, self.vdiv = coarse, span_sd, {}, None

    def read(self, s, ch, key):
        """(mean V, V/div used, coarse V or nan, sd V, retries)."""
        if key in self.last:
            m_prev, d, dm = self.last[key]
            v, clip = grab(s, ch, d, -m_prev, settle=0.25 if d != self.vdiv else 0.15)
            self.vdiv = d
            out = (float(v.mean()), d, float("nan"), float(v.std()), 0) if not clip else None
        else:
            out = None
        if out is None:
            out = zoom_read(s, ch, self.coarse, self.span_sd)
        self.vdiv = out[1]
        step = abs(out[0] - self.last[key][0]) if key in self.last else 0.0
        need, k = self.span_sd * out[3] + 1.5 * step, VDIVS.index(out[1])
        if 4 * VDIVS[k] < 0.9 * need and k < len(VDIVS) - 1:
            k += 1                       # coarser before it clips
        elif k > 0 and 4 * VDIVS[k - 1] > 1.6 * need:
            k -= 1                       # finer only with margin, so the range does not flip point to point
        self.last[key] = (out[0], VDIVS[k], step)
        return out
