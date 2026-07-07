"""
glob 模式遍历演示

运行：python3 src/day11/glob_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.paths import get_path
from tools.doc_reader import iter_text_files


def main() -> None:
    sample_dir = get_path("sample_docs")
    print("=== glob 遍历 sample_docs ===\n")

    files = list(iter_text_files(sample_dir, "*.txt"))
    for path in files:
        print(f"  📄 {path.name}  ({path.stat().st_size} bytes)")

    print(f"\n共 {len(files)} 个 .txt 文件")


if __name__ == "__main__":
    main()
