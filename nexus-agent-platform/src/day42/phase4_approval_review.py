"""Phase 4 人工审批日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/approval_config.py — require_rag_approval / mock_auto_approve",
    "agent/approval_checkpoint.py — 中断检查点存取",
    "agent/approval_workflow_graph.py — human_approval 节点",
    "POST /api/agent/approval-preview — 可中断",
    "POST /api/agent/approval-resume — 审批后恢复",
    "POST /api/chat approval_mode=true → approval + graph_trace",
]


def main() -> int:
    print("=" * 58)
    print("  Day 42 人工审批工作流回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
