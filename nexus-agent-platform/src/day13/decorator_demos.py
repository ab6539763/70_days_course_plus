"""
装饰器基础演示 — 无参、带参、functools.wraps

运行：python3 src/day13/decorator_demos.py
"""

from __future__ import annotations

import functools
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def log_call(func):
    """简单装饰器：打印函数名"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  → 调用 {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def repeat(times: int):
    """装饰器工厂：重复执行"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(times):
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


@log_call
def greet(name: str) -> str:
    return f"Hello, {name}"


@repeat(3)
def count() -> int:
    print("    tick")
    return 1


def main() -> None:
    print("=== 装饰器基础 ===\n")
    print("greet('NexusAgent'):", greet("NexusAgent"))
    print("\nrepeat(3):")
    count()


if __name__ == "__main__":
    main()
