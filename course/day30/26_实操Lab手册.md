# Day 30 实操 Lab 手册

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

## Step 1：incremental_demo（15 min）

```bash
python3 src/day30/incremental_demo.py
```

记录 document_count 与 index_mode。

## Step 2：重复上传不 reset（20 min）

```bash
python3 -m pytest tests/day30/test_incremental_index.py::test_reupload_does_not_reset_chroma -v
```

阅读测试源码，理解 patch。

## Step 3：API demo（15 min）

```bash
python3 src/day30/incremental_api_demo.py
```

## Step 4：rebuild 回 full（15 min）

POST rebuild，确认 index_mode=full。

## Step 5：TF-IDF 词表扩张实验（40 min）——必做

创建 `expansion_lab.md`：

```markdown
# 扩张实验专用
本文件包含独有术语：{UNIQUE_TOKEN}
```

将 `{UNIQUE_TOKEN}` 替换为随机串如 `ZlNaReq030Xy7`。

```python
from unittest.mock import patch
from pathlib import Path
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

store = KnowledgeStore.bootstrap_from_sample_docs()
old_len = len(store.embedding_state.get("vocab") or {})
text = Path("expansion_lab.md").read_text(encoding="utf-8")
with patch.object(ChromaVectorIndex, "reset") as m:
    store.ingest_bytes(text.encode(), filename="expansion_lab.md", incremental=True)
    new_len = len(store.embedding_state.get("vocab") or {})
    print("old", old_len, "new", new_len, "expanded", new_len > old_len)
    print("reset calls", m.call_count)
```

**期望**：new_len > old_len 时 reset calls == 1；chroma_count == chunk_count。

**报告须回答**：为何扩张必须 reset？若只 upsert 新文档向量会怎样？

## Step 6：测试全绿（15 min）

```bash
python3 -m pytest tests/day30/ -v
```

## 提交

`lab/day30-<姓名>.md` 含 Step 5 输出与三问答案。

---

## 附录 A：Step 5 三问参考答案

**Q1：为何扩张必须 reset？**  
TF-IDF 向量维度随词表增长，旧向量与新向量维度不同，Chroma 要求 collection 内等维，必须销毁旧 collection 重建。

**Q2：若只 upsert 新文档向量？**  
旧 chunk 仍是低维向量，与新文档高维向量共存失败；检索时 query 已是高维，无法匹配低维存量。

**Q3：同内容 re-upload 为何 reset=0？**  
无新 token，vocab 大小不变，仅替换 chunk_id 对应向量，upsert 即可。

---

## 附录 B：故障注入

手动删除 JSON 中某 chunk 但不删 Chroma 对应 id，运行 health 检查，再 incremental upload 观察是否自愈（预期：需 rebuild）。

---

## 附录 C：评分 Rubric

| 项 | 分值 |
|----|------|
| Step 1–4 | 30 |
| Step 5 扩张实验 | 40 |
| Step 6 测试 | 10 |
| 报告质量 | 20 |

---

## 附录 D：环境变量

| 变量 | 用途 |
|------|------|
| PYTHONPATH=src | 导入 |
| NEXUS_LLM_MOCK=1 | mock LLM |

---

## 附录 E：教师演示计时

| 步骤 | 建议分钟 |
|------|----------|
| 1–3 | 50 |
| 4 | 15 |
| 5 | 40 |
| 6 | 15 |

---

## 附录 F：Step5 完整脚本（可复制）

```python
from __future__ import annotations
import uuid
from pathlib import Path
from unittest.mock import patch
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

token = "ZlNa030_" + uuid.uuid4().hex[:8]
md = f"# 扩张实验\n独有术语：{token}\n"
store = KnowledgeStore.bootstrap_from_sample_docs()
old = len((store.embedding_state or {}).get("vocab") or {})
with patch.object(ChromaVectorIndex, "reset") as m:
    store.ingest_bytes(md.encode(), filename="expansion_lab.md", incremental=True)
    new = len((store.embedding_state or {}).get("vocab") or {})
print("token", token)
print("vocab", old, "->", new, "expanded", new > old)
print("reset_calls", m.call_count)
print("counts", store._chroma_index().count(), store.chunk_count)
```

---

## 附录 G：常见问题

**Q Step5 reset=0？**  token 与已有词撞车，换 UUID。  
**Q pytest 失败？**  查 sample md 是否存在。  
**Q：chroma 锁？**  关其他 API 进程。

---

## 附录 H：六步检查表（可打印）

| Step | 完成 | 签名 |
|------|------|------|
| 1 demo | ☐ | |
| 2 pytest reset | ☐ | |
| 3 API demo | ☐ | |
| 4 rebuild full | ☐ | |
| 5 expansion | ☐ | |
| 6 all tests | ☐ | |

---

## 附录 I：扩张实验报告模板

```markdown
# Day30 Lab
- token: 
- vocab: ___ -> ___
- reset_calls: 
- 为何扩张要 reset（三句话）:
```

---

## 附录 J：16 项测试清单

| # | 测试名 | 文件 |
|---|--------|------|
| 1 | test_reupload_does_not_reset_chroma | index |
| 2 | test_reupload_replaces_document_not_duplicates | index |
| 3 | test_incremental_updates_last_incremental_at | index |
| 4 | test_chroma_count_matches_chunks_after_incremental | index |
| 5 | test_remove_document_by_source_deletes_chroma_vectors | index |
| 6 | test_rebuild_still_uses_full_index_mode | index |
| 7 | test_incremental_persists_index_mode | index |
| 8 | test_non_incremental_ingest_uses_full_rebuild | index |
| 9 | test_chroma_delete_by_source | index |
| 10 | test_rag_retrieval_after_incremental_upload | index |
| 11 | test_health_version | api |
| 12 | test_upload_returns_incremental_mode | api |
| 13 | test_status_shows_incremental_fields | api |
| 14 | test_reupload_same_file_no_duplicate_docs | api |
| 15 | test_rebuild_switches_to_full_mode | api |
| 16 | test_chat_works_after_incremental_upload | api |

---

## 附录 K：故障排查扩展

| 症状 | 深入排查 |
|------|----------|
| reset 过多 | 统计每日新 token 数 |
| 扩张后搜不到 | 等 upsert 完成再查 |
| API 500 on upload | chromadb 日志 |
| index_mode  stuck | 手动 rebuild |

---

## 附录 L：Step5 预期输出样例

```
token ZlNa030_a1b2c3d4
vocab 128 -> 129 expanded True
reset_calls 1
counts 15 15
```

---

## 附录 M：与 Day29 Lab 差异

| 项 | Day29 | Day30 |
|----|-------|-------|
| 核心实验 | 删 chroma 目录 | patch reset |
| 关键测试 | top-1 一致 | reupload no reset |
| 必读源码 | chroma_store | _incremental_index |

---

## 附录 N：讲师时间盒

若课时不足，优先保 Step 2（mock reset）与 Step 5（扩张）；Step 4 rebuild 可作业补做。

---

## 附录 O：rebuild curl 参考

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"include_sample_docs": true}' | jq '{index_mode,chunks_after}'
```

期望 `index_mode` 为 `full`（或字段在 status 中为 full）。

---

## 附录 P：Windows 学员 Step5 注意

PowerShell 创建 expansion_lab.md 时注意 UTF-8 BOM；Python `read_text(encoding='utf-8')` 读入后 `encode()` 再 `ingest_bytes`。
