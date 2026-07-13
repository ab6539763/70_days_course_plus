# Day 44 实操 Lab 手册（Lab 0-6）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
pytest tests/day44/ --collect-only -q
```

**通过标准**：collect ≥20 tests。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.status_dict().get('mcp_config'))
"
```

---

## Lab 2：核心 demo（25 min）

```bash
python3 src/day44/mcp_demo.py
```

**通过标准**：所有 case study 都打印出委派/决策结果与 `mcp_trace`。

---

## Lab 3：API demo（20 min）

```bash
python3 src/day44/mcp_api_demo.py
```

**通过标准**：health version 为 `v0.44.0`。

---

## Lab 4：chat 对比（35 min）——必做

对每条 case study query 分别发一次 `mcp_mode=true` 与默认（不带该字段）的 chat 请求，记录 `mcp_trace` 是否出现。

| query | mcp_mode=true | 默认 |
|-------|---------------------|------|
| | | |

---

## Lab 5：curl 全家桶（20 min）

```bash
curl -s http://127.0.0.1:8000/api/agent/mcp-config | jq .
curl -s -X POST http://127.0.0.1:8000/api/agent/mcp-preview -H 'Content-Type: application/json' -d '{"query":"测试"}' | jq .
curl -s -X POST http://127.0.0.1:8000/api/agent/mcp-list-tools -H 'Content-Type: application/json' -d '{}'
```

---

## Lab 6：全量回归（20 min）

```bash
pytest tests/day44/ -v
```

**通过标准**：20 passed。

---

## 提交

`lab/day44-<姓名>.md` 含 Lab 4 表格 + Lab 6 截图。

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
| chat 无 `mcp_trace` | 检查 `mcp_mode` 是否为 true 且配置 enabled |
| API 404 | 确认 uvicorn 已重启加载新路由 |
| 测试失败 | 检查 `PYTHONPATH=src` 是否设置 |
