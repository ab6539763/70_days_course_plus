"""Day 7 通讯录与周测测试。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DAY07 = SRC / "day07"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def svc(tmp_path):
    return _load("contact_service_test", DAY07 / "contact_service.py")


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "contacts.json"


def test_empty_store(svc):
    store = svc.empty_store()
    assert store["next_id"] == 1
    assert store["contacts"] == []


def test_add_contact_success(svc):
    store = svc.empty_store()
    contact, err = svc.add_contact(store, "张三", "13800138000", "a@b.com", "研发部")
    assert err is None
    assert contact["name"] == "张三"
    assert len(store["contacts"]) == 1


def test_add_contact_invalid_phone(svc):
    store = svc.empty_store()
    contact, err = svc.add_contact(store, "张三", "123", "a@b.com")
    assert contact is None
    assert err is not None


def test_add_contact_invalid_email(svc):
    store = svc.empty_store()
    contact, err = svc.add_contact(store, "张三", "13800138000", "bad-email")
    assert contact is None


def test_search_by_name(svc):
    store = svc.empty_store()
    svc.add_contact(store, "张三", "13800138000", "a@b.com")
    svc.add_contact(store, "李四", "13800138001", "b@b.com")
    assert len(svc.search_by_name(store["contacts"], "张")) == 1


def test_search_by_group(svc):
    store = svc.empty_store()
    svc.add_contact(store, "张三", "13800138000", "a@b.com", "研发部")
    svc.add_contact(store, "李四", "13800138001", "b@b.com", "产品部")
    assert len(svc.search_by_group(store["contacts"], "研发部")) == 1


def test_delete_contact(svc):
    store = svc.empty_store()
    svc.add_contact(store, "张三", "13800138000", "a@b.com")
    assert svc.delete_contact(store, 1) is True
    assert len(store["contacts"]) == 0


def test_save_load_roundtrip(svc, store_path):
    store = svc.empty_store()
    svc.add_contact(store, "王五", "13800138002", "c@b.com")
    svc.save_store(store_path, store)
    loaded = svc.load_store(store_path)
    assert len(loaded["contacts"]) == 1
    assert loaded["contacts"][0]["name"] == "王五"


def test_group_stats(svc):
    store = svc.empty_store()
    svc.add_contact(store, "A", "13800138000", "a@b.com", "研发部")
    svc.add_contact(store, "B", "13800138001", "b@b.com", "研发部")
    svc.add_contact(store, "C", "13800138002", "c@b.com", "产品部")
    stats = svc.group_stats(store["contacts"])
    assert stats["研发部"] == 2
    assert stats["产品部"] == 1


def test_update_contact(svc):
    store = svc.empty_store()
    svc.add_contact(store, "张三", "13800138000", "a@b.com")
    contact = store["contacts"][0]
    err = svc.update_contact(contact, name="张三丰", phone="13800138099")
    assert err is None
    assert contact["name"] == "张三丰"


def test_week1_quiz_questions():
    quiz = _load("week1_quiz_test", DAY07 / "week1_quiz.py")
    assert len(quiz.QUESTIONS) == 10
    for q in quiz.QUESTIONS:
        assert 0 <= q["answer"] < len(q["options"])
