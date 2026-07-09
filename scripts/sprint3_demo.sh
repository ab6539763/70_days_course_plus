#!/usr/bin/env bash
# Sprint 3 演示冒烟脚本 — Day 24
set -euo pipefail
cd "$(dirname "$0")/../nexus-agent-platform"
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1

echo "=== Sprint 3 Demo Script ==="
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
python3 src/day24/e2e_smoke.py
python3 src/day24/sprint3_demo.py
echo ""
echo "启动服务: PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py --serve"
