# Day 36 实操 Lab 手册（Lab 0-6）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
pytest tests/day36/ --collect-only -q
```

**通过标准**：collect ≥20 tests。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.status_dict().get('route_config'))
"
```

---

## Lab 2：核心 demo（25 min）

```bash
python3 src/day36/route_demo.py
```

**通过标准**：所有 case study 都打印出处理结果。

---

## Lab 3：API demo（20 min）

```bash
python3 src/day36/route_api_demo.py
```

**通过标准**：health version 为 `v0.36.0`。

---

## Lab 4：chat 对比（35 min）——必做

对每条 case study query 分别发一次 chat 请求，记录响应差异。

| query | 结果摘要 |
|-------|---------|
| | |

---

## Lab 5：curl 全家桶（20 min）

```bash
curl -s http://127.0.0.1:8000/api/knowledge/route-config | jq .
curl -s -X POST http://127.0.0.1:8000/api/knowledge/route-preview -H 'Content-Type: application/json' -d '{"query":"测试"}' | jq .
```

---

## Lab 6：全量回归（20 min）

```bash
pytest tests/day36/ -v
```

**通过标准**：20 passed。

---

## 提交

`lab/day36-<姓名>.md` 含 Lab 4 表格 + Lab 6 截图。

---

## 评分 Rubric

| Lab | 分值 |
|-----|------|
| 0-1 | 10 |
| 2-3 | 30 |
| 4 | 30 |
| 5-6 | 30 |

---

## 故障排查

| 症状 | 处理 |
|------|------|
| chat 无变化 | 检查 `route_config.enabled` |
| API 404 | 确认 uvicorn 已重启加载新路由 |
| 测试失败 | 检查 `PYTHONPATH=src` 是否设置 |
