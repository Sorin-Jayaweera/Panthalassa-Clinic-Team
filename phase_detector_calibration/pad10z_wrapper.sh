#!/bin/bash
# 18 Nov night from 21:45: two-round zoomed scope readings (scope_zoom.py, finest V/div per point). 10 dB pad at each mixer port (cables B and D), IF short cable + 50 ohm load. 600-1600 MHz at 1 MHz, 5 Pluto levels,
# coarse to fine, repeated; hard stop 07:55 19 Nov (Sorin: done by 8 a.m.). Relaunches (resuming) if the Pluto or scope drops.
cd "$(dirname "$0")/../signal_hound"
for t in $(seq 1 60); do
  [ -f ../phase_detector_calibration/STOP_PD_RUN ] && break
  [ "$(date +%Y%m%d%H%M)" -ge 202611190755 ] && break
  echo "=== pads-10dB-zoom launch $t $(date +%H:%M:%S)"
  PD_PLAN=fine PD_FINE_TAG=pad10z PD_ZOOM=1 PD_DEADLINE=2026-11-19T07:55 PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py && break
  sleep 30
done
echo "=== pads-10dB-zoom wrapper ended $(date +%H:%M:%S)"
