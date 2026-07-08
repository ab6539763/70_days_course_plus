"""
函数特性演示

涵盖：默认参数、*args、**kwargs、lambda、递归、作用域

运行：python src/day06/function_demos.py
"""

from __future__ import annotations


def demo_basic():
    print("=== 基本函数 ===")

    def add(a: int, b: int) -> int:
        return a + b

    print("add(3,5) =", add(3, 5))


def demo_default_and_kwargs():
    print("\n=== 默认参数与 **kwargs ===")

    def build_config(model: str, temperature: float = 0.7, **extra):
        config = {"model": model, "temperature": temperature}
        config.update(extra)
        return config

    cfg = build_config("deepseek-chat", max_tokens=1024, stream=False)
    print(cfg)


def demo_args():
    print("\n=== *args ===")

    def summarize(prefix: str, *items):
        return f"{prefix}: " + ", ".join(str(i) for i in items)

    print(summarize("待办", "清洗", "CLI", "JSON"))


def demo_lambda():
    print("\n=== lambda ===")
    todos = [
        {"id": 1, "priority": 3, "done": False},
        {"id": 2, "priority": 1, "done": True},
    ]
    sorted_todos = sorted(todos, key=lambda t: (t["done"], t["priority"]))
    print(sorted_todos)


def demo_recursion():
    print("\n=== 递归 ===")

    def factorial(n: int) -> int:
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    print("5! =", factorial(5))


def demo_scope():
    print("\n=== 作用域 ===")
    x = "global"

    def outer():
        x = "enclosing"

        def inner():
            nonlocal x
            x = "local"
            return x

        return inner()

    print(outer(), "| global:", x)


def main():
    demo_basic()
    demo_default_and_kwargs()
    demo_args()
    demo_lambda()
    demo_recursion()
    demo_scope()


if __name__ == "__main__":
    main()
