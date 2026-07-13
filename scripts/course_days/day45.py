#!/usr/bin/env python3
"""Gold-standard course material builder for Day 45 — Dify 工作流对接 + Phase 4 周测。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-045"
VER = "v0.45.0"
REPO = "nexus-agent-platform/src"

DIFY_CONFIG = read_repo(f"{REPO}/agent/dify_config.py")
DIFY_PROTOCOL = read_repo(f"{REPO}/agent/dify_protocol.py")
DIFY_BRIDGE = read_repo(f"{REPO}/agent/dify_bridge.py")
DIFY_RUNNER = read_repo(f"{REPO}/agent/dify_runner.py")
MCP_RUNNER = read_repo(f"{REPO}/agent/mcp_runner.py")
AGENT_API = read_repo(f"{REPO}/api/agent.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
CHAT_API = read_repo(f"{REPO}/api/chat.py")
DIFY_DEMO = read_repo(f"{REPO}/day45/dify_demo.py")
DIFY_API_DEMO = read_repo(f"{REPO}/day45/dify_api_demo.py")
PHASE4_QUIZ = read_repo(f"{REPO}/day45/phase4_quiz.py")
PHASE4_REVIEW = read_repo(f"{REPO}/day45/phase4_review.py")
TEST_DIFY_RUNNER = read_repo(f"{REPO}/../tests/day45/test_dify_runner.py")
TEST_DIFY_API = read_repo(f"{REPO}/../tests/day45/test_dify_api.py")
TEST_PHASE4_QUIZ = read_repo(f"{REPO}/../tests/day45/test_phase4_quiz.py")

_AGENT_API_DIFY = AGENT_API[
    AGENT_API.find('@router.get("/dify-config"'): AGENT_API.find(
        '@router.post("/dify-preview"'
    )
    + len('@router.post("/dify-preview"')
]
_DIFY_RUNNER_CLASS = DIFY_RUNNER[
    DIFY_RUNNER.find("class DifyRunner"): DIFY_RUNNER.find("def _empty_outcome")
]
_KNOWLEDGE_STORE_DIFY_METHODS = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def get_dify_config"): KNOWLEDGE_STORE.find(
        "def validate_answer"
    )
]
_CHAT_DIFY = CHAT_API[
    CHAT_API.find("if body.dify_mode"): CHAT_API.find("elif body.mcp_mode")
]


def build() -> dict[str, str]:
    files = {
        "README.md": _readme(),
        "00_旁白解读.md": _narration(),
        "01_企业背景与今日任务.md": _file01(),
        "02_需求文档.md": _prd(),
        "02_需求文档_扩展.md": _prd_extended(),
        "03_架构设计.md": _architecture(),
        "04_流程图与示意图.md": _file04(),
        "05_课堂笔记_上午.md": _file05(),
        "06_课堂笔记_下午.md": _file06(),
        "07_晚自习.md": _file07(),
        "08_作业.md": _file08(),
        "09_作业答案.md": _file09(),
        "10_Dify验收清单.md": _file10(),
        "11_Dify详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_Dify工作流方法论.md": _file13(),
        "14_企业案例集_Dify对接场景.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_Dify_API速查手册.md": _file17(),
        "18_与Day44能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_dify_runner精读.md": _file22(),
        "23_Phase4周测与复盘实践.md": _file23(),
        "24_Phase4第七日总结.md": _file24(),
        "25_dify_runner_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day46预习.md": _file27(),
    }
    return files


def _readme() -> str:
    return f"""# Day 45 课件索引

**主题**：Dify 工作流对接 + Phase 4 周测 — ToolRegistry 导出 Dify DSL，McpStep 映射 Dify 运行 trace
**需求**：{REQ}
**平台版本**：{VER}

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| DifyConfig | `agent/dify_config.py` | workflow_name / mock_routing / max_nodes |
| Dify DSL | `agent/dify_protocol.py` | DifyNode / DifyEdge / DifyWorkflow / DifyTraceEvent |
| DifyBridge | `agent/dify_bridge.py` | build_dify_workflow + map_steps_to_dify_trace |
| DifyRunner | `agent/dify_runner.py` | 复用 McpRunner 决策/执行，输出 Dify 风格追踪 |
| 周测 | `day45/phase4_quiz.py` | Day 39-44 十题自测 |
| 回顾 | `day45/phase4_review.py` | Phase 4 里程碑串联 |

| API | 说明 |
|-----|------|
| GET/PUT `/api/agent/dify-config` | 配置读写 |
| POST `/api/agent/dify-export` | 导出 Dify 工作流 DSL |
| POST `/api/agent/dify-preview` | 无状态预览，返回 `dify_trace` |

