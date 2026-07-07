"""
doc_reader 批量清洗演示 — Day 11 主入口

替代 Day 3 platform_cli 的批处理逻辑，使用 tools 生产层。

运行：python3 src/day11/doc_reader_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.paths import get_path
from tools.doc_reader import batch_clean_directory


def main() -> int:
    input_dir = get_path("sample_docs")
    output_dir = get_path("doc_output")

    print("=" * 48)
    print("  NexusAgent doc_reader 批量清洗")
    print("=" * 48)
    print(f"  输入: {input_dir}")
    print(f"  输出: {output_dir}\n")

    records = batch_clean_directory(input_dir, output_dir, mask_phone=True)

    if not records:
        print("  ⚠️  未找到可处理文件")
        return 0

    for record in records:
        stats = record.stats
        raw_len = stats.get("raw_len", 0)
        clean_len = stats.get("clean_len", 0)
        ratio = (raw_len - clean_len) / raw_len if raw_len else 0.0
        print(f"  ✅ {record.name}")
        print(f"     编码 {record.encoding} | 压缩率 {ratio:.1%}")
        print(f"     敏感词 {stats.get('replace_count', 0)} | 手机 {stats.get('phone_masked', 0)}")

    print(f"\n  共处理 {len(records)} 个文件")
    print("=" * 48)
    return 0


if __name__ == "__main__":
    sys.exit(main())
