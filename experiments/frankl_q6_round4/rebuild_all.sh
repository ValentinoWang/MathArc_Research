#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
"$PYTHON_BIN" "$ROOT/audit_archive.py" --require-rebuild-sources
BIN="$ROOT/bin"; RES="$ROOT/results"; LOG="$ROOT/logs"
mkdir -p "$BIN" "$RES" "$LOG"
compile(){ g++ -O3 -std=c++20 "$ROOT/verifier/$1" -o "$BIN/$2"; }
compile verify_positive_core_hmin.cpp verify_positive_core_hmin
compile verify_q6_exact4.cpp verify_q6_exact4
compile verify_q6_exact5_card.cpp verify_q6_exact5
compile verify_q6_exact6_card.cpp verify_q6_exact6
compile verify_q6_exact7_pair.cpp verify_q6_exact7_nonfull
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k-le-3.time" "$PYTHON_BIN" "$ROOT/verifier/verify_q6_at_most_three_small.py" --output "$RES/q6-at-most-three-small.json" > "$LOG/k-le-3.log"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/hmin.time" "$BIN/verify_positive_core_hmin" > "$RES/q6-positive-core-hmin.json"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k4.time" "$BIN/verify_q6_exact4" > "$RES/q6-exact4.json"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k5.time" "$BIN/verify_q6_exact5" > "$RES/q6-exact5.json"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k6.time" "$BIN/verify_q6_exact6" > "$RES/q6-exact6.json"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k7-nonfull.time" "$BIN/verify_q6_exact7_nonfull" > "$RES/q6-exact7-nonfull.json"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/k7-full.time" "$PYTHON_BIN" "$ROOT/verifier/verify_q6_k7_full_cases.py" --output "$RES/q6-exact7-full.json" > "$LOG/k7-full.log"
/usr/bin/time -f '%e sec %M KB' -o "$LOG/kge8.time" "$PYTHON_BIN" "$ROOT/verifier/verify_q6_many_small.py" --hmin "$RES/q6-positive-core-hmin.json" --output "$RES/q6-many-small.json" > "$LOG/kge8.log"
"$PYTHON_BIN" "$ROOT/verifier/aggregate_q6.py" \
  --root "$ROOT" \
  --output "$RES/q6-round4-rebuilt.json" \
  > "$LOG/aggregate-rebuilt.log"
"$PYTHON_BIN" "$ROOT/audit_archive.py" --require-full-replay-inputs
"$PYTHON_BIN" - "$RES/q6-round4-rebuilt.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
assert payload["all_checks_passed"] is True
assert payload["conclusion"]["full_frankl_conjecture"] == "INCONCLUSIVE"
print("ROUND4_REBUILD_OUTPUT_VALIDATED / EXTERNAL_REVIEW_NOT_IMPLIED")
PY
