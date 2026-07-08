"""
检索配置 — 关键词 / 向量 / 混合模式与融合参数

需求：ZL-NA-REQ-031
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MODE_VECTOR = "vector"
MODE_KEYWORD = "keyword"
MODE_HYBRID = "hybrid"
FUSION_WEIGHTED = "weighted"
FUSION_RRF = "rrf"


@dataclass
class RetrievalConfig:
    """知识库检索策略配置"""

    mode: str = MODE_HYBRID
    keyword_weight: float = 0.35
    vector_weight: float = 0.65
    fusion: str = FUSION_WEIGHTED
    rrf_k: int = 60

    def validate(self) -> None:
        if self.mode not in (MODE_VECTOR, MODE_KEYWORD, MODE_HYBRID):
            raise ValueError(f"mode 须为 vector|keyword|hybrid，收到 {self.mode!r}")
        if self.fusion not in (FUSION_WEIGHTED, FUSION_RRF):
            raise ValueError(f"fusion 须为 weighted|rrf，收到 {self.fusion!r}")
        if self.mode == MODE_HYBRID:
            total = self.keyword_weight + self.vector_weight
            if total <= 0:
                raise ValueError("混合模式下 keyword_weight + vector_weight 须 > 0")
        if self.rrf_k < 1:
            raise ValueError("rrf_k 须 >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "keyword_weight": round(self.keyword_weight, 4),
            "vector_weight": round(self.vector_weight, 4),
            "fusion": self.fusion,
            "rrf_k": self.rrf_k,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RetrievalConfig:
        if not data:
            return cls()
        return cls(
            mode=str(data.get("mode", MODE_HYBRID)),
            keyword_weight=float(data.get("keyword_weight", 0.35)),
            vector_weight=float(data.get("vector_weight", 0.65)),
            fusion=str(data.get("fusion", FUSION_WEIGHTED)),
            rrf_k=int(data.get("rrf_k", 60)),
        )