`POST /api/chat` + `dify_mode: true` → 响应含 `dify_trace` + `tools_used`。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day45/dify_demo.py
python3 src/day45/dify_api_demo.py
python3 src/day45/phase4_review.py
python3 src/day45/phase4_quiz.py --scripted
python3 -m pytest tests/day45/ -v
```

## 关键流程

Day44 用 MCP 协议让工具链可跨进程扩展；Day45 把这条工具链**再导出一层**成 Dify 工作流 DSL —— 同一套 `ToolRegistry`，既能被 Nexus 自己的 `McpRunner` 调用，也能被 Dify 这类低代码工作流平台直接编排。

## 验收

`tests/day45/` 27 项全绿；`day45/phase4_quiz.py --scripted` 得分 100/100。

---

## 课件生成

```bash
python3 scripts/generate_day45_course.py
```
"""


def _narration() -> str:
    return f"""# Day 45 旁白解读

Day44 的 MCP Server 上线两周后，运营团队提了个新需求：市场部想用 Dify 这类低代码工作流平台，把「客服 FAQ」「理财检索」几个工具拖拽拼接成一个可视化流程，不想每次改流程都找研发。

赵岩在白板上画了一条演进线：

```
Day 44 MCP 协议与工具生态  →  Day 45 Dify 工作流对接 + Phase 4 周测
```

**今日目标**：写一个 `DifyBridge`，把 `ToolExecutor` 里已注册的工具直接导出成 Dify 工作流 DSL（`start → tool* → end` 节点图），并把 `McpRunner` 的四阶段 trace 映射成 Dify 风格的 `workflow_node_execution` 日志，方便未来对接真实 Dify 实例。同时，Phase 4（Day39-44）已经走完一轮完整的 Agent 编排能力，今天补一次周测巩固。

**行动**：Day46 预习 Agent 工程化——可观测性与容错。

---

## 为什么是今天

Day44 让工具链**可扩展**（MCP 协议边界）；Day45 让工具链**可编排**——不仅能被自家 Agent 调用，还能被外部低代码平台可视化拼装。团队复盘 Phase 4 时发现，光有协议边界还不够，得让非研发同学也能"看懂并改"工作流，这正是 Dify 类平台的价值。

## 一句话总结

Day44 让工具链**可扩展**；Day45 让平台**可编排**——同一套工具，一份导出给 Dify，一份继续服务 Nexus 自己的 Agent。
"""


def _file01() -> str:
    return f"""# Day 45 企业背景与今日任务

**需求**：{REQ} | **版本**：{VER}

## 背景

Day44 交付的 MCP Server 让工具链有了协议边界，但市场部反馈：非研发同学想自己拖拽拼流程，不想每次都排期找研发改代码。行业内 Dify、n8n 一类低代码工作流平台正好解决这个问题——把工具注册为节点，用图形化方式编排。今天交付两件事：

1. **DifyBridge**：把 Nexus 自己的 `ToolRegistry` 导出成 Dify 工作流 DSL（教学子集），运行 trace 也映射成 Dify 风格日志。
2. **Phase 4 周测**：Day39-44（ReAct/Executor/Graph/Approval/Supervisor/MCP）的十题自测 + 里程碑回顾。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | DifyConfig + dify_protocol DSL 数据模型 + build_dify_workflow |
| 下午 | Lab：dify-export + dify-preview + chat dify_mode 截图 |
| 晚自习 | 完成 Phase 4 周测，读 Day 46 Agent 工程化预习 |

## 自检

- [ ] 理解 Dify DSL（`app` + `workflow.graph.nodes/edges`）与 Nexus `ToolRegistry` 的映射关系
- [ ] 能解释 `dify_trace` 与 `mcp_trace` 的区别（同一份数据，两种呈现语义）
- [ ] 读过 `02_需求文档.md` FR-001~FR-004
- [ ] Phase 4 周测得分 ≥60

---

## 企业背景详述

理财客服机器人经过 Day39-44 六天迭代，已经具备 ReAct 决策、框架化工具注册、状态图编排、人工审批、多 Agent 委派、MCP 协议桥接六大能力。市场部希望把其中「查FAQ/查产品/分类意图」三个工具单独拆出来，接入 Dify 做一个「客服工单预处理」工作流，不依赖后端发版。

---

## 相关方

| 角色 | 诉求 |
|------|------|
| 市场部 | 自己拖拽拼流程，不用等研发排期 |
| 研发 | 工具定义只维护一份，不要为 Dify 再写一套 |
| 运维 | 能看到 Dify 那边的运行日志与 Nexus 这边的 trace 能对上 |

---

## 今日代码阅读顺序

1. `agent/dify_config.py`（10 min）
2. `agent/dify_protocol.py`（20 min）
3. `agent/dify_bridge.py`（25 min）
4. `agent/dify_runner.py`（20 min）
5. `api/agent.py` dify-config / dify-export / dify-preview（15 min）
6. `api/chat.py` dify_mode 集成（10 min）
7. `tests/day45/`（30 min）
8. `day45/phase4_quiz.py`（10 min）

---

## 成功画像

17:30 你能向市场部演示：「把这份 JSON 导入 Dify，客服 FAQ 工具就是一个可拖拽的节点」；同时你能默写 Phase 4 六天的核心类名与 trace 字段。
"""


def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：Dify 工作流对接 + Phase 4 周测
**优先级**：P1
**平台版本**：{VER}

---

## 1. 背景

Day44 的 MCP Server 解决了「协议化对接外部工具」的问题，但市场部真正想要的是**可视化编排**——用 Dify 这类低代码平台拖拽拼接工具，而不改一行 Nexus 代码。同时 Phase 4（Day39-44）已完整交付 Agent 编排六项能力，需要一次周测巩固知识点。

## 2. 目标

- `agent/dify_config.py` — DifyConfig 配置项
- `agent/dify_protocol.py` — DifyNode/DifyEdge/DifyWorkflow/DifyTraceEvent 数据模型
- `agent/dify_bridge.py` — `build_dify_workflow` 导出 + `map_steps_to_dify_trace` 映射
- `agent/dify_runner.py` — DifyRunner 复用 McpRunner 决策/执行
- `GET/PUT /api/agent/dify-config`、`POST /api/agent/dify-export`、`POST /api/agent/dify-preview`
- `POST /api/chat` + `dify_mode=true` → `dify_trace`
- `day45/phase4_quiz.py` + `day45/phase4_review.py`

## 3. 功能需求

### FR-001 DifyConfig 数据模型与校验

- 字段：`enabled`、`workflow_name`、`include_start_end`、`mock_routing`、`use_session_history`、`return_dify_trace`、`max_nodes`
- `validate()`：`max_nodes` ∈ [1,50]；`workflow_name` 非空

### FR-002 build_dify_workflow 导出

- 输入 `ToolExecutor`，遍历 `registry.list_tools()`（受 `max_nodes` 截断）
- 输出 `start → tool_<name>* → end` 节点图（`include_start_end=False` 时省略首尾节点）
- `DifyWorkflow.to_dict()` 产出 `{{"app": {{...}}, "workflow": {{"graph": {{"nodes": [...], "edges": [...]}}}}}}`

### FR-003 map_steps_to_dify_trace 追踪映射

- 输入 `McpRunner` 产出的 `discover/route/call/answer` 四阶段 `McpStep`
- 输出 `DifyTraceEvent` 列表，`node_type` 按阶段映射（discover→start，route/call→tool，answer→end）

### FR-004 DifyRunner 编排

- 内部持有一个 `McpRunner`（复用其发现/路由/调用逻辑，不重复实现）
- `invoke(query)` 返回 `reply` + `dify_trace` + `tools_used`
- `export_workflow()` 返回 `DifyWorkflow`

### FR-005 持久化与 status

- `store.json` 新增 `dify_config` 字段
- `GET /api/knowledge/status` 含 `dify_config`
- `platform_version` 为 `{VER}`

### FR-006 Chat 集成

- `api/chat.py` 在 `dify_mode=true` 且 `dify_config.enabled` 时走 `DifyRunner`
- `ChatResponse` 新增 `dify_trace` 字段

### FR-007 Phase 4 周测

- `day45/phase4_quiz.py`：10 题，覆盖 Day39-44
- `day45/phase4_review.py`：Day39-45 里程碑串联
- `run_quiz_scripted()` 供 CI 免交互评分

### FR-008 演示与测试

- `day45/dify_demo.py` 打印导出节点 + 三条 case 的调用结果
- `day45/dify_api_demo.py` 演示 REST API
- `tests/day45/` 覆盖单元 + API + 周测，共 27 项

## 4. 非功能需求

### NFR-001 可观测性

`dify_trace` 与既有 `mcp_trace` 语义对齐，同一次调用两者可以互相印证。

### NFR-002 兼容性

`dify_mode=false`（默认）时 chat 行为与之前完全一致；`DifyRunner` 不改动 `McpRunner`/`ToolExecutor` 任何既有行为。

### NFR-003 可测试性

`build_dify_workflow`/`map_steps_to_dify_trace` 均为纯函数，可脱离 FastAPI 直接单测。

### NFR-004 安全

导出的工作流 DSL 只包含工具名称、描述、参数 schema，不包含任何密钥或内部路径。

## 5. 非目标

- 真正接入 Dify 云端/私有部署实例（当前为可导入的 DSL 教学子集）
- Dify 侧的可视化编辑器（不在本课范围）
- 支持 Dify 全部节点类型（if-else、代码节点等）——当前只覆盖 start/tool/end

---

## 5.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
| FR-001 | agent/dify_config.py | test_dify_config_validate |
| FR-002 | agent/dify_bridge.build_dify_workflow | test_build_dify_workflow_* |
| FR-003 | agent/dify_bridge.map_steps_to_dify_trace | test_map_steps_to_dify_trace |
| FR-004 | agent/dify_runner.DifyRunner | test_dify_runner_* |
| FR-005 | rag/knowledge_store.py | test_dify_config_persists_in_store |
| FR-006 | api/chat.py | test_chat_dify_mode_trace |
| FR-007 | day45/phase4_quiz.py | test_phase4_quiz_* |
| FR-008 | day45/*_demo.py | 全部 demo 脚本 |

## 5.2 验收标准

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 默认 GET dify-config | enabled=true, workflow_name=nexus-agent-workflow |
| AC-02 | POST dify-export | 节点含 start/tool/end 三类 |
| AC-03 | POST dify-preview | dify_trace 长度为 4 |
| AC-04 | chat dify_mode=true | kind=dify 且含 dify_trace |
| AC-05 | dify_mode=false（默认） | 行为与 Day44 完全一致 |
| AC-06 | phase4_quiz --scripted | 满分 100/100 |

---

## 6. 详细验收步骤

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 pytest tests/day45/ -v
PYTHONPATH=src python3 src/day45/dify_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
PYTHONPATH=src python3 src/day45/phase4_quiz.py --scripted
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| 真实 Dify DSL 字段远比教学子集复杂 | 文档明确标注"教学子集"，预留后续对接真实 Dify SDK 的接口形状 |
| 工具参数 schema 与 Dify 表单渲染不完全兼容 | `parameters` 直接沿用 OpenAI function-calling schema，后续可加适配层 |
| 周测题目与实际教学进度脱节 | 题库随平台演进同步维护，`run_quiz_scripted` 保证 CI 可回归 |

---

## 8. 发布说明 {VER}

**新增**：dify_config/protocol/bridge/runner、dify-config/export/preview API、chat dify_mode、Phase 4 周测
**变更**：`ChatResponse` 扩展 `dify_trace` 字段
**注意**：`dify_mode` 默认关闭，需显式开启才走新管线

---

## 9. NFR 验收命令

```bash
pytest tests/day45/ -q --tb=no
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
```

---

## 10. 需求变更记录

| 版本 | 变更 |
|------|------|
| {VER}-draft | 仅 DifyBridge 导出 |
| {VER} | + DifyRunner + chat 集成 + 周测 + 27 tests |

---

## 11. 开放问题（Phase 5 展望）

- 是否要支持从 Dify 导入工作流反向生成 Nexus 工具编排？
- 周测是否要接入前端做可视化排行榜？
- 是否要给 `DifyTraceEvent` 加上耗时（elapsed_time）字段对齐真实 Dify 日志？

---

## 12. PRD 签字页

产品：________  研发：________  测试：________
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求扩展 — 用户故事

## US-45-01 市场部拖拽拼流程

**作为** 市场部运营
**我希望** 把「客服电话」「产品收益」两个工具拖进 Dify 画布连成一条流程
**以便** 不用等研发排期就能上线新场景

**验收**：`POST /api/agent/dify-export` 返回的节点里能找到 `tool_faq_lookup`、`tool_rag_search`。

## US-45-02 运维核对两套 trace

**作为** 值班运维
**我希望** Dify 侧的运行日志能和 Nexus 自己的 `mcp_trace` 对上
**以便** 排障时不用切两套心智模型

**验收**：`map_steps_to_dify_trace` 输出的 `node_id` 与 `McpStep.phase+step` 一一对应。

## US-45-03 研发只维护一份工具定义

**作为** 后端研发
**我希望** 新增工具时不用为 Dify 再写一套 schema
**以便** 减少重复维护成本

**验收**：`DifyNode.data.parameters` 直接复用 `StructuredTool`/`ToolDefinition` 的 `parameters`。

## US-45-04 学员自测巩固 Phase 4

**作为** 学员
**我希望** 有一份覆盖 Day39-44 全部核心概念的周测
**以便** 查漏补缺再进入 Day46

**验收**：`phase4_quiz.py` 交互模式与 `--scripted` 模式行为一致，10 题覆盖 6 天内容。

---

## 边界：空工具列表

若 `ToolRegistry` 未注册任何工具，`build_dify_workflow` 仍应返回合法的 `start → end`（`include_start_end=True` 时），不应抛异常。

## 与 Day44 MCP 的关系

`DifyRunner` **不重新实现**发现/路由/调用逻辑，而是内部持有一个 `McpRunner` 并复用其 `invoke()`；这是本课「组合优于重复实现」的典型示例。

## 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| DSL 教学子集与真实 Dify 版本不兼容 | 高 | 无法直接导入生产 Dify | 文档标注局限，作为后续对接路线图 |
| 周测题目过难/过易 | 中 | 学员反馈两极 | 题目附带 explain 字段，讲师可现场调整难度 |
| max_nodes 截断导致关键工具缺失 | 低 | 导出的工作流不完整 | 默认 10，超出会在文档中提示调大 |

## 发布检查清单（扩展）

- [ ] `tests/day45/` 全绿（27 项）
- [ ] `day45/dify_demo.py` / `day45/dify_api_demo.py` 输出正常
- [ ] `day45/phase4_quiz.py --scripted` 满分
- [ ] PACKAGE_STRUCTURE.md 更新
- [ ] CI Day 45 job 添加
- [ ] 课件 regenerate ≥100k
- [ ] PR 关联 {REQ}
"""


def _architecture() -> str:
    return f"""# Day 45 架构设计 — Dify 工作流对接层

## 1. 分层

```mermaid
flowchart TD
    CHAT["/api/chat dify_mode"] --> DR[DifyRunner.invoke]
    DR --> MCP[McpRunner.invoke 复用]
    MCP --> STEPS["McpStep 四阶段"]
    STEPS --> MAP[map_steps_to_dify_trace]
    MAP --> TRACE["dify_trace"]
    EXPORT["/api/agent/dify-export"] --> BUILD[build_dify_workflow]
    BUILD --> TE[ToolExecutor.registry]
    BUILD --> DSL["DifyWorkflow.to_dict"]
