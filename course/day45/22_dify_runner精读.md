# Day 45 精读：dify_runner 与工作流对接管线

**需求**：ZL-NA-REQ-045 | **学时**：120 min

---

## 一、dify_runner.py 全文

```python
"""
DifyRunner — 复用 McpRunner 决策/执行，输出 Dify 工作流风格追踪 + 导出 DSL

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DifyWorkflow
from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class DifyRunOutcome:
    query: str
    reply: str
    dify_trace: tuple[dict[str, Any], ...]
    tools_used: tuple[str, ...]
    workflow_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "dify_trace": [dict(e) for e in self.dify_trace],
            "tools_used": list(self.tools_used),
            "workflow_name": self.workflow_name,
        }


class DifyRunner:
    """在 McpRunner 的 discover→route→call→answer 之上，附加 Dify 工作流语义"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or DifyConfig()
        self._mcp = McpRunner.from_executor(
            executor,
            config=McpConfig(
                enabled=True,
                mock_routing=self._config.mock_routing,
                use_session_history=self._config.use_session_history,
                return_mcp_trace=True,
            ),
        )

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> DifyRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> DifyConfig:
        return self._config

    def export_workflow(self) -> DifyWorkflow:
        return build_dify_workflow(
            self._executor,
            workflow_name=self._config.workflow_name,
            include_start_end=self._config.include_start_end,
            max_nodes=self._config.max_nodes,
        )

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> DifyRunOutcome:
        cfg = self._config
        if not (query or "").strip():
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "Dify 工作流对接已关闭。")

        outcome = self._mcp.invoke(query, history=history)
        events = map_steps_to_dify_trace(outcome.steps) if cfg.return_dify_trace else []
        return DifyRunOutcome(
            query=outcome.query,
            reply=outcome.reply,
            dify_trace=tuple(e.to_dict() for e in events),
            tools_used=outcome.tools_used,
            workflow_name=cfg.workflow_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> DifyRunOutcome:
        return DifyRunOutcome(
            query=query,
            reply=reply,
            dify_trace=(),
            tools_used=(),
            workflow_name=self._config.workflow_name,
        )
```


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

```python
class DifyRunner:
    """在 McpRunner 的 discover→route→call→answer 之上，附加 Dify 工作流语义"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or DifyConfig()
        self._mcp = McpRunner.from_executor(
            executor,
            config=McpConfig(
                enabled=True,
                mock_routing=self._config.mock_routing,
                use_session_history=self._config.use_session_history,
                return_mcp_trace=True,
            ),
        )

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> DifyRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> DifyConfig:
        return self._config

    def export_workflow(self) -> DifyWorkflow:
        return build_dify_workflow(
            self._executor,
            workflow_name=self._config.workflow_name,
            include_start_end=self._config.include_start_end,
            max_nodes=self._config.max_nodes,
        )

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> DifyRunOutcome:
        cfg = self._config
        if not (query or "").strip():
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "Dify 工作流对接已关闭。")

        outcome = self._mcp.invoke(query, history=history)
        events = map_steps_to_dify_trace(outcome.steps) if cfg.return_dify_trace else []
        return DifyRunOutcome(
            query=outcome.query,
            reply=outcome.reply,
            dify_trace=tuple(e.to_dict() for e in events),
            tools_used=outcome.tools_used,
            workflow_name=cfg.workflow_name,
        )
```


| 行 | 讲解 |
|----|------|
| `self._mcp = McpRunner.from_executor(...)` | 核心：不重写发现/路由/调用，直接持有一个 McpRunner |
| `McpConfig(mock_routing=self._config.mock_routing, ...)` | 把 DifyConfig 的相关字段转发给内部 McpConfig |
| `invoke()` | 先调 `self._mcp.invoke`，再 `map_steps_to_dify_trace` |
| `export_workflow()` | 委托给 `build_dify_workflow` 纯函数 |

---

## 四、dify_bridge.py 全文

