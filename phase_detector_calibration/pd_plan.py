"""Coarse-to-fine sweep plan for the delay-line detector: every pass fills in only frequencies not yet taken, so a run cut off at
any point still covers the whole band evenly. Yields run_pd_overnight stages: (stage, rep, [(freq, want_dbm)], kitty, label)."""
import numpy as np

OFF = [(0.0, -999.0)] * 12   # tone-off readings


def fine_sweep(tag, levels, lo=600.0, hi=1600.0, steps=(8.0, 4.0, 2.0, 1.0), reps=2, base=0, level_major=False):
    """level_major: each level across all frequencies of a pass in turn (the zoomed scope reading then keeps its V/div)."""
    yield "off", base, OFF, False, f"tone off before {tag}"
    for n in range(1, reps + 1):
        done = set()
        for s in steps:
            fs = [f for f in np.round(np.arange(lo, hi + s / 2, s), 3).tolist() if f not in done]
            done.update(fs)
            pts = [(f, w) for w in levels for f in fs] if level_major else [(f, w) for f in fs for w in levels]
            yield f"{tag}_{s:g}mhz", n, pts, False, \
                f"repeat {n}: {lo:g}-{hi:g} MHz, {len(fs)} new frequencies at {s:g} MHz spacing x {len(levels)} levels {levels}"
        yield "off", base + n, OFF, False, f"tone off after repeat {n}"