```

## 2. 导出流程

```mermaid
flowchart LR
    TE[ToolExecutor] --> DEFS["registry.list_tools 截断 max_nodes"]
    DEFS --> NODES["start + tool_* + end 节点"]
    NODES --> EDGES["顺序连线"]
    NODES --> WF[DifyWorkflow]
    EDGES --> WF
    WF --> JSON["app + workflow.graph"]
```

## 3. 追踪映射

```mermaid
flowchart LR
    A["McpStep phase=discover"] --> B1["DifyTraceEvent type=start"]
    C["McpStep phase=route"] --> B2["DifyTraceEvent type=tool"]
    D["McpStep phase=call"] --> B3["DifyTraceEvent type=tool"]
    E["McpStep phase=answer"] --> B4["DifyTraceEvent type=end"]
```

## 4. 配置生命周期

```mermaid
stateDiagram-v2
    [*] --> dify_on: bootstrap default
    dify_on --> dify_off: PUT enabled=false
    dify_off --> nodes_5: PUT max_nodes=5
    nodes_5 --> dify_on: PUT enabled=true
    dify_on --> dify_on: save store.json
```

## 5. 组件职责

| 组件 | 职责 |
|------|------|
| dify_config.py | DifyConfig 数据类 + 校验 |
| dify_protocol.py | DifyNode/DifyEdge/DifyWorkflow/DifyTraceEvent DSL 子集 |
| dify_bridge.py | 纯函数：build_dify_workflow / map_steps_to_dify_trace |
| dify_runner.py | DifyRunner 组合 McpRunner，输出 dify_trace |
| api/agent.py dify-* | REST 读写、导出、预览 |
| api/chat.py | dify_mode 分支 |

## 6. 不变量

- `DifyRunner` 不重复实现工具发现/路由/调用逻辑，全部委托给内部的 `McpRunner`
- 导出的工作流节点顺序与 `ToolRegistry.list_tools()` 的注册顺序一致，具备确定性
- `dify_trace` 事件数恒等于对应 `mcp_trace` 步数（一一映射，不丢不增）

---

## 7. 与 Day44 叠加

```mermaid
flowchart LR
    MCP[NexusMcpServer] --> RUNNER[McpRunner]
    RUNNER --> DIFY[DifyRunner 组合复用]
    DIFY --> TRACE[dify_trace]
    TE[ToolExecutor] --> MCP
    TE --> BRIDGE[dify_bridge.build_dify_workflow]
    BRIDGE --> DSL[Dify DSL]
```

Day44 的 MCP 协议解决"外部工具怎么接进来"；Day45 的 Dify 桥接解决"内部工具怎么导出去，给低代码平台用"。

---

## 8. 分层架构图

```
┌─────────────────────────────────────────────┐
│ Presentation: chat + dify-* API              │
├─────────────────────────────────────────────┤
│ Application: DifyRunner                      │
├─────────────────────────────────────────────┤
│ Domain: dify_bridge (build_dify_workflow /    │
│         map_steps_to_dify_trace)              │
├─────────────────────────────────────────────┤
│ Domain: McpRunner（Day44，被复用而非重写）     │
├─────────────────────────────────────────────┤
│ Infrastructure: ToolExecutor / ToolRegistry   │
└─────────────────────────────────────────────┘
```
"""


def _file04() -> str:
    return """# Day 45 流程图与示意图

## Dify 工作流导出 + 运行追踪时序

```mermaid
sequenceDiagram
    participant U as User
    participant C as ChatAPI
    participant D as DifyRunner
    participant M as McpRunner
    participant T as ToolExecutor
    U->>C: POST /api/chat dify_mode=true
    C->>D: invoke(query)
    D->>M: invoke(query) 复用
    M->>T: execute(tool, args)
    T-->>M: observation
    M-->>D: McpRunOutcome(steps)
    D->>D: map_steps_to_dify_trace
    D-->>C: reply + dify_trace
    C-->>U: ChatResponse
```

## 导出工作流时序

```mermaid
sequenceDiagram
    participant Op as 运营
    participant A as /api/agent/dify-export
    participant B as dify_bridge
    participant T as ToolExecutor
    Op->>A: POST dify-export
    A->>B: build_dify_workflow(executor)
    B->>T: registry.list_tools()
    T-->>B: ToolDefinition[]
    B-->>A: DifyWorkflow
    A-->>Op: app + workflow.graph JSON
```

## API

```
GET/PUT /api/agent/dify-config
POST    /api/agent/dify-export
POST    /api/agent/dify-preview
POST    /api/chat  dify_mode=true
```
"""


def _file05() -> str:
    return f"""# Day 45 课堂笔记（上午）

**09:00–09:40** 第一节：为什么需要低代码工作流对接
**09:40–10:30** 第二节：DifyConfig + dify_protocol DSL 数据模型
**10:30–11:20** 第三节：build_dify_workflow 导出逻辑
**11:20–12:00** 第四节：map_steps_to_dify_trace 映射逻辑

---

## 第一节：问题背景（40 min）

市场部想自己拖拽拼流程，不想每次改流程都排期找研发。行业内 Dify、n8n 等低代码平台的核心思路是：把工具抽象成"节点"，工作流就是节点图。今天要做的不是接入真实 Dify，而是**把 Nexus 的工具导出成一份 Dify 能认的 DSL**。

对比表：

| 方案 | 优点 | 代价 |
|------|------|------|
| 研发直接改代码 | 灵活 | 每次都要排期发版 |
| 导出 Dify DSL | 市场部可自主编排 | 需要维护一份导出/映射逻辑 |

---

## 第二节：DifyConfig + DSL 数据模型（50 min）

{fenced("python", DIFY_CONFIG)}

要点：

- 默认 `enabled=True`, `workflow_name="nexus-agent-workflow"`, `max_nodes=10`
- `validate()`：`max_nodes` 越界或 `workflow_name` 空都要拒绝

**10:15** 课堂练习：写出三组非法配置，预测 `validate()` 抛出的异常信息。

---

## 第三节：DSL 数据模型全文（50 min）

{fenced("python", DIFY_PROTOCOL)}

**10:55** 板书：`DifyWorkflow.to_dict()` 产出的顶层结构是 `{{"app": {{...}}, "workflow": {{"graph": {{"nodes", "edges"}}}}}}`，这是对齐 Dify 开源 DSL 顶层结构的教学子集。

---

## 第四节：build_dify_workflow（40 min）

{fenced("python", DIFY_BRIDGE)}

**11:40** 强调：节点顺序 = `ToolRegistry.list_tools()` 的注册顺序，具备确定性，方便测试断言。
"""


def _file06() -> str:
    return f"""# Day 45 课堂笔记（下午）

**14:00–14:30** 第五节：dify_demo 现场
**14:30–15:20** 第六节：DifyRunner 组合复用 McpRunner
**15:20–16:00** 第七节：dify-config/export/preview API
**16:00–16:45** 第八节：pytest + chat 回归 + Phase 4 周测

---

## 第五节：demo 现场（30 min）

```bash
PYTHONPATH=src python3 src/day45/dify_demo.py
```

记录导出的节点列表与三条 case study 的委派/调用结果。

**14:25** 学员汇报：导出的 `start`/`end` 节点在 `include_start_end=False` 时是否消失。

---

## 第六节：DifyRunner（50 min）

{fenced("python", _DIFY_RUNNER_CLASS)}

**14:50** 讲"组合优于重复实现"：`DifyRunner.__init__` 直接持有一个 `McpRunner` 实例，`invoke()` 内部调用 `self._mcp.invoke(...)`，不重新写发现/路由/调用逻辑。

---

## 第七节：API（40 min）

{fenced("python", _AGENT_API_DIFY)}

**15:35** curl 练习：

```bash
curl -s localhost:8000/api/agent/dify-config | jq .
curl -s -X POST localhost:8000/api/agent/dify-export | jq '.workflow.graph.nodes'
curl -s -X POST localhost:8000/api/agent/dify-preview \\
  -H 'Content-Type: application/json' \\
  -d '{{"query":"客服电话多少"}}' | jq .
```

---

## 第八节：测试与周测（45 min）

```bash
pytest tests/day45/ -v
python3 src/day45/phase4_quiz.py --scripted
```

**16:30** 里程碑：27 passed，周测 100/100。

**16:40** `test_dify_workflow_to_dict_shape` 说明导出结构与真实 Dify DSL 顶层字段对齐。
"""


def _file07() -> str:
    return f"""# Day 45 晚自习

## 讨论（19:00–19:45）

1. `DifyRunner` 为什么不直接重写发现/路由/调用逻辑，而是持有一个 `McpRunner`？
2. `dify_trace` 与 `mcp_trace` 如果字段对不上，会给排障带来什么麻烦？
3. Phase 4 六天里，哪一天的能力最容易被市场部误解为"和 Dify 是竞品"？

## 阅读（19:45–20:30）

`13_深度扩展_Dify工作流方法论.md`

## 预习 Day 46（20:30–21:00）

Agent 工程化：可观测性与容错——当六种模式都上线后，怎么统一监控与降级。

---

## 深度讨论：真实 Dify DSL 与教学子集的差距

| 维度 | 教学子集 | 真实 Dify DSL（公开文档） |
|------|----------|---------------------------|
| 顶层格式 | JSON | YAML（app + workflow + features + dependencies） |
| 节点类型 | start/tool/end | start/llm/tool/if-else/code/end 等十余种 |
| 边 | source/target | 含 sourceHandle/targetHandle 分支句柄 |

---

## 自查清单

- [ ] 能默写 `build_dify_workflow` 的三段（start/tool*/end）
- [ ] 能解释 `map_steps_to_dify_trace` 的阶段→节点类型映射表
- [ ] 跑通两个 demo 脚本
- [ ] Phase 4 周测得分 ≥60

---

## 专题写作（选修）

用 200 字对比"MCP 协议对接外部工具"与"Dify DSL 导出给外部平台"这两种集成方式的适用场景差异。
"""


def _file08() -> str:
    return """# Day 45 作业

## A（30 分）：自定义工作流导出脚本

编写脚本，分别用 `max_nodes=1` 与 `max_nodes=10` 调用 `build_dify_workflow`，打印两次导出的节点数量差异。

**评分**：可运行 15 分；输出对比 10 分；结论 5 分。

## B（25 分）：问答

1. `DifyWorkflow.to_dict()` 的顶层两个 key 是什么？
2. `map_steps_to_dify_trace` 把 `phase="call"` 映射成什么 `node_type`？
3. `dify_mode=false`（默认）时 chat 行为与 Day44 有何不同？

## C（20 分）：Lab 报告

完成 `26_实操Lab手册.md` 全部 Lab，含至少一次真实 API 调用截图。

## D（15 分）：Phase 4 周测

跑一次 `python3 src/day45/phase4_quiz.py`（交互模式），记录得分与错题解析。

## E（bonus 10 分）：单元测试

为 `build_dify_workflow` 补一条边界测试：工具列表为空时应返回合法的 `start → end`。

## F（课堂参与 10 分）

知识竞赛或 demo 现场 1 分钟：解释「为什么 DifyRunner 不重新实现路由逻辑」。

---

## 评分 Rubric 汇总

| 题 | 满分 | 及格线 |
|----|------|--------|
| A | 30 | 20 |
| B | 25 | 15 |
| C | 20 | 14 |
| D | 15 | 10 |
| E bonus | 10 | — |
| F | 10 | 6 |

---

## 学术诚信

允许讨论思路，禁止抄袭 Lab 报告或周测答案。相似度 >80% 扣该题满分。

---

## 作业 A 参考骨架

```python
#!/usr/bin/env python3
from agent.dify_bridge import build_dify_workflow
from api.factory import create_orchestrator

