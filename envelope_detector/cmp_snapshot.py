"""2.8 us waveform snapshots of IN+, IN-, OUT+, OUT- at fixed C2BJ0VL codes.
    .venv-scope/bin/python cmp_snapshot.py <out.csv>
IN+ is returned to code 2750 at the end.
"""
import csv, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cgr_guard, cmp_sweep
from ed_sweep import CGR201

out = sys.argv[1]
g = CGR201("/dev/cu.usbserial-C2BJ0VL"); assert "CircuitGear" in g.identify()
sc = cmp_sweep.Scope()
sc.s.write("TDIV 200E-9"); time.sleep(0.5)
sc.sara = float(sc.s.query("SARA?").split()[-1].replace("Sa/s", ""))
rows = []
try:
    for code in (2750, 2796, 2807, 2812, 2821, 2840):
        cgr_guard.send_dc(g, "C2BJ0VL", code); time.sleep(0.4)
        w = sc.acquire()
        t = np.arange(len(w[1])) / sc.sara * 1e9
        rows += [[code, round(t[i], 2), w[1][i], w[2][i], w[3][i], w[4][i]] for i in range(len(t))]
        d = w[3] - w[4]
        print(code, f"IN+-IN- {1e3*(w[1].mean()-w[2].mean()):+.1f} mV  OUT+-OUT- {1e3*d.mean():+.0f} mV  rms {1e3*d.std():.0f} mV  IN+ pk-pk {1e3*(w[1].max()-w[1].min()):.0f} mV", flush=True)
finally:
    cgr_guard.send_dc(g, "C2BJ0VL", 2750)
    sc.s.write("TDIV 1E-6"); g.close(); sc.close()
with open(out, "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["code", "t_ns", "in_p", "in_m", "out_p", "out_m"]); wr.writerows(rows)
print("saved", out)
