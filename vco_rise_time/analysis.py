"""Signal processing for the VCO step-response test.

The VCO runs at ~0.75-0.9 GHz, far above the scope's Nyquist frequency, so the
scope records an aliased copy. The alias frequency maps one-to-one onto the true
frequency within a Nyquist zone, so we track the alias and unfold it.
"""
import numpy as np

# Measured tuning curve from "VCO tests.xlsx" (absolute accuracy, 10 s column).
VT_TABLE = np.array([0.0, 0.5, 1.0, 1.5, 2.12, 2.72, 3.34, 4.01])
F_TABLE_GHZ = np.array([0.732740546, 0.751433546, 0.778137832, 0.799501261,
                        0.834216833, 0.866261977, 0.906318406, 0.949374836])


def expected_freq_hz(vt):
    """Expected VCO frequency from the earlier spectrum-analyzer measurements."""
    return float(np.interp(vt, VT_TABLE, F_TABLE_GHZ)) * 1e9


def datasheet_freq_hz(vt):
    """Straight-line prediction used in the spreadsheet (0.8 GHz + 60 MHz/V)."""
    return (0.8 + 0.06 * vt) * 1e9


def edge_time(t, v, lo, hi, frac=0.5):
    """First time v crosses lo + frac*(hi-lo) going up (linear interpolation)."""
    level = lo + frac * (hi - lo)
    idx = np.nonzero((v[:-1] < level) & (v[1:] >= level))[0]
    if len(idx) == 0:
        return np.nan
    i = idx[0]
    return t[i] + (level - v[i]) * (t[i + 1] - t[i]) / (v[i + 1] - v[i])


def levels(v):
    """Low/high plateau levels of a two-level waveform."""
    mid = 0.5 * (v.min() + v.max())
    return float(np.median(v[v < mid])), float(np.median(v[v >= mid]))


def rise_10_90(t, y, y0, y1):
    """10-90 % transition time of y going from y0 to y1 (either direction)."""
    s = (y - y0) / (y1 - y0)
    t10 = edge_time(t, s, 0.0, 1.0, 0.1)
    t90 = edge_time(t, s, 0.0, 1.0, 0.9)
    return t90 - t10, t10, t90


def settle_time(t, y, y0, y1, tol=0.05):
    """Last time y is outside +/- tol*(step) of its final value."""
    bad = np.nonzero(np.abs(y - y1) > tol * abs(y1 - y0))[0]
    if len(bad) == 0:
        return t[0]
    return t[min(bad[-1] + 1, len(t) - 1)]


SCOPE_SPURS_HZ = (62.5e6, 83.3333e6, 120e6, 125e6, 166.6667e6, 250e6)  # SDS1104X-E internal lines
WIDE_SPURS_HZ = (72.0e6, 80.8e6, 83.0e6, 83.7e6, 104.17e6, 137.5e6)  # broader lines seen on CH2


def remove_periodic(t, v, edges, period):
    """Subtract everything locked to the square wave (drive feedthrough) from v.

    The VCO's phase is random from edge to edge, so the edge-locked average holds
    only the leakage of the drive into the RF channel.
    """
    dt = t[1] - t[0]
    grid = np.arange(0.0, period, dt)
    tmpl, n = stack_edges(t, v.astype(complex), edges[:-1], grid)
    tmpl = tmpl.real / max(n, 1)
    k = np.searchsorted(edges, t, side="right") - 1
    tau = np.where(k >= 0, t - edges[np.maximum(k, 0)], t - (edges[0] - period))
    return v - np.interp(np.mod(tau, period), grid, tmpl, period=period)


def choose_band(fa_lo, fa_hi, fs, margin=5e6, max_lag=8):
    """Pick (start, stop, taper_lo, taper_hi) and the lag for a step between two alias plateaus.

    Wide steps get wide filter skirts: a narrow skirt rings for longer, and the strong
    plateau's ringing would otherwise reach back over the weak one.
    The lag is the largest one whose unambiguous range fs/lag still covers the band.
    """
    lo, hi = min(fa_lo, fa_hi), max(fa_lo, fa_hi)
    taper = float(np.clip(0.25 * (hi - lo), 6e6, 30e6))
    b = min(hi + margin + taper, fs / 2 - 1e6)
    taper_hi = max(b - (hi + margin), 3e6)
    a = max(lo - margin - taper, 3e6)
    lag = max_lag
    while lag > 1 and fs / lag < (b - a):
        lag -= 1
    return (a, b, taper, taper_hi), lag


def plateau_noise_psd(t, v, edges, fs, m=2048):
    """Noise density (variance per sample, vs frequency) from the settled stretches only.

    Estimating the floor from the whole record does not work: the frequency sweeps at
    every edge spread signal energy across the band and inflate the estimate.
    """
    win = np.hanning(m)
    starts = np.concatenate([edges + 4e-6, edges - 6e-6])
    idx = np.round((starts - t[0]) * fs).astype(int)
    idx = idx[(idx >= 0) & (idx + m <= len(v))]
    segs = np.stack([v[i:i + m] for i in idx])
    p = np.abs(np.fft.rfft((segs - segs.mean(axis=1, keepdims=True)) * win, axis=1)) ** 2
    psd = np.median(p, axis=0) / np.log(2) / np.sum(win ** 2)
    k = 9  # running median across frequency removes the narrow plateau lines
    pad = np.pad(psd, k // 2, mode="edge")
    psd = np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=1)
    return np.fft.rfftfreq(m, 1 / fs), psd


