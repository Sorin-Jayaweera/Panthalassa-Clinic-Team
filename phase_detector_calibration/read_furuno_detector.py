"""Single-shot captures of the phase detector output with the Furuno as the source (scope CH1).

Saves each trigger as a CSV and one screen image. Reads only; drives nothing but the scope.
"""
import csv
import io
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vco_rise_time"))
from sds import SDS  # noqa: E402

OUT = HERE / f"furuno_detector_1nov_{sys.argv[1]}"
OUT.mkdir(exist_ok=True)

s = SDS()
for c in ("C1:TRA ON", "C1:ATTN 1", "C1:CPL D1M", "BWL C1,OFF", "C1:VDIV 1.00E-01V", "C1:OFST -2.00E-01V",
          "C2:TRA OFF", "TDIV 1.00E-06S", "TRDL 0S", "TRSE EDGE,SR,C1,HT,OFF", "C1:TRSL POS"):
    s.write(c)

done = 0
for level in (0.40, 0.30, 0.25, 0.20, 0.15, 0.12, 0.10):
    s.write(f"C1:TRLV {level:.3f}V")
    for shot in range(3):
        if not s.single(timeout=12.0):
            print(f"trigger {level*1e3:.0f} mV: no trigger in 12 s")
            s.write("TRMD STOP")
            break
        t, v = s.waveform(1)
        pre = v[t < -0.5e-6]
        k = int(v.argmax())
        w = v > 0.5 * (v.max() + pre.mean())
        print(f"trigger {level*1e3:.0f} mV shot {shot}: peak {v.max()*1e3:.1f} mV at {t[k]*1e6:.2f} us, baseline {pre.mean()*1e3:.1f} mV, "
              f"pre rms {pre.std()*1e3:.1f} mV, above half {w.sum()*(t[1]-t[0])*1e6:.2f} us", flush=True)
        with open(OUT / f"shot_{done:02d}_trig{level*1e3:.0f}mV.csv", "w", newline="") as f:
            csv.writer(f).writerows([["t_s", "v"], *zip(t, v)])
        if done == 0:
            s.write("SCDP")
            Image.open(io.BytesIO(s.inst.read_raw())).save(OUT / "first_screen.png")
        done += 1
    if done >= 3:
        break
s.write("TRMD AUTO")
s.close()
print("captures", done)
