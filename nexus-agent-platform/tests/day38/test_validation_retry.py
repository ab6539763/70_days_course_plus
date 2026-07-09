"""Day 38 Validation Retry 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.knowledge_store import KnowledgeStore
from rag.route_config import INTENT_RAG_WIDE
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_fetch_citations_retry_forces_rag_wide(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations_retry("理财安全吗", attempt=1)
    route = data.get("route") or {}
    assert route.get("intent") == INTENT_RAG_WIDE
    assert route.get("expand") is True
    assert data.get("retry_attempt") == 1


def test_apply_validation_retry_no_retry_when_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(enabled=True, retry_on_fail=False, refuse_on_fail=False)
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 0
    assert outcome.validation.passed is False


def test_apply_validation_retry_increments_retries(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 1


def test_apply_validation_retry_passes_with_matching_reply(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("客服电话多少")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "客服电话多少",
        "请拨打客服热线 400-888-1234。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.passed is True


def test_apply_validation_retry_refuses_after_exhausted(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            mode="strict",
            min_score=0.9,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=True,
        )
    )
    cite = store.fetch_citations("智链科技总部在哪")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "智链科技总部在哪",
        "今天北京天气晴朗，适合出游。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.refused is True
    assert outcome.reply.startswith("[校验未通过]")
    assert outcome.validation.retries == 1


def test_validation_config_persists_retry_fields(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(retry_on_fail=True, max_retries=2, refuse_on_fail=False)
    )
    store.save(tmp_path / "store.json")
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    cfg = loaded.get_validation_config()
    assert cfg.retry_on_fail is True
    assert cfg.max_retries == 2
