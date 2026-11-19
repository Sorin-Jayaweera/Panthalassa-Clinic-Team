"""One-off check of the amp chain: SM200B power with the tone off (amp noise) and with 1160 MHz at -50 dBm. Leaves the tone off."""
import sys, time
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__file__))
import run_amp_chain_iq as A

h = A.sm_open_device()["device"]
try:
    A.sm_set_attenuator(h, A.SM_AUTO_ATTEN); A.sm_set_ref_level(h, 0.0)
    A.sm_set_IQ_base_sample_rate(h, A.SM_IQ_STREAM_SAMPLE_RATE_NATIVE); A.sm_set_IQ_sample_rate(h, 1)
    A.sm_set_IQ_bandwidth(h, A.SM_FALSE, 41.5e6); A.sm_set_IQ_data_type(h, A.SM_DATA_TYPE_32_FC)
    A.tone_off(); time.sleep(0.5)
    x, fs = A.iq(h, 1000e6 - A.OFS)
    print(f"tone off: {10*np.log10(np.mean(abs(x)**2)) + A.PAD_DB:.1f} dBm in 41.5 MHz at amp output (working chain: about -3)")
    att = max(A.att_for(1160.0, -50.0), A.ATT_MIN_DB)
    A.retry(lambda: A.tone_on(1160e6, att, A.SCALE), "tone 1160"); time.sleep(0.3)
    x, fs = A.iq(h, 1160e6 - A.OFS)
    t = A.line(x, fs, A.OFS) + A.PAD_DB
    print(f"1160 MHz -50 dBm: tone {t:.1f} dBm out (working chain: about +21)")
finally:
    A.tone_off(); A.sm_close_device(h)
sys.exit(0 if t > 10 else 1)
