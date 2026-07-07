"""
分块 A/B 实验演示

运行：PYTHONPATH=src python3 src/day27/ab_experiment_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_SAMPLE = _SRC / "day26" / "sample_docs" / "product_notice.md"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day27.constants import EVAL_QUERIES
from rag.chunk_config import PRESET_CONFIGS
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes


def main() -> int:
    print("=" * 56)
    print("  Day 27 分块 A/B 实验")
    print("=" * 56)

    doc = parse_bytes(_SAMPLE.read_bytes(), _SAMPLE.name)
    queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]
    results = run_ab_experiment(doc, list(PRESET_CONFIGS), queries)

    for r in results:
        cfg = r.config
        print(
            f"\n  [{cfg.name}] size={cfg.chunk_size} overlap={cfg.overlap} "
            f"strategy={cfg.strategy}"
        )
        print(f"    chunks={r.chunk_count} hit_rate={r.hit_rate:.0%} avg_score={r.avg_top_score:.3f}")

    best = pick_best_config(results)
    if best:
        print(f"\n  ✅ 推荐配置: {best.config.name} (hit_rate={best.hit_rate:.0%})")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
