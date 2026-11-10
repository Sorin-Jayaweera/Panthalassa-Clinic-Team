"""Record EVERY I/Q sample to disk, nothing thrown away. 50 MS/s, 41.5 MHz wide, complex64 (I, Q float32, sqrt(mW) so I^2+Q^2 = mW at the SM200B).

    python racon_raw.py 300 [--center 9408.5e6]

Writes C:/racon_raw/<time>/iq.c64 (raw interleaved float32 I,Q, 400 MB/s) and meta.json (rate, centre, levels, chain, every block's
sample loss and time). Outside Dropbox on purpose: 5 min is about 120 GB.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "signal_hound"))
os.chdir(HERE.parent.parent / "signal_hound")
from smdevice.sm_api import *  # noqa: E402,F403
import racon_setup as S  # noqa: E402
import racon_analyze as A  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("seconds", type=float)
ap.add_argument("--center", type=float, default=9408.5e6)
ap.add_argument("--ref", type=float, default=-10.0, help="reference level dBm (strongest radar pulse was -15 dBm)")
a = ap.parse_args()

out = Path("C:/racon_raw") / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
out.mkdir(parents=True, exist_ok=True)
BLK = 500_000
h = sm_open_device()["device"]
blocks = []
try:
    t0c = sm_get_device_diagnostics(h)["temperature"]
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, a.ref)
    sm_set_IQ_center_freq(h, a.center)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_set_IQ_queue_size(h, 100.0)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    par = sm_get_IQ_parameters(h)
    fs = par["sample_rate"]
    n = int(a.seconds * fs / BLK)
    t_start = time.time()
    print(f"recording {n*BLK/fs:.0f} s at {fs/1e6:.0f} MS/s, {par['bandwidth']/1e6:.1f} MHz wide, centre {a.center/1e6:.1f} MHz, ref {a.ref} dBm -> {out}", flush=True)
    with open(out / "iq.c64", "wb", buffering=0) as fh:
        for b in range(n):
            r = sm_get_IQ(h, BLK, 0, SM_TRUE if b == 0 else SM_FALSE)
            fh.write(r["iq_buf"].tobytes())
            pk = float(np.max(r["iq_buf"].real ** 2 + r["iq_buf"].imag ** 2))
            blocks.append((r["ns_since_epoch"], r["sample_loss"], r["samples_remaining"], round(10 * np.log10(pk + 1e-30), 2)))
            if b == 0:
                noise = float(np.median(r["iq_buf"].real ** 2 + r["iq_buf"].imag ** 2)) / np.log(2)
                thr = noise * 10 ** 1.5
                live = dict(radar=0, late=0, best_late=-300.0)
            if b % 5 == 0:                                   # live look at every 5th block (status only; every block is saved)
                x = r["iq_buf"]
                pp = x.real ** 2 + x.imag ** 2
                for st in A.find_starts(pp, thr, int(60e-6 * fs)):
                    live["radar"] += 1
                    late = pp[st + int(1.5e-6 * fs): st + int(60e-6 * fs)]
                    if len(late) and late.max() > thr:
                        live["late"] += 1
                        live["best_late"] = max(live["best_late"], 10 * np.log10(late.max()))
            if b and b % int(5 * fs / BLK) == 0:
                seen = "RACON-LIKE REPLIES SEEN" if live["late"] else "no reply after pulses"
                print(f"  {b*BLK/fs:5.0f} s  peak {max(x[3] for x in blocks[-int(5*fs/BLK):]):+.1f} dBm | pulses {live['radar']} | {seen}"
                      + (f" ({live['late']}, strongest {live['best_late']:+.1f} dBm)" if live["late"] else "")
                      + f" | noise {10*np.log10(noise):.1f} dBm | lost {sum(x[1] for x in blocks)}", flush=True)
                live = dict(radar=0, late=0, best_late=-300.0)
                if blocks[-1][3] > S.SM_LIMIT_DBM - 10:
                    print("STOP: within 10 dB of +20 dBm", flush=True)
                    break
    t1c = sm_get_device_diagnostics(h)["temperature"]
finally:
    try:
        sm_abort(h)
    finally:
        sm_close_device(h)
        meta = dict(file="iq.c64", format="complex64 interleaved float32 I,Q little-endian; I^2+Q^2 = mW at SM200B input", fs=fs, center=a.center,
                    bandwidth=par["bandwidth"], ref_dbm=a.ref, atten="auto", block_samples=BLK, blocks=len(blocks),
                    block_cols="ns_since_epoch, sample_loss, samples_remaining, peak_dbm", block_log=blocks,
                    wall_start=dt.datetime.fromtimestamp(t_start).isoformat(timespec="seconds"), temps_c=[t0c, locals().get("t1c")],
                    chain=[list(c) for c in S.CHAIN], chain_gain_db=S.chain_gain_db(), d_radar_m=S.D_RADAR_M, d_racon_m=S.D_RACON_M)
        (out / "meta.json").write_text(json.dumps(meta, default=float))
        print(f"saved {len(blocks)*BLK/fs:.1f} s, samples lost {sum(x[1] for x in blocks)}, {out}", flush=True)
