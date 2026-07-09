"""
查询改写配置 — 开关、模式与回退策略

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"


@dataclass
class RewriteConfig:
    """检索前查询改写策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_to_original: bool = True
    max_rewrite_len: int = 200

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        if self.max_rewrite_len < 10:
            raise ValueError("max_rewrite_len 须 >= 10")
        if self.max_rewrite_len > 500:
            raise ValueError("max_rewrite_len 须 <= 500")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_to_original": self.fallback_to_original,
            "max_rewrite_len": self.max_rewrite_len,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RewriteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_to_original=bool(data.get("fallback_to_original", True)),
            max_rewrite_len=int(data.get("max_rewrite_len", 200)),
        )