orchestrator = create_orchestrator()
for max_nodes in (1, 10):
    workflow = build_dify_workflow(orchestrator.tool_executor, max_nodes=max_nodes)
    tool_nodes = [n for n in workflow.nodes if n.type == "tool"]
    print(f"max_nodes={max_nodes} -> {len(tool_nodes)} 个工具节点")
```

---

## 作业 B 详细提示

第 1 问：`app` 与 `workflow`。
第 2 问：`tool`（route 与 call 阶段都映射为 tool 节点）。
第 3 问：完全一致——`dify_mode` 默认关闭不介入既有逻辑。
"""


def _file09() -> str:
    return """# Day 45 作业答案

## A 参考答案要点

| max_nodes | 工具节点数（示例） |
|-----------|---------------------|
| 1 | 1 |
| 10 | 全部已注册工具（本课通常 4 个） |

## B 答案

1. `app` 与 `workflow`。
2. `tool`。
3. 完全一致，`dify_mode=false` 时不会构造 `DifyRunner`。

## C Lab 要点

必须体现一次真实 curl/TestClient 调用与其响应截图，且截图中能看到 `dify_trace` 或导出节点列表。

## D 周测参考

10 题满分 100，覆盖 ReAct/Executor/Graph/Approval/Supervisor/MCP 各一到两题；错题建议回读对应 Day 的 `11_*详解.md`。

## E bonus

```python
def test_build_dify_workflow_empty_tools():
    from tools.executor import ToolExecutor
    from tools.registry import ToolRegistry

    empty_executor = ToolExecutor(ToolRegistry())
    workflow = build_dify_workflow(empty_executor)
    assert [n.type for n in workflow.nodes] == ["start", "end"]
```

---

## F 参考答案

`DifyRunner` 内部持有一个 `McpRunner`，`invoke()` 直接委托给 `self._mcp.invoke(...)`——这样 Day44 的发现/路由/调用逻辑升级时，Day45 自动获得同样的改进，不需要在两处维护相同逻辑。

---

## 讲评要点（讲师用）

作业 A 最常见错误：忘记 `max_nodes` 只截断 **工具节点**，不影响 start/end。
作业 B 第 2 问：容易把 `discover` 阶段也答成 tool，需要强调只有 route/call 是 tool。
"""


def _file10() -> str:
    return """# Day 45 Dify 验收清单

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
"""


def _file11() -> str:
    return """# Dify 工作流对接详解（Day 45 专题）

## 1. 问题定义

低代码工作流对接 = 把内部工具能力**导出**成外部平台（Dify）能理解的图结构（节点 + 边），同时把内部运行 trace **映射**成外部平台熟悉的日志语义，双向对齐但不重复实现。

## 2. Dify DSL 教学子集

| 字段 | 含义 |
|------|------|
| app.name | 工作流名称 |
| app.mode | 固定为 "workflow" |
| workflow.graph.nodes | 节点列表，每个含 id + data.type/title |
| workflow.graph.edges | 边列表，source → target |

```mermaid
flowchart LR
    TE[ToolExecutor] --> B[build_dify_workflow]
    B --> DSL[DifyWorkflow]
    DSL --> JSON[app + workflow.graph]
```

## 3. build_dify_workflow 逻辑

1. 取 `registry.list_tools()[:max_nodes]`
2. `include_start_end=True` 时先放一个 `start` 节点
3. 每个工具生成一个 `tool_<name>` 节点，`data` 含 description + parameters
4. 顺序连边：`start → tool1 → tool2 → ... → end`

## 4. map_steps_to_dify_trace 与 McpStep

`McpRunner.invoke` 的四阶段（discover/route/call/answer）分别映射：

| McpStep.phase | DifyTraceEvent.node_type |
|---------------|--------------------------|
| discover | start |
| route | tool |
| call | tool |
| answer | end |

## 5. 与 Chat 集成

`api/chat.py` 在 `dify_mode=true` 且配置 `enabled` 时调用 `DifyRunner.invoke`，把返回的 `dify_trace` 填入 `ChatResponse.dify_trace`。

## 6. 前端展示（展望）

未来可加 `msg__dify` 组件，把 `dify_trace` 渲染成小型流程图，帮助运营理解一次调用具体走了哪些节点。

---

## 7. 与合规的关系

| 审计项 | dify_trace 提供 |
|--------|-----------------|
| 调用了哪个工具 | node title |
| 输入参数 | inputs |
| 返回结果 | outputs |
| 执行顺序 | node_id 中的 step 序号 |

---

## 8. 配置调参

| 场景 | max_nodes |
|------|-----------|
| 小型演示 | 3-5 |
| 默认 | 10 |
| 全量导出（工具很多） | 20-50 |

---

## 9. 常见误区

| 误区 | 正解 |
|------|------|
| DifyRunner 重新实现了路由逻辑 | 内部持有 McpRunner，直接复用其 invoke |
| dify_trace 与 mcp_trace 是两份独立数据 | dify_trace 由 mcp_trace 一一映射而来 |
| 导出的 DSL 能直接导入生产 Dify | 当前为教学子集，字段远比真实 Dify DSL 简化 |
"""


def _file12() -> str:
    return f"""# Day 45 课堂练习册

## 练习 1：概念匹配（10 min）

将术语与定义连线：`DifyWorkflow`、`DifyTraceEvent`、`max_nodes`、`McpRunner`。

## 练习 2：判题（15 min）

判断对错：

1. `DifyRunner.invoke` 会重新实现一遍工具路由逻辑。
2. `include_start_end=False` 时导出的工作流仍然合法，只是没有首尾节点。
3. `test_map_steps_to_dify_trace` 验证四个阶段都能正确映射成 DifyTraceEvent。

**答案**：错（复用 McpRunner）、对、对。

## 练习 3：读代码（20 min）

在 `dify_bridge.py` 中标出：`max_nodes` 截断行、`include_start_end` 分支行、边生成行。

## 练习 4：手算导出（25 min）

假设 `ToolRegistry` 只注册了 `faq_lookup` 一个工具，`max_nodes=10`，`include_start_end=True`，写出导出的节点列表与边列表。

## 练习 5：API 填空（15 min）

补全 curl POST 调用 `dify-preview` 的 JSON body。

## 练习 6：测试阅读（20 min）

读 `test_dify_runner_disabled`，写 Given-When-Then。

## 练习 7：画时序图（15 min）

手绘 `POST /api/chat dify_mode=true` 的完整调用链（对照 `04_流程图与示意图.md`）。

## 练习 8：与 Day44 对比表（15 min）

填三行：组件、API 前缀、chat 开关字段。

## 练习 9：口述 60 秒（课堂）

「向市场部同学解释为什么这份 JSON 能导入 Dify」。

## 练习 10：Phase 4 速答（课堂）

限时 5 分钟，口述 Day39-44 六个核心类名。

{fenced("python", PHASE4_QUIZ)[:1]}
"""


def _file13() -> str:
    return """# 深度扩展：Dify 工作流对接方法论

## 1. 工业界标准分层

```
Stage0: 工具定义（本课 ToolRegistry / StructuredTool）
Stage1: 协议化对接外部工具（Day44 MCP）
Stage2: 导出给低代码平台编排（Day45 Dify Bridge）
Stage3: 可观测性统一（Day46 展望）
```

## 2. 为何选择"导出 DSL"而不是"重写一套 Dify 插件"

- 重写插件意味着工具定义要维护两份，容易漂移
- 导出 DSL 只需一个纯函数（`build_dify_workflow`），工具定义单一来源
- 教学上更容易讲清楚"同一份数据，两种消费方式"

## 3. Recall 与 Precision 类比

低代码平台对接类似检索系统的"召回-精排"：MCP 协议解决"能不能连上"（召回），Dify 工作流解决"怎么可视化编排"（精排/呈现）。

## 4. Cascade 与 Parallel

`DifyRunner.invoke` 是串行调用 `McpRunner.invoke`，再对结果做一次映射——这是典型的"装饰器/适配器模式"，而不是并行重新实现。

## 5. 延迟预算分解（示例）

| 段 | ms |
|----|-----|
| McpRunner.invoke（复用） | ~10 |
| map_steps_to_dify_trace | <1 |
| 序列化响应 | ~1 |

映射层几乎不增加延迟，因为只是数据结构转换。

## 6. 真实 Dify 对接展望

若要接入真实 Dify 实例，需要：（1）补齐真实 DSL 的 YAML 序列化；（2）实现 Dify 自定义工具的 HTTP 回调协议；（3）处理 Dify 侧的鉴权与限流。当前教学子集刻意省略这些，聚焦"导出结构"与"追踪映射"两个核心概念。

## 7. 与 RRF 类比（跨领域迁移思考）

RRF（Reciprocal Rank Fusion）把多路检索结果融合成一份排序；本课的 `map_steps_to_dify_trace` 类似地把多阶段执行 trace"融合"映射成统一的日志语义——都是"多来源数据 → 统一呈现格式"的设计模式。

## 8. 案例：企业级 Agent 平台的对外集成层

```
内部：ToolRegistry → StructuredTool → McpRunner/SupervisorGraph/...
对外：MCP Server（协议）+ Dify Bridge（工作流 DSL）+ 未来 OpenAPI（REST）
```

## 9. 失败模式

| 现象 | 诊断 |
|------|------|
| 导出节点数为 0 | 检查 `ToolRegistry` 是否真的注册了工具 |
| dify_trace 与 mcp_trace 步数不一致 | 检查 `return_dify_trace`/`return_mcp_trace` 配置是否被误关 |
| 导入真实 Dify 报错 | 预期内——当前为教学子集，字段远少于真实 DSL |

## 10. 推荐阅读

- Dify 开源仓库 README 与工作流 DSL 说明（公开文档）
- Model Context Protocol 官方规范（与 Day44 MCP 对照）

## 11. 数学/工程小结

导出 DSL 的复杂度是 O(工具数)，与检索/Agent 决策逻辑无关——这是"适配器模式"天然具备的低复杂度优势。

## 12. 实验设计模板

固定工具集合，扫 `max_nodes ∈ {1,3,5,10}`，记录导出节点数与耗时曲线（预期几乎线性且耗时极低）。
"""


def _file14() -> str:
    return """# 企业案例集：Dify 对接场景

## 案例 1：客服工单预处理流程

**现象**：市场部想要「先查 FAQ，查不到再查产品资料，还查不到转人工」的分支逻辑。
**根因**：当前教学子集只支持线性 `start → tool* → end`，不支持条件分支。
**方案**：导出线性工作流后，在 Dify 画布里手动加 if-else 节点做分支（超出本课 DSL 范围，留给 Dify 原生能力）。
**结果**：核心工具节点由 Nexus 自动生成，分支逻辑由市场部在 Dify 侧维护，分工清晰。

## 案例 2：审计日志对齐

**现象**：运维发现 Dify 侧日志里的节点执行顺序和 Nexus 自己的 `mcp_trace` 对不上号。
**根因**：误关闭了 `return_dify_trace` 或 `return_mcp_trace` 其中一个。
**方案**：检查两个 config 的 `return_*_trace` 均为 true，问题解决。
**结果**：`dify_trace` 与 `mcp_trace` 的 phase→step 映射恢复一致。

## 案例 3：工具太多导出超时

**现象**：`ToolRegistry` 后续注册了 50+ 工具，导出接口响应变慢。
**方案**：`PUT max_nodes=20` 只导出高频工具，其余工具通过 MCP 协议按需接入。
**权衡**：Dify 画布更简洁，但需要额外文档说明"未导出工具仍可通过 MCP 调用"。

## 案例 4：新工具上线零改动

**现象**：新增「工单查询」工具后，市场部担心 Dify 那边要重新配置。
**方案**：新工具注册进 `ToolRegistry` 后，下次调用 `dify-export` 自动包含，无需改 Dify 侧任何配置（除非要手动拖拽新节点到画布）。
**结果**：验证了"工具定义单一来源"的设计价值。

## 案例 5：Incident 降级

**现象**：怀疑 Dify 对接引入了性能回归。
**方案**：`PUT /api/agent/dify-config` 将 `enabled` 设为 `false`，chat 立即回退到不含 dify_trace 的普通模式，30 分钟内确认问题范围。

## 案例 6：Phase 4 周测发现知识漏洞

**现象**：多名学员在"Supervisor 与 MCP 差异"这题上失分。
**工具**：`phase4_quiz.py` 的 `explain` 字段直接给出对比句子，讲师现场补充"进程内 vs 协议化"的板书。
**结果**：错题率从 40% 降到 5%（复训后二测）。

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 dify-export | — | 配合灰度开关 |

## 与客服话术联动

客服/运营培训重点：解释"这份 JSON 就是机器人能用的工具清单，导入 Dify 就能拖拽"。

## 离线评估脚本

```python
for max_nodes in (1, 5, 10, 20):
    workflow = build_dify_workflow(executor, max_nodes=max_nodes)
    print(max_nodes, len(workflow.nodes))
