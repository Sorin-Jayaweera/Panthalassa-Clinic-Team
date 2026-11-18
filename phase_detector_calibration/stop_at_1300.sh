#!/bin/bash
# 18 Nov: Sorin needs the bench by 13:00. Hard stop at 12:59:00, then turn the Pluto tone off.
cd "$(dirname "$0")"
while [ "$(date +%H%M)" -lt 1259 ]; do sleep 5; done
touch STOP_PD_RUN
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*run_pd_overnight*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
sleep 3
cd ../signal_hound && python -c "import sys; sys.path.insert(0,'../phase_detector_calibration'); sys.path.insert(0,'../sdr'); from pluto_cw import tone_off; tone_off(); print('tone off')"
echo "$(date +%H:%M:%S) hard stop for 13:00 deadline, tone off" >> ../phase_detector_calibration/pd_overnight_13nov.log
