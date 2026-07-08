"""Day 26 知识库 API 多格式上传测试。"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
SAMPLES = SRC / "day26" / "sample_docs"

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


def test_health_version_026(client):
    assert client.get("/api/health").json()["version"] == "0.33.0"


def test_status_supported_formats(client):
    data = client.get("/api/knowledge/status").json()
    assert data["platform_version"] == "0.33.0"
    exts = {f["extension"] for f in data["supported_formats"]}
    assert ".pdf" in exts


def test_upload_markdown(client):
    md = (SAMPLES / "product_notice.md").read_bytes()
    resp = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_notice.md", io.BytesIO(md), "text/markdown")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "markdown"
    assert body["chunk_count"] >= 3


def test_upload_pdf(client):
    pdf_path = SAMPLES / "product_notice.pdf"
    if not pdf_path.is_file():
        pytest.skip("sample pdf missing")
    resp = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_notice.pdf", io.BytesIO(pdf_path.read_bytes()), "application/pdf")},
    )
    assert resp.status_code == 200
    assert resp.json()["format"] == "pdf"


def test_upload_rejects_docx(client):
    resp = client.post(
        "/api/knowledge/upload",
        files={"file": ("x.docx", io.BytesIO(b"PK"), "application/octet-stream")},
    )
    assert resp.status_code == 422


def test_chat_after_md_upload(client):
    md = (SAMPLES / "product_notice.md").read_bytes()
    client.post(
        "/api/knowledge/upload",
        files={"file": ("notice.md", io.BytesIO(md), "text/markdown")},
    )
    chat = client.post(
        "/api/chat",
        json={"message": "最低起购金额", "session_id": "md-chat"},
    )
    assert chat.status_code == 200
    assert len(chat.json()["reply"]) > 0


def test_knowledge_store_ingest_parsed_format(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
    doc = __import__("tools.doc_parser", fromlist=["parse_bytes"]).parse_bytes(
        (SAMPLES / "product_notice.md").read_bytes(),
        "p.md",
    )
    meta = store.ingest_parsed(doc)
    assert meta.format == "markdown"
    assert meta.chunk_count >= 3
