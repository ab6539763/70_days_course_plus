# Day 43 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.citation_builder; print('ok')"
pytest tests/day37/ --collect-only -q
```

**通过标准**：collect ≥20 tests。

---

## Lab 1：读默认 citation 配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_citation_config().to_dict())
"
```

**通过标准**：`enabled=True`, `max_citations=3`。

---

## Lab 2：route_demo（25 min）

```bash
python3 src/day37/route_demo.py | tee /tmp/day37_demo.txt
```

**通过标准**：三条 Q；每条有 citations 列表；末尾 `✅`。

---

## Lab 3：citation-preview API（20 min）

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/citation-preview \
  -H 'Content-Type: application/json' \
  -d '{"query":"那个理财能赚多少"}' | jq .
```

**通过标准**：`citations` 非空；`rewrite.changed` 为 true。

---

## Lab 4：chat citations 对比（35 min）——必做

对「年化收益率是多少」「投资有风险吗」各发一条 chat，记录 `citations[0].source` 与 `preview` 前 40 字。

| query | citations 数 | top1 source | preview 摘要 |
|-------|--------------|-------------|--------------|
| | | | |
| | | | |

---

## Lab 5：API demo（20 min）

```bash
python3 src/day37/route_api_demo.py
```

**通过标准**：citation-preview 200；chat citations ≥1；version v0.43.0。

---

## Lab 6：关闭 citations（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled":false,"max_citations":3,"preview_max_chars":120,"include_route_meta":true}'
```

再调 citation-preview，**通过标准**：`citations` 为空数组。

---

## Lab 7：全量回归（20 min）

```bash
pytest tests/day37/ -q
```

**通过标准**：20 passed。

---

## 提交

`lab/day37-<姓名>.md` 含 Lab 4 表格 + Lab 7 截图 + 前端 citations 截图。

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
| chat 无 citations | 查 citation_config.enabled |
| preview 空 | 换 query 或检查知识库 |
| 20 tests 失败 | 查 PYTHONPATH |

---

## 附录：20 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1–11 | test_query_router.py | 单元 |
| 12–20 | test_route_api.py | API |

---

## 附录 B：Citation JSON 样例

```json
{
  "rank": 1,
  "chunk_id": "raw_notice.txt-0",
  "source": "raw_notice.txt",
  "score": 0.92,
  "preview": "本产品年化收益率可达 8%...",
  "matched_tokens": ["年化", "收益"]
}
```

---

## 附录 C：教师演示脚本

```python
from rag.knowledge_store import KnowledgeStore
store = KnowledgeStore.bootstrap_from_sample_docs()
for q in ("年化收益率", "那个理财能赚多少", "投资有风险"):
    d = store.fetch_citations(q)
    print(q, len(d["citations"]), d["citations"][0]["source"] if d["citations"] else "—")
```

---

## 附录 D：前端验收

打开静态页，确认 bot 气泡下出现灰色「引用来源」区块与改写斜体行。

---

## 附录 E：与 Day33 差异

| 项 | Day33 | Day34 |
|----|-------|-------|
| 核心 | rewrite query | 展示 citations |
| API | rewrite-preview | citation-preview |
| chat 字段 | 无 | expansion.queries + merged citations |
