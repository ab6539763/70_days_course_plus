"""Day 10 core 包、异常与包结构测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.bootstrap import ensure_importable, setup_python_path
from core.exceptions import (
    ConfigError,
    JsonParseError,
    ModelValidationError,
    NexusError,
    StorageError,
)
from core.paths import SRC_ROOT, get_path
from models import ChatMessage
from services import MessageHistory


def test_nexus_error_hierarchy():
    err = ConfigError("test")
    assert isinstance(err, NexusError)
    assert err.code == "CONFIG_ERROR"


def test_model_validation_is_value_error():
    e = ModelValidationError("bad", model_type="X")
    assert isinstance(e, ValueError)
    assert isinstance(e, NexusError)


def test_get_path():
    p = get_path("messages")
    assert "messages.json" in str(p)


def test_get_path_unknown():
    with pytest.raises(ConfigError):
        get_path("nonexistent_key_xyz")


def test_setup_python_path():
    root = setup_python_path()
    assert root == SRC_ROOT
    assert str(SRC_ROOT) in sys.path


def test_ensure_importable():
    ensure_importable("core", "models", "utils")


def test_message_history_service_load_save(tmp_path):
    h = MessageHistory()
    h.add_user("服务层测试")
    path = tmp_path / "m.json"
    h.save_json(path)
    loaded = MessageHistory.load_json(path)
    assert len(loaded) == 1


def test_message_history_strict_load_bad_json(tmp_path):
    from services.message_history import MessageHistoryService

    path = tmp_path / "bad.json"
    path.write_text('{"messages": "not-list"}', encoding="utf-8")
    with pytest.raises(JsonParseError):
        MessageHistoryService.load(path)


def test_package_init_files_exist():
    for pkg in ("core", "models", "services", "llm", "chat", "tools"):
        assert (SRC_ROOT / pkg / "__init__.py").exists()


def test_models_import_validation_error_from_core():
    from core import ModelValidationError as CoreMVE
    from models import ModelValidationError as ModelsMVE

    assert CoreMVE is ModelsMVE
