#!/bin/bash
# 19 Nov (Sorin 08:25): after 3 full 900-1200 MHz sweeps at -40 dBm, stop that run between points and start the six-level cycle.
cd "$(dirname "$0")"
until grep -q "tone off after repeat 3" pd_pad10z40_19nov.log; do sleep 10; done
touch STOP_PD_RUN
until grep -q "900-1200 wrapper ended" pd_pad10z40_19nov.log; do sleep 3; done
rm -f STOP_PD_RUN
echo "=== $(date +%H:%M:%S) -40 dBm block done (3 sweeps); starting six levels" >> pd_pad10z40_19nov.log
bash pad10zn_wrapper.sh >> pd_pad10z40_19nov.log 2>&1
