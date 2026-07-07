"""
猜数字游戏

练习 while 循环、if/elif/else 分支、break/continue。

规则：
    - 系统随机生成 1-100 的整数
    - 用户最多猜 10 次
    - 每次提示「大了」或「小了」
    - 猜对后 break 退出
    - 非法输入使用 continue 不计入次数

使用方式：
    python src/day03/guess_number.py

需求文档：ZL-NA-REQ-003（子功能 ZL-NA-013）
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent


def _load_constants():
    path = _CURRENT_DIR / "constants.py"
    spec = importlib.util.spec_from_file_location("day03_constants", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cfg = _load_constants()
GUESS_MIN = _cfg.GUESS_MIN
GUESS_MAX = _cfg.GUESS_MAX
GUESS_MAX_ATTEMPTS = _cfg.GUESS_MAX_ATTEMPTS


def play_guess_number(
    min_val: int = GUESS_MIN,
    max_val: int = GUESS_MAX,
    max_attempts: int = GUESS_MAX_ATTEMPTS,
) -> None:
    """
    运行猜数字游戏主逻辑

    Args:
        min_val: 随机数下限（含）
        max_val: 随机数上限（含）
        max_attempts: 最大猜测次数
    """
    target = random.randint(min_val, max_val)
    attempts = 0

    print()
    print("=" * 40)
    print(f"  猜数字游戏：{min_val}-{max_val}")
    print(f"  你有 {max_attempts} 次机会")
    print("=" * 40)
    print()

    # while 循环：未猜对且未超过次数时继续
    while attempts < max_attempts:
        guess_str = input(f"第 {attempts + 1} 次猜测：").strip()

        # 输入校验：非数字则 continue，不增加 attempts
        if not guess_str.lstrip("-").isdigit():
            print("  ⚠️  请输入整数")
            continue

        guess = int(guess_str)
        attempts += 1

        # 分支判断
        if guess == target:
            print(f"  🎉 恭喜！猜对了！答案就是 {target}，用了 {attempts} 次")
            return
        elif guess > target:
            print("  📉 大了")
        else:
            print("  📈 小了")

        remaining = max_attempts - attempts
        if remaining > 0:
            print(f"  还剩 {remaining} 次机会")
        print()

    # while 正常结束（未 break）= 次数用尽
    print(f"😢 次数用尽！正确答案是 {target}")


def main() -> None:
    """程序入口"""
    play_guess_number()


if __name__ == "__main__":
    main()
