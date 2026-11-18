#!/bin/bash
# 18 Nov: amplifier chain alone into the SM200B (29 dB pads). Waits for the SM200B on USB (Signal Hound VID 2817),
# then runs, relaunching and resuming after any USB drop, until every point is done or STOP_AMP_RUN exists.
cd "$(dirname "$0")/../signal_hound"
D=../phase_detector_calibration
sm() { powershell -NoProfile -Command 'if (Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like "USB\VID_2817*" -or $_.FriendlyName -match "Signal Hound|SM200" }) { exit 0 } else { exit 1 }'; }
until sm; do [ -f $D/STOP_AMP_RUN ] && exit 0; sleep 20; done
echo "=== SM200B on USB $(date +%H:%M:%S)"
for t in $(seq 1 60); do
  [ -f $D/STOP_AMP_RUN ] || [ -f $D/AMP_RUN_DONE ] && break
  echo "=== amp chain launch $t $(date +%H:%M:%S)"
  python -u $D/run_amp_chain_iq.py
  sleep 20
done
echo "=== amp chain wrapper ended $(date +%H:%M:%S)"
