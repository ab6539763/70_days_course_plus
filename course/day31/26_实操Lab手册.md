# Day 31 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.hybrid_retriever; print('ok')"
pytest tests/day31/ --collect-only -q
```

**通过标准**：collect ≥17 tests，无 ImportError。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_retrieval_config().to_dict())
"
```

**通过标准**：`mode=hybrid`，`fusion` 为 weighted 或文档默认值。

---

## Lab 2：hybrid_demo 三模式（25 min）

```bash
python3 src/day31/hybrid_demo.py | tee /tmp/day31_demo.txt
```

**通过标准**：输出含三条 Q；每条有 vector/keyword/hybrid 三列；末尾 `✅`。

---

## Lab 3：切换 RRF（20 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, MODE_HYBRID
s = KnowledgeStore.bootstrap_from_sample_docs()
s.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF))
h = s.as_rag_service().index.retriever
print(h.search('投资有风险吗', top_k=3)[0].score)
"
```

**通过标准**：无异常；返回 1–3 条结果。

---

## Lab 4：weighted vs RRF 对比表（35 min）——必做

对 `HYBRID_QUERIES` 每条记录两种 fusion 的 top-1 `chunk_id` 是否相同。

**通过标准**：表格 ≥3 行；至少 1 条 query 两 fusion 不同或能解释为何相同。

---

## Lab 5：API demo（20 min）

```bash
python3 src/day31/hybrid_api_demo.py
```

**通过标准**：PUT 200；chat 200；打印 version 0.31.0。

---

## Lab 6：单测精读（25 min）

```bash
pytest tests/day31/test_hybrid_retriever.py::test_exact_phone_keyword_favors_hybrid -v
pytest tests/day31/test_hybrid_retriever.py::test_rrf_merge_helper -v
```

**通过标准**：2 passed；能口述测试意图。

---

## Lab 7：全量回归 + chat（20 min）

```bash
pytest tests/day31/ -q
curl -s -X POST http://127.0.0.1:8000/api/chat -H 'Content-Type: application/json' \
  -d '{"message":"最低起购金额？"}' | jq '.reply | length'
```

（若无服务，用 `test_chat_with_hybrid_retrieval` 代替。）

**通过标准**：17 passed；chat reply 非空。

---

## 提交

`lab/day31-<姓名>.md` 含 Lab 4 表格 + Lab 7 截图。

---

## 评分 Rubric

| Lab | 分值 |
|-----|------|
| 0–1 | 10 |
| 2–3 | 20 |
| 4 | 30 |
| 5–7 | 40 |

---

## 故障排查

| 症状 | 处理 |
|------|------|
| hybrid 与 vector 相同 | 增大 pool 或调权重 |
| PUT 422 | 检查 JSON mode 拼写 |
| 17 tests 失败 | 查 PYTHONPATH |

---

## 附录 A：Lab 4 表格模板

| query | weighted top1 | rrf top1 | 相同? |
|-------|---------------|----------|-------|
| 年化收益率可达 | | | |
| 13900001111 | | | |
| 投资有风险 | | | |

---

## 附录 B：curl retrieval-config 完整

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/retrieval-config \
  -H 'Content-Type: application/json' \
  -d '{"mode":"hybrid","fusion":"weighted","keyword_weight":0.35,"vector_weight":0.65,"rrf_k":60}'
```

---

## 附录 C：17 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1 | test_retrieval_config_validate | retriever |
| 2 | test_hybrid_mode_vector_only | retriever |
| 3 | test_hybrid_mode_keyword_only | retriever |
| 4 | test_hybrid_weighted_merge | retriever |
| 5 | test_hybrid_rrf_merge | retriever |
| 6 | test_exact_phone_keyword_favors_hybrid | retriever |
| 7 | test_knowledge_store_persists_retrieval_config | retriever |
| 8 | test_status_includes_retrieval_config | retriever |
| 9 | test_rrf_merge_helper | retriever |
| 10 | test_weighted_merge_helper | retriever |
| 11 | test_health_version | api |
| 12 | test_get_retrieval_config_default_hybrid | api |
| 13 | test_put_retrieval_config_rrf | api |
| 14 | test_status_includes_retrieval_config | api |
| 15 | test_invalid_retrieval_mode_422 | api |
| 16 | test_chat_with_hybrid_retrieval | api |
| 17 | test_switch_to_keyword_mode | api |

---

## 附录 D：教师演示脚本（可复制）

```python
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, FUSION_WEIGHTED, MODE_HYBRID

store = KnowledgeStore.bootstrap_from_sample_docs()
q = "13900001111"
for fusion in (FUSION_WEIGHTED, FUSION_RRF):
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=fusion))
    h = store.as_rag_service().index.retriever
    t = h.search(q, top_k=1)[0]
    print(fusion, t.chunk.source, t.score)
```

---

## 附录 E：Windows 注意

PowerShell 下 curl 别名可能是 Invoke-WebRequest；用 `curl.exe` 或 Python requests。

---

## 附录 F：与 Day30 Lab 差异

| 项 | Day30 | Day31 |
|----|-------|-------|
| 核心实验 | vocab 扩张 reset | fusion 对比 |
| 关键 API | upload | retrieval-config |
| 必读源码 | _incremental_index | hybrid_retriever |

---

## 附录 G：预期 Lab 7 输出

```
17 passed in 2.5s
```

---

## 附录 H：讲师时间盒

| Lab | 分钟 |
|-----|------|
| 0–1 | 25 |
| 2–3 | 45 |
| 4 | 35 |
| 5–7 | 65 |
