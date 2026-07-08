# Day 29 实操 Lab 手册

**学时**：120 分钟 | **环境**：nexus-agent-platform | **需求**：ZL-NA-REQ-029

## 前置条件

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Step 1：Bootstrap 与 status 基线（15 min）

```bash
python3 src/day29/chroma_demo.py
```

**记录**：`vector_backend`, `chunk_count`, `chroma_count`。  
**期望**：三者满足 backend=chroma 且 count 相等。

---

## Step 2：检查 Chroma 落盘目录（10 min）

```bash
ls -la data/knowledge/chroma/
```

**期望**：存在 `chroma.sqlite3` 等文件。  
**思考**：这些文件与 `store.json` 的关系？

---

## Step 3：rebuild 实验（20 min）

```bash
python3 src/day29/chroma_api_demo.py
```

或手动：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' -d '{"include_sample_docs": true}' | jq .
```

**记录**：`chunks_before`, `chunks_after`, rebuild 后 `chroma_count`。

---

## Step 4：删除 chroma 目录冷启动（25 min）

```bash
rm -rf data/knowledge/chroma
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.load_or_bootstrap()
st = s.status_dict()
print('chroma_count', st['chroma_count'], 'chunk_count', st['chunk_count'])
"
```

**期望**：`chroma_count` 自动恢复等于 `chunk_count`。  
**原理**：`_sync_chroma_from_json`。

---

## Step 5：测试套件（30 min）

```bash
python3 -m pytest tests/day29/test_chroma_index.py -v
python3 -m pytest tests/day29/test_chroma_api.py -v
```

**重点阅读**：`test_chroma_matches_in_memory_retriever_top1` 源码。

```python
def test_chroma_matches_in_memory_retriever_top1(tmp_path):
    store = _store(tmp_path)
    query = "年化收益率是多少"
    mem = EmbeddingRetriever(store.chunks)
    chroma = store._chroma_index()
    client = EmbeddingClient()
    client.model.load_state(store.embedding_state)
    chroma_r = ChromaEmbeddingRetriever(store.chunks, chroma, client=client)

    mem_top = mem.search(query, top_k=1)
    chroma_top = chroma_r.search(query, top_k=1)
    assert mem_top and chroma_top
    assert mem_top[0].chunk.chunk_id == chroma_top[0].chunk.chunk_id


def test_empty_store_clears_chroma(tmp_path):
    path = tmp_path / "empty.json"
    store = KnowledgeStore(store_path=path, chroma_path=tmp_path / "chroma_empty")
    store._rebuild_index()
    assert store._chroma_index().count() == 0
```


---

## Step 6：实验报告（20 min）

撰写 Markdown，包含：

1. 五步命令输出摘要  
2. 删 chroma 前后对比表  
3. 双存储架构自手绘图照片  
4. 一条你踩的坑  

**提交**：`lab/day29-<姓名>.md`

---

## 附录 A：故障注入实验（选做 30 min）

### A.1 人为制造 count 不一致

```bash
python3 -c "
from pathlib import Path
from rag.knowledge_store import KnowledgeStore
from rag.chroma_store import ChromaVectorIndex
s = KnowledgeStore.load_or_bootstrap()
c = ChromaVectorIndex(s._resolve_chroma_path())
# 仅删除一个 id（若库非空）
if c.count() > 0:
    col = c._ensure_collection()
    ids = col.get(include=[])['ids']
    if ids:
        c.delete_by_ids([ids[0]])
        print('deleted one, chroma', c.count(), 'chunks', s.chunk_count)
"
```

运行作业 A 健康检查脚本，应报警。再 `POST rebuild` 修复。

### A.2 对比内存与 Chroma 延迟（粗略）

```bash
python3 -c "
import time
from rag.knowledge_store import KnowledgeStore
from rag.embedding_retriever import EmbeddingRetriever
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding import EmbeddingClient
s = KnowledgeStore.load_or_bootstrap()
q = '年化收益率'
mem = EmbeddingRetriever(s.chunks)
t0=time.perf_counter()
mem.search(q, top_k=3)
t1=time.perf_counter()
client = EmbeddingClient()
client.model.load_state(s.embedding_state)
ch = ChromaEmbeddingRetriever(s.chunks, s._chroma_index(), client=client)
t2=time.perf_counter()
ch.search(q, top_k=3)
t3=time.perf_counter()
print('mem ms', (t1-t0)*1000, 'chroma ms', (t3-t2)*1000)
"
```

教学规模两者接近；记录结果写入实验报告「观察」小节。

---

## 附录 B：Lab 评分 Rubric

| 项 | 优秀 | 及格 | 不及格 |
|----|------|------|--------|
| Step 1–5 命令完整 | 全部可复现 | 缺 1 步 | 缺 ≥2 步 |
| 删 chroma 实验 | 有前后对比表 | 仅文字描述 | 未做 |
| 原理说明 | 能解释 sync | 复述课件 | 错误 |
| 踩坑记录 | 真实具体 | 泛泛 | 无 |

---

## 附录 C：常用路径与环境

| 项 | 路径 |
|----|------|
| 默认 store | data/knowledge/store.json |
| 默认 chroma | data/knowledge/chroma |
| 源码 chroma_store | src/rag/chroma_store.py |
| 测试 | tests/day29/ |
| 演示 | src/day29/chroma_demo.py |

Windows 学员请注意：路径分隔符与 `rm -rf` 替换为 PowerShell 等价命令。
