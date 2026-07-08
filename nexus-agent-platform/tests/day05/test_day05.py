"""Day 5 单元测试"""

import importlib.util
import json
import tempfile
from pathlib import Path

import pytest

DAY05 = Path(__file__).resolve().parent.parent.parent / "src" / "day05"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"test_day05_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


storage = _load("storage", DAY05 / "todo_storage.py")
parser = _load("parser", DAY05 / "api_response_parser.py")


class TestTodoStorage:
    def test_empty_store(self):
        s = storage.empty_store()
        assert s["todos"] == []
        assert s["next_id"] == 1

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "todos.json"
        data = storage.empty_store()
        todo = storage.create_todo_dict(1, "测试", "", 2)
        data["todos"].append(todo)
        data["next_id"] = 2
        storage.save_store(path, data)
        loaded = storage.load_store(path)
        assert len(loaded["todos"]) == 1
        assert loaded["todos"][0]["title"] == "测试"

    def test_load_missing_file(self, tmp_path):
        loaded = storage.load_store(tmp_path / "missing.json")
        assert loaded["todos"] == []


class TestApiParser:
    def test_parse_chat_completion(self):
        raw = json.loads((DAY05 / "sample_data/chat_completion.json").read_text())
        parsed = parser.parse_chat_completion(raw)
        assert parsed["model"] == "deepseek-chat"
        assert "年化" in parsed["content"] or len(parsed["content"]) > 0
        assert parsed["total_tokens"] == 184

    def test_parse_error(self):
        raw = json.loads((DAY05 / "sample_data/error_response.json").read_text())
        parsed = parser.parse_error_response(raw)
        assert parsed["type"] == "error"
        assert "API key" in parsed["message"]

    def test_detect_chat(self):
        raw = json.loads((DAY05 / "sample_data/chat_completion.json").read_text())
        parsed = parser.detect_and_parse(raw)
        assert parsed["type"] == "chat.completion"

    def test_detect_error(self):
        raw = json.loads((DAY05 / "sample_data/error_response.json").read_text())
        parsed = parser.detect_and_parse(raw)
        assert parsed["type"] == "error"

    def test_parse_stream_chunk(self):
        raw = json.loads((DAY05 / "sample_data/stream_chunk.json").read_text())
        parsed = parser.parse_stream_chunk(raw)
        assert parsed["delta_content"] == "你好"
