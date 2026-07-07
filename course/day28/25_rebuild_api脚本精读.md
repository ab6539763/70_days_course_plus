# rebuild_api 脚本精读

## rebuild_demo.py

```python
"""
知识库全量重建演示

运行：PYTHONPATH=src python3 src/day28/rebuild_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.chunk_config import ChunkConfig
from rag.knowledge_rebuild import collect_source_files, rebuild_store
from rag.knowledge_store import KnowledgeStore


def main() -> int:
    print("=" * 56)
    print("  Day 28 知识库全量重建演示")
    print("=" * 56)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_chunk_config(ChunkConfig(name="wide", chunk_size=400, overlap=60))
    print(f"\n  重建前: {store.document_count} 篇 / {store.chunk_count} 块")
    print(f"  配置: size={store.chunk_config.chunk_size} overlap={store.chunk_config.overlap}")

    sources = collect_source_files()
    print(f"  源文件: {[p.name for p in sources]}")

    report = rebuild_store(store)
    print(f"\n  重建后: {report.documents_after} 篇 / {report.chunks_after} 块")
    print(f"  处理源: {report.sources_processed} 个")
    print(f"  时间: {report.rebuilt_at}")
    print("\n  ✅ 重建演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


**流程**：

1. bootstrap store  
2. 可选 `set_chunk_config(wide)` 使前后块数差异明显  
3. `collect_source_files()` 打印源列表  
4. `rebuild_store(store)`  
5. 打印 RebuildReport 关键字段  

## rebuild_api_demo.py

```python
"""
重建 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day28/rebuild_api_demo.py
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

    print("=== Day 28 Rebuild API Demo ===\n")
    resp = client.post(
        "/api/knowledge/rebuild",
        json={"include_sample_docs": True, "apply_best_config": False},
    )
    print(f"  POST rebuild: {resp.status_code}")
    data = resp.json()
    print(f"    chunks {data.get('chunks_before')} → {data.get('chunks_after')}")
    print(f"    sources: {data.get('source_files')}")

    status = client.get("/api/knowledge/status").json()
    print(f"\n  last_rebuilt_at: {status.get('last_rebuilt_at')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


**验证点**：

- HTTP 200  
- chunks_before → chunks_after  
- status.last_rebuilt_at  

## 与单元测试差异

| 层级 | 文件 |
|------|------|
| 纯函数 | test_knowledge_rebuild.py |
| HTTP | test_rebuild_api.py |
| 手动演示 | rebuild_api_demo.py |

## 常见错误

- 未设 PYTHONPATH  
- store 路径只读  
- 忘记 NEXUS_LLM_MOCK 导致 LLM 调用（部分环境）
