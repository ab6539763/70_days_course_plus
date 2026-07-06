"""
Day 6 作业练习 02 — *args 与 **kwargs
"""

from __future__ import annotations


def build_prompt(template: str, **variables) -> str:
    """使用 template 与 variables 生成最终字符串"""
    raise NotImplementedError


def main() -> None:
    s = build_prompt("你好 {name}，任务：{task}", name="Nexus", task="utils")
    print(s)


if __name__ == "__main__":
    main()
