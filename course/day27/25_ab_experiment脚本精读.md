# ab_experiment 脚本精读

## ab_experiment_demo.py

CLI 入口，不启动 HTTP 服务。

```python
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
```


### 执行流程

1. 读取 `product_notice.md`  
2. `EvalQuery.from_dict` 加载 EVAL_QUERIES  
3. `run_ab_experiment(doc, PRESET_CONFIGS, queries)`  
4. 打印每套 hit_rate、chunk_count  
5. `pick_best_config` 输出推荐  

### 预期输出解读

```
[compact] size=120 ... hit_rate=75%
[wide]    size=400 ... hit_rate=100%
✅ 推荐配置: wide
```

## chunk_tune_api_demo.py

```python
"""
分块调参 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day27/chunk_tune_api_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


def main() -> int:
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())
    client = TestClient(create_app())

    print("=== Day 27 Chunk Tune API Demo ===\n")
    cfg = client.get("/api/knowledge/chunk-config").json()
    print(f"  GET chunk-config: {cfg}")

    updated = client.put(
        "/api/knowledge/chunk-config",
        json={"chunk_size": 300, "overlap": 50, "strategy": "auto", "name": "tuned"},
    )
    print(f"\n  PUT chunk-config: {updated.json()}")

    ev = client.post("/api/knowledge/evaluate", json={"use_presets": True})
    print(f"\n  POST evaluate best: {ev.json().get('best_config')}")
    print(f"  eval queries: {ev.json().get('eval_query_count')}")

    health = client.get("/api/health").json()
    print(f"\n  version: {health.get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


### 与 CLI 差异

- 走 HTTP 层，验证路由与 schema  
- 需 `NEXUS_LLM_MOCK=1`  
- 演示 PUT 后 GET 一致性  

## 排错

| 症状 | 检查 |
|------|------|
| ModuleNotFoundError: day27 | PYTHONPATH=src |
| 样例找不到 | day26/sample_docs 是否存在 |
| evaluate 500 | 查看服务端日志 detail |
