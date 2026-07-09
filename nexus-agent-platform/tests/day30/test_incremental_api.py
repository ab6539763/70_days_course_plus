"""Day 30 增量索引 API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import INDEX_MODE_INCREMENTAL, KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_upload_returns_incremental_mode(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    with patch.object(ChromaVectorIndex, "reset") as mock_reset:
        with sample.open("rb") as fh:
            resp = client.post(
                "/api/knowledge/upload",
                files={"file": ("notice.md", fh, "text/markdown")},
            )
        assert mock_reset.call_count == 0
    data = resp.json()
    assert data["index_mode"] == INDEX_MODE_INCREMENTAL
    assert "增量" in data["message"]


def test_status_shows_incremental_fields(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["index_mode"] == INDEX_MODE_INCREMENTAL
    assert status["last_incremental_at"]
    assert status["chroma_count"] == status["chunk_count"]


def test_reupload_same_file_no_duplicate_docs(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status1 = client.get("/api/knowledge/status").json()
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status2 = client.get("/api/knowledge/status").json()
    assert status2["document_count"] == status1["document_count"]


def test_rebuild_switches_to_full_mode(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    client.post("/api/knowledge/rebuild", json={"include_sample_docs": True})
    status = client.get("/api/knowledge/status").json()
    assert status["index_mode"] == "full"


def test_chat_works_after_incremental_upload(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    resp = client.post("/api/chat", json={"message": "产品收益？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]
