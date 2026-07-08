"""
Rerank 配置 — 候选池大小、开关与模型标识

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODEL_MOCK = "mock"


@dataclass
class RerankConfig:
    """混合召回后的交叉编码器重排策略"""

    enabled: bool = True
    candidate_pool: int = 20
    model: str = MODEL_MOCK

    def validate(self) -> None:
        if self.candidate_pool < 1:
            raise ValueError("candidate_pool 须 >= 1")
        if self.candidate_pool > 100:
            raise ValueError("candidate_pool 须 <= 100")
        if self.model not in (MODEL_MOCK,):
            raise ValueError(f"model 须为 mock，收到 {self.model!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "candidate_pool": self.candidate_pool,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RerankConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            candidate_pool=int(data.get("candidate_pool", 20)),
            model=str(data.get("model", MODEL_MOCK)),
        )
