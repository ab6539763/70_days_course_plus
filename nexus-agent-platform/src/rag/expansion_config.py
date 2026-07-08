"""
多查询扩展配置 — HyDE / 模板变体开关与上限

需求：ZL-NA-REQ-035
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_TEMPLATES = "templates"
MODE_HYDE_MOCK = "hyde_mock"


@dataclass
class ExpansionConfig:
    """检索前多 query 扩展策略"""

    enabled: bool = True
    mode: str = MODE_TEMPLATES
    max_queries: int = 4
    include_original: bool = True
    per_query_top_k: int = 5

    def validate(self) -> None:
        if self.mode not in (MODE_TEMPLATES, MODE_HYDE_MOCK):
            raise ValueError(f"mode 须为 templates 或 hyde_mock，收到 {self.mode!r}")
        if self.max_queries < 1:
            raise ValueError("max_queries 须 >= 1")
        if self.max_queries > 8:
            raise ValueError("max_queries 须 <= 8")
        if self.per_query_top_k < 1:
            raise ValueError("per_query_top_k 须 >= 1")
        if self.per_query_top_k > 20:
            raise ValueError("per_query_top_k 须 <= 20")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "max_queries": self.max_queries,
            "include_original": self.include_original,
            "per_query_top_k": self.per_query_top_k,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ExpansionConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_TEMPLATES)),
            max_queries=int(data.get("max_queries", 4)),
            include_original=bool(data.get("include_original", True)),
            per_query_top_k=int(data.get("per_query_top_k", 5)),
        )
