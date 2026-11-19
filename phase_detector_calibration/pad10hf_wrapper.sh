#!/bin/bash
# 19 Nov afternoon: pads as pad10z with cable H (7 cm) on the LO arm and B + barrel + F on the RF arm, about 25 cm longer (see pd_runs.py row pad10hf) (10 dB pad at each mixer port, 50 ohm IF load), zoomed readings,
# 600-1600 MHz (Sorin 12:45: whole range), six levels -36 -40 -45 -54 -63 -72 dBm cycled for repeats (Sorin 08:25) coarse to fine at 1 MHz, repeated. Sorin will unplug the scope at some point:
# one launch only, so after the scope is gone the run retries for 15 min (covers Pluto USB drops), then stops with the tone off.
cd "$(dirname "$0")"; rm -f STOP_PD_RUN; cd ../signal_hound
echo "=== pads-10dB-zoom six levels 600-1600 H and B+F launch $(date +%H:%M:%S)"
PD_PLAN=fine PD_FINE_TAG=pad10hf PD_LO=600 PD_HI=1600 PD_LEVELS=-36,-40,-45,-54,-63,-72 PD_REPS=100 PD_ZOOM=1 PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py
echo "=== pads-10dB-zoom six levels 600-1600 H and B+F wrapper ended $(date +%H:%M:%S)"
