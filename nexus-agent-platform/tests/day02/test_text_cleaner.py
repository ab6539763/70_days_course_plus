"""Day 2 text_cleaner 单元测试"""

import importlib.util
import sys
from pathlib import Path

import pytest

DAY02_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "day02"


def _load_module(name: str, filepath: Path):
    """加载 day02 模块，避免与 day01 等同名模块冲突"""
    spec = importlib.util.spec_from_file_location(f"test_day02_{name}", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_text_cleaner = _load_module("text_cleaner", DAY02_DIR / "text_cleaner.py")

clean_text = _text_cleaner.clean_text
collapse_whitespace = _text_cleaner.collapse_whitespace
collapse_duplicate_punctuation = _text_cleaner.collapse_duplicate_punctuation
mask_sensitive_words = _text_cleaner.mask_sensitive_words
format_report = _text_cleaner.format_report


class TestCollapseWhitespace:
    def test_multiple_spaces(self):
        assert collapse_whitespace("a    b") == "a b"

    def test_tabs(self):
        assert collapse_whitespace("a\t\tb") == "a b"

    def test_leading_trailing(self):
        # collapse_whitespace 不处理首尾，由 strip 处理
        assert collapse_whitespace("  a  ") == " a "


class TestCollapsePunctuation:
    def test_exclamation(self):
        assert collapse_duplicate_punctuation("!!!") == "!"

    def test_chinese_punctuation(self):
        assert collapse_duplicate_punctuation("。。") == "。"

    def test_preserve_letters(self):
        assert collapse_duplicate_punctuation("aaa") == "aaa"


class TestMaskSensitiveWords:
    def test_basic(self):
        result, count = mask_sensitive_words("【内部资料】", ["内部资料"])
        assert "***" in result
        assert count == 1

    def test_case_insensitive(self):
        result, count = mask_sensitive_words("SECRET 机密 file", ["机密"])
        assert count >= 1


class TestCleanText:
    def test_trim_and_collapse(self):
        raw = "  Hello   World  "
        cleaned, stats = clean_text(raw)
        assert cleaned == "Hello World"

    def test_drop_empty_lines(self):
        raw = "line1\n\n\nline2"
        cleaned, stats = clean_text(raw)
        assert stats["empty_dropped"] == 2
        assert cleaned == "line1\nline2"

    def test_sensitive_word(self):
        raw = "这是内部资料"
        cleaned, stats = clean_text(raw)
        assert "***" in cleaned
        assert stats["replace_count"] >= 1

    def test_lower_option(self):
        raw = "API"
        cleaned, _ = clean_text(raw, to_lower=True)
        assert cleaned == "api"

    def test_punctuation_collapse(self):
        raw = "注意！！！"
        cleaned, _ = clean_text(raw)
        assert "!!!" not in cleaned


class TestFormatReport:
    def test_report_contains_fields(self):
        stats = {
            "raw_len": 100,
            "clean_len": 80,
            "replace_count": 2,
            "empty_dropped": 1,
            "raw_lines": 5,
            "clean_lines": 4,
        }
        report = format_report("test.txt", stats)
        assert "test.txt" in report
        assert "20.0%" in report

    def test_zero_raw_len(self):
        stats = {
            "raw_len": 0,
            "clean_len": 0,
            "replace_count": 0,
            "empty_dropped": 0,
            "raw_lines": 0,
            "clean_lines": 0,
        }
        report = format_report("empty", stats)
        assert "0.0%" in report


class TestSampleDocs:
    @pytest.mark.parametrize(
        "filename",
        ["raw_notice.txt", "raw_faq.txt", "raw_policy.txt"],
    )
    def test_sample_docs_clean(self, filename):
        path = DAY02_DIR / "sample_docs" / filename
        raw = path.read_text(encoding="utf-8")
        cleaned, stats = clean_text(raw)
        assert len(cleaned) <= len(raw)
        assert stats["clean_len"] == len(cleaned)
