"""
分块参数配置 — chunk_size / overlap / strategy

需求：ZL-NA-REQ-027
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ChunkConfig:
    """知识库分块参数（可持久化、可 A/B 对比）"""

    chunk_size: int = 200
    overlap: int = 40
    strategy: str = "auto"  # auto | fixed | markdown
    name: str = "default"

    def validate(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size 必须为正整数")
        if self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")
        if self.strategy not in ("auto", "fixed", "markdown"):
            raise ValueError("strategy 须为 auto / fixed / markdown")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkConfig:
        return cls(
            chunk_size=int(data.get("chunk_size", 200)),
            overlap=int(data.get("overlap", 40)),
            strategy=str(data.get("strategy", "auto")),
            name=str(data.get("name", "default")),
        )


DEFAULT_CHUNK_CONFIG = ChunkConfig()

PRESET_CONFIGS: tuple[ChunkConfig, ...] = (
    ChunkConfig(name="compact", chunk_size=120, overlap=20, strategy="auto"),
    ChunkConfig(name="default", chunk_size=200, overlap=40, strategy="auto"),
    ChunkConfig(name="wide", chunk_size=400, overlap=60, strategy="auto"),
    ChunkConfig(name="markdown_wide", chunk_size=500, overlap=50, strategy="markdown"),
)
