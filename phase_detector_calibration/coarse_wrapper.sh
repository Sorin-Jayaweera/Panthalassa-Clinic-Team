#!/bin/bash
# 15 Nov: coarse repeat sweeps, a fresh python launch per rep. Skips a rep's remaining points only if the Pluto's libiio fails 3 launches in a row.
cd "$(dirname "$0")/../signal_hound"
PY=python
for n in $(seq 1 12); do
  [ -f ../phase_detector_calibration/STOP_PD_RUN ] && break
  for t in 1 2 3; do
    echo "=== coarse rep $n launch $t $(date +%H:%M:%S)"
    COARSE_REP=$n $PY -u ../phase_detector_calibration/run_pd_overnight.py && break
    sleep 20
  done
done
echo "=== coarse wrapper ended $(date +%H:%M:%S)"
