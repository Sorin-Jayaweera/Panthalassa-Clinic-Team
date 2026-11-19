#!/bin/bash
# 18 Nov evening: cable E moved to the LO arm (port 2): LO = D + E, RF = B; IF short cable + 50 ohm load; same high-density plan. Relaunches (resuming where it stopped) if the Pluto or scope drops.
cd "$(dirname "$0")/../signal_hound"
for t in $(seq 1 30); do
  [ -f ../phase_detector_calibration/STOP_PD_RUN ] && break
  echo "=== E-on-LO launch $t $(date +%H:%M:%S)"
  HD_NIGHT=1 HD_TAG=elo PD_DITHER=1 PD_VDIV=0.1 PD_OFST=-0.04 PD_CLIP_MV=380 python -u ../phase_detector_calibration/run_pd_overnight.py && break
  sleep 30
done
echo "=== E-on-LO wrapper ended $(date +%H:%M:%S)"
