"""Scan a whole raw recording (racon_raw.py output) block by block: every pulse, and anything 1.5-60 us after it. Prints a timeline."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import racon_analyze as A
d = Path(sys.argv[1]); m = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {"fs": 50e6}
fs = m["fs"]; x = np.memmap(d / "iq.c64", dtype=np.complex64, mode="r")
B = 500_000; nb = len(x) // B
noise = float(np.median(np.abs(x[:B]) ** 2)) / np.log(2); thr = noise * 10 ** 1.5
W = int(60e-6 * fs); g0 = int(1.5e-6 * fs)
out = []
for b in range(nb):
    blk = x[b * B:(b + 1) * B + W] if b < nb - 1 else x[b * B:(b + 1) * B]
    p = blk.real ** 2 + blk.imag ** 2
    for s in A.find_starts(p[:B], thr, W):
        late = p[s + g0:s + W]
        lm = float(late.max()) if len(late) else 0.0
        out.append(((b * B + s) / fs, 10 * np.log10(p[s:s + g0].max()), 10 * np.log10(lm + 1e-30), (int(np.argmax(late)) + g0) / fs * 1e6 if lm else 0))
a = np.array(out)
print(f"{len(x)/fs:.1f} s, noise {10*np.log10(noise):.1f} dBm, {len(a)} triggers")
late = a[a[:, 2] > 10 * np.log10(thr)]
print(f"triggers with something 1.5-60 us later: {len(late)}")
if len(late):
    t = late[:, 0]
    groups = np.split(late, np.flatnonzero(np.diff(t) > 0.5) + 1)
    for g in groups:
        print(f"  {g[0,0]:7.3f}-{g[-1,0]:7.3f} s: {len(g):4d} triggers, pulse {np.median(g[:,1]):+.1f} dBm, later energy up to {g[:,2].max():+.1f} dBm at {np.median(g[:,3]):.1f} us")
np.save(d / "scan.npy", a)