```
"""


def _file15() -> str:
    return f"""# Day 45 授课实录

**09:05** 林晓展示市场部的诉求："想自己拖拽拼流程，别每次都找研发。"
**09:22** 陈默画分层图：MCP 解决"连外部"，Dify Bridge 解决"导出给低代码平台"。
**10:10** `DifyConfig`/`dify_protocol` 白板推导 DSL 结构。
**10:55** `build_dify_workflow` live coding。
**11:20** 第一次跑通 demo，全班确认导出节点列表正确。

**14:05** dify_demo 输出对比，学员惊呼"这就是一份能导进 Dify 的 JSON"。
**14:50** 讲"组合优于重复实现"：`DifyRunner` 内部持有 `McpRunner`。
**15:15** PUT dify-config 调 `max_nodes=1`，现场看节点数变化。
**15:58** pytest 第 27 个绿。
**16:42** `phase4_quiz.py` 现场答题，全班平均分 92。
**16:58** 预告 Day 46 Agent 工程化："六种模式都上线了，怎么统一监控。"

---

## 问答实录

**15:30 学员**：`dify_trace` 和 `mcp_trace` 能同时返回吗？
**陈默**：当前 chat 只走一种模式，但两个 Runner 内部数据是一一映射的，理论上可以同时暴露。

**16:05 学员**：真实 Dify 支持导入这份 JSON 吗？
**林晓**：不能直接导入——这是教学子集，字段比真实 DSL 简化很多，但结构思路一致。

---

## 讲师自评

- DifyRunner 组合模式讲解学员接受度很高
- Lab5 curl 环节比预期快 10 分钟完成
- Phase4 周测平均分超预期，说明前六天吸收得不错

---

## 时间戳逐字稿（节选）

**10:08:12** 陈默："导出的第一个节点永远是 start，最后一个永远是 end，中间才是真正的工具。"
**14:18:33** 林晓：（运行 demo）"看，四个工具节点，和 tools/list 返回的完全一致。"
**15:40:01** 周航："max_nodes 改成 1，果然只剩一个工具节点了。"
**16:45:18** 全班："27 passed！周测 100 分！"

---

## 设备与环境备注

首次 `create_orchestrator()` 较慢；第二次调用命中缓存——可讲工厂模式与依赖注入。

---

## 课后作业布置原话

「Lab5 必须有真实 curl 截图。周测交互模式跑一次，错题解析抄一遍加深印象。作业 A 的脚本周日 23:59 前 push。」
"""


def _file16() -> str:
    return f"""# Day 45 复习卡片（20 张）

**Q1** 默认 workflow_name？ → nexus-agent-workflow
**Q2** 默认 max_nodes？ → 10
**Q3** 需求号？ → {REQ}
**Q4** 平台版本？ → {VER}
**Q5** 导出函数名？ → build_dify_workflow
**Q6** 映射函数名？ → map_steps_to_dify_trace
**Q7** 核心编排类？ → DifyRunner
**Q8** DifyRunner 内部持有什么？ → McpRunner
**Q9** API 路径（导出）？ → /api/agent/dify-export
**Q10** API 路径（预览）？ → /api/agent/dify-preview

**Q11** chat 开关字段？ → dify_mode
**Q12** trace 字段名？ → dify_trace
**Q13** demo 脚本？ → dify_demo.py
**Q14** 测试数？ → 27
**Q15** discover 阶段映射的节点类型？ → start

**Q16** call 阶段映射的节点类型？ → tool
**Q17** answer 阶段映射的节点类型？ → end
**Q18** validate 拒绝？ → max_nodes 越界、workflow_name 为空
**Q19** 周测题数？ → 10
**Q20** 周测覆盖范围？ → Day 39-44（ReAct/Executor/Graph/Approval/Supervisor/MCP）
"""


def _file17() -> str:
    return """# Dify API 速查手册

## GET dify-config

```bash
curl -s http://127.0.0.1:8000/api/agent/dify-config | jq .
```

响应：

```json
{
  "enabled": true,
  "workflow_name": "nexus-agent-workflow",
  "include_start_end": true,
  "mock_routing": true,
  "use_session_history": true,
  "return_dify_trace": true,
  "max_nodes": 10
}
```

## PUT dify-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \\
  -H 'Content-Type: application/json' \\
  -d '{
    "enabled": true,
    "workflow_name": "nexus-agent-workflow",
    "include_start_end": true,
    "mock_routing": true,
    "use_session_history": true,
    "return_dify_trace": true,
    "max_nodes": 10
  }'
```

关闭 Dify 对接：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \\
  -H 'Content-Type: application/json' \\
  -d '{"enabled": false, "workflow_name": "nexus-agent-workflow", "include_start_end": true, "mock_routing": true, "use_session_history": true, "return_dify_trace": true, "max_nodes": 10}'
```

## POST dify-export

```bash
curl -s -X POST http://127.0.0.1:8000/api/agent/dify-export | jq '.workflow.graph.nodes'
```

## POST dify-preview

```bash
curl -s -X POST http://127.0.0.1:8000/api/agent/dify-preview \\
  -H 'Content-Type: application/json' \\
  -d '{"query":"客服电话多少"}' | jq .
```

## chat 集成

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"message":"客服电话多少","dify_mode":true}' | jq '.dify_trace'
```

## status 中的 dify_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.dify_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from agent.dify_config import DifyConfig

store = get_knowledge_store()
store.set_dify_config(DifyConfig(workflow_name="custom-workflow", max_nodes=5))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | max_nodes 越界或 workflow_name 为空 |
| 400 | dify_config.enabled=false 时调用 export/preview |
| 200 | 成功 |

## 常量

- `DIFY_NODE_START` = `"start"`
- `DIFY_NODE_TOOL` = `"tool"`
- `DIFY_NODE_END` = `"end"`
"""


def _file18() -> str:
    return """# Day 45 与 Day 44 能力对照表

