"""
pathlib 文件操作演示

运行：python3 src/day11/file_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.paths import get_path


def demo_path_basics() -> None:
    sample = get_path("sample_docs")
    print("=== pathlib 基础 ===")
    print(f"目录: {sample}")
    print(f"存在: {sample.exists()}")
    print(f"父目录: {sample.parent.name}")
    print(f"是否为目录: {sample.is_dir()}")


def demo_read_write(tmp_dir: Path | None = None) -> None:
    print("\n=== 读写文本 ===")
    target = (tmp_dir or Path("/tmp")) / "nexus_day11_demo.txt"
    target.write_text("  智链科技   内部资料  \n", encoding="utf-8")
    raw = target.read_text(encoding="utf-8")
    print(f"写入 → 读取: {raw!r}")
    print(f"字节大小: {target.stat().st_size}")


def main() -> None:
    demo_path_basics()
    demo_read_write()


if __name__ == "__main__":
    main()
