# Day 19 rag 包精读

**文件**：`nexus-agent-platform/src/rag/`（chunker、retriever、context）  
**关联**：`prompts/intent.py` 中 `query_context_provider`  
**阅读方式**：自下而上 + 测试反查

---

## 1. 包职责边界

| 负责 | 不负责 |
|------|--------|
| 文档分块 | 意图分类 |
| 关键词检索 | Prompt 渲染 |
| context 拼接 | LLM 调用 |
| 索引内存结构 | 向量库持久化 |

---

## 2. chunker.py 精读

### 2.1 导入

```python
from tools.doc_reader import DocumentRecord
```

与 Day 更早 `doc_reader` 工具链衔接，不重复实现读文件。

### 2.2 _PARA_SPLIT

```python
_PARA_SPLIT = re.compile(r"\n\s*\n+")
```

匹配空行分隔段落，`\s*` 容忍行尾空格。

### 2.3 _merge_paragraphs

贪心合并：能放进 `chunk_size` 就合并，否则 flush buffer。减少「一句话一块」。

### 2.4 offset 维护

整块路径 `offset += len(block) + 1`；滑动路径在块内用 `offset + start`。字符偏移供未来 UI 高亮。

### 2.5 chunk_documents

```python
for doc in docs:
    content = doc.cleaned if use_cleaned and doc.cleaned else doc.content
    chunks = chunk_text(..., source=doc.name)
    all_chunks.extend(chunks)
```

`index` 在 `chunk_text` 内随 `len(chunks)` 递增，跨文档连续。

---

## 3. retriever.py 精读

### 3.1 类设计

`KeywordRetriever` 持有 `_chunks` 列表，无倒排索引 —— MVP 暴力扫描，块数上百可接受。

### 3.2 search 早退

```python
if not query or not self._chunks:
    return []
tokens = _tokenize(query)
if not tokens:
    return []
```

### 3.3 bigram 循环

```python
for i in range(len(part) - 1):
    bg = part[i : i + 2]
```

对中文段 `年化收益率` 产生 `年化`,`化收`,`收益`,`益率`。

### 3.4 preview

```python
def preview(self, max_len: int = 60) -> str:
    text = self.chunk.text.replace("\n", " ")
```

换行压成空格，便于终端单行显示。

---

## 4. context.py 精读

### 4.1 DocumentIndex

轻量聚合：`chunks` + `retriever`。`search` 委托 retriever —— **替换检索器的唯一锚点**。

### 4.2 from_directory

```python
docs = read_documents(directory, pattern=pattern, clean=clean)
return cls.from_documents(docs, **kwargs)
```

`pattern` 默认 `*.txt`。

### 4.3 retrieve_context 空 query

```python
if not query:
    return "（请输入检索问题）"
```

与零命中文案区分，便于 UX。

### 4.4 截断逻辑

```python
if remain <= 20:
    break
```

剩余空间过小则放弃写下一块，避免无意义碎片。

### 4.5 retrieve_summary

```python
kw = ", ".join(r.matched_tokens[:5]) or "—"
```

最多展示 5 个命中 token，防刷屏。

---

## 5. __init__.py 导出

```python
from rag.chunker import TextChunk, chunk_text, chunk_documents
from rag.retriever import KeywordRetriever, RetrievalResult
from rag.context import DocumentIndex, RAGContextService
```

对外稳定 API，内部模块可重构。

---

## 6. intent.py 衔接精读

```python
QueryContextProvider = Callable[[str], str]

def _resolve_rag_context(self, query: str) -> str:
    if self.query_context_provider:
        return self.query_context_provider(query)
```

`service.retrieve_context` 方法绑定满足 `Callable[[str], str]`（额外 kw 参数 Python 允许）。

---

## 7. cli_assistant.py 衔接

```python
rag_service: RAGContextService | None = None
```

类型注解明确运维依赖，IDE 可自动补全。

---

## 8. 测试反查表

| 源码行/行为 | 测试 |
|-------------|------|
| overlap 切多块 | test_chunk_text_splits_with_overlap |
| overlap>=size | test_chunk_text_invalid_overlap |
| sample_docs | test_chunk_documents_from_reader |
| 年化命中 | test_retriever_finds_yield_info |
| max_chars | test_retrieve_context_respects_max_chars |
| query provider | test_intent_router_query_context_provider |

---

## 9. 修改指南

### 9.1 调整 header 格式

改 `retrieve_context` 中 `header = f"..."` → 同步更新 `test_retrieve_context_respects_max_chars` 容差。

### 9.2 新增检索器

```python
class MyRetriever:
    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        ...

index = DocumentIndex(chunks=chunks, retriever=MyRetriever())
```

### 9.3 新增文件类型

扩展 `read_documents` 或预处理为 `DocumentRecord`，**勿**在 chunker 内读盘。

---

## 10. 精读自检

1. `chunk_id` 中 `block_idx` 与 `sub_idx` 何时递增？  
2. `search` 的 `top_k` 最小返回几条？`max(1, top_k)` 含义？  
3. `retrieve_context` 与 `retrieve_summary` 能否合并？为何不合并？  

<details><summary>答案</summary>
1. 每个 merged block 一个 block_idx；滑动子块 sub_idx++  
2. 至少请求 1 条上限；`[:max(1, top_k)]`  
3. 能但不合并：输出格式与受众不同（Prompt vs 运维）  
</details>

---

## 11. Day 20 阅读预告

精读 `EmbeddingRetriever` 时对照本章 `DocumentIndex.retriever` 注入点 —— **一处替换，全局生效**。
