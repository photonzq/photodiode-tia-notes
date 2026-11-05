#!/usr/bin/env bash
# Run every case of g_opa846_3d.py, one process per case, one after another, recording into
# data/parasitic_cf/numerical/opa846_3d.json and logging each case's printed output.
# Usage (from this folder):  bash run_opa846.sh [python]      about an hour; 3.5-4.5 GB per solve
set -u
PY="${1:-python}"
REC="../../../data/parasitic_cf/numerical/opa846_3d.json"
LOG="../../../data/parasitic_cf/numerical/opa846_3d.log"
: > "$LOG"
for c in under_body_0402 double_sided_0402 around_0402 under_body_0603 double_sided_0603 around_0603 \
         under_body_0402_fine under_body_0402_enclosure16 \
         under_body_0402_parts double_sided_0402_parts around_0402_parts; do
    echo "=== $c ($(date +%H:%M:%S))" >> "$LOG"
    "$PY" g_opa846_3d.py run "$c" --record "$REC" >> "$LOG" 2>&1
done
echo "=== done ($(date +%H:%M:%S))" >> "$LOG"