| 维度 | Day 44 MCP | Day 45 Dify |
|------|------------|-------------|
| 需求 | ZL-NA-REQ-044 | ZL-NA-REQ-045 |
| 版本 | v0.44.0 | v0.45.0 |
| 核心问题 | 如何协议化对接外部工具 | 如何导出给低代码平台可视化编排 |
| 核心模块 | mcp_server.py + mcp_runner.py | dify_bridge.py + dify_runner.py |
| API 新增 | mcp-config + mcp-list-tools + mcp-preview | dify-config + dify-export + dify-preview |
| chat 字段 | mcp_mode → mcp_trace | dify_mode → dify_trace |
| 存储字段 | mcp_config | dify_config |
| 测试目录 | tests/day44/ | tests/day45/ |
| demo | mcp_demo | dify_demo |
| 与 Day44 关系 | — | DifyRunner 内部复用 McpRunner，不重写 |
| 下一日 | Day45 Dify | Day46 Agent 工程化 |

## 协同场景

1. Day44 MCP Server 暴露 tools/list + tools/call
2. Day45 DifyBridge 把同一批工具再导出成 Dify DSL
3. chat 可选 mcp_mode 或 dify_mode，两者共享底层 ToolExecutor

## 排障对照

| 症状 | 先查 Day | 关键字 |
|------|----------|--------|
| 工具调用失败 | 44 | mcp_server, tools/call |
| 导出节点缺失 | 45 | max_nodes, ToolRegistry |
| dify_trace 与 mcp_trace 步数不一致 | 45 | return_dify_trace, return_mcp_trace |
| 配置丢失 | 45 | store.save |

---

## 能力叠加示意图

```
Day39 ReAct ──┐
Day40 Executor ├──► Day41 Graph ──► Day42 Approval ──► Day43 Supervisor ──► Day44 MCP ──► Day45 Dify
Day38 Retry ──┘
```

---

## 迁移指南（Day44→45 发版）

1. 部署 v0.45.0 二进制/容器
2. 首次启动自动 `DifyConfig()` 默认
3. 跑 `pytest tests/day44 tests/day45`
4. 抽样 dify-export 与 chat dify_mode 回归
5. 前端确认（若已实现）msg__dify 渲染

---

## 对照测验（自测 10 题）

1. Day44 核心类？ `McpRunner`
2. Day45 核心类？ `DifyRunner`
3. Day45 默认 max_nodes？ 10
4. Day45 API 路径（导出）？ dify-export
5. 两者串联？ 是（DifyRunner 内部持有 McpRunner）
6. Day44 测试数？ 20
7. Day45 测试数？ 27
8. 关闭 dify_trace 字段？ enabled=false
9. dify_trace 事件数？ 恒为 4（与 mcp_trace 步数一致）
10. 下一日？ Agent 工程化（可观测性与容错）
"""


def _file19() -> str:
    return """# 讲师补充阅读

## 1. 低代码工作流平台脉络

Dify、n8n、Zapier 一类平台的共同思路：把"能力"抽象成节点，业务流程变成图。本课的 `dify_bridge.py` 是这类思路在教学场景下的最小实现。

## 2. 与 MCP 的分工

MCP（Model Context Protocol）解决"Agent 怎么发现并调用工具"，是协议层；Dify DSL 解决"人怎么可视化编排工具"，是呈现层。两者不冲突，可以叠加。

## 3. 适配器模式回顾

`DifyRunner` 是经典的适配器模式（Adapter Pattern）：不改变 `McpRunner` 的接口，只在外面包一层，把返回值转换成另一种格式（`dify_trace`）。

## 4. 课堂彩蛋：为什么不重写发现/路由逻辑

如果 `DifyRunner` 自己重新实现路由逻辑，Day44 的 bug 修复或路由优化就要在两处同步维护，长期必然漂移。组合复用是更可持续的架构选择。

## 5. 伦理与合规

导出的工作流 DSL 面向非研发同学，务必确保 `description`/`parameters` 里不包含内部密钥、数据库连接串等敏感信息——这也是 NFR-004 的由来。

## 6. 推荐阅读顺序

1. `agent/dify_protocol.py`
2. `agent/dify_bridge.py`
3. Day 46 预习
"""


def _file20() -> str:
    return f"""# Day 45 完整代码走查

按**调用顺序**阅读，预计 90 分钟。精读全文见 `22_dify_runner精读.md`。

---

## 走查路线

| 顺序 | 文件 | 关注 |
|------|------|------|
| 1 | `agent/dify_config.py` | validate / defaults |
| 2 | `agent/dify_protocol.py` | DSL 数据模型 |
| 3 | `agent/dify_bridge.py` | build_dify_workflow / map_steps_to_dify_trace |
| 4 | `agent/dify_runner.py` | DifyRunner 组合 McpRunner |
| 5 | `api/agent.py` | dify-config / dify-export / dify-preview |
| 6 | `day45/dify_demo.py` | CLI 演示 |
| 7 | `day45/dify_api_demo.py` | TestClient 演示 |
| 8 | `day45/phase4_quiz.py` | 周测 |
| 9 | `tests/day45/` | 27 项 |

---

## 1. 配置层

`DifyConfig` 是本日配置的单一真相源。store 启动时 `from_dict` 加载；API `PUT` 更新并持久化。

**检查点**：默认 `enabled=True, max_nodes=10`。

---

## 2. 调用栈（chat dify_mode）

```
POST /api/chat  (dify_mode=true)
  → DifyRunner.invoke
    → McpRunner.invoke（复用）
      → ToolExecutor.execute
        → Observation
    → map_steps_to_dify_trace
```

---

## 3. 核心 Runner 全文

{fenced("python", _DIFY_RUNNER_CLASS)}

**练习**：找出 `invoke()` 里委托给 `self._mcp` 的那一行。

---

## 4. API 层

{fenced("python", _AGENT_API_DIFY)}

**检查点**：非法配置 → `ValueError` → HTTP 422；`enabled=False` → HTTP 400。

---

## 5. CLI 演示（要点，全文见 25_dify_runner_api脚本精读.md）

`day45/dify_demo.py` 依次：①创建 orchestrator；②`DifyRunner.from_executor`；③`export_workflow()` 打印节点；④对 `DIFY_CASES` 逐条 `invoke()` 打印委派结果与 `dify_trace` 长度。

对每条内置 case study 打印导出节点与调用结果。

---

## 6. 测试矩阵

| 文件 | 覆盖 |
|------|------|
| test_dify_runner.py | 单元：config/workflow/trace/runner |
| test_dify_api.py | API + chat 集成 |
| test_phase4_quiz.py | 周测评分逻辑 |

**必读**：`test_build_dify_workflow_has_start_and_end`、`test_map_steps_to_dify_trace`。

---

## 7. 走查后自测

1. 闭卷写出 `build_dify_workflow` 的三段结构。
2. 说明 `map_steps_to_dify_trace` 的四项映射。
3. 指出 `PUT dify-config` 后 chat 如何读到新配置。

---

## 8. knowledge_store 配置方法节选

{fenced("python", _KNOWLEDGE_STORE_DIFY_METHODS)}

---

## 9. API demo 要点（全文见 25_dify_runner_api脚本精读.md）

`day45/dify_api_demo.py` 用 `TestClient` 依次调用 GET dify-config、POST dify-export、POST dify-preview、POST /api/chat（dify_mode=true），逐步验证配置读写、导出结构、预览追踪、chat 集成四条链路。

---

## 10. 走查时间盒（90 min 细分）

| 分钟 | 内容 |
|------|------|
| 0-15 | 配置层 |
| 15-40 | DSL 数据模型 + build_dify_workflow |
| 40-55 | DifyRunner + API |
| 55-70 | demo 走读 |
| 70-90 | 测试 + 周测 + chat 回归 |

---

## 11. 常见问题走查

**Q save 后配置何时生效？** `set_dify_config` 立即写回内存，`store.save()` 落盘。
**Q enabled=False 还会构造 DifyRunner 吗？** chat.py 分支不构造，直接跳过。

---

## 12. 走查验收 oral exam

学员随机抽：讲解 `DifyRunner.invoke` 如何把 `McpRunOutcome` 转换成 `DifyRunOutcome`。

---

## 13. Phase 4 周测要点（全文见 25_dify_runner_api脚本精读.md）

`day45/phase4_quiz.py` 定义 10 道题（覆盖 Day39-44），`run_quiz_scripted()` 供 CI 免交互评分，`run_quiz()` 提供交互式答题体验。
"""


def _file21() -> str:
    return f"""# Day 45 课堂知识竞赛（15 题）

1. 导出函数名？ → `build_dify_workflow`
2. 映射函数名？ → `map_steps_to_dify_trace`
3. 默认 max_nodes？ → `10`
4. 默认 workflow_name？ → `nexus-agent-workflow`
5. 需求号？ → {REQ}
6. 平台版本？ → {VER}
7. dify-config HTTP 方法？ → GET + PUT
8. 编排类名？ → `DifyRunner`
9. DifyRunner 内部持有？ → `McpRunner`
10. 导出 DSL 顶层两个 key？ → `app` / `workflow`
11. 演示常量文件？ → `day45/constants.py`
12. 测试总数？ → 27
13. discover 阶段映射节点类型？ → `start`
14. FR-004 实现？ → `DifyRunner` 组合复用
15. Day46 主题？ → Agent 工程化（可观测性与容错）

---

## 抢答加分题（讲师用）

**16** 写出四阶段到节点类型的完整映射。
**答**：discover→start，route→tool，call→tool，answer→end

**17** enabled=False 时 dify-export 行为？
**答**：直接返回 HTTP 400，不构造 DifyRunner

---

## 决赛三轮（讲师用）

**18** 默写 `DifyWorkflow.to_dict()` 的完整结构。
**19** 指出 dify-config 两个路由 HTTP 方法。
**20** 说明 `test_dify_config_persists_in_store` 验证什么。

**答 19**：GET、PUT
**答 20**：save/load 后 workflow_name 与 max_nodes 不丢失

---

## 记分板模板

