"""Day 11 常量"""

from __future__ import annotations

from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent

OUTPUT_DIR_REL = "day11/output"
SAMPLE_GLOB = "*.txt"

# 教学用敏感词配置文件（相对 src/）
SENSITIVE_WORDS_REL = "day11/config/sensitive_words.txt"
