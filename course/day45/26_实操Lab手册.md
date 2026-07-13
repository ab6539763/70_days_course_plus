# Day 45 实操 Lab 手册（Lab 0-7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import agent.dify_runner; print('ok')"
pytest tests/day45/ --collect-only -q
```

**通过标准**：collect ≥27 tests。

---

## Lab 1：读默认 Dify 配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_dify_config().to_dict())
"
```

**通过标准**：`enabled=True`, `workflow_name='nexus-agent-workflow'`, `max_nodes=10`。

---

## Lab 2：dify_demo（25 min）

```bash
python3 src/day45/dify_demo.py | tee /tmp/day45_demo.txt
```

**通过标准**：导出节点含 start/end；三条 case study 都打印出委派结果；末尾 `✅`。

---

## Lab 3：dify-export API（20 min）

```bash
curl -s -X POST http://127.0.0.1:8000/api/agent/dify-export | jq '.workflow.graph.nodes'
```

**通过标准**：节点数组含 `start`、若干 `tool_*`、`end`。

---

## Lab 4：chat dify_trace 对比（35 min）——必做

对「客服电话多少」「年化收益怎么样」各发一条 chat（`dify_mode=true`），记录 `dify_trace` 的节点数与 `node_type` 序列。

| query | dify_trace 节点数 | node_type 序列 |
|-------|-------------------|-----------------|
| | | |
| | | |

---

## Lab 5：API demo（20 min）

```bash
python3 src/day45/dify_api_demo.py
```

**通过标准**：dify-export 200；chat dify_trace 长度=4；version v0.45.0。

---

## Lab 6：关闭 Dify 对接（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled":false,"workflow_name":"nexus-agent-workflow","include_start_end":true,"mock_routing":true,"use_session_history":true,"return_dify_trace":true,"max_nodes":10}'
```

再调 dify-export，**通过标准**：返回 HTTP 400。

---

## Lab 7：Phase 4 周测 + 全量回归（25 min）

```bash
python3 src/day45/phase4_quiz.py --scripted
pytest tests/day45/ -q
```

**通过标准**：周测 100/100；27 passed。

---

## 提交

`lab/day45-<姓名>.md` 含 Lab 4 表格 + Lab 7 截图 + 周测得分。

---

## 评分 Rubric

| Lab | 分值 |
|-----|------|
| 0-1 | 10 |
| 2-3 | 20 |
| 4 | 30 |
| 5-7 | 40 |

---

## 故障排查

| 症状 | 处理 |
|------|------|
| chat 无 dify_trace | 查 dify_config.enabled |
| 导出节点为空 | 检查 ToolRegistry 是否注册了工具 |
| 27 tests 失败 | 查 PYTHONPATH |

---

## 附录：27 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1-13 | test_dify_runner.py | 单元 |
| 14-24 | test_dify_api.py | API |
| 25-27 | test_phase4_quiz.py | 周测 |

---

## 附录 B：DifyWorkflow JSON 样例

```json
{
  "app": {"name": "nexus-agent-workflow", "mode": "workflow"},
  "workflow": {
    "graph": {
      "nodes": [
        {"id": "start", "data": {"type": "start", "title": "开始"}},
        {"id": "tool_faq_lookup", "data": {"type": "tool", "title": "faq_lookup"}},
        {"id": "end", "data": {"type": "end", "title": "结束"}}
      ],
      "edges": [
        {"id": "start->tool_faq_lookup", "source": "start", "target": "tool_faq_lookup"},
        {"id": "tool_faq_lookup->end", "source": "tool_faq_lookup", "target": "end"}
      ]
    }
  }
}
```

---

## 附录 C：教师演示脚本

```python
from agent.dify_runner import DifyRunner
from api.factory import create_orchestrator

orchestrator = create_orchestrator()
runner = DifyRunner.from_executor(orchestrator.tool_executor)
for q in ("客服电话多少", "年化收益怎么样", "帮我总结一下理财产品"):
    outcome = runner.invoke(q)
    print(q, outcome.tools_used, len(outcome.dify_trace))
```

---

## 附录 D：前端验收（展望）

未来打开静态页，发送「年化收益率是多少」并开启 dify_mode，确认 bot 气泡下能看到 dify_trace 节点序列（当前教学子集未接前端，留作扩展）。

---

## 附录 E：与 Day44 差异

| 项 | Day44 MCP | Day45 Dify |
|----|-----------|------------|
| 核心 | 协议化对接外部工具 | 导出给低代码平台编排 |
| API | mcp-preview | dify-export + dify-preview |
| chat 字段 | mcp_mode → mcp_trace | dify_mode → dify_trace |