```python
"""
Dify 桥接 — ToolExecutor → DifyWorkflow 导出 / McpStep → DifyTraceEvent 映射

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from agent.dify_protocol import (
    DIFY_NODE_END,
    DIFY_NODE_START,
    DIFY_NODE_TOOL,
    DIFY_STATUS_SUCCEEDED,
    DifyEdge,
    DifyNode,
    DifyTraceEvent,
    DifyWorkflow,
)
from agent.mcp_runner import McpStep
from tools.executor import ToolExecutor


def build_dify_workflow(
    executor: ToolExecutor,
    *,
    workflow_name: str = "nexus-agent-workflow",
    include_start_end: bool = True,
    max_nodes: int = 10,
) -> DifyWorkflow:
    """将 ToolRegistry 中已注册工具导出为 Dify 工作流 DSL（start → tool* → end）"""
    definitions = executor.registry.list_tools()[:max_nodes]

    nodes: list[DifyNode] = []
    edges: list[DifyEdge] = []
    prev_id = "start"

    if include_start_end:
        nodes.append(DifyNode(id="start", type=DIFY_NODE_START, title="开始"))

    for definition in definitions:
        node_id = f"tool_{definition.name}"
        nodes.append(
            DifyNode(
                id=node_id,
                type=DIFY_NODE_TOOL,
                title=definition.name,
                data={
                    "tool_name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            )
        )
        if include_start_end or prev_id != "start":
            edges.append(DifyEdge(id=f"{prev_id}->{node_id}", source=prev_id, target=node_id))
        prev_id = node_id

    if include_start_end:
        nodes.append(DifyNode(id="end", type=DIFY_NODE_END, title="结束"))
        edges.append(DifyEdge(id=f"{prev_id}->end", source=prev_id, target="end"))

    return DifyWorkflow(name=workflow_name, nodes=tuple(nodes), edges=tuple(edges))


_PHASE_TO_NODE_TYPE = {
    "discover": DIFY_NODE_START,
    "route": DIFY_NODE_TOOL,
    "call": DIFY_NODE_TOOL,
    "answer": DIFY_NODE_END,
}


def map_steps_to_dify_trace(steps: tuple[McpStep, ...]) -> list[DifyTraceEvent]:
    """把 McpRunner 的 discover/route/call/answer 四阶段 trace 映射为 Dify 风格的
    workflow_node_execution 事件列表，便于对接 Dify 工作流运行日志展示。
    """
    events: list[DifyTraceEvent] = []
    for step in steps:
        node_type = _PHASE_TO_NODE_TYPE.get(step.phase, DIFY_NODE_TOOL)
        title = step.tool or step.phase
        inputs: dict = {}
        outputs: dict = {}
        if step.arguments:
            inputs = dict(step.arguments)
        if step.observation:
            outputs["observation"] = step.observation
        if step.final_answer:
            outputs["final_answer"] = step.final_answer
        events.append(
            DifyTraceEvent(
                node_id=f"{step.phase}_{step.step}",
                node_type=node_type,
                title=title,
                status=DIFY_STATUS_SUCCEEDED,
                inputs=inputs,
                outputs=outputs,
            )
        )
    return events
```


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

```python
"""
Dify 桥接 — ToolExecutor → DifyWorkflow 导出 / McpStep → DifyTraceEvent 映射

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from agent.dify_protocol import (
    DIFY_NODE_END,
    DIFY_NODE_START,
    DIFY_NODE_TOOL,
    DIFY_STATUS_SUCCEEDED,
    DifyEdge,
    DifyNode,
    DifyTraceEvent,
    DifyWorkflow,
)
from agent.mcp_runner import McpStep
from tools.executor import ToolExecutor


def build_dify_workflow(
    executor: ToolExecutor,
    *,
    workflow_name: str = "nexus-agent-workflow",
    include_start_end: bool = True,
    max_nodes: int = 10,
) -> DifyWorkflow:
    """将 ToolRegistry 中已注册工具导出为 Dify 工作流 DSL（start → tool* → end）"""
    definitions = executor.registry.list_tools()[:max_nodes]

    nodes: list[DifyNode] = []
    edges: list[DifyEdge] = []
    prev_id = "start"

    if include_start_end:
        nodes.append(DifyNode(id="start", type=DIFY_NODE_START, title="开始"))

    for definition in definitions:
        node_id = f"tool_{definition.name}"
        nodes.append(
            DifyNode(
                id=node_id,
                type=DIFY_NODE_TOOL,
                title=definition.name,
                data={
                    "tool_name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            )
        )
        if include_start_end or prev_id != "start":
            edges.append(DifyEdge(id=f"{prev_id}->{node_id}", source=prev_id, target=node_id))
        prev_id = node_id

    if include_start_end:
        nodes.append(DifyNode(id="end", type=DIFY_NODE_END, title="结束"))
        edges.append(DifyEdge(id=f"{prev_id}->end", source=prev_id, target="end"))

    return DifyWorkflow(name=workflow_name, nodes=tuple(nodes), edges=tuple(edges))


_PHASE_TO_NODE_TYPE = {
    "discover": DIFY_NODE_START,
    "route": DIFY_NODE_TOOL,
    "call": DIFY_NODE_TOOL,
    "answer": DIFY_NODE_END,
}


def map_steps_to_dify_trace(steps: tuple[McpStep, ...]) -> list[DifyTraceEvent]:
    """把 McpRunner 的 discover/route/call/answer 四阶段 trace 映射为 Dify 风格的
    workflow_node_execution 事件列表，便于对接 Dify 工作流运行日志展示。
    """
    events: list[DifyTraceEvent] = []
    for step in steps:
        node_type = _PHASE_TO_NODE_TYPE.get(step.phase, DIFY_NODE_TOOL)
        title = step.tool or step.phase
        inputs: dict = {}
        outputs: dict = {}
        if step.arguments:
            inputs = dict(step.arguments)
        if step.observation:
            outputs["observation"] = step.observation
        if step.final_answer:
            outputs["final_answer"] = step.final_answer
        events.append(
            DifyTraceEvent(
                node_id=f"{step.phase}_{step.step}",
                node_type=node_type,
                title=title,
                status=DIFY_STATUS_SUCCEEDED,
                inputs=inputs,
                outputs=outputs,
            )
        )
    return events
```


