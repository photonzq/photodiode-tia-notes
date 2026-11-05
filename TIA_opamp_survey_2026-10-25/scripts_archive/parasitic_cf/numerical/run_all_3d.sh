#!/usr/bin/env bash
# Run every three-dimensional case of g_resistor_3d.py, one process per case, one after another,
# recording into data/parasitic_cf/numerical/resistor_3d.json and logging each case's printed output.
# Usage (from this folder):  bash run_all_3d.sh [python]          about 40 minutes in total
set -u
PY="${1:-python}"
REC="../../../data/parasitic_cf/numerical/resistor_3d.json"
LOG="../../../data/parasitic_cf/numerical/resistor_3d.log"
: > "$LOG"
for c in size_0201 size_0402 size_0603 size_0805 eps_corners_0402 film_down_0402 details_0402 \
         substrates_0402 substrates_0805 substrates_enclosure_0402 opa855_layout opa855_plane_edge; do
    echo "=== $c ($(date +%H:%M:%S))" >> "$LOG"
    "$PY" g_resistor_3d.py run "$c" --record "$REC" >> "$LOG" 2>&1
done
echo "=== done ($(date +%H:%M:%S))" >> "$LOG"
