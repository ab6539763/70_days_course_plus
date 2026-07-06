"""
领域模型抽象基类 — NexusAgent 模型体系根基

所有可序列化、可校验的领域对象（ChatMessage、Contact、ModelConfig 等）
均继承 BaseModel，统一 validate / to_dict / from_dict 契约。

Day 23 Pydantic 模型将与此概念对齐；今日为轻量自研实现。

需求：ZL-NA-REQ-009

作者：NexusAgent 项目组
创建日期：2026-07-14
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T", bound="BaseModel")


class ModelValidationError(ValueError):
    """模型校验失败时抛出"""

    def __init__(self, message: str, *, model_type: str = "BaseModel") -> None:
        self.model_type = model_type
        super().__init__(f"[{model_type}] {message}")


class BaseModel(ABC):
    """
    领域模型抽象基类

    子类必须实现：
        - validate() -> str | None
        - to_dict() -> dict
        - from_dict(data) -> 子类实例
    """

    @abstractmethod
    def validate(self) -> str | None:
        """
        校验模型状态

        Returns:
            错误消息；通过则返回 None
        """

    @abstractmethod
    def to_dict(self) -> dict:
        """序列化为 dict（可 JSON 化）"""

    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], data: dict) -> T:
        """从 dict 反序列化"""

    @property
    def model_type(self) -> str:
        """模型类名，用于日志与错误消息"""
        return self.__class__.__name__

    def is_valid(self) -> bool:
        """是否通过 validate"""
        return self.validate() is None

    def ensure_valid(self) -> None:
        """校验失败则抛出 ModelValidationError"""
        err = self.validate()
        if err:
            raise ModelValidationError(err, model_type=self.model_type)

    def to_json_ready(self) -> dict:
        """ensure_valid 后返回 to_dict（持久化前调用）"""
        self.ensure_valid()
        return self.to_dict()

    @classmethod
    def from_dict_safe(cls: type[T], data: dict) -> tuple[T | None, str | None]:
        """
        安全构造：返回 (instance, error)

        适合 CLI 层，不抛异常。
        """
        try:
            obj = cls.from_dict(data)
        except (TypeError, ValueError, KeyError) as exc:
            return None, f"反序列化失败：{exc}"
        err = obj.validate()
        if err:
            return None, err
        return obj, None

    def __repr__(self) -> str:
        return f"{self.model_type}()"