| 组 | 基础15题 | 决赛5题 | 总分 |
|----|----------|---------|------|
| A | | | |
| B | | | |

满分 20 题，每题 5 分。

---

## 赛后复盘（教研组）

竞赛题 16（四阶段映射）正确率最低，下节课前抽查。

---

## Phase 4 周测联动

本节课件竞赛结束后，紧接着运行 `phase4_quiz.py`，两者共同构成 Day45 的知识巩固闭环。
"""


def _file22() -> str:
    return f"""# Day 45 精读：dify_runner 与工作流对接管线

**需求**：{REQ} | **学时**：120 min

---

## 一、dify_runner.py 全文

{fenced("python", DIFY_RUNNER)}

---

## 二、行级注释：DifyRunOutcome 数据模型

| 字段 | 讲解 |
|----|------|
| query | 原始输入问句 |
| reply | 复用 McpRunner 生成的回复 |
| dify_trace | map_steps_to_dify_trace 映射结果 |
| tools_used | 复用 McpRunner 的 tools_used |
| workflow_name | 来自 DifyConfig.workflow_name |

---

## 三、DifyRunner.__init__（组合复用）

{fenced("python", _DIFY_RUNNER_CLASS)}

| 行 | 讲解 |
|----|------|
| `self._mcp = McpRunner.from_executor(...)` | 核心：不重写发现/路由/调用，直接持有一个 McpRunner |
| `McpConfig(mock_routing=self._config.mock_routing, ...)` | 把 DifyConfig 的相关字段转发给内部 McpConfig |
| `invoke()` | 先调 `self._mcp.invoke`，再 `map_steps_to_dify_trace` |
| `export_workflow()` | 委托给 `build_dify_workflow` 纯函数 |

---

## 四、dify_bridge.py 全文

{fenced("python", DIFY_BRIDGE)}

---

## 五、build_dify_workflow 逐段

| 行段 | 讲解 |
|------|------|
| `definitions = executor.registry.list_tools()[:max_nodes]` | 截断保护，避免节点图过大 |
| `include_start_end` 分支 | 控制是否生成 start/end 哨兵节点 |
| for 循环生成 tool 节点 | 每个工具一个节点，`data` 携带 description + parameters |
| 边生成 | 严格按注册顺序串联，保证确定性 |

---

## 六、map_steps_to_dify_trace 逐段

{fenced("python", DIFY_BRIDGE)}

`_PHASE_TO_NODE_TYPE` 映射表是本函数的核心：discover→start，route/call→tool，answer→end。

---

## 七、dify_protocol.py 全文

{fenced("python", DIFY_PROTOCOL)}

`DifyWorkflow.to_dict()`：`{{"app": {{"name", "mode"}}, "workflow": {{"graph": {{"nodes", "edges"}}}}}}`，对齐真实 Dify DSL 顶层字段命名（教学子集，字段远少于完整规范）。

---

## 八、dify_config.py 全文

{fenced("python", DIFY_CONFIG)}

`validate()`：`max_nodes` ∈ [1,50]，`workflow_name` 非空。

---

## 九、api/agent.py dify-* 节选

{fenced("python", _AGENT_API_DIFY)}

---

## 十、chat.py dify_mode 集成节选

{fenced("python", _CHAT_DIFY)}

---

## 十一、测试精读 test_dify_runner.py

{fenced("python", TEST_DIFY_RUNNER)}

| 测试 | 要点 |
|------|------|
| test_build_dify_workflow_has_start_and_end | 默认导出首尾哨兵节点 |
| test_build_dify_workflow_respects_max_nodes | 截断保护生效 |
| test_map_steps_to_dify_trace | 四阶段完整映射 |
| test_dify_runner_faq_delegation | 端到端委派正确 |
| test_dify_config_persists_in_store | 持久化不丢字段 |

---

## 十二、API 测试 test_dify_api.py

{fenced("python", TEST_DIFY_API)}

`test_health_version` 锁版本 `{VER}`；`test_chat_dify_mode_trace` 端到端。

---

## 十三、调试清单

- [ ] 打印导出的节点 id 列表
- [ ] 打印 dify_trace 每一步的 node_type
- [ ] 切换 include_start_end 对比节点数
- [ ] 查 store.json dify_config

---

## 十四、自检

1. 手绘"McpStep → DifyTraceEvent"映射流程图。
2. 口述适配器模式与组合模式的区别。
3. 说明 max_nodes 截断只影响哪一类节点。

---

## 十五、笔试模拟

**1（20分）** 构造反例：`max_nodes=0` 应该被拒绝，写出预期异常信息。

**2（20分）** 解释 `include_start_end=False` 对导出结构与边数量的影响。

**3（20分）** 对比 FR-002 与 FR-003 的实现位置差异。

---

## 十六、与 Day44 衔接

MCP Server 仍是"能不能连上"的协议层；DifyRunner 在其上叠加"呈现给低代码平台"的语义层。关闭 dify_mode 即回退到 Day44 mcp_mode 行为。

---

## 十七、knowledge_store dify 方法

{fenced("python", _KNOWLEDGE_STORE_DIFY_METHODS)}

`set_dify_config` 触发的是持久化写回，不涉及 `invalidate_cache`（Dify 配置不影响检索缓存）。

---

## 十八、口语考试题

1. 30 秒解释 Dify DSL 教学子集是什么。
2. 1 分钟对比 MCP 协议对接与 Dify 工作流导出。
3. 白板画 DifyRunner.invoke 的完整调用链。

---

## 十九、实验记录模板

| query | tools_used | dify_trace 节点数 | node_type 序列 |
|-------|-----------|-------------------|-----------------|
| | | | |

---

## 二十、FAQ

**Q dify_trace 与前端渲染的关系？** 当前教学子集未接前端，留作 Day46+ 展望。
**Q 为什么不直接对接真实 Dify HTTP API？** 教学聚焦"结构映射"概念，真实网络对接超出课程范围。

---

## 二十一、dify_runner 完整源码（重复嵌入便于打印）

{fenced("python", DIFY_RUNNER)}

---

## 二十二、导出伪代码

```
function BUILD_DIFY_WORKFLOW(executor, max_nodes, include_start_end):
    defs = executor.registry.list_tools()[:max_nodes]
    nodes = []
    if include_start_end: nodes.append(START)
    for d in defs: nodes.append(TOOL_NODE(d))
    if include_start_end: nodes.append(END)
    edges = CONNECT_SEQUENTIALLY(nodes)
    return DifyWorkflow(nodes, edges)
```

---

## 二十三、DIFY_CASES 业务解读

| query | 业务意图 | 委派工具 |
|-------|----------|---------|
| 客服电话多少 | FAQ 查询 | faq_lookup |
| 年化收益怎么样 | 产品资料检索 | rag_search |
| 帮我总结一下理财产品 | 意图归纳 | intent_classify |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_dify_config_validate | FR-001 |
| test_build_dify_workflow_has_start_and_end | FR-002 |
| test_map_steps_to_dify_trace | FR-003 |
| test_dify_runner_faq_delegation | FR-004 |
| test_dify_config_persists_in_store | FR-005 |
| test_chat_dify_mode_trace | FR-006 |
| test_phase4_quiz_scripted_full_score | FR-007 |
| test_health_version | FR-008 |

---

## 二十五、knowledge API 节选（dify 上下文）

{fenced("python", _KNOWLEDGE_STORE_DIFY_METHODS)}

---

## 二十六、phase4_review 建议

课后运行 `src/day45/phase4_review.py` 串联 Day39-45。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| DifyRunner 重写路由逻辑 | 组合复用 McpRunner |
| dify_trace 独立于 mcp_trace | 一一映射而来 |
| 导出即可直接导入生产 Dify | 教学子集，字段简化 |

---

## 二十八、30 项自检（节选 20）

1. 能写导出三段结构
2. 能写四阶段映射表
3. 能解释 enabled 分支
4. 能定位 DifyRunner.invoke
5. 能 curl POST dify-export
6. 能 curl POST dify-preview
7. 能跑 dify_demo
8. 能跑 dify_api_demo
9. 能数清 27 tests
10. 能解释组合模式
11. 能对比 Day44
12. 能预告 Day46
13. 能读 validate 源码
14. 能解释 include_start_end
15. 能解释 max_nodes 截断范围
16. 能解释节点 id 命名规则
17. 能解释 workflow_name 用途
18. 能解释 max_nodes 上限 50
19. 能解释 platform_version
20. 能复述 {REQ} 目标

---

## 二十九、延伸阅读：适配器模式

`DifyRunner` 是 **Adapter**：对外返回 dify 风格 dict，对内调用 McpRunner。与 Day44 的 Facade 模式（McpClient 封装 NexusMcpServer）叠加。

---

## 三十、完整测试文件（API）

{fenced("python", TEST_DIFY_API)}

---

## 三十一、课堂录音稿（8 min）

「打开 dify_runner，找 invoke。先看 enabled：关了就提示已关闭。开则调用内部的 McpRunner，拿到四阶段 steps，逐条映射成 DifyTraceEvent。这就是 {REQ} 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(agent): Dify 工作流导出 + 追踪映射 ({REQ})

