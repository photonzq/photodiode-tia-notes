#!/usr/bin/env bash
# Run every case of g_eight_lead_3d.py, one process per case, one after another, recording into
# data/parasitic_cf/numerical/eight_lead_3d.json and logging each case's printed output.
# The SOIC-8 cases come first and the PDIP-8 cases last; a case whose mesh would exceed the
# script's MAX_ELEMENTS (1.25 million, about 5 GB) stops after meshing and the next one starts.
# The last two cases are checks of the mesh level of the PDIP cases and of the mesh policy.
# Usage (from this folder):  bash run_eight_lead.sh [python]      about 20 min; up to about 4.5 GB per solve
set -u
PY="${1:-python}"
REC="../../../data/parasitic_cf/numerical/eight_lead_3d.json"
LOG="../../../data/parasitic_cf/numerical/eight_lead_3d.log"
: > "$LOG"
for c in opa846_so8_double_sided_0402 opa846_so8_vias_under_0402 opa846_so8_under_body_0402 \
         opa637_so8_bottom_0805 ada4530_so8_1206 lmp7721_so8_1206 \
         lmc6001_dip8_bottom_1206 lmc6001_dip8_bottom_guard_1206 opa637_so8_bottom_0805_refine16 \
         opa846_sot23_double_sided_0402_policy; do
    echo "=== $c ($(date +%H:%M:%S))" >> "$LOG"
    "$PY" g_eight_lead_3d.py run "$c" --record "$REC" >> "$LOG" 2>&1
done
echo "=== done ($(date +%H:%M:%S))" >> "$LOG"
