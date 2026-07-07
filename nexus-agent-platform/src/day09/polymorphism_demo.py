"""
多态与模型注册表

演示：同一接口 validate/to_dict 处理不同 BaseModel 子类。

运行：python3 src/day09/polymorphism_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models import BaseModel, ChatMessage, Contact, ModelConfig, ModelValidationError


class ModelRegistry:
    """BaseModel 子类注册表 — Day 39 工具注册的雏形"""

    def __init__(self) -> None:
        self._items: list[BaseModel] = []

    def register(self, model: BaseModel) -> str | None:
        err = model.validate()
        if err:
            return err
        self._items.append(model)
        return None

    def validate_all(self) -> list[str]:
        errors = []
        for i, m in enumerate(self._items):
            err = m.validate()
            if err:
                errors.append(f"[{i}] {m.model_type}: {err}")
        return errors

    def export_all(self) -> list[dict]:
        return [m.to_dict() for m in self._items if m.is_valid()]

    def count_by_type(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for m in self._items:
            stats[m.model_type] = stats.get(m.model_type, 0) + 1
        return stats


def serialize_models(models: list[BaseModel]) -> list[dict]:
    """多态：不关心具体类型，只调用 BaseModel 接口"""
    result = []
    for m in models:
        m.ensure_valid()
        result.append(m.to_dict())
    return result


def main():
    print("=" * 44)
    print("  多态演示 — ModelRegistry")
    print("=" * 44)

    registry = ModelRegistry()
    samples = [
        ChatMessage("system", "你是助手"),
        ChatMessage("user", "查询余额"),
        Contact(1, "李四", "13800138001", "l@b.com"),
        ModelConfig(temperature=0.5),
    ]
    for s in samples:
        err = registry.register(s)
        if err:
            print(f"  跳过: {err}")
        else:
            print(f"  注册: {s.model_type}")

    print("\n按类型统计:", registry.count_by_type())
    print("批量导出条数:", len(registry.export_all()))

    print("\nserialize_models 多态调用:")
    try:
        data = serialize_models(samples)
        print(f"  序列化 {len(data)} 条")
    except ModelValidationError as e:
        print(f"  校验失败: {e}")


if __name__ == "__main__":
    main()
