"""Shared pieces of the phase detector plots: CSV rows, curves, tone-off zeros, local slope, one-to-one ranges, level colours, wiring.
Search here (or the Code library tab) before writing a helper in a plot script."""
import csv
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
L5 = (-36.0, -43.0, -50.0, -57.0, -64.0)
PADS = ("3 dB pad at the LO port", "6 dB pad at the RF port")


@lru_cache(None)
def rows(name):
    p = HERE / name
    return tuple(csv.DictReader(open(p))) if p.exists() else ()


def mv(r):
    return float(r["detector_mean_v"]) * 1e3


def fv(rr, first=False, x="freq_mhz"):
    """2 x n array (x, mV) sorted by x; first=True keeps the first reading at each x."""
    if first:
        d = {}
        for r in rr:
            d.setdefault(float(r[x]), mv(r))
        a = sorted(d.items())
    else:
        a = sorted((float(r[x]), mv(r)) for r in rr)
    return np.array(a).reshape(-1, 2).T


def zero(rr, reps=None, stages=("off",), default=np.nan):
    """Median tone-off reading (mV) of the given stages, optionally only the given reps."""
    v = [mv(r) for r in rr if r["stage"] in stages and (reps is None or r["rep"] in reps)]
    return float(np.median(v)) if v else default


def slope(f, v, half, nmin=0):
    """Local least-squares slope over +-half MHz around each point, all points at once (NaN where fewer than nmin points)."""
    W, f = (np.abs(f[:, None] - f[None, :]) <= half).astype(float), f - f.mean()
    n, sx, sy, sxx, sxy = W.sum(1), W @ f, W @ v, W @ f ** 2, W @ (f * v)
    s = (n * sxy - sx * sy) / (n * sxx - sx ** 2)
    return np.where(n >= nmin, s, np.nan)


def delay(f, v, deg=1, taus=np.arange(0.3, 4.0, 0.002)):
    """Best single delay: v = polynomial(f, deg) + A cos(2 pi f tau + phi), f in MHz. Returns (tau ns, A).
    The polynomial is projected out (Frisch-Waugh), leaving a 2 x 2 least-squares solve per tau, done for every tau at once."""
    x = f / 1e3
    Q = np.linalg.qr(np.vander(x, deg + 1))[0]
    P = lambda y: y - Q @ (Q.T @ y)
    ph = 2 * np.pi * np.outer(x, taus)
    C, S, r = P(np.cos(ph)), P(np.sin(ph)), P(v)
    a, b, c, p, q = (C * C).sum(0), (C * S).sum(0), (S * S).sum(0), C.T @ r, S.T @ r
    det = a * c - b * b
    ac, asn = (c * p - b * q) / det, (a * q - b * p) / det
    ok = det > 0.05 * (len(x) / 2) ** 2   # delays too slow to tell from the polynomial over this span are left out
    k = np.argmax(np.where(ok, ac * p + asn * q, -np.inf))   # largest explained variance = smallest residual
    return taus[k], np.hypot(ac[k], asn[k])


def runs(f, ok):
    """Contiguous (start, end) stretches of f where ok is true."""
    e = np.diff(np.r_[0, np.asarray(ok, int), 0])
    return list(zip(f[e[:-1] == 1], f[np.flatnonzero(e == -1) - 1]))


def colours(levels, top=0.9, cmap=plt.cm.viridis):
    return dict(zip(levels, cmap(np.linspace(0, top, len(levels)))))


def chain(pluto, amps="4.03 V, 0.23 A", left="B + E", pads=True, scope="\n1 Mohm, reads the mV", sm="20 dB of pads\nthen SM200B", rf_extra=""):
    """Wiring of the delay-line detector: Pluto, four ZX60-P162LN+, splitter, arms (D right, B + left on the left), mixer, scope and SM200B."""
    lo, rf = PADS if pads else ("no pad", "no pad")
    return [f"Pluto TX\n{pluto}", f"4 x ZX60-P162LN+\n{amps}", "ZFRSC-42-S+\nsplitter",
            [f"right arm (LO): cable D\n{lo}", f"left arm (RF): cable {left}\n{rf}{rf_extra}"], "ZX05-30W-S+\nLO and RF in, IF out", [f"SDS1104X-E CH1{scope}", sm]]