`_PHASE_TO_NODE_TYPE` 映射表是本函数的核心：discover→start，route/call→tool，answer→end。

---

## 七、dify_protocol.py 全文

```python
"""
Dify 工作流 DSL 数据模型 — 节点/边/追踪事件

对齐 Dify 开源工作流 DSL（app + workflow.graph.nodes/edges）核心结构的教学子集
（无 dify 依赖，字段精简但语义对齐）。

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DIFY_NODE_START = "start"
DIFY_NODE_TOOL = "tool"
DIFY_NODE_LLM = "llm"
DIFY_NODE_END = "end"

DIFY_STATUS_SUCCEEDED = "succeeded"
DIFY_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class DifyNode:
    """Dify workflow.graph.nodes[] 元素的教学子集"""

    id: str
    type: str
    title: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "data": {"type": self.type, "title": self.title, **self.data},
        }


@dataclass(frozen=True)
class DifyEdge:
    """Dify workflow.graph.edges[] 元素"""

    id: str
    source: str
    target: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "source": self.source, "target": self.target}


@dataclass(frozen=True)
class DifyWorkflow:
    """Dify DSL 顶层结构（app + workflow.graph）教学子集"""

    name: str
    nodes: tuple[DifyNode, ...]
    edges: tuple[DifyEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": {"name": self.name, "mode": "workflow"},
            "workflow": {
                "graph": {
                    "nodes": [n.to_dict() for n in self.nodes],
                    "edges": [e.to_dict() for e in self.edges],
                }
            },
        }


@dataclass(frozen=True)
class DifyTraceEvent:
    """workflow_node_execution 风格的运行事件（对齐 Dify 工作流运行日志语义）"""

    node_id: str
    node_type: str
    title: str
    status: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "status": self.status,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
        }
```


`DifyWorkflow.to_dict()`：`{"app": {"name", "mode"}, "workflow": {"graph": {"nodes", "edges"}}}`，对齐真实 Dify DSL 顶层字段命名（教学子集，字段远少于完整规范）。

---

## 八、dify_config.py 全文

```python
"""
Dify 配置 — Nexus 工具链导出为 Dify 工作流 DSL

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DifyConfig:
    """Dify 工作流导出与追踪映射策略"""

    enabled: bool = True
    workflow_name: str = "nexus-agent-workflow"
    include_start_end: bool = True
    mock_routing: bool = True
    use_session_history: bool = True
    return_dify_trace: bool = True
    max_nodes: int = 10

    def validate(self) -> None:
        if self.max_nodes < 1 or self.max_nodes > 50:
            raise ValueError(f"max_nodes 须在 1~50，收到 {self.max_nodes}")
        if not (self.workflow_name or "").strip():
            raise ValueError("workflow_name 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "workflow_name": self.workflow_name,
            "include_start_end": self.include_start_end,
            "mock_routing": self.mock_routing,
            "use_session_history": self.use_session_history,
            "return_dify_trace": self.return_dify_trace,
            "max_nodes": self.max_nodes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DifyConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            workflow_name=str(data.get("workflow_name", "nexus-agent-workflow")),
            include_start_end=bool(data.get("include_start_end", True)),
            mock_routing=bool(data.get("mock_routing", True)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_dify_trace=bool(data.get("return_dify_trace", True)),
            max_nodes=int(data.get("max_nodes", 10)),
        )
```


`validate()`：`max_nodes` ∈ [1,50]，`workflow_name` 非空。

---

## 九、api/agent.py dify-* 节选

```python
@router.get("/dify-config", response_model=DifyConfigResponse)
def get_dify_config() -> DifyConfigResponse:
    cfg = get_knowledge_store().get_dify_config()
    return DifyConfigResponse(**cfg.to_dict())


@router.put("/dify-config", response_model=DifyConfigResponse)
def update_dify_config(body: DifyConfigRequest) -> DifyConfigResponse:
    store = get_knowledge_store()
    try:
        cfg = DifyConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_dify_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DifyConfigResponse(**cfg.to_dict())


@router.post("/dify-export", response_model=DifyExportResponse)
def dify_export(body: DifyExportRequest) -> DifyExportResponse:
    """将当前 ToolRegistry 导出为 Dify 工作流 DSL（start → tool* → end）"""
    _ = body
    store = get_knowledge_store()
    cfg = store.get_dify_config()
    if not cfg.enabled:
        raise HTTPException(status_code=400, detail="Dify 工作流对接已关闭")

    orchestrator = create_orchestrator()
    runner = DifyRunner.from_executor(orchestrator.tool_executor, config=cfg)
    payload = runner.export_workflow().to_dict()
    return DifyExportResponse(**payload)


@router.post("/dify-preview"
```


---

## 十、chat.py dify_mode 集成节选

```python
if body.dify_mode and store.get_dify_config().enabled:
            dcfg = store.get_dify_config()
            dify_runner = DifyRunner.from_executor(
                orchestrator.tool_executor,
                config=dcfg,
            )
            history = _session_history(orchestrator, enabled=dcfg.use_session_history)
            dify_outcome = dify_runner.invoke(message, history=history)
            reply = dify_outcome.reply
            dify_trace = [dict(e) for e in dify_outcome.dify_trace]
            tools_used = list(dify_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
```


