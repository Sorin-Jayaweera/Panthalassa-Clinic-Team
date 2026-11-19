#!/bin/bash
# 18 Nov evening: equal arms, cable B and D 15 cm each (zero delay difference), IF straight into a 50 ohm load at the scope; same high-density plan. Relaunches (resuming where it stopped) if the Pluto or scope drops.
cd "$(dirname "$0")/../signal_hound"
for t in $(seq 1 30); do
  [ -f ../phase_detector_calibration/STOP_PD_RUN ] && break
  echo "=== equal-arms-50ohm launch $t $(date +%H:%M:%S)"
  HD_NIGHT=1 HD_TAG=eq PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py && break
  sleep 30
done
echo "=== equal-arms-50ohm wrapper ended $(date +%H:%M:%S)"
