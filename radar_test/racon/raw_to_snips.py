"""Cut a raw recording (racon_raw.py) into one snippet per trigger, keeping EVERY trigger that has something after the pulse
(plus every 20th of the rest for comparison), as an npz racon_analyze.py reads. The raw file itself is untouched."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import racon_analyze as A
d = Path(sys.argv[1]); m = json.loads((d / "meta.json").read_text())
fs, fc = m["fs"], m["center"]
x = np.memmap(d / "iq.c64", dtype=np.complex64, mode="r"); B = 500_000
noise = float(np.median(np.abs(x[:B]) ** 2)) / np.log(2); thr = noise * 10 ** 1.5
pre, W = int(3e-6 * fs), int(80e-6 * fs); k = np.ones(25) / 25
snips, T, late_db, n = [], [], [], 0
for b in range(len(x) // B - 1):
    blk = np.asarray(x[b * B:(b + 1) * B + W])
    p = blk.real ** 2 + blk.imag ** 2
    for s in A.find_starts(p[:B], thr, W):
        if s < pre:
            continue
        lm = np.convolve(p[s + 100:s + W - pre], k, "valid").max()
        n += 1
        if lm > noise * 10 or n % 20 == 0:          # 10 dB over noise on a 0.5 us average
            snips.append(blk[s - pre:s - pre + W]); T.append((b * B + s) / fs); late_db.append(10 * np.log10(lm))
meta = dict(kind=f"raw recording {d.name}, triggers with a reply + every 20th other", chain_gain_db=m["chain_gain_db"], ref_dbm=m["ref_dbm"], triggers=n, raw=d.name)
out = Path(__file__).parent / "data" / f"raw_{d.name}.npz"
np.savez(out, snippets=np.array(snips, np.complex64), t_abs_s=np.array(T), pre=pre, fs=fs, center=fc, all_t_s=np.array(T), all_peak_dbm=np.array(late_db), meta=json.dumps(meta))
print(f"{n} triggers, {len(snips)} kept, {sum(np.array(late_db) > 10*np.log10(noise*10))} with a reply; noise {10*np.log10(noise):.1f} dBm -> {out}")
