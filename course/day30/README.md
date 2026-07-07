# Day 30 课件索引

**日期**：2026-08-06（星期四）  
**主题**：增量索引（incremental upsert）  
**需求**：ZL-NA-REQ-030  
**平台版本**：v0.30.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| _incremental_index | `rag/knowledge_store.py` | upload 不 reset，仅 upsert 受影响 chunk |
| _remove_document_by_source | `rag/knowledge_store.py` | 同名上传先删旧 JSON + Chroma |
| delete_by_ids / delete_by_source | `rag/chroma_store.py` | 向量级删除 |
| IncrementalReport | `rag/knowledge_incremental.py` | API 报告模型 |
| index_mode / last_incremental_at | store.json + status | 持久化状态 |
| 测试 | `tests/day30/` | 16 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day30/incremental_demo.py
python3 src/day30/incremental_api_demo.py
python3 -m pytest tests/day30/ -v
```

## 关键流程

Day 29 每次 upload 都 `chroma.reset()` → Day 30 **upload 增量**：仅 upsert 新文档 chunk；`rebuild` 仍全量 reset。

## 核心难点（必读）

**TF-IDF 词表扩张**：新文档引入 JSON 词表中不存在的新 token 时，向量**维度变长**。Chroma 同一 collection 内所有向量须等维——故 `_incremental_index` 在 `vocab_expanded=True` 时调用 `chroma.reset()` 后**全量 upsert** 所有 chunk（仍比 Day 29 少一次不必要的 reset 场景：同内容 re-upload 仅 upsert 受影响 id）。

## 设计决策

1. `ingest_bytes` 默认 `incremental=True`  
2. `rebuild_store` 仍 `_rebuild_index` + reset，`index_mode=full`  
3. 词表扩张 → affected=all chunks + chroma reset  
4. 评估路径仍用内存 EmbeddingRetriever  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_增量索引详解 | TF-IDF 扩张专题 |
| 22_knowledge_incremental精读 | 源码 + _incremental_index |
| 26_实操Lab手册 | 六步含 vocab 扩张实验 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
PYTHONPATH=src pytest tests/day30/ -q
```

通过标准：重复 upload `reset` 调用 0 次（mock 测试）；vocab 扩张时 `reset` 1 次且 `chroma_count==chunk_count`。

---

## TF-IDF 词表扩张（课程核心）

新 token → 向量维度增加 → Chroma collection 内旧向量维度不足 → **`chroma.reset()` 后全量 upsert**。详见 `11_增量索引详解.md` 与 `22_knowledge_incremental精读.md`。

---

## 配套代码路径

| 类型 | 路径 |
|------|------|
| 核心逻辑 | `src/rag/knowledge_store.py` |
| 报告模型 | `src/rag/knowledge_incremental.py` |
| 演示 | `src/day30/incremental_demo.py` |
| 测试 | `tests/day30/`（16 项） |

---

## 常见问题（课前）

**Q upload 仍慢？**  可能触发了 vocab 扩张；查 token 是否全新。  
**Q reset 能否禁用？**  扩张时不能；否则检索错误。  
**Q 与 Day29 关系？**  先 Chroma 再 incremental，顺序不可颠倒。  

---

## 一周复习计划

| 天 | 内容 |
|----|------|
| D0 | 11 专题 + 22 精读 |
| D1 | Lab Step5 |
| D2 | pytest day30 |
| D3 | 作业 A |
| D4 | 口述扩张原理 |
| D5 | Day31 预习 |

---

## 发版检查（Release Captain）

- [ ] PLATFORM_VERSION 0.30.0  
- [ ] tests day29+day30 绿  
- [ ] 课件 30 篇 regenerate  
- [ ] 产品话术 FR-006 已同步客服  
- [ ] 备份 SOP 未变（仍 JSON+chroma）  

---

## 相关仓库路径速查

```
nexus-agent-platform/src/rag/knowledge_store.py      # _incremental_index
nexus-agent-platform/src/rag/knowledge_incremental.py
nexus-agent-platform/src/rag/chroma_store.py       # delete_*
nexus-agent-platform/src/day30/incremental_demo.py
nexus-agent-platform/tests/day30/
```

---

## 学员画像（完成后）

你将能够：配置 incremental 环境；向运营解释扩张延迟；编写 mock reset 测试；在 incident 时判断该 rebuild 还是重传。
