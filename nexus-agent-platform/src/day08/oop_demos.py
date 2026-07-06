"""
面向对象基础演示

涵盖：class 定义、__init__、实例方法、@classmethod、__str__/__repr__

运行：python3 src/day08/oop_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models.message import ChatMessage


def demo_basic_class():
    print("=== 基本类与实例 ===")

    class Dog:
        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

        def bark(self) -> str:
            return f"{self.name}: 汪汪！"

    d = Dog("Lucky", 3)
    print(d.bark())
    print(f"name={d.name}, age={d.age}")


def demo_chat_message():
    print("\n=== ChatMessage 类 ===")
    msg = ChatMessage("user", "你好，NexusAgent！")
    print("str:", msg)
    print("repr:", repr(msg))
    print("dict:", msg.to_dict())
    print("API:", msg.to_api_message())


def demo_from_dict():
    print("\n=== from_dict 反序列化 ===")
    raw = {"role": "assistant", "content": "你好，有什么可以帮您？"}
    msg = ChatMessage.from_dict(raw)
    print(msg)
    print("is_assistant:", msg.is_assistant())


def demo_validation():
    print("\n=== validate 校验 ===")
    bad = ChatMessage("bot", "")
    print("错误:", bad.validate())
    good = ChatMessage("user", "合法消息")
    print("合法:", good.validate())


def demo_classmethod():
    print("\n=== 类方法 from_api_response ===")
    parsed = {
        "role": "assistant",
        "content": "根据产品说明书，年化收益率约为 3.5%。",
    }
    msg = ChatMessage.from_api_response(parsed)
    print(msg)


def main():
    demo_basic_class()
    demo_chat_message()
    demo_from_dict()
    demo_validation()
    demo_classmethod()


if __name__ == "__main__":
    main()
