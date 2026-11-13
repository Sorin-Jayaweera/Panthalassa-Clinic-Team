"""Export the whole 250 MS/s horn recording (seg_horn_racon_250M) as raw I/Q for the interactive viewer on the site.

Writes claude/docs/racon_iq/:
  meta.json        sample rate, centre, scale, per-snippet start time, chunk layout, reply type per snippet
  overview.bin     int16 [snippet][bin][5] = I min, I max, Q min, Q max, |I+jQ| max over BIN samples
  chunks/cNNN.bin  int16 interleaved I, Q, raw samples, CHUNK snippets per file, in time order
  wiring.png       the setup
The viewer page itself is docs/racon_iq/index.html (hand-written, not generated).
Run:  python racon_iq_web.py
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import racon_stats as R  # noqa: E402

REC = "seg_horn_racon_250M"
OUT = HERE.parent.parent / "docs" / "racon_iq"
CHUNK = 32
BIN = 125          # 0.5 us at 250 MS/s


def main():
    (OUT / "chunks").mkdir(parents=True, exist_ok=True)
    d = R.A.load(R.path_for(REC))
    snips, t, fs, fc, pre = d["snips"], d["t"].astype(float), d["fs"], d["fc"], d["pre"]
    good = t > 1e6
    bad = np.flatnonzero(~good).tolist()
    order = np.argsort(np.where(good, t, -np.inf))                 # bad-time snippets first (only snippet 0, the capture start)
    tg0 = t[good].min()
    t_rel = np.where(good, t - tg0, 0.0)
    for k in bad:                                                  # no valid time stamp: put it one pulse period before the first good one
        t_rel[k] = -1.666e-3
    t0 = t_rel[order] - pre / fs                                   # time of each snippet's FIRST sample, s from the first trigger
    n = snips.shape[1]
    scale = float(np.abs(snips).max()) / 32000.0                   # mW^0.5 per count
    rows = {int(float(r["snip"])): r for r in csv.DictReader(open(R.DATA / f"stats_{REC}_replies.csv"))}
    kind = [rows[int(k)]["variant"] if int(k) in rows else "" for k in order]
    nb = n // BIN
    ov = np.zeros((len(order), nb, 5), np.int16)
    for j0 in range(0, len(order), CHUNK):
        ks = order[j0:j0 + CHUNK]
        q = np.round(snips[ks] / scale)
        I, Q = q.real.astype(np.int16), q.imag.astype(np.int16)
        np.stack([I, Q], -1).astype("<i2").tofile(OUT / "chunks" / f"c{j0 // CHUNK:03d}.bin")
        Ib, Qb = I[:, :nb * BIN].reshape(len(ks), nb, BIN), Q[:, :nb * BIN].reshape(len(ks), nb, BIN)
        A = np.sqrt(Ib.astype(float) ** 2 + Qb.astype(float) ** 2).max(-1)
        ov[j0:j0 + len(ks)] = np.stack([Ib.min(-1), Ib.max(-1), Qb.min(-1), Qb.max(-1), np.minimum(A, 32767).astype(np.int16)], -1)
    ov.astype("<i2").tofile(OUT / "overview.bin")
    entry = R.Z.apply(R.S, REC)
    meta = dict(rec=REC, fs=fs, fc=fc, n=int(n), pre=int(pre), scale_mw05=scale, bin=BIN, nbins=int(nb), chunk=CHUNK,
                nsnip=int(len(order)), t0=[round(float(x), 9) for x in t0], orig=[int(k) for k in order], kind=kind,
                bad_time=[int(np.flatnonzero(order == k)[0]) for k in bad],
                label=entry.get("LABEL", ""), chain_gain_db=R.S.chain_gain_db(),
                note="Segmented capture: the SM200B records 83 us (20750 samples) after each video trigger, so between snippets nothing was recorded.")
    (OUT / "meta.json").write_text(json.dumps(meta))
    fig = plt.figure(figsize=(16, 2.3))
    R.A.wiring.draw(fig.add_axes([0.01, 0.02, 0.98, 0.94]), R.S.stages(), R.S.strip_title())
    fig.savefig(OUT / "wiring.png", dpi=100)
    plt.close(fig)
    tot = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(order)} snippets x {n} samples, scale {scale:.3e} mW^0.5/count, {tot/1e6:.1f} MB in {OUT}")


if __name__ == "__main__":
    main()
