"""
异常处理演示

涵盖：try/except、异常层次、raise from、自定义 NexusError

运行：python3 src/day10/exception_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.exceptions import (
    ConfigError,
    JsonParseError,
    ModelValidationError,
    NexusError,
    StorageError,
)
from models import ChatMessage, ModelConfig


def demo_catch_specific():
    print("=== 捕获具体异常 ===")
    try:
        ChatMessage("bot", "hi").ensure_valid()
    except ModelValidationError as e:
        print(f"  ModelValidationError: {e}")
        print(f"  code={e.code}, model_type={getattr(e, 'model_type', '?')}")


def demo_catch_base():
    print("\n=== 捕获 NexusError 基类 ===")
    errors = [
        ConfigError("缺少 API Key"),
        ModelValidationError("内容为空", model_type="ChatMessage"),
        StorageError("磁盘满", path="/tmp/x.json"),
    ]
    for err in errors:
        try:
            raise err
        except NexusError as e:
            print(f"  [{e.code}] {e.message}")


def demo_valueerror_compat():
    print("\n=== ValueError 兼容 ===")
    try:
        ModelConfig(temperature=9.9).ensure_valid()
    except ValueError as e:
        print(f"  可用 except ValueError 捕获: {e}")


def demo_raise_from():
    print("\n=== raise from 链 ===")
    try:
        int("not-a-number")
    except ValueError as exc:
        wrapped = JsonParseError("字段类型错误", path="data.json")
        try:
            raise wrapped from exc
        except JsonParseError as e:
            print(f"  {e}")
            print(f"  __cause__: {e.__cause__}")


def demo_no_bare_except():
    print("\n=== 避免 bare except ===")
    print("  不要用 except: 吞掉所有异常")
    print("  推荐 except NexusError / except OSError 等具体类型")


def main():
    demo_catch_specific()
    demo_catch_base()
    demo_valueerror_compat()
    demo_raise_from()
    demo_no_bare_except()


if __name__ == "__main__":
    main()
