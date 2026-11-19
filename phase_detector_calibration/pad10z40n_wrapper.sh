#!/bin/bash
# 19 Nov morning: same wiring as pad10z (10 dB pad at each mixer port, cables B and D, 50 ohm IF load), zoomed readings,
# one more level, -40 dBm, 900-1200 MHz only (Sorin 08:20: focus there) coarse to fine at 1 MHz, repeated. Sorin will unplug the scope at some point:
# one launch only, so after the scope is gone the run retries for 15 min (covers Pluto USB drops), then stops with the tone off.
cd "$(dirname "$0")/../signal_hound"
echo "=== pads-10dB-zoom -40 dBm 900-1200 launch $(date +%H:%M:%S)"
PD_PLAN=fine PD_FINE_TAG=pad10z40n PD_LO=900 PD_HI=1200 PD_LEVELS=-40 PD_REPS=100 PD_ZOOM=1 PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py
echo "=== pads-10dB-zoom -40 dBm 900-1200 wrapper ended $(date +%H:%M:%S)"
