"""
引用溯源配置 — 开关、条数上限与预览长度

需求：ZL-NA-REQ-034
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CitationConfig:
    """RAG 引用溯源展示策略"""

    enabled: bool = True
    max_citations: int = 3
    preview_max_chars: int = 120
    include_rewrite_meta: bool = True
    include_expansion_meta: bool = True
    include_route_meta: bool = True

    def validate(self) -> None:
        if self.max_citations < 1:
            raise ValueError("max_citations 须 >= 1")
        if self.max_citations > 10:
            raise ValueError("max_citations 须 <= 10")
        if self.preview_max_chars < 20:
            raise ValueError("preview_max_chars 须 >= 20")
        if self.preview_max_chars > 500:
            raise ValueError("preview_max_chars 须 <= 500")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_citations": self.max_citations,
            "preview_max_chars": self.preview_max_chars,
            "include_rewrite_meta": self.include_rewrite_meta,
            "include_expansion_meta": self.include_expansion_meta,
            "include_route_meta": self.include_route_meta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CitationConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_citations=int(data.get("max_citations", 3)),
            preview_max_chars=int(data.get("preview_max_chars", 120)),
            include_rewrite_meta=bool(data.get("include_rewrite_meta", True)),
            include_expansion_meta=bool(data.get("include_expansion_meta", True)),
            include_route_meta=bool(data.get("include_route_meta", True)),
        )
