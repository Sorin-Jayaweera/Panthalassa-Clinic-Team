#!/bin/bash
# 18 Nov: after the frequency sweep (AMP_RUN_DONE), amplifier chain output against Pluto level, -90 to -36 dBm, repeated.
# Relaunches and resumes after USB drops, until all reps are done or STOP_AMP_RUN exists.
cd "$(dirname "$0")/../signal_hound"
D=../phase_detector_calibration
until [ -f $D/AMP_RUN_DONE ]; do [ -f $D/STOP_AMP_RUN ] && exit 0; sleep 10; done
until ! powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -like '*run_amp_chain_iq*' -and \$_.CommandLine -notlike '*Get-Cim*' }) { exit 0 } else { exit 1 }"; do sleep 5; done
for t in $(seq 1 100); do
  [ -f $D/STOP_AMP_RUN ] || [ -f $D/AMP_RAMP_DONE ] && break
  echo "=== amp ramp launch $t $(date +%H:%M:%S)"
  AMP_MODE=ramp python -u $D/run_amp_chain_iq.py
  sleep 20
done
echo "=== amp ramp wrapper ended $(date +%H:%M:%S)"
