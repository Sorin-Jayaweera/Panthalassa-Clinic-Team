#!/bin/bash
# 19 Nov night: if pad10hfp2_wrapper.sh ends early (Pluto off USB longer than the run's own retries), wait until the Pluto answers again and relaunch;
# the run resumes from the counts already in pd_dither_14nov.csv. Stops when the run finishes, when STOP_PD_RUN exists, or after 6 relaunches (e.g. scope unplugged).
cd "$(dirname "$0")"; LOG=pd_pad10hfp2_19nov.log
until grep -q "wrapper ended" $LOG; do sleep 30; done
for n in 1 2 3 4 5 6; do
  { [ -f STOP_PD_RUN ] || tail -5 $LOG | grep -q "ALL STAGES FINISHED"; } && exit 0
  echo "=== relaunch $n: run ended early $(date +%H:%M:%S), waiting for the Pluto" >> $LOG
  until ping -n 1 -w 1000 192.168.2.1 | grep -q "TTL="; do sleep 30; done
  sleep 20; bash pad10hfp2_wrapper.sh >> $LOG 2>&1
done
