"""
继承与抽象类演示

涵盖：继承、super、抽象类 ABC、多态、isinstance

运行：python3 src/day09/inheritance_demos.py
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models import BaseModel, ChatMessage, Contact, ModelConfig


def demo_animal_inheritance():
    print("=== 经典继承示例 ===")

    class Animal:
        def speak(self) -> str:
            return "..."

    class Dog(Animal):
        def speak(self) -> str:
            return "汪汪"

    class Cat(Animal):
        def speak(self) -> str:
            return "喵喵"

    for animal in [Dog(), Cat()]:
        print(animal.speak())


def demo_abstract_shape():
    print("\n=== 抽象类 ABC ===")

    class Shape(ABC):
        @abstractmethod
        def area(self) -> float:
            ...

    class Rectangle(Shape):
        def __init__(self, w: float, h: float):
            self.w, self.h = w, h

        def area(self) -> float:
            return self.w * self.h

    r = Rectangle(3, 4)
    print("矩形面积:", r.area())


def demo_base_model_subclasses():
    print("\n=== BaseModel 子类 ===")
    models: list[BaseModel] = [
        ChatMessage("user", "你好"),
        Contact(1, "张三", "13800138000", "a@b.com"),
        ModelConfig("deepseek-chat", 0.7, 512),
    ]
    for m in models:
        print(f"  {m.model_type}: valid={m.is_valid()}, dict keys={list(m.to_dict().keys())}")


def demo_ensure_valid():
    print("\n=== ensure_valid 与异常 ===")
    good = ChatMessage("user", "ok")
    good.ensure_valid()
    print("  合法消息通过 ensure_valid")

    bad = ChatMessage("bot", "x")
    try:
        bad.ensure_valid()
    except Exception as e:
        print(f"  非法消息: {type(e).__name__}: {e}")


def demo_from_dict_safe():
    print("\n=== from_dict_safe ===")
    obj, err = ChatMessage.from_dict_safe({"role": "user", "content": "安全构造"})
    print("  成功:", obj)
    obj2, err2 = ChatMessage.from_dict_safe({"role": "user", "content": ""})
    print("  失败:", err2)


def main():
    demo_animal_inheritance()
    demo_abstract_shape()
    demo_base_model_subclasses()
    demo_ensure_valid()
    demo_from_dict_safe()


if __name__ == "__main__":
    main()