---

## 十一、测试精读 test_dify_runner.py

```python
"""Day 45 Dify Bridge/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DIFY_NODE_END, DIFY_NODE_START, DIFY_NODE_TOOL, DifyWorkflow
from agent.dify_runner import DifyRunner
from agent.mcp_runner import McpStep
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return DifyRunner.from_executor(orch.tool_executor, config=DifyConfig())


def test_dify_config_validate():
    DifyConfig().validate()
    with pytest.raises(ValueError):
        DifyConfig(max_nodes=0).validate()
    with pytest.raises(ValueError):
        DifyConfig(workflow_name="  ").validate()


def test_build_dify_workflow_has_start_and_end(runner):
    workflow = runner.export_workflow()
    assert isinstance(workflow, DifyWorkflow)
    types = [n.type for n in workflow.nodes]
    assert types[0] == DIFY_NODE_START
    assert types[-1] == DIFY_NODE_END
    assert any(t == DIFY_NODE_TOOL for t in types)


def test_build_dify_workflow_respects_max_nodes(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, max_nodes=1, include_start_end=True)
    tool_nodes = [n for n in workflow.nodes if n.type == DIFY_NODE_TOOL]
    assert len(tool_nodes) == 1


def test_build_dify_workflow_without_start_end(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, include_start_end=False)
    types = {n.type for n in workflow.nodes}
    assert DIFY_NODE_START not in types
    assert DIFY_NODE_END not in types


def test_dify_workflow_to_dict_shape(runner):
    workflow = runner.export_workflow()
    payload = workflow.to_dict()
    assert payload["app"]["mode"] == "workflow"
    assert "nodes" in payload["workflow"]["graph"]
    assert "edges" in payload["workflow"]["graph"]


def test_map_steps_to_dify_trace():
    steps = (
        McpStep(step=1, phase="discover", thought="发现工具"),
        McpStep(step=2, phase="route", thought="路由", tool="faq_lookup", arguments={"query": "x"}),
        McpStep(step=3, phase="call", thought="调用", tool="faq_lookup", observation="obs"),
        McpStep(step=4, phase="answer", thought="汇总", final_answer="reply"),
    )
    events = map_steps_to_dify_trace(steps)
    assert len(events) == 4
    assert events[0].node_type == DIFY_NODE_START
    assert events[-1].node_type == DIFY_NODE_END
    assert events[2].outputs.get("observation") == "obs"


def test_dify_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert len(outcome.dify_trace) == 4


def test_dify_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_dify_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_dify_runner_empty_query(runner):
    outcome = runner.invoke("")
    assert outcome.dify_trace == ()
    assert "有效问题" in outcome.reply


def test_dify_runner_disabled():
    orch = create_orchestrator()
    runner = DifyRunner.from_executor(orch.tool_executor, config=DifyConfig(enabled=False))
    outcome = runner.invoke("客服电话多少")
    assert outcome.dify_trace == ()
    assert "关闭" in outcome.reply


def test_dify_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_dify_config(DifyConfig(workflow_name="custom-workflow", max_nodes=5))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_dify_config()
    assert cfg.workflow_name == "custom-workflow"
    assert cfg.max_nodes == 5
```


| 测试 | 要点 |
|------|------|
| test_build_dify_workflow_has_start_and_end | 默认导出首尾哨兵节点 |
| test_build_dify_workflow_respects_max_nodes | 截断保护生效 |
| test_map_steps_to_dify_trace | 四阶段完整映射 |
| test_dify_runner_faq_delegation | 端到端委派正确 |
| test_dify_config_persists_in_store | 持久化不丢字段 |

---

## 十二、API 测试 test_dify_api.py

```python
"""Day 45 Dify API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_dify_config_default(client):
    data = client.get("/api/agent/dify-config").json()
    assert data["enabled"] is True
    assert data["workflow_name"] == "nexus-agent-workflow"


def test_put_dify_config(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_nodes"] == 5


def test_dify_export(client):
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 200
    data = resp.json()
    nodes = data["workflow"]["graph"]["nodes"]
    assert any(n["data"]["type"] == "start" for n in nodes)
    assert any(n["data"]["type"] == "end" for n in nodes)
    assert any(n["data"]["type"] == "tool" for n in nodes)


def test_dify_preview_rag(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert len(data["dify_trace"]) == 4


def test_dify_preview_with_history(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_dify_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["dify_config"]["enabled"] is True


def test_chat_dify_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace")
    assert body["kind"] == "dify"


def test_chat_dify_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace") is None
    assert body["kind"] == "faq"


def test_invalid_dify_max_nodes_422(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 999,
        },
    )
    assert resp.status_code == 422


def test_dify_export_disabled_400(client):
    client.put(
        "/api/agent/dify-config",
        json={
            "enabled": False,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 10,
        },
    )
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 400
```


`test_health_version` 锁版本 `v0.45.0`；`test_chat_dify_mode_trace` 端到端。

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

