"""
LLM 调用配置模型

封装 model / temperature / max_tokens，供 Day 12 client 使用。

需求：ZL-NA-REQ-009
"""

from __future__ import annotations

from models.llm_base import BaseModel

DEFAULT_MODEL = "deepseek-chat"
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0


class ModelConfig(BaseModel):
    """大模型 API 调用参数配置"""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> None:
        self.model = (model or "").strip()
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)

    def validate(self) -> str | None:
        if not self.model:
            return "model 名称不能为空"
        if not (TEMPERATURE_MIN <= self.temperature <= TEMPERATURE_MAX):
            return f"temperature 须在 {TEMPERATURE_MIN}-{TEMPERATURE_MAX} 之间"
        if self.max_tokens <= 0:
            return "max_tokens 必须为正整数"
        return None

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelConfig:
        return cls(
            model=data.get("model", DEFAULT_MODEL),
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=int(data.get("max_tokens", 1024)),
        )

    def to_api_params(self) -> dict:
        """导出为 API 请求参数字段（不含 messages）"""
        self.ensure_valid()
        return self.to_dict()

    def __repr__(self) -> str:
        return (
            f"ModelConfig(model={self.model!r}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )
