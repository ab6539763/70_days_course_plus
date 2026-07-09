"""
文本清洗工具

从 Day 2 text_cleaner 抽取的核心函数，供全项目复用。
Day 28 RAG 预处理将直接 import 本模块。
"""

from __future__ import annotations

# 敏感词表（Day 11 改配置文件）
SENSITIVE_WORDS = [
    "内部资料",
    "禁止外传",
    "机密",
    "保密",
]

MASK_TOKEN = "***"


def collapse_whitespace(text: str) -> str:
    """合并连续空白为单个空格"""
    result: list[str] = []
    prev_space = False
    for char in text:
        if char in (" ", "\t"):
            if not prev_space:
                result.append(" ")
                prev_space = True
        else:
            result.append(char)
            prev_space = False
    return "".join(result)


def collapse_duplicate_punctuation(text: str) -> str:
    """合并连续相同非字母数字字符"""
    if not text:
        return text
    result: list[str] = [text[0]]
    for char in text[1:]:
        if char == result[-1] and not char.isalnum():
            continue
        result.append(char)
    return "".join(result)


def mask_sensitive_words(text: str, words: list[str] | None = None) -> tuple[str, int]:
    """敏感词替换，返回 (新文本, 替换次数)"""
    words = words or SENSITIVE_WORDS
    count = 0
    result = text
    for word in words:
        if not word:
            continue
        lower_word = word.lower()
        lower_result = result.lower()
        start = 0
        while True:
            idx = lower_result.find(lower_word, start)
            if idx == -1:
                break
            result = result[:idx] + MASK_TOKEN + result[idx + len(word) :]
            lower_result = result.lower()
            count += 1
            start = idx + len(MASK_TOKEN)
    return result, count


def clean_text(raw: str, *, to_lower: bool = False, sensitive_words: list[str] | None = None) -> tuple[str, dict]:
    """
    完整文本清洗管道

    Returns:
        (清洗后文本, 统计 dict)
    """
    stats = {
        "raw_len": len(raw),
        "replace_count": 0,
        "empty_dropped": 0,
        "raw_lines": len(raw.splitlines()),
    }
    cleaned_lines: list[str] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            stats["empty_dropped"] += 1
            continue
        line = collapse_whitespace(line)
        line = collapse_duplicate_punctuation(line)
        line, n = mask_sensitive_words(line, sensitive_words)
        stats["replace_count"] += n
        if to_lower:
            line = line.lower()
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)
    stats["clean_len"] = len(result)
    stats["clean_lines"] = len(cleaned_lines)
    return result, stats