```python
def get_dify_config(self) -> DifyConfig:
        return DifyConfig.from_dict(self.dify_config.to_dict())

    def set_dify_config(self, config: DifyConfig) -> DifyConfig:
        config.validate()
        self.dify_config = DifyConfig.from_dict(config.to_dict())
        return self.dify_config
```


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

```python
"""
DifyRunner — 复用 McpRunner 决策/执行，输出 Dify 工作流风格追踪 + 导出 DSL

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DifyWorkflow
from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class DifyRunOutcome:
    query: str
    reply: str
    dify_trace: tuple[dict[str, Any], ...]
    tools_used: tuple[str, ...]
    workflow_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "dify_trace": [dict(e) for e in self.dify_trace],
            "tools_used": list(self.tools_used),
            "workflow_name": self.workflow_name,
        }


class DifyRunner:
    """在 McpRunner 的 discover→route→call→answer 之上，附加 Dify 工作流语义"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or DifyConfig()
        self._mcp = McpRunner.from_executor(
            executor,
            config=McpConfig(
                enabled=True,
                mock_routing=self._config.mock_routing,
                use_session_history=self._config.use_session_history,
                return_mcp_trace=True,
            ),
        )

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> DifyRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> DifyConfig:
        return self._config

    def export_workflow(self) -> DifyWorkflow:
        return build_dify_workflow(
            self._executor,
            workflow_name=self._config.workflow_name,
            include_start_end=self._config.include_start_end,
            max_nodes=self._config.max_nodes,
        )

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> DifyRunOutcome:
        cfg = self._config
        if not (query or "").strip():
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "Dify 工作流对接已关闭。")

        outcome = self._mcp.invoke(query, history=history)
        events = map_steps_to_dify_trace(outcome.steps) if cfg.return_dify_trace else []
        return DifyRunOutcome(
            query=outcome.query,
            reply=outcome.reply,
            dify_trace=tuple(e.to_dict() for e in events),
            tools_used=outcome.tools_used,
            workflow_name=cfg.workflow_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> DifyRunOutcome:
        return DifyRunOutcome(
            query=query,
            reply=reply,
            dify_trace=(),
            tools_used=(),
            workflow_name=self._config.workflow_name,
        )
```


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

```python
def get_dify_config(self) -> DifyConfig:
        return DifyConfig.from_dict(self.dify_config.to_dict())

    def set_dify_config(self, config: DifyConfig) -> DifyConfig:
        config.validate()
        self.dify_config = DifyConfig.from_dict(config.to_dict())
        return self.dify_config
```


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
20. 能复述 ZL-NA-REQ-045 目标

---

## 二十九、延伸阅读：适配器模式

`DifyRunner` 是 **Adapter**：对外返回 dify 风格 dict，对内调用 McpRunner。与 Day44 的 Facade 模式（McpClient 封装 NexusMcpServer）叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 45 Dify API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_dify_config_default(client):
    data = client.get("/api/agent/dify-config").json()
    assert data["enabled"] is True
    assert data["workflow_name"] == "nexus-agent-workflow"


