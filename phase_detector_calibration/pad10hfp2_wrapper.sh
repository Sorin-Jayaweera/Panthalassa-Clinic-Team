#!/bin/bash
# 19 Nov evening: pad10hf wiring (10 dB pads, H on LO, B + F on RF) with 2 x ZX60-P103LN+ (5.00 V) ahead of the 4 x ZX60-P162LN+ (4.04 V), see pd_runs.py row pad10hfp2.
# Sorin 19 Nov: check for oscillation first, then a night of data. Eight levels -36 to -89 dBm (the extra ~31 dB moves the railed edge down), 600-1600 MHz, coarse to fine, repeated.
# -89, not -90: below about 1 GHz -90 dBm needs more than the 89.75 dB attenuator maximum.
cd "$(dirname "$0")"; rm -f STOP_PD_RUN; cd ../signal_hound
echo "=== pads-10dB-zoom H and B+F, 2 x P103 ahead, eight levels launch $(date +%H:%M:%S)"
PD_PLAN=fine PD_FINE_TAG=pad10hfp2 PD_LO=600 PD_HI=1600 PD_LEVELS=-36,-40,-45,-54,-63,-72,-81,-89 PD_REPS=90 PD_ZOOM=1 PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py
echo "=== pads-10dB-zoom H and B+F, 2 x P103 ahead, eight levels wrapper ended $(date +%H:%M:%S)"
