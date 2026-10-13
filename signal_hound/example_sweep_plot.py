# -*- coding: utf-8 -*-

# This example configures the receiver for a basic sweep and
# plots the sweep. The x-axis frequency is derived from the start_freq
# and bin_size values returned after configuring the device.

from smdevice.sm_api import *

import matplotlib.pyplot as plt
import seaborn as sns; sns.set() # styling

def sweep():
    # Open device
    handle = sm_open_device()["device"]

    # Configure device
    sm_set_sweep_speed(handle, SM_SWEEP_SPEED_AUTO)
    sm_set_sweep_center_span(handle, 1e9, 100e6)
    sm_set_ref_level(handle, -30.0)
    sm_set_sweep_coupling(handle, 10e3, 10e3, 0.001)
    sm_set_sweep_detector(handle, SM_DETECTOR_MIN_MAX, SM_VIDEO_LOG)
    sm_set_sweep_scale(handle, SM_SCALE_LOG)
    sm_set_sweep_window(handle, SM_WINDOW_FLAT_TOP)
    sm_set_sweep_spur_reject(handle, SM_FALSE)

    # Initialize
    sm_configure(handle, SM_MODE_SWEEPING)
    query = sm_get_sweep_parameters(handle)
    actual_start_freq = query["actual_start_freq"]
    bin_size = query["bin_size"]
    sweep_size = query["sweep_size"]

    # Get sweep
    sweep = sm_get_sweep(handle)

    peak_max = -1000
    peak_min = -1000
    for i in range(sweep_size):
        if sweep["sweep_max"][i] > peak_max:
            peak_max = sweep["sweep_max"][i]
        if sweep["sweep_min"][i] > peak_min:
            peak_min = sweep["sweep_min"][i]

    if numpy.array_equal(sweep["sweep_max"], sweep["sweep_min"]):
        bp = 0

    # Device no longer needed, close it
    sm_close_device(handle)

    # Plot
    freqs = [actual_start_freq + i * bin_size for i in range(sweep_size)]
    plt.plot(freqs, sweep_max)
    plt.show()

if __name__ == "__main__":
    sweep()
