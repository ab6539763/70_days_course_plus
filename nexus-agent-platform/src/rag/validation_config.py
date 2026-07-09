"""
答案校验配置 — Self-RAG 生成后引用一致性检查

需求：ZL-NA-REQ-037
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_OVERLAP = "overlap"
MODE_STRICT = "strict"

REFUSAL_MESSAGE = (
    "根据现有引用无法确认该回答的准确性，请查阅引用来源或换个问法。"
)


@dataclass
class ValidationConfig:
    """Self-RAG 答案校验策略"""

    enabled: bool = True
    mode: str = MODE_OVERLAP
    min_score: float = 0.35
    refuse_on_fail: bool = True
    retry_on_fail: bool = False
    max_retries: int = 1

    def validate(self) -> None:
        if self.mode not in (MODE_OVERLAP, MODE_STRICT):
            raise ValueError(f"mode 须为 overlap 或 strict，收到 {self.mode!r}")
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score 须在 0~1，收到 {self.min_score}")
        if self.max_retries < 0 or self.max_retries > 3:
            raise ValueError(f"max_retries 须在 0~3，收到 {self.max_retries}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "min_score": round(self.min_score, 4),
            "refuse_on_fail": self.refuse_on_fail,
            "retry_on_fail": self.retry_on_fail,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_OVERLAP)),
            min_score=float(data.get("min_score", 0.35)),
            refuse_on_fail=bool(data.get("refuse_on_fail", True)),
            retry_on_fail=bool(data.get("retry_on_fail", False)),
            max_retries=int(data.get("max_retries", 1)),
        )
