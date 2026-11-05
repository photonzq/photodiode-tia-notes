#!/usr/bin/env bash
# Recompute every recorded result of Section G.14 from scratch, one process per case, in order:
#   1. the checks of the package (pcbcap.checks)            -> data/parasitic_cf/numerical/checks.json
#   2. the two-dimensional closed-form comparisons           -> closed_forms_2d.json
#   3. the three-dimensional resistor cases (run_all_3d.sh)  -> resistor_3d.json
#   4. the OPA846 cases (run_opa846.sh)                      -> opa846_3d.json
#   5. the 0402 coupling split by region (field_regions.py)  -> field_regions.json
# Each record is deleted first, so that it holds only results of the current code.  Each step logs
# its printed output next to its record (checks.log, closed_forms_2d.log, resistor_3d.log,
# opa846_3d.log, field_regions.log).  If a backup folder is given, the previous records and logs are
# copied there first.
#
# Usage (from this folder):  bash rerun_all.sh [python] [backup_folder]
# Run time: about 1 h 45 min in total on a workstation that was also in other use (steps 1 and 2 take
# about 3 minutes, step 3 about 40, step 4 about 60, step 5 about 1).
set -u
PY="${1:-python}"
BACKUP="${2:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="$(cd "$HERE/../../../data/parasitic_cf/numerical" && pwd)"
PKG="$(cd "$HERE/../../../../pcbcap" && pwd)"

if [ -n "$BACKUP" ]; then
    mkdir -p "$BACKUP"
    cp "$DATA"/*.json "$DATA"/*.log "$BACKUP"/ 2>/dev/null
fi

# 1. checks
LOG="$DATA/checks.log"
rm -f "$DATA/checks.json"
: > "$LOG"
for c in strips_free_space strips_on_interface mirror_vs_full layered_plates_2d layered_plates_3d \
         floating_slab film_linear_block extrusion_3d_vs_2d symmetry_declaration resistor_section_shares; do
    echo "=== $c ($(date +%H:%M:%S))" >> "$LOG"
    (cd "$PKG" && "$PY" -m pcbcap.checks run "$c" --record "$DATA/checks.json") >> "$LOG" 2>&1
done
echo "=== done ($(date +%H:%M:%S))" >> "$LOG"

# 2. closed forms in two dimensions
LOG="$DATA/closed_forms_2d.log"
rm -f "$DATA/closed_forms_2d.json"
: > "$LOG"
for c in $("$PY" "$HERE/g_closed_forms_2d.py" list | awk '{print $1}'); do
    echo "=== $c ($(date +%H:%M:%S))" >> "$LOG"
    "$PY" "$HERE/g_closed_forms_2d.py" run "$c" --record "$DATA/closed_forms_2d.json" >> "$LOG" 2>&1
done
echo "=== done ($(date +%H:%M:%S))" >> "$LOG"

# 3. and 4. three-dimensional cases (the two batch scripts work from this folder)
cd "$HERE"
rm -f "$DATA/resistor_3d.json"
bash run_all_3d.sh "$PY"
rm -f "$DATA/opa846_3d.json"
bash run_opa846.sh "$PY"

# 5. where the coupling of the 0402 sits (the text beside Figure 45)
rm -f "$DATA/field_regions.json"
"$PY" "$HERE/field_regions.py" --record "$DATA/field_regions.json" > "$DATA/field_regions.log" 2>&1
echo "all done $(date +%H:%M:%S)"
