#!/usr/bin/env bash
# Reads the normalized coverage TSV produced by parse-coverage.py and exits 1
# if any file is below the threshold on any dimension (line, branch, function).
#
# Usage:
#   python scripts/parse-coverage.py < cov.txt | bash scripts/check-threshold.sh [threshold]
#   bash scripts/check-threshold.sh 90 < normalized.tsv
#
# threshold defaults to 90.

set -uo pipefail

THRESHOLD="${1:-90}"
FAILED=0
PASS_COUNT=0

while IFS=$'\t' read -r file line_pct branch_pct func_pct; do
  [ "$file" = "FILE" ] && continue

  below=$(awk -v l="$line_pct" -v b="$branch_pct" -v f="$func_pct" -v thr="$THRESHOLD" \
    'BEGIN { print (l+0 < thr+0 || b+0 < thr+0 || f+0 < thr+0) ? "1" : "0" }')

  if [ "$below" = "1" ]; then
    echo "FAIL  $file"
    echo "      line=${line_pct}%  branch=${branch_pct}%  func=${func_pct}%  (threshold=${THRESHOLD}%)"
    FAILED=1
  else
    PASS_COUNT=$((PASS_COUNT + 1))
  fi
done

if [ "$PASS_COUNT" -eq 0 ] && [ "$FAILED" -eq 0 ]; then
  echo "ERROR: No coverage data received — check that parse-coverage.py produced output." >&2
  exit 2
fi

if [ "$FAILED" -eq 0 ]; then
  echo "PASS  All ${PASS_COUNT} file(s) meet the ${THRESHOLD}% coverage threshold."
fi

exit $FAILED
