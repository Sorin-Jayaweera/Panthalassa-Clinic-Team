#!/bin/bash
# 18 Nov: the chain lost all signal at 14:40. Probe every 2 min (tone off, then 1160 MHz at -50 dBm); once the output is back above +10 dBm, resume the ramp.
cd "$(dirname "$0")/../signal_hound"
D=../phase_detector_calibration
until python -u $D/amp_probe.py; do [ -f $D/STOP_AMP_RUN ] && exit 0; echo "-- no signal yet $(date +%H:%M:%S)"; sleep 120; done
echo "=== signal back $(date +%H:%M:%S), resuming ramp"
bash $D/amp_ramp_wrapper.sh
