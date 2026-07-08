# RAGContextService 速查手册

**模块**：`src/rag/*` + `IntentRouter` / `ChatAssistant`  
**需求**：ZL-NA-REQ-019

---

## 快速开始

```python
from rag import RAGContextService
from prompts import IntentRouter
from chat import ChatAssistant

service = RAGContextService.from_sample_docs()
router = IntentRouter(query_context_provider=service.retrieve_context)

assistant = ChatAssistant(
    client=client,
    intent_router=router,
    auto_route=True,
    rag_service=service,
)
```

---

## chunker API

### chunk_text

```python
from rag import chunk_text

chunks = chunk_text(
    text,
    chunk_size=200,   # 单块最大字符
    overlap=40,       # 重叠字符
    source="doc.txt", # 来源标识
)
```

### chunk_documents

```python
from rag import chunk_documents
from tools.doc_reader import read_documents
from core.paths import get_path

docs = read_documents(get_path("sample_docs"), clean=True)
chunks = chunk_documents(docs, chunk_size=200, overlap=40)
```

### TextChunk 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| chunk_id | str | 唯一标识 |
| text | str | 块正文 |
| source | str | 文件名 |
| index | int | 全局序号 |
| start_char / end_char | int | 原文偏移 |
| char_count | property | len(text) |

---

## KeywordRetriever API

```python
from rag import KeywordRetriever

retriever = KeywordRetriever(chunks)
results = retriever.search("年化收益率", top_k=3)

for r in results:
    print(r.score, r.matched_tokens, r.preview())
```

### RetrievalResult

| 字段 | 说明 |
|------|------|
| chunk | TextChunk |
| score | float，0–1 |
| matched_tokens | tuple[str, ...] |
| preview(max_len=60) | 单行摘要 |

---

## RAGContextService API

### 工厂方法

| 方法 | 用途 |
|------|------|
| `from_sample_docs(**kwargs)` | 读内置 sample_docs |
| `from_directory(path, pattern="*.txt", **kwargs)` | 读目录 |
| `from_documents(docs, **kwargs)` | 已有 DocumentRecord 列表 |

### retrieve_context

```python
context = service.retrieve_context(
    query,
    top_k=3,           # 检索块数
    max_chars=800,     # 总字符上限
    separator="\n---\n",
)
```

### retrieve_summary

```python
summary = service.retrieve_summary("客服电话", top_k=3)
# 供 /retrieve 命令
```

---

## IntentRouter 集成

```python
def _resolve_rag_context(self, query: str) -> str:
    if self.query_context_provider:
        return self.query_context_provider(query)
    if self.context_provider:
        return self.context_provider()
    return "（暂无检索上下文）"
```

构造：

```python
IntentRouter(
    query_context_provider=service.retrieve_context,
    # 或向后兼容：
    # context_provider=lambda: "静态",
)
```

---

## ChatAssistant 命令

| 命令 | 依赖 | 行为 |
|------|------|------|
| `/retrieve [query]` | `rag_service` | `retrieve_summary`，不调 LLM |
| `/route [text]` | `intent_router` | 意图预览（Day 18） |

未设 `rag_service` 时 `/retrieve` 返回启用提示。

---

## 演示脚本

```bash
export PYTHONPATH=src
python3 src/day19/chunk_demos.py
python3 src/day19/retriever_demos.py
python3 src/day19/rag_context_demo.py
NEXUS_LLM_MOCK=1 python3 src/day19/routed_rag_demo.py
```

---

## 测试入口

```bash
python3 -m pytest tests/day19/test_rag.py -v
```

---

## 默认参数一览

| 参数 | 默认值 | 模块 |
|------|--------|------|
| chunk_size | 200 | chunker |
| overlap | 40 | chunker |
| top_k | 3 | retriever / context |
| max_chars | 800 | context |

---

## 排错速查

| 现象 | 检查 |
|------|------|
| 导入失败 | PYTHONPATH=src |
| 无命中 | `/retrieve` + 换关键词 |
| context 占位 | query_context_provider |
| /retrieve 未启用 | rag_service |

---

## Day 20 预告

`KeywordRetriever` → `EmbeddingRetriever`，`RAGContextService` 接口不变。
