"""Measure a few fixed IN+ points (C2BJ0VL codes) and compare with sweep 6 and an earlier run.
    .venv-scope/bin/python cmp_points.py [label]
Results appended to data/cmp_points_20261123.csv. IN+ is returned to code 2750 at the end.
"""
import csv, os, sys, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cgr_guard, cmp_sweep
from ed_sweep import CGR201

label = sys.argv[1] if len(sys.argv) > 1 else "run"
REF = {2750: (3.2, -394), 2796: (42.3, -393), 2807: (102.5, -81), 2812: (112.9, -23), 2821: (110.2, 83)}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cmp_points_20261123.csv")
g = CGR201("/dev/cu.usbserial-C2BJ0VL")
assert "CircuitGear" in g.identify()
sc = cmp_sweep.Scope()
rows = []
print(f"{label}: code  IN+-IN-  rms now (sweep 6)  mean now (sweep 6)  low/high  IN- pk-pk")
try:
    for code in (2750, 2796, 2807, 2812, 2821, 2750):
        cgr_guard.send_dc(g, "C2BJ0VL", code)
        time.sleep(0.4)
        w = sc.acquire()
        r = cmp_sweep.classify(w, sc.sara)
        inm = 1e3 * (w[2].max() - w[2].min())
        rr, rd = REF[code]
        print(f"  {code}  {r['diff_in_mv']:+7.1f}  {r['out_rms_mv']:6.1f} ({rr:5.1f})   {1e3*r['out_diff']:+6.0f} ({rd:+5d})      "
              f"{r['frac_low']:.2f}/{r['frac_high']:.2f}   {inm:.0f}")
        rows.append(dict(label=label, time=datetime.now().isoformat(timespec="seconds"), code=code,
                         diff_in_mv=round(r["diff_in_mv"], 2), out_rms_mv=round(r["out_rms_mv"], 1),
                         out_diff_mv=round(1e3 * r["out_diff"], 1), frac_low=round(r["frac_low"], 3),
                         frac_high=round(r["frac_high"], 3), in_minus_pkpk_mv=round(inm, 1)))
finally:
    cgr_guard.send_dc(g, "C2BJ0VL", 2750)
    g.close()
    sc.close()
new = not os.path.exists(out)
with open(out, "a", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0]))
    if new:
        wr.writeheader()
    wr.writerows(rows)
