"""
pluto_sweep_cli.py - no-GUI Pluto frequency stepper + measurement logger for the
JACON delay-line discriminator bench test.

    %USERPROFILE%\\radioconda\\python.exe pluto_sweep_cli.py --manual
    %USERPROFILE%\\radioconda\\python.exe pluto_sweep_cli.py --start 0.5e9 --stop 3e9 --step 25e6 --manual

--manual : at every frequency it waits for you to type the mixer output voltage
           you read on the DMM / scope (Enter = skip, q = quit). The CSV it writes
           (measurements/meas_*.csv) goes straight into compare_sim_vs_measured.py.
without --manual it just dwells --dwell seconds per step and logs timestamps,
so you can line up a scope/DAQ recording afterwards.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import time
from pathlib import Path

import numpy as np
from gnuradio import analog, gr, iio

HERE = Path(__file__).resolve().parent


class PlutoTone(gr.top_block):
    def __init__(self, uri: str, samp_rate: float, f_rf: float, atten: float, offset: float, amp: float):
        gr.top_block.__init__(self, "JACON Pluto tone")
        self.offset = offset
        self.src = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, offset, amp, 0)
        self.sink = iio.fmcomms2_sink_fc32(uri if uri else iio.get_pluto_uri(), [True, True], 32768, False)
        self.sink.set_len_tag_key("")
        self.sink.set_bandwidth(20000000)
        self.sink.set_frequency(int(f_rf - offset))
        self.sink.set_samplerate(int(samp_rate))
        self.sink.set_attenuation(0, atten)
        self.sink.set_filter_params("Auto", "", 0, 0)
        self.connect(self.src, self.sink)

    def tune(self, f_rf: float):
        self.sink.set_frequency(int(f_rf - self.offset))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=float, default=1.0e9)
    ap.add_argument("--stop", type=float, default=1.2e9)
    ap.add_argument("--step", type=float, default=5e6)
    ap.add_argument("--atten", type=float, default=10.0, help="Pluto TX attenuation, dB (0 = max power)")
    ap.add_argument("--dwell", type=float, default=2.0, help="seconds per step when not --manual")
    ap.add_argument("--settle", type=float, default=0.3, help="seconds after retune before logging")
    ap.add_argument("--offset", type=float, default=200e3, help="baseband tone offset, Hz")
    ap.add_argument("--amp", type=float, default=0.9)
    ap.add_argument("--rate", type=float, default=2.5e6)
    ap.add_argument("--uri", default="", help="e.g. ip:192.168.2.1 (default: first USB Pluto)")
    ap.add_argument("--manual", action="store_true", help="prompt for the measured voltage at each step")
    ap.add_argument("--note", default="", help="free text stored in the CSV header (cable lengths, amp, ...)")
    a = ap.parse_args()

    freqs = np.arange(a.start, a.stop + a.step / 2, a.step)
    outdir = HERE / "measurements"
    outdir.mkdir(exist_ok=True)
    fname = outdir / ("meas_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")

    tb = PlutoTone(a.uri, a.rate, freqs[0], a.atten, a.offset, a.amp)
    tb.start()
    print(f"Pluto transmitting. {len(freqs)} steps {a.start/1e6:.1f}-{a.stop/1e6:.1f} MHz, atten {a.atten} dB")
    print(f"log -> {fname}")
    try:
        with open(fname, "w", newline="") as fh:
            fh.write(f"# JACON delay-line discriminator bench sweep {datetime.datetime.now().isoformat()}\n")
            fh.write(f"# atten_db={a.atten} tone_offset_hz={a.offset} amp={a.amp} note={a.note}\n")
            w = csv.writer(fh)
            w.writerow(["freq_hz", "v_out_V", "unix_time_s", "atten_db"])
            for i, f in enumerate(freqs):
                tb.tune(f)
                time.sleep(a.settle)
                if a.manual:
                    s = input(f"[{i+1}/{len(freqs)}] {f/1e6:9.3f} MHz  -> mixer Vout in volts (Enter=skip, q=quit): ").strip()
                    if s.lower() == "q":
                        break
                    v = s if s else ""
                else:
                    print(f"[{i+1}/{len(freqs)}] {f/1e6:9.3f} MHz", flush=True)
                    time.sleep(max(0.0, a.dwell - a.settle))
                    v = ""
                w.writerow([f"{f:.0f}", v, f"{time.time():.3f}", a.atten])
                fh.flush()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        tb.stop()
        tb.wait()
    print("saved", fname)


if __name__ == "__main__":
    main()