def lag_product(v, fs, band, lag, noise=None, avoid=()):
    """z[n+lag] * conj(z[n]) for the analytic signal restricted to band = (start, stop).

    The band edges are raised-cosine tapers: a brick-wall filter rings for microseconds
    and smears the strong high-level signal back over the weak low-level plateau.
    `noise` = (freqs, psd) from plateau_noise_psd; its contribution is subtracted so that
    weak signals are not dragged toward wherever the noise floor is strongest.
    """
    n = len(v)
    spec = np.fft.fft(v - v.mean())
    f = np.fft.fftfreq(n, 1 / fs)
    a, b, taper_lo, taper_hi = band
    w = np.clip((f - a) / taper_lo, 0, 1) * np.clip((b - f) / taper_hi, 0, 1)
    w = np.sin(0.5 * np.pi * w) ** 2
    # No notches for the scope's internal spurs: a narrow notch rings for microseconds and
    # smears the strong plateau over the weak one. The spurs are far smaller than that error.
    z = np.fft.ifft(2 * spec * w)
    p = z[lag:] * np.conj(z[:-lag])
    if noise is not None:
        sel = w > 0
        psd = np.interp(f[sel], noise[0], noise[1])
        p = p - 4.0 / n * np.sum(psd * w[sel] ** 2 * np.exp(2j * np.pi * f[sel] * lag / fs))
    return p


def lag_to_alias(p, fs, band_start, lag):
    """Alias frequency from an (averaged) lag product, resolved inside the band."""
    ph = np.angle(p * np.exp(-2j * np.pi * band_start * lag / fs))
    return band_start + np.mod(ph, 2 * np.pi) * fs / (2 * np.pi * lag)


def stack_edges(tp, p, edges, grid):
    """Sum p(t - edge) over all edges, interpolated onto the common grid."""
    dt = tp[1] - tp[0]
    acc = np.zeros(len(grid), complex)
    n = 0
    for e in edges:
        x = (grid + e - tp[0]) / dt
        if x[0] < 0 or x[-1] > len(p) - 2:
            continue
        i0 = np.floor(x).astype(int)
        w = x - i0
        acc += p[i0] * (1 - w) + p[i0 + 1] * w
        n += 1
    return acc, n


def rising_edges(t, v, lo, hi):
    """Times of all low->high crossings of the 50 % level (with hysteresis)."""
    mid, hyst = 0.5 * (lo + hi), 0.25 * (hi - lo)
    state = np.zeros(len(v), dtype=np.int8)
    state[v > mid + hyst] = 1
    state[v < mid - hyst] = -1
    idx = np.nonzero(state)[0]
    s = state[idx]
    ups = idx[1:][(s[1:] == 1) & (s[:-1] == -1)]  # first sample above the upper threshold
    out = []
    for k in ups:
        j = k
        while j > 0 and v[j - 1] >= mid:
            j -= 1
        if j > 0:
            out.append(t[j - 1] + (mid - v[j - 1]) * (t[j] - t[j - 1]) / (v[j] - v[j - 1]))
    return np.array(out)


def smooth(x, n):
    n = max(1, int(n)) | 1
    if n < 3:
        return x
    w = np.hanning(n + 2)[1:-1]
    return np.convolve(x, w / w.sum(), mode="same")


def unfold(f_alias, fs, f_expected):
    """Map alias frequency to the true frequency in the zone containing f_expected."""
    zone = int(f_expected // (fs / 2))  # 0-based Nyquist zone
    if zone % 2 == 0:
        return zone * fs / 2 + f_alias
    return (zone + 1) * fs / 2 - f_alias


def fold(f_true, fs):
    """Alias frequency of f_true when sampled at fs."""
    r = np.mod(f_true, fs)
    return np.minimum(r, fs - r)


class LevelStack:
    """Accumulates all rising edges of one voltage level into a frequency-vs-time trace."""

    def __init__(self, grid, f_lo_guess, f_hi_guess, sq_hz, n_groups=4):
        self.grid, self.sq_hz, self.n_groups = grid, sq_hz, n_groups
        self.f_lo_guess, self.f_hi_guess = f_lo_guess, f_hi_guess
        self.acc = np.zeros((n_groups, len(grid)), complex)
        self.drive = np.zeros(len(grid))
        self.n_edges, self.n_caps, self.fs, self.band, self.lag = 0, 0, None, None, None

    def add(self, t, vd, vr, fs):
        if self.band is None:
            self.fs = fs
            self.alias = (fold(self.f_lo_guess, fs), fold(self.f_hi_guess, fs))
            self.band, self.lag = choose_band(*self.alias, fs)
        dlo, dhi = levels(vd)
        edges = rising_edges(t, vd, dlo, dhi)
        vr = remove_periodic(t, vr, edges, 1.0 / self.sq_hz)
        noise = plateau_noise_psd(t, vr, edges, fs)
        p = lag_product(vr, fs, self.band, self.lag, noise=noise, avoid=self.alias)
        pa, ne = stack_edges(t[:-self.lag] + 0.5 * self.lag / fs, p, edges, self.grid)
        self.acc[self.n_caps % self.n_groups] += pa
        self.drive += stack_edges(t, vd.astype(complex), edges, self.grid)[0].real
        self.n_edges += ne
        self.n_caps += 1

    def freq(self, group=None, smooth_pts=11):
        acc = self.acc.sum(axis=0) if group is None else self.acc[group]
        f_alias = lag_to_alias(smooth(acc, smooth_pts), self.fs, self.band[0], self.lag)
        return unfold(f_alias, self.fs, 0.5 * (self.f_lo_guess + self.f_hi_guess))

    def drive_mean(self):
        return self.drive / max(self.n_edges, 1)

    def lag_magnitude(self):
        return np.abs(self.acc.sum(axis=0)) / max(self.n_edges, 1)


if __name__ == "__main__":
    pass
