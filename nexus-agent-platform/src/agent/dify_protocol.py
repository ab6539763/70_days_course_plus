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
