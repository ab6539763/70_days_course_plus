"""
人工审批配置 — RAG 工具结果需审批后方可输出

需求：ZL-NA-REQ-042
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApprovalConfig:
    """LangGraph 人工审批卡点策略"""

    enabled: bool = True
    require_rag_approval: bool = True
    mock_auto_approve: bool = True
    reviewer_label: str = "值班审核员"
    reject_message: str = "审批未通过，请补充材料后重试。"

    def validate(self) -> None:
        label = (self.reviewer_label or "").strip()
        if not label:
            raise ValueError("reviewer_label 不能为空")
        if len(label) > 32:
            raise ValueError("reviewer_label 过长")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "require_rag_approval": self.require_rag_approval,
            "mock_auto_approve": self.mock_auto_approve,
            "reviewer_label": self.reviewer_label,
            "reject_message": self.reject_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ApprovalConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            require_rag_approval=bool(data.get("require_rag_approval", True)),
            mock_auto_approve=bool(data.get("mock_auto_approve", True)),
            reviewer_label=str(data.get("reviewer_label", "值班审核员")),
            reject_message=str(
                data.get("reject_message", "审批未通过，请补充材料后重试。")
            ),
        )
