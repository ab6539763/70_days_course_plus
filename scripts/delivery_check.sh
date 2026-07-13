#!/usr/bin/env bash
# One-command delivery gate: course audit + full E2E + tests
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "========== 1/3 Course audit day01-45 =========="
python3 scripts/audit_all_courses.py --ensure-code

echo "========== 2/3 E2E demos day01-45 =========="
bash scripts/e2e_full_check.sh

echo "========== 3/3 Sprint3 deployment smoke =========="
bash scripts/sprint3_demo.sh

echo ""
echo "✅ DELIVERY CHECK PASSED — day01-day45 ready"
