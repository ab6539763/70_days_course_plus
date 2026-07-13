# Day 33 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.rewriteer; print('ok')"
pytest tests/day33/ --collect-only -q
```

**通过标准**：collect ≥18 tests。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_rewrite_config().to_dict())
"
```

**通过标准**：`enabled=True`, `max_rewrite_len=20`。

---

## Lab 2：rewrite_demo 开关（25 min）

```bash
python3 src/day33/rewrite_demo.py | tee /tmp/day34_demo.txt
```

**通过标准**：三条 Q；每条有关闭/开启两列；末尾 `✅`。

---

## Lab 3：翻牌单测（20 min）

```bash
pytest tests/day33/test_rewriteer.py::test_mock_rewrite_reorders_candidates -v
```

**通过标准**：passed；能口述噪声 chunk 被翻下去。

---

## Lab 4：pool 对比表（35 min）——必做

对 `RERANK_QUERIES` 记录 pool=10 vs pool=20 的 top-1 预览是否相同。

---

## Lab 5：API demo（20 min）

```bash
python3 src/day33/rewrite_api_demo.py
```

**通过标准**：PUT 200；chat 200；version 0.32.0。

---

## Lab 6：关闭 rewrite（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rewrite-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled":false,"max_rewrite_len":20,"model":"mock"}'
```

**通过标准**：200；status 显示 enabled false。

---

## Lab 7：全量回归（20 min）

```bash
pytest tests/day33/ -q
```

**通过标准**：18 passed。

---

## 提交

`lab/day34-<姓名>.md` 含 Lab 4 表格 + Lab 7 输出截图。

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
| rewrite 无效果 | 查 enabled |
| 延迟高 | 缩 pool |
| 18 tests 失败 | 查 PYTHONPATH |

---

## 附录：20 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1–11 | test_rewriteer.py | 单元 |
| 12–18 | test_rewrite_api.py | API |
