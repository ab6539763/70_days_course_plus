"""utils 包单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.formatters import format_box_report, format_todo_line
from utils.json_utils import ensure_dict_keys, load_json, save_json
from utils.text_utils import clean_text, collapse_whitespace, mask_sensitive_words
from utils.validators import parse_positive_int, parse_priority, require_non_empty, validate_email, validate_phone


def test_clean_text():
    text, stats = clean_text("  a  b  \n\nline2")
    assert "a b" in text
    assert stats["empty_dropped"] >= 1


def test_collapse_whitespace():
    assert collapse_whitespace("a    b\t\tc") == "a b c"


def test_mask_sensitive():
    masked, n = mask_sensitive_words("这是内部资料")
    assert "内部资料" not in masked
    assert n >= 1


def test_require_non_empty():
    assert require_non_empty("", "标题") is not None
    assert require_non_empty("ok", "标题") is None


def test_parse_priority():
    assert parse_priority("1") == 1
    assert parse_priority("2") == 2
    assert parse_priority("") == 2
    assert parse_priority("9") == 2


def test_parse_positive_int():
    assert parse_positive_int("3") == 3
    assert parse_positive_int("0") is None
    assert parse_positive_int("x") is None


def test_validate_email():
    assert validate_email("a@b.c") is None
    assert validate_email("bad") is not None


def test_validate_phone():
    assert validate_phone("13800138000") is None
    assert validate_phone("23800138000") is not None
    assert validate_phone("138") is not None


def test_load_save_json(tmp_path):
    p = tmp_path / "t.json"
    save_json(p, {"a": 1})
    assert load_json(p)["a"] == 1
    assert load_json(tmp_path / "missing.json", default={}) == {}


def test_ensure_dict_keys():
    d = ensure_dict_keys({"x": 1}, {"x": 0, "y": 0})
    assert d["y"] == 0


def test_format_box_report():
    out = format_box_report("标题", ["行1", "行2"])
    assert "标题" in out
    assert "行1" in out


def test_format_todo_line():
    line = format_todo_line({"id": 1, "title": "t", "done": False, "priority": 1})
    assert "[ ]" in line and "高" in line


def test_format_contact_line():
    from utils.formatters import format_contact_line

    line = format_contact_line(
        {"id": 1, "name": "张三", "phone": "13800138000", "email": "a@b.com", "group": "研发部"}
    )
    assert "张三" in line and "研发部" in line
