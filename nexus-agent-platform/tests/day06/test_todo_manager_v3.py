"""Day 6 todo_manager_v3 测试。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DAY06 = SRC / "day06"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def v3_module(tmp_path, monkeypatch):
    data = tmp_path / "todos.json"
    data.write_text(
        json.dumps(
            {
                "version": "1.0",
                "next_id": 2,
                "todos": [
                    {
                        "id": 1,
                        "title": "测试",
                        "description": "",
                        "priority": 2,
                        "done": False,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
                "updated_at": "2026-01-01T00:00:00Z",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    mod = _load("todo_manager_v3_test", DAY06 / "todo_manager_v3.py")
    monkeypatch.setattr(mod, "TODOS_PATH", data)
    return mod


def test_load_store(v3_module):
    store = v3_module.load_store()
    assert len(store["todos"]) == 1
    assert store["next_id"] == 2


def test_create_and_save_roundtrip(v3_module):
    store = v3_module.load_store()
    todo = v3_module.create_todo(store["next_id"], "新任务", "描述", 1)
    store["todos"].append(todo)
    store["next_id"] += 1
    v3_module.save_store(store)
    reloaded = v3_module.load_store()
    assert len(reloaded["todos"]) == 2
    assert reloaded["todos"][-1]["title"] == "新任务"


def test_find_todo(v3_module):
    store = v3_module.load_store()
    found = v3_module.find_todo(store["todos"], 1)
    assert found is not None
    assert v3_module.find_todo(store["todos"], 999) is None
