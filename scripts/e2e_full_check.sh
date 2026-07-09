#!/usr/bin/env bash
# Full-chain E2E check mirroring .github/workflows/ci.yml (day01-day39)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/nexus-agent-platform"
export NEXUS_LLM_MOCK=1
export PYTHONPATH=src
PY=python3
FAIL=0

run() {
  echo ">>> $*"
  if ! "$@"; then
    echo "FAILED: $*"
    FAIL=1
  fi
}

cd "$ROOT"
run $PY scripts/regenerate_courses_day24_30.py

cd "$ROOT/nexus-agent-platform"
run $PY src/day01/hello.py
run $PY src/day02/text_cleaner.py --input src/day02/sample_docs/raw_notice.txt --report
run $PY -c "
import importlib.util
from pathlib import Path
p = Path('src/day03/platform_cli.py')
spec = importlib.util.spec_from_file_location('pc', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.handle_batch_clean()
"
run $PY src/day04/list_demos.py
run $PY src/day05/api_response_parser.py --input src/day05/sample_data/chat_completion.json
run $PY src/day06/function_demos.py
run $PY -c "import importlib.util; from pathlib import Path; p=Path('src/day07/week1_quiz.py'); s=importlib.util.spec_from_file_location('q',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert len(m.QUESTIONS)==10"
run $PY src/day08/oop_demos.py
run $PY src/day09/inheritance_demos.py
run $PY src/day10/structure_audit.py
run $PY src/day11/doc_reader_demo.py
run $PY src/day12/llm_client_demo.py
run $PY src/day13/resilient_client_demo.py
run $PY src/day14/cli_assistant_demo.py
run $PY src/day15/token_counter_demo.py
run $PY src/day15/assistant_token_demo.py
run $PY src/day16/streaming_demo.py
run $PY src/day17/prompt_demos.py
run $PY src/day17/registry_demos.py
run $PY src/day17/rag_prompt_demo.py
run $PY src/day18/intent_demos.py
run $PY src/day18/router_demos.py
run $PY src/day18/routed_assistant_demo.py
run $PY src/day19/chunk_demos.py
run $PY src/day19/retriever_demos.py
run $PY src/day19/rag_context_demo.py
run $PY src/day19/routed_rag_demo.py
run $PY src/day20/embedding_demos.py
run $PY src/day20/vector_search_demos.py
run $PY src/day20/faq_matcher_demo.py
run $PY src/day20/routed_embedding_demo.py
run $PY src/day21/sprint3_quiz.py --scripted
run $PY src/day21/sprint3_review.py
run $PY src/day21/tool_demos.py
run $PY src/day21/integrated_assistant_demo.py
run $PY src/day22/frontend_audit.py
run $PY src/day22/html_demos.py
run $PY src/day22/mock_bridge_demo.py
run $PY src/day23/api_health_demo.py
run $PY src/day23/api_chat_demo.py

for d in $(seq 24 39); do
  dd=$(printf '%02d' "$d")
  for f in "$ROOT/nexus-agent-platform/src/day${dd}"/*_demo.py; do
    [ -f "$f" ] || continue
    run $PY "$f"
  done
  for f in "$ROOT/nexus-agent-platform/src/day${dd}"/*_api_demo.py; do
    [ -f "$f" ] || continue
    run $PY "$f"
  done
  for f in "$ROOT/nexus-agent-platform/src/day${dd}"/phase3_*_review.py; do
    [ -f "$f" ] || continue
    run $PY "$f"
  done
  if [ -d "$ROOT/nexus-agent-platform/tests/day${dd}" ]; then
    run $PY -m pytest "tests/day${dd}/" -q
  fi
done

# day24 extras
run $PY src/day24/sprint3_launch.py
run $PY src/day24/e2e_smoke.py
run $PY src/day24/sprint3_demo.py
run $PY src/day24/sprint3_review.py

run $PY -m pytest tests/ -q --tb=no

if [ "$FAIL" -ne 0 ]; then
  echo "E2E CHECK: FAILED"
  exit 1
fi
echo "E2E CHECK: ALL PASSED"
