"""
模块与 import 演示

涵盖：import/from、__name__、__all__、包内相对导入概念

运行：python3 src/day10/module_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.bootstrap import ensure_importable, setup_python_path
from core.paths import SRC_ROOT, get_path


def demo_name_main():
    print("=== __name__ ===")
    print(f"本模块 __name__ = {__name__!r}")
    print("直接运行时 __name__ 为 __main__，被 import 时为模块名")


def demo_import_styles():
    print("\n=== import 风格 ===")
    # 绝对导入（推荐）
    from models import ChatMessage
    from utils.json_utils import load_json

    msg = ChatMessage("user", "import 测试")
    print(msg)

    # 从 core 导入
    from core import get_path
    print("messages 路径:", get_path("messages"))


def demo_bootstrap():
    print("\n=== bootstrap ===")
    root = setup_python_path()
    print("SRC_ROOT:", root)
    ensure_importable("core", "models", "utils", "services")
    print("核心包导入检查通过")


def demo_package_list():
    print("\n=== 包目录 ===")
    for name in ("core", "models", "services", "llm", "chat", "tools"):
        pkg_dir = SRC_ROOT / name
        init = pkg_dir / "__init__.py"
        status = "OK" if init.exists() else "MISSING"
        print(f"  {name:10} [{status}]")


def main():
    demo_name_main()
    demo_import_styles()
    demo_bootstrap()
    demo_package_list()


if __name__ == "__main__":
    main()
