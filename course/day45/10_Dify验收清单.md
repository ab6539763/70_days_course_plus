# Day 45 Dify 验收清单

- [ ] `agent/dify_config.py` — DifyConfig + validate
- [ ] `agent/dify_protocol.py` — DifyNode/DifyEdge/DifyWorkflow/DifyTraceEvent
- [ ] `agent/dify_bridge.py` — build_dify_workflow + map_steps_to_dify_trace
- [ ] `agent/dify_runner.py` — DifyRunner 组合复用 McpRunner
- [ ] `store.json` 持久化 dify_config
- [ ] GET/PUT `/api/agent/dify-config`
- [ ] POST `/api/agent/dify-export`
- [ ] POST `/api/agent/dify-preview`
- [ ] `api/chat` dify_mode=true → dify_trace
- [ ] `tests/day45/` 27 项全绿
- [ ] `dify_demo.py` / `dify_api_demo.py` ✅
- [ ] `phase4_quiz.py --scripted` 满分 100/100
- [ ] `phase4_review.py` 打印 Day39-45 里程碑

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认配置 | GET dify-config | enabled=true |
| AC-02 | 导出结构 | POST dify-export | 含 start/tool/end |
| AC-03 | 预览追踪 | POST dify-preview | dify_trace 长度=4 |
| AC-04 | chat 集成 | POST /api/chat dify_mode=true | kind=dify |
| AC-05 | 版本 | GET /api/health | 0.45.0 |
| AC-06 | 持久化 | save/load store | workflow_name 保留 |
| AC-07 | 422 | max_nodes=999 | 422 |
| AC-08 | 周测 | phase4_quiz.py --scripted | 100/100 |

---

## 非功能验收

- [ ] 全量 pytest ≥660 passed
- [ ] 课件 regenerate ≥100k chars
- [ ] CI Day 45 job 绿

---

## 回归范围

day23–day44 API version 断言；day39-44 各模式测试在完整平台下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day45/ -q
python3 src/day45/dify_demo.py | grep -q "完成"
python3 src/day45/dify_api_demo.py | grep -q "完成"
python3 src/day45/phase4_quiz.py --scripted | grep -q "100/100"
echo DAY45_OK
```

---

## 学员能力达成

A：能配置 dify-config 并解释每个字段
B：能解释 dify_trace 与 mcp_trace 的映射关系
C：能跑通 Lab 5 curl 全家桶
D：能教他人读 dify_demo 输出并复述 Phase 4 六天里程碑
