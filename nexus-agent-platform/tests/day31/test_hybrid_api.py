"""Day 31 混合检索 API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


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


def test_get_retrieval_config_default_hybrid(client):
    data = client.get("/api/knowledge/retrieval-config").json()
    assert data["mode"] == "hybrid"
    assert data["fusion"] in ("weighted", "rrf")


def test_put_retrieval_config_rrf(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={
            "mode": "hybrid",
            "fusion": "rrf",
            "keyword_weight": 0.4,
            "vector_weight": 0.6,
            "rrf_k": 60,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fusion"] == "rrf"


def test_status_includes_retrieval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["retrieval_config"]["mode"] == "hybrid"


def test_invalid_retrieval_mode_422(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "invalid", "fusion": "weighted"},
    )
    assert resp.status_code == 422


def test_chat_with_hybrid_retrieval(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_switch_to_keyword_mode(client):
    client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "keyword", "fusion": "weighted", "keyword_weight": 1.0, "vector_weight": 0.0},
    )
    cfg = client.get("/api/knowledge/retrieval-config").json()
    assert cfg["mode"] == "keyword"
