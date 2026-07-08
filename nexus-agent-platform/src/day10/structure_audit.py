"""
包结构审计脚本

检查 Day 10 要求的生产包是否就位。

运行：python3 src/day10/structure_audit.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day10.constants import REQUIRED_PACKAGES


def check_packages() -> list[str]:
    errors = []
    for name in REQUIRED_PACKAGES:
        init = _SRC / name / "__init__.py"
        if not init.exists():
            errors.append(f"缺少包: {name}/__init__.py")
    return errors


def check_no_circular_hint() -> list[str]:
    """简单检查 core 不 import day10"""
    core_init = _SRC / "core" / "__init__.py"
    text = core_init.read_text(encoding="utf-8")
    warnings = []
    if "day10" in text or "day0" in text:
        warnings.append("core/__init__.py 不应 import dayXX")
    return warnings


def main() -> int:
    print("=" * 44)
    print("  NexusAgent 包结构审计")
    print("=" * 44)
    errors = check_packages()
    warnings = check_no_circular_hint()

    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ 必需包齐全: {', '.join(REQUIRED_PACKAGES)}")

    for w in warnings:
        print(f"  ⚠️  {w}")

    from core.bootstrap import ensure_importable
    try:
        ensure_importable("core", "models", "services")
        print("  ✅ 核心模块可导入")
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        errors.append(str(e))

    print("=" * 44)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