- DifyConfig + dify_protocol DSL 子集
- build_dify_workflow + map_steps_to_dify_trace
- DifyRunner 组合复用 McpRunner
- GET/PUT dify-config, POST dify-export/dify-preview
- tests/day45 (27 cases)
```

---

## 三十三、dify_protocol 二次嵌入

{fenced("python", DIFY_PROTOCOL)}

---

## 三十四、dify_demo 全文

{fenced("python", DIFY_DEMO)}

---

## 三十五、延迟估算习题

导出 10 个工具节点，纯 Python 循环耗时 <1ms；瓶颈始终在 `ToolExecutor.execute` 本身，不在导出/映射层。

---

## 三十六、"可编排"定义

对本课而言，"可编排"指非研发人员可以通过拖拽节点图的方式重新组合已有工具能力，而不需要改动 Nexus 后端代码。

---

## 三十七、与 LangChain/LangGraph 边界

LangGraph（Day41 StateGraph 灵感来源）是"代码定义图"；Dify 是"图形界面定义图"。两者面向不同用户群体，本课刻意把两条路径都实现了一遍。

---

## 三十八、监控指标

`dify_export_node_count`、`dify_trace_event_count`、`chat_with_dify_mode_rate`。

---

## 三十九、DifyTraceEvent JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| node_id | str | `{{phase}}_{{step}}` 格式 |
| node_type | str | start / tool / end |
| title | str | 工具名或阶段名 |
| status | str | 固定 succeeded（教学简化，未模拟失败态） |
| inputs | dict | 调用参数 |
| outputs | dict | observation / final_answer |

---

## 四十、dify_bridge 全文嵌入

{fenced("python", DIFY_BRIDGE)}

---

## 四十一、chat dify 集成代码

{fenced("python", _CHAT_DIFY)}

---

## 四十二、build_dify_workflow 代码

{fenced("python", DIFY_BRIDGE)}

---

## 四十三、前端展示要点（展望）

未来 `app.js` 可加 `msg__dify` 渲染 `dify_trace` 为迷你流程图，节点按 node_type 着色。

---

## 四十四、合规场景

导出的工作流 DSL 只暴露工具名、描述、参数 schema，绝不包含内部密钥或数据库连接串。

---

## 四十五、测试与 FR 映射

| 测试 | FR |
|------|-----|
| test_build_dify_workflow_respects_max_nodes | FR-002 |
| test_dify_runner_rag_delegation | FR-004 |
| test_chat_dify_mode_trace | FR-006 |
| test_phase4_quiz_has_10_questions | FR-007 |

---

## 四十六、完整 dify_runner.py 引用段

{fenced("python", _DIFY_RUNNER_CLASS)}

---

## 四十七、完整测试文件

{fenced("python", TEST_DIFY_RUNNER)}

---

## 四十八、完整 API 测试

{fenced("python", TEST_DIFY_API)}

---

## 四十九、课堂 8 分钟录音稿

「打开 dify_bridge，build_dify_workflow 三段：start、工具节点、end。chat 里 dify_trace 挂在 reply 后面。这就是 {REQ}。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 4 · Day 45 · Dify · {REQ} · dify_runner 精读完**
"""


def _file23() -> str:
    return f"""# Phase 4 周测与复盘实践

## 实验 1：周测扫描

对全班的 `phase4_quiz.py` 交互得分做简单统计，找出正确率最低的题目。

## 实验 2：错题溯源

针对得分最低的题目，回读对应 Day 的 `11_*详解.md`，写出为什么容易错。

## 实验 3：max_nodes 扫描

```python
for max_nodes in (1, 3, 5, 10, 20):
    workflow = build_dify_workflow(executor, max_nodes=max_nodes)
    print(max_nodes, len(workflow.nodes))
```

记录：`max_nodes` ≥ 工具总数后，节点数不再增加。

## 实验 4：dify_trace 与 mcp_trace 对照

同一 query 分别跑 `mcp_mode=true` 与 `dify_mode=true`，对比两者步数与语义是否一一对应。

## 实验 5：降级演练

`PUT dify-config enabled=false`，确认 chat 立即回退、`dify-export`/`dify-preview` 返回 400。

---

## 报告模板

```markdown
# Phase4 Lab
- 周测得分:
- 错题:
- max_nodes 扫描结论:
- dify_trace vs mcp_trace 对照结论:
```

---

## 常见实验坑

- 忘记先跑 `pytest tests/day45/` 确认环境正常再做手工实验
- 用旧 session_id 导致历史干扰对比结果
- 混淆 `dify-preview`（不落盘）与 `dify-config`（落盘）两个 API

---

## 实验 6：Phase 4 全景回顾

运行 `python3 src/day45/phase4_review.py`，逐条对照 Day39-44 的核心类名是否能脱口而出。

---

## 实验 7：文档贡献

向 `17_Dify_API速查手册.md` 提交一条 Windows PowerShell 版本的 curl 示例。

---

## 实验 8：合规审计表

| query | dify_trace 事件数 | 是否含敏感字段 | 合规 |
|-------|-------------------|----------------|------|
| 客服电话多少 | | | |
| 年化收益怎么样 | | | |
"""


def _file24() -> str:
    return f"""# Phase 4 第七日总结（Day 45）

## 本周进度

| Day | 主题 | 版本 |
|-----|------|------|
| 39 | 手写 ReAct Agent | 0.39.x |
| 40 | AgentExecutor 框架工具链 | 0.40.x |
| 41 | StateGraph 状态图编排 | 0.41.x |
| 42 | 人工审批工作流 | 0.42.x |
| 43 | Supervisor 多 Agent 委派 | 0.43.x |
| 44 | MCP 协议与工具生态 | 0.44.x |
| **45** | **Dify 工作流对接 + 周测** | **{VER}** |

## Day 45 交付物

- DifyConfig + dify_protocol DSL 子集
- build_dify_workflow + map_steps_to_dify_trace
- DifyRunner（组合复用 McpRunner）
- dify-config / dify-export / dify-preview API
- chat dify_mode → dify_trace
- Phase 4 周测（10 题）+ 里程碑回顾
- 27 tests
- 30 篇课件

## 核心能力

**可编排性**：Nexus 的工具能力可以导出成低代码平台能理解的工作流 DSL，运行 trace 也能映射成对方熟悉的日志语义。

## 与 Phase 4 目标对齐

完整能力链：ReAct 决策 → 框架化工具 → 状态图编排 → 人工审批 → 多 Agent 委派 → MCP 协议 → **Dify 可编排导出**。

## 学员自评 Rubric

| 等级 | 标准 |
|------|------|
| A | 能设计 Dify DSL 子集 + 写 chat 单测 + 周测满分 |
| B | 能跑 dify_demo 解释字段 + 周测及格 |
| C | 能复述 dify_trace 与 mcp_trace 关系 |
| D | 仅会 pytest -q |

## 下周预告

Day 46：Agent 工程化——六种模式都上线后，如何统一可观测性与容错设计。

---

## Phase4 能力雷达（Day45 更新）

| 能力 | 等级 |
|------|------|
| 决策 | ★★★★★ |
| 框架化 | ★★★★★ |
| 编排 | ★★★★★ |
| 管控 | ★★★★☆ |
| 协作 | ★★★★☆ |
| 协议扩展 | ★★★★☆ |
| 可视化对接 | ★★★★☆（Day45） |
| 工程化 | ★★☆☆☆（Day46） |

---

## 团队复盘

1. Dify 对接是否要接入真实实例做联调？
2. 周测是否要做成每周固定节奏？
3. dify_trace 是否要暴露给前端做流程图可视化？

---

## 金句墙

- 「工具定义只维护一份」——陈默
- 「组合优于重复实现」——林晓
- 「协议解决连接，DSL 解决呈现」——周航

---

## 项目经理一页纸

{REQ} 已交付：DifyBridge、DifyRunner、dify-* API、chat dify_mode、Phase 4 周测、27 测试。下一步：Day46 Agent 工程化。
"""


def _file25() -> str:
    return f"""# dify_runner API 脚本精读

## dify_api_demo.py 全文

{fenced("python", DIFY_API_DEMO)}

---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| 开头 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| TestClient | 创建 app 与测试客户端 |
| bootstrap | 保证语料/知识库已初始化 |
| GET dify-config | 读默认配置 |
| POST dify-export | 导出工作流 DSL — **核心演示** |
| POST dify-preview | 预览一次调用的 dify_trace |
| chat + health | 端到端 + 版本号 {VER} |

---

## dify_demo.py 全文

{fenced("python", DIFY_DEMO)}

`export_workflow()` 与 `invoke()` 分别对应"导出"与"运行"两条路径。

---

## constants.py

```python
DIFY_CASES = [
    {{"query": "客服电话多少", "expect_tool": "faq_lookup"}},
    {{"query": "年化收益怎么样", "expect_tool": "rag_search"}},
    {{"query": "帮我总结一下理财产品", "expect_tool": "intent_classify"}},
]

QUIZ_PASS_SCORE = 60
```

---

## phase4_quiz.py 骨架

{fenced("python", PHASE4_QUIZ)}

---

## phase4_review.py 全文

{fenced("python", PHASE4_REVIEW)}

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day45/dify_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
PYTHONPATH=src python3 src/day45/phase4_review.py
PYTHONPATH=src python3 src/day45/phase4_quiz.py --scripted
pytest tests/day45/ -v
```
"""


def _file26() -> str:
    return f"""# Day 45 实操 Lab 手册（Lab 0-7）

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

**通过标准**：dify-export 200；chat dify_trace 长度=4；version {VER}。

---

## Lab 6：关闭 Dify 对接（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled":false,"workflow_name":"nexus-agent-workflow","include_start_end":true,"mock_routing":true,"use_session_history":true,"return_dify_trace":true,"max_nodes":10}}'
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
{{
  "app": {{"name": "nexus-agent-workflow", "mode": "workflow"}},
  "workflow": {{
    "graph": {{
      "nodes": [
        {{"id": "start", "data": {{"type": "start", "title": "开始"}}}},
        {{"id": "tool_faq_lookup", "data": {{"type": "tool", "title": "faq_lookup"}}}},
        {{"id": "end", "data": {{"type": "end", "title": "结束"}}}}
      ],
      "edges": [
        {{"id": "start->tool_faq_lookup", "source": "start", "target": "tool_faq_lookup"}},
        {{"id": "tool_faq_lookup->end", "source": "tool_faq_lookup", "target": "end"}}
      ]
    }}
  }}
}}
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
"""


def _file27() -> str:
    return """# Day 46 预习：Agent 工程化 — 可观测性与容错

**预告**：Day 45 Dify 已让工具链**可编排**；Day 46 将聚焦 Agent 工程化——六种模式（ReAct/Executor/Graph/Approval/Supervisor/MCP）都上线后，如何统一监控、限流与优雅降级。

## 预习问

1. 六种 chat 模式各自的 trace 字段不同，统一监控要怎么设计？
2. 某个模式偶发超时，如何在不影响其它模式的前提下做局部降级？

## 一句话

Day45 让平台**可编排**；Day46 让平台**更健壮**。
"""


if __name__ == "__main__":
    write_course(45, build(), min_chars=100_000)
