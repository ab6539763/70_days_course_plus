"""
编码回退读取演示

运行：python3 src/day11/encoding_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from tools.doc_reader import read_text_file


def main() -> None:
    demo_dir = Path(__file__).resolve().parent / "sample_encoding"
    demo_dir.mkdir(exist_ok=True)

    utf8_path = demo_dir / "utf8.txt"
    utf8_path.write_text("UTF-8 中文测试", encoding="utf-8")

    gbk_path = demo_dir / "gbk.txt"
    gbk_path.write_bytes("GBK 中文测试".encode("gbk"))

    print("=== 编码自动检测（回退链）===\n")
    for path in sorted(demo_dir.glob("*.txt")):
        content, encoding = read_text_file(path)
        print(f"  {path.name}: encoding={encoding}, content={content!r}")


if __name__ == "__main__":
    main()
