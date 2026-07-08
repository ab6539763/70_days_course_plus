"""Day 4 todo_manager 单元测试"""

import importlib.util
from pathlib import Path

import pytest

DAY04 = Path(__file__).resolve().parent.parent.parent / "src" / "day04"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"test_day04_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_tm = _load("todo_manager", DAY04 / "todo_manager.py")

add_todo = _tm.add_todo
mark_done = _tm.mark_done
delete_todo = _tm.delete_todo
edit_todo = _tm.edit_todo
get_stats = _tm.get_stats
search_todos = _tm.search_todos
find_by_id = _tm.find_by_id


@pytest.fixture
def empty_todos():
    return [], 1


class TestTodoCrud:
    def test_add(self):
        todos, nid = [], 1
        nid = add_todo(todos, nid, "任务A", "描述", 1)
        assert len(todos) == 1
        assert todos[0][1] == "任务A"
        assert nid == 2

    def test_mark_done(self):
        todos, nid = [], 1
        add_todo(todos, nid, "任务", "", 2)
        assert mark_done(todos, 1)
        assert todos[0][4] is True

    def test_delete(self):
        todos, nid = [], 1
        add_todo(todos, nid, "A", "", 1)
        add_todo(todos, nid + 1, "B", "", 2)
        assert delete_todo(todos, 1)
        assert len(todos) == 1
        assert todos[0][1] == "B"

    def test_edit(self):
        todos, nid = [], 1
        add_todo(todos, nid, "旧标题", "", 3)
        edit_todo(todos, 1, "新标题", 1)
        assert todos[0][1] == "新标题"
        assert todos[0][3] == 1

    def test_find_missing(self):
        assert find_by_id([], 99) is None


class TestStats:
    def test_stats(self):
        todos, nid = [], 1
        nid = add_todo(todos, nid, "A", "", 1)
        add_todo(todos, nid, "B", "", 2)
        mark_done(todos, 1)
        total, done, pending = get_stats(todos)
        assert total == 2
        assert done == 1
        assert pending == 1


class TestSearch:
    def test_search(self):
        todos, nid = [], 1
        add_todo(todos, nid, "完成清洗", "", 1)
        add_todo(todos, nid + 1, "写 API", "", 2)
        results = search_todos(todos, "清洗")
        assert len(results) == 1
        assert "清洗" in results[0][1]


class TestSort:
    def test_priority_order(self):
        todos, nid = [], 1
        add_todo(todos, nid, "低", "", 3)
        add_todo(todos, nid + 1, "高", "", 1)
        sorted_todos = sorted(todos, key=lambda t: t[3])
        assert sorted_todos[0][3] == 1
