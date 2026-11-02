"""Check the SM200B can be opened and read: one 10 ms I/Q block centred 1.05 GHz, nothing saved. Spike must be closed."""
import warnings

import numpy as np

warnings.filterwarnings("ignore", category=SyntaxWarning)
from smdevice.sm_api import *  # noqa: E402,F403

h = sm_open_device()["device"]
try:
    sm_set_attenuator(h, SM_AUTO_ATTEN)
    sm_set_ref_level(h, -10.0)
    sm_set_IQ_center_freq(h, 1.05e9)
    sm_set_IQ_base_sample_rate(h, SM_IQ_STREAM_SAMPLE_RATE_NATIVE)
    sm_set_IQ_sample_rate(h, 1)
    sm_set_IQ_bandwidth(h, SM_FALSE, 41.5e6)
    sm_set_IQ_data_type(h, SM_DATA_TYPE_32_FC)
    sm_configure(h, SM_MODE_IQ_STREAMING)
    fs = sm_get_IQ_parameters(h)["sample_rate"]
    iq = sm_get_IQ(h, 500_000, 0, SM_TRUE)["iq_buf"]
    sm_abort(h)
finally:
    sm_close_device(h)
p = iq.real ** 2 + iq.imag ** 2
print(f"read OK: {len(iq)} samples at {fs/1e6:.1f} MS/s, mean {10*np.log10(p.mean()):.1f} dBm, peak {10*np.log10(p.max()):.1f} dBm at the SM200B, centre 1.05 GHz")
