# Day 29 课件索引

**日期**：2026-08-05（星期三）  
**主题**：Chroma 向量库持久化  
**需求**：ZL-NA-REQ-029  
**平台版本**：v0.29.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| ChromaVectorIndex | `rag/chroma_store.py` | PersistentClient 封装、upsert/query/reset |
| ChromaEmbeddingRetriever | `rag/chroma_retriever.py` | 与 EmbeddingRetriever 接口对齐 |
| KnowledgeStore 集成 | `rag/knowledge_store.py` | `_rebuild_index` / `_sync_chroma_from_json` |
| status API | `api/schemas.py` | `vector_backend` / `chroma_count` / `chroma_path` |
| 演示脚本 | `src/day29/chroma_demo.py` | 本地验证 Chroma 落盘 |
| 测试 | `tests/day29/` | 15 项（index + API） |

## 关键流程

Day 28 的 `rebuild_store` 流程**不变**；Day 29 将向量从 `store.json` 的 `embedding` 字段**外迁**到 `data/knowledge/chroma/`。JSON 仍保留 TF-IDF 词表（`vocab` / `idf`），供 `EmbeddingClient` 编码 query。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day29/chroma_demo.py
python3 src/day29/chroma_api_demo.py
python3 -m pytest tests/day29/ -v
```

## 设计决策（课堂必背）

1. **双存储**：`store.json` = 元数据 + TF-IDF 词表；Chroma = chunk 向量 + metadata  
2. **重建语义不变**：`_rebuild_index()` 先 fit TF-IDF，再 `chroma.reset()` + `upsert_chunks`  
3. **冷启动迁移**：`load()` 时若 Chroma 空且 chunks 存在 → `_sync_chroma_from_json()` 自动回填  
4. **评估隔离**：Day 27 `retrieval_eval` 仍用内存 `EmbeddingRetriever`，避免 A/B 实验污染生产 Chroma  

## 课件导航

| 序号 | 文件 | 学时建议 |
|------|------|----------|
| 02 | 需求文档 + 扩展 | 30 min |
| 03 | 架构设计 | 45 min |
| 11 | Chroma 向量库详解 | 60 min |
| 22 | chroma_store 精读 | 90 min |
| 26 | 实操 Lab | 120 min |
| 27 | Day 30 预习 | 15 min |

## 验收命令

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day29/chroma_api_demo.py
PYTHONPATH=src pytest tests/day29/ -q
```

通过标准：`chroma_count == chunk_count`，`vector_backend == "chroma"`，chat 检索正常。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.29.0 | 2026-08-05 | 首版 Chroma 课件 30 篇 |
| 0.28.x | 2026-08-04 | 前一日 rebuild 课件 |

---

## 学员常见问题（课前售后）

**安装 chromadb 失败**：先 `pip install -U pip`，Python 3.10+，ARM 用 conda-forge。  

**data/knowledge 权限**：Docker 挂载卷时注意 uid。  

**Windows 路径**：`chroma_path` 反斜杠由 pathlib 处理，勿手改 JSON。  

**与队友 merge 冲突**：`store.json` 和 `chroma/` 不应进 git；若误提交用 `git rm --cached`。

---

## 学时分配建议（共 6 课时）

| 课时 | 内容 | 文件 |
|------|------|------|
| 1 | PRD + 架构 | 02, 03 |
| 2 | Chroma 专题 | 11 |
| 3 | 源码精读 | 22, 25 |
| 4 | 实操 Lab | 26 |
| 5 | 练习 + 竞赛 | 12, 21 |
| 6 | 作业讲评 + Day30 预习 | 09, 27 |