def test_put_dify_config(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_nodes"] == 5


def test_dify_export(client):
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 200
    data = resp.json()
    nodes = data["workflow"]["graph"]["nodes"]
    assert any(n["data"]["type"] == "start" for n in nodes)
    assert any(n["data"]["type"] == "end" for n in nodes)
    assert any(n["data"]["type"] == "tool" for n in nodes)


def test_dify_preview_rag(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert len(data["dify_trace"]) == 4


def test_dify_preview_with_history(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_dify_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["dify_config"]["enabled"] is True


def test_chat_dify_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace")
    assert body["kind"] == "dify"


def test_chat_dify_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace") is None
    assert body["kind"] == "faq"


def test_invalid_dify_max_nodes_422(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 999,
        },
    )
    assert resp.status_code == 422


def test_dify_export_disabled_400(client):
    client.put(
        "/api/agent/dify-config",
        json={
            "enabled": False,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 10,
        },
    )
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 400
```


---

## 三十一、课堂录音稿（8 min）

「打开 dify_runner，找 invoke。先看 enabled：关了就提示已关闭。开则调用内部的 McpRunner，拿到四阶段 steps，逐条映射成 DifyTraceEvent。这就是 ZL-NA-REQ-045 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(agent): Dify 工作流导出 + 追踪映射 (ZL-NA-REQ-045)

- DifyConfig + dify_protocol DSL 子集
- build_dify_workflow + map_steps_to_dify_trace
- DifyRunner 组合复用 McpRunner
- GET/PUT dify-config, POST dify-export/dify-preview
- tests/day45 (27 cases)
```

---

## 三十三、dify_protocol 二次嵌入

```python
"""
Dify 工作流 DSL 数据模型 — 节点/边/追踪事件

对齐 Dify 开源工作流 DSL（app + workflow.graph.nodes/edges）核心结构的教学子集
（无 dify 依赖，字段精简但语义对齐）。

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DIFY_NODE_START = "start"
DIFY_NODE_TOOL = "tool"
DIFY_NODE_LLM = "llm"
DIFY_NODE_END = "end"

DIFY_STATUS_SUCCEEDED = "succeeded"
DIFY_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class DifyNode:
    """Dify workflow.graph.nodes[] 元素的教学子集"""

    id: str
    type: str
    title: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "data": {"type": self.type, "title": self.title, **self.data},
        }


@dataclass(frozen=True)
class DifyEdge:
    """Dify workflow.graph.edges[] 元素"""

    id: str
    source: str
    target: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "source": self.source, "target": self.target}


@dataclass(frozen=True)
class DifyWorkflow:
    """Dify DSL 顶层结构（app + workflow.graph）教学子集"""

    name: str
    nodes: tuple[DifyNode, ...]
    edges: tuple[DifyEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": {"name": self.name, "mode": "workflow"},
            "workflow": {
                "graph": {
                    "nodes": [n.to_dict() for n in self.nodes],
                    "edges": [e.to_dict() for e in self.edges],
                }
            },
        }


@dataclass(frozen=True)
class DifyTraceEvent:
    """workflow_node_execution 风格的运行事件（对齐 Dify 工作流运行日志语义）"""

    node_id: str
    node_type: str
    title: str
    status: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "status": self.status,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
        }
```


---

## 三十四、dify_demo 全文

```python
"""
Dify 工作流对接演示

运行：PYTHONPATH=src python3 src/day45/dify_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.dify_config import DifyConfig
from agent.dify_runner import DifyRunner
from api.factory import create_orchestrator
from day45.constants import DIFY_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 45 Dify 工作流对接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = DifyRunner.from_executor(
        orchestrator.tool_executor,
        config=DifyConfig(enabled=True),
    )

    workflow = runner.export_workflow()
    node_ids = [n.id for n in workflow.nodes]
    print(f"\n  导出 Dify 工作流「{workflow.name}」节点: {node_ids}")

    for item in DIFY_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    tools_used={list(outcome.tools_used)} {flag}")
        print(f"    dify_trace 节点数={len(outcome.dify_trace)}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ Dify 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


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
| node_id | str | `{phase}_{step}` 格式 |
| node_type | str | start / tool / end |
| title | str | 工具名或阶段名 |
| status | str | 固定 succeeded（教学简化，未模拟失败态） |
| inputs | dict | 调用参数 |
| outputs | dict | observation / final_answer |

---

## 四十、dify_bridge 全文嵌入

```python
"""
Dify 桥接 — ToolExecutor → DifyWorkflow 导出 / McpStep → DifyTraceEvent 映射

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from agent.dify_protocol import (
    DIFY_NODE_END,
    DIFY_NODE_START,
    DIFY_NODE_TOOL,
    DIFY_STATUS_SUCCEEDED,
    DifyEdge,
    DifyNode,
    DifyTraceEvent,
    DifyWorkflow,
)
from agent.mcp_runner import McpStep
from tools.executor import ToolExecutor


def build_dify_workflow(
    executor: ToolExecutor,
    *,
    workflow_name: str = "nexus-agent-workflow",
    include_start_end: bool = True,
    max_nodes: int = 10,
) -> DifyWorkflow:
    """将 ToolRegistry 中已注册工具导出为 Dify 工作流 DSL（start → tool* → end）"""
    definitions = executor.registry.list_tools()[:max_nodes]

    nodes: list[DifyNode] = []
    edges: list[DifyEdge] = []
    prev_id = "start"

    if include_start_end:
        nodes.append(DifyNode(id="start", type=DIFY_NODE_START, title="开始"))

    for definition in definitions:
        node_id = f"tool_{definition.name}"
        nodes.append(
            DifyNode(
                id=node_id,
                type=DIFY_NODE_TOOL,
                title=definition.name,
                data={
                    "tool_name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            )
        )
        if include_start_end or prev_id != "start":
            edges.append(DifyEdge(id=f"{prev_id}->{node_id}", source=prev_id, target=node_id))
        prev_id = node_id

    if include_start_end:
        nodes.append(DifyNode(id="end", type=DIFY_NODE_END, title="结束"))
        edges.append(DifyEdge(id=f"{prev_id}->end", source=prev_id, target="end"))

    return DifyWorkflow(name=workflow_name, nodes=tuple(nodes), edges=tuple(edges))


_PHASE_TO_NODE_TYPE = {
    "discover": DIFY_NODE_START,
    "route": DIFY_NODE_TOOL,
    "call": DIFY_NODE_TOOL,
    "answer": DIFY_NODE_END,
}


def map_steps_to_dify_trace(steps: tuple[McpStep, ...]) -> list[DifyTraceEvent]:
    """把 McpRunner 的 discover/route/call/answer 四阶段 trace 映射为 Dify 风格的
    workflow_node_execution 事件列表，便于对接 Dify 工作流运行日志展示。
    """
    events: list[DifyTraceEvent] = []
    for step in steps:
        node_type = _PHASE_TO_NODE_TYPE.get(step.phase, DIFY_NODE_TOOL)
        title = step.tool or step.phase
        inputs: dict = {}
        outputs: dict = {}
        if step.arguments:
            inputs = dict(step.arguments)
        if step.observation:
            outputs["observation"] = step.observation
        if step.final_answer:
            outputs["final_answer"] = step.final_answer
        events.append(
            DifyTraceEvent(
                node_id=f"{step.phase}_{step.step}",
                node_type=node_type,
                title=title,
                status=DIFY_STATUS_SUCCEEDED,
                inputs=inputs,
                outputs=outputs,
            )
        )
    return events
```


---

## 四十一、chat dify 集成代码

```python
if body.dify_mode and store.get_dify_config().enabled:
            dcfg = store.get_dify_config()
            dify_runner = DifyRunner.from_executor(
                orchestrator.tool_executor,
                config=dcfg,
            )
            history = _session_history(orchestrator, enabled=dcfg.use_session_history)
            dify_outcome = dify_runner.invoke(message, history=history)
            reply = dify_outcome.reply
            dify_trace = [dict(e) for e in dify_outcome.dify_trace]
            tools_used = list(dify_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
```


---

## 四十二、build_dify_workflow 代码

```python
"""
Dify 桥接 — ToolExecutor → DifyWorkflow 导出 / McpStep → DifyTraceEvent 映射

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from agent.dify_protocol import (
    DIFY_NODE_END,
    DIFY_NODE_START,
    DIFY_NODE_TOOL,
    DIFY_STATUS_SUCCEEDED,
    DifyEdge,
    DifyNode,
    DifyTraceEvent,
    DifyWorkflow,
)
from agent.mcp_runner import McpStep
from tools.executor import ToolExecutor


def build_dify_workflow(
    executor: ToolExecutor,
    *,
    workflow_name: str = "nexus-agent-workflow",
    include_start_end: bool = True,
    max_nodes: int = 10,
) -> DifyWorkflow:
    """将 ToolRegistry 中已注册工具导出为 Dify 工作流 DSL（start → tool* → end）"""
    definitions = executor.registry.list_tools()[:max_nodes]

    nodes: list[DifyNode] = []
    edges: list[DifyEdge] = []
    prev_id = "start"

    if include_start_end:
        nodes.append(DifyNode(id="start", type=DIFY_NODE_START, title="开始"))

    for definition in definitions:
        node_id = f"tool_{definition.name}"
        nodes.append(
            DifyNode(
                id=node_id,
                type=DIFY_NODE_TOOL,
                title=definition.name,
                data={
                    "tool_name": definition.name,
                    "description": definition.description,
                    "parameters": definition.parameters,
                },
            )
        )
        if include_start_end or prev_id != "start":
            edges.append(DifyEdge(id=f"{prev_id}->{node_id}", source=prev_id, target=node_id))
        prev_id = node_id

    if include_start_end:
        nodes.append(DifyNode(id="end", type=DIFY_NODE_END, title="结束"))
        edges.append(DifyEdge(id=f"{prev_id}->end", source=prev_id, target="end"))

    return DifyWorkflow(name=workflow_name, nodes=tuple(nodes), edges=tuple(edges))


_PHASE_TO_NODE_TYPE = {
    "discover": DIFY_NODE_START,
    "route": DIFY_NODE_TOOL,
    "call": DIFY_NODE_TOOL,
    "answer": DIFY_NODE_END,
}


def map_steps_to_dify_trace(steps: tuple[McpStep, ...]) -> list[DifyTraceEvent]:
    """把 McpRunner 的 discover/route/call/answer 四阶段 trace 映射为 Dify 风格的
    workflow_node_execution 事件列表，便于对接 Dify 工作流运行日志展示。
    """
    events: list[DifyTraceEvent] = []
    for step in steps:
        node_type = _PHASE_TO_NODE_TYPE.get(step.phase, DIFY_NODE_TOOL)
        title = step.tool or step.phase
        inputs: dict = {}
        outputs: dict = {}
        if step.arguments:
            inputs = dict(step.arguments)
        if step.observation:
            outputs["observation"] = step.observation
        if step.final_answer:
            outputs["final_answer"] = step.final_answer
        events.append(
            DifyTraceEvent(
                node_id=f"{step.phase}_{step.step}",
                node_type=node_type,
                title=title,
                status=DIFY_STATUS_SUCCEEDED,
                inputs=inputs,
                outputs=outputs,
            )
        )
    return events
```


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

```python
class DifyRunner:
    """在 McpRunner 的 discover→route→call→answer 之上，附加 Dify 工作流语义"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or DifyConfig()
        self._mcp = McpRunner.from_executor(
            executor,
            config=McpConfig(
                enabled=True,
                mock_routing=self._config.mock_routing,
                use_session_history=self._config.use_session_history,
                return_mcp_trace=True,
            ),
        )

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> DifyRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> DifyConfig:
        return self._config

    def export_workflow(self) -> DifyWorkflow:
        return build_dify_workflow(
            self._executor,
            workflow_name=self._config.workflow_name,
            include_start_end=self._config.include_start_end,
            max_nodes=self._config.max_nodes,
        )

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> DifyRunOutcome:
        cfg = self._config
        if not (query or "").strip():
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "Dify 工作流对接已关闭。")

        outcome = self._mcp.invoke(query, history=history)
        events = map_steps_to_dify_trace(outcome.steps) if cfg.return_dify_trace else []
        return DifyRunOutcome(
            query=outcome.query,
            reply=outcome.reply,
            dify_trace=tuple(e.to_dict() for e in events),
            tools_used=outcome.tools_used,
            workflow_name=cfg.workflow_name,
        )
```


---

## 四十七、完整测试文件

```python
"""Day 45 Dify Bridge/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DIFY_NODE_END, DIFY_NODE_START, DIFY_NODE_TOOL, DifyWorkflow
from agent.dify_runner import DifyRunner
from agent.mcp_runner import McpStep
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return DifyRunner.from_executor(orch.tool_executor, config=DifyConfig())


def test_dify_config_validate():
    DifyConfig().validate()
    with pytest.raises(ValueError):
        DifyConfig(max_nodes=0).validate()
    with pytest.raises(ValueError):
        DifyConfig(workflow_name="  ").validate()


def test_build_dify_workflow_has_start_and_end(runner):
    workflow = runner.export_workflow()
    assert isinstance(workflow, DifyWorkflow)
    types = [n.type for n in workflow.nodes]
    assert types[0] == DIFY_NODE_START
    assert types[-1] == DIFY_NODE_END
    assert any(t == DIFY_NODE_TOOL for t in types)


def test_build_dify_workflow_respects_max_nodes(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, max_nodes=1, include_start_end=True)
    tool_nodes = [n for n in workflow.nodes if n.type == DIFY_NODE_TOOL]
    assert len(tool_nodes) == 1


def test_build_dify_workflow_without_start_end(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, include_start_end=False)
    types = {n.type for n in workflow.nodes}
    assert DIFY_NODE_START not in types
    assert DIFY_NODE_END not in types


def test_dify_workflow_to_dict_shape(runner):
    workflow = runner.export_workflow()
    payload = workflow.to_dict()
    assert payload["app"]["mode"] == "workflow"
    assert "nodes" in payload["workflow"]["graph"]
    assert "edges" in payload["workflow"]["graph"]


def test_map_steps_to_dify_trace():
    steps = (
        McpStep(step=1, phase="discover", thought="发现工具"),
        McpStep(step=2, phase="route", thought="路由", tool="faq_lookup", arguments={"query": "x"}),
        McpStep(step=3, phase="call", thought="调用", tool="faq_lookup", observation="obs"),
        McpStep(step=4, phase="answer", thought="汇总", final_answer="reply"),
    )
    events = map_steps_to_dify_trace(steps)
    assert len(events) == 4
    assert events[0].node_type == DIFY_NODE_START
    assert events[-1].node_type == DIFY_NODE_END
    assert events[2].outputs.get("observation") == "obs"


def test_dify_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert len(outcome.dify_trace) == 4


def test_dify_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_dify_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_dify_runner_empty_query(runner):
    outcome = runner.invoke("")
    assert outcome.dify_trace == ()
    assert "有效问题" in outcome.reply


def test_dify_runner_disabled():
    orch = create_orchestrator()
    runner = DifyRunner.from_executor(orch.tool_executor, config=DifyConfig(enabled=False))
    outcome = runner.invoke("客服电话多少")
    assert outcome.dify_trace == ()
    assert "关闭" in outcome.reply


def test_dify_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_dify_config(DifyConfig(workflow_name="custom-workflow", max_nodes=5))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_dify_config()
    assert cfg.workflow_name == "custom-workflow"
    assert cfg.max_nodes == 5
```


---

## 四十八、完整 API 测试

```python
"""Day 45 Dify API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_dify_config_default(client):
    data = client.get("/api/agent/dify-config").json()
    assert data["enabled"] is True
    assert data["workflow_name"] == "nexus-agent-workflow"


def test_put_dify_config(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_nodes"] == 5


def test_dify_export(client):
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 200
    data = resp.json()
    nodes = data["workflow"]["graph"]["nodes"]
    assert any(n["data"]["type"] == "start" for n in nodes)
    assert any(n["data"]["type"] == "end" for n in nodes)
    assert any(n["data"]["type"] == "tool" for n in nodes)


def test_dify_preview_rag(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert len(data["dify_trace"]) == 4


def test_dify_preview_with_history(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_dify_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["dify_config"]["enabled"] is True


def test_chat_dify_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace")
    assert body["kind"] == "dify"


def test_chat_dify_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace") is None
    assert body["kind"] == "faq"


def test_invalid_dify_max_nodes_422(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 999,
        },
    )
    assert resp.status_code == 422


def test_dify_export_disabled_400(client):
    client.put(
        "/api/agent/dify-config",
        json={
            "enabled": False,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 10,
        },
    )
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 400
```


---

## 四十九、课堂 8 分钟录音稿

「打开 dify_bridge，build_dify_workflow 三段：start、工具节点、end。chat 里 dify_trace 挂在 reply 后面。这就是 ZL-NA-REQ-045。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 4 · Day 45 · Dify · ZL-NA-REQ-045 · dify_runner 精读完**
