"""Day 27 分块调参 API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "store.json")
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version_027(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_chunk_config(client):
    data = client.get("/api/knowledge/chunk-config").json()
    assert data["chunk_size"] == 200
    assert data["strategy"] == "auto"


def test_put_chunk_config(client):
    resp = client.put(
        "/api/knowledge/chunk-config",
        json={"chunk_size": 250, "overlap": 30, "strategy": "markdown", "name": "lab"},
    )
    assert resp.status_code == 200
    assert resp.json()["chunk_size"] == 250


def test_put_invalid_overlap(client):
    resp = client.put(
        "/api/knowledge/chunk-config",
        json={"chunk_size": 100, "overlap": 100, "strategy": "auto", "name": "bad"},
    )
    assert resp.status_code == 422


def test_evaluate_presets(client):
    resp = client.post("/api/knowledge/evaluate", json={"use_presets": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["eval_query_count"] >= 4
    assert "best_config" in data
    assert len(data["results"]) >= 3


def test_status_has_chunk_config(client):
    data = client.get("/api/knowledge/status").json()
    assert data["platform_version"] == "0.45.0"
    assert "chunk_config" in data
