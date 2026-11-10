#!/bin/bash
# Cut and analyse every 9 Nov raw recording, 3 at a time. Log per recording in data/proc_<name>.log
cd "$(dirname "$0")"
run() { d=$1; [ -f data/raw_$d.npz ] || python raw_to_snips.py C:/racon_raw/$d; python racon_analyze.py data/raw_$d.npz; }
export -f run
ls C:/racon_raw | grep 2026 | while read d; do [ -f C:/racon_raw/$d/iq.c64 ] && echo $d; done | xargs -P 3 -I{} bash -c 'run {} > data/proc_{}.log 2>&1; echo "finished {} $(date +%T)"'
echo "ALL PROCESSED $(date +%T)"
