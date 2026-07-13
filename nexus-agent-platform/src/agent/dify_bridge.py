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
