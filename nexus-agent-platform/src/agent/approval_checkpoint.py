"""
审批中断检查点 — 支持人工审批后恢复执行

需求：ZL-NA-REQ-042
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from agent.graph_state import AgentGraphState


@dataclass
class ApprovalCheckpoint:
    checkpoint_id: str
    state: AgentGraphState
    steps: list[dict[str, Any]] = field(default_factory=list)
    node_path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "state": self.state.to_dict(),
            "steps": list(self.steps),
            "node_path": list(self.node_path),
        }


class ApprovalCheckpointStore:
    """内存检查点仓库 — 教学环境足够"""

    def __init__(self) -> None:
        self._checkpoints: dict[str, ApprovalCheckpoint] = {}

    def save(
        self,
        state: AgentGraphState,
        *,
        steps: list[dict[str, Any]] | None = None,
        node_path: list[str] | None = None,
        checkpoint_id: str | None = None,
    ) -> ApprovalCheckpoint:
        cid = checkpoint_id or str(uuid.uuid4())
        state.checkpoint_id = cid
        cp = ApprovalCheckpoint(
            checkpoint_id=cid,
            state=AgentGraphState.from_dict(state.to_dict()),
            steps=list(steps or []),
            node_path=list(node_path or []),
        )
        self._checkpoints[cid] = cp
        return cp

    def get(self, checkpoint_id: str) -> ApprovalCheckpoint | None:
        return self._checkpoints.get(checkpoint_id)

    def delete(self, checkpoint_id: str) -> bool:
        return self._checkpoints.pop(checkpoint_id, None) is not None

    def clear(self) -> None:
        self._checkpoints.clear()


approval_checkpoint_store = ApprovalCheckpointStore()
