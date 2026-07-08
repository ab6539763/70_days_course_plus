"""
Phase 3 启动回顾 — Day 25 知识库

运行：python3 src/day25/phase3_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MILESTONES = [
    ("Day 24", "网页 Chat 完整整合"),
    ("Day 25", "知识库 ingestion + 持久化 ← 今日"),
    ("Day 26+", "文档解析增强、分块策略调优"),
    ("Day 29+", "Chroma 向量库（预告）"),
]

DELIVERABLES = [
    "rag/knowledge_store.py — JSON 持久化知识库",
    "rag/ingestion.py — 上传与批量入库",
    "POST /api/knowledge/upload — 文档上传 API",
    "GET /api/knowledge/status — 库状态查询",
    "factory 注入共享 KnowledgeStore",
]


def main() -> int:
    print("=" * 58)
    print("  Phase 3 启动回顾（Day 25 知识库）")
    print("=" * 58)
    print("\n  里程碑:")
    for phase, desc in MILESTONES:
        print(f"    ✅ {phase}: {desc}")
    print("\n  今日交付:")
    for item in DELIVERABLES:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
