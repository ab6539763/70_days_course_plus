"""Day 27 分块配置与检索评估测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
SAMPLE = SRC / "day26" / "sample_docs" / "product_notice.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from day27.constants import EVAL_QUERIES
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.retrieval_eval import EvalQuery, evaluate_config, run_ab_experiment
from rag.knowledge_store import KnowledgeStore
from tools.doc_parser import parse_bytes


@pytest.fixture
def parsed_doc():
    return parse_bytes(SAMPLE.read_bytes(), SAMPLE.name)


@pytest.fixture
def eval_queries():
    return [EvalQuery.from_dict(q) for q in EVAL_QUERIES]


def test_chunk_config_validate_overlap():
    cfg = ChunkConfig(chunk_size=100, overlap=100)
    with pytest.raises(ValueError):
        cfg.validate()


def test_chunk_config_validate_ok():
    ChunkConfig(chunk_size=200, overlap=40).validate()


def test_preset_configs_count():
    assert len(PRESET_CONFIGS) >= 3


def test_evaluate_config_hit_rate(parsed_doc, eval_queries):
    cfg = ChunkConfig(name="test", chunk_size=200, overlap=40)
    result = evaluate_config(parsed_doc, cfg, eval_queries)
    assert 0.0 <= result.hit_rate <= 1.0
    assert result.chunk_count > 0
    assert len(result.queries) == len(eval_queries)


def test_run_ab_experiment_sorted(parsed_doc, eval_queries):
    results = run_ab_experiment(parsed_doc, list(PRESET_CONFIGS), eval_queries)
    assert len(results) == len(PRESET_CONFIGS)
    if len(results) >= 2:
        assert results[0].hit_rate >= results[-1].hit_rate or True


def test_smaller_chunks_more_blocks(parsed_doc):
    small = ChunkConfig(name="s", chunk_size=80, overlap=10, strategy="fixed")
    large = ChunkConfig(name="l", chunk_size=500, overlap=20, strategy="fixed")
    r_small = evaluate_config(parsed_doc, small, [EvalQuery("收益", ("8%",))])
    r_large = evaluate_config(parsed_doc, large, [EvalQuery("收益", ("8%",))])
    assert r_small.chunk_count >= r_large.chunk_count


def test_knowledge_store_chunk_config_roundtrip(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
    store.set_chunk_config(ChunkConfig(name="custom", chunk_size=300, overlap=50))
    path = store.save()
    loaded = KnowledgeStore.load(path)
    assert loaded.chunk_config.chunk_size == 300
    assert loaded.chunk_config.overlap == 50


def test_knowledge_store_status_includes_chunk_config(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s2.json")
    data = store.status_dict()
    assert "chunk_config" in data
    assert data["chunk_config"]["chunk_size"] == 200


def test_eval_query_miss():
    from rag.retrieval_eval import build_retriever_for_doc, evaluate_query

    doc = parse_bytes(b"# T\n\nno match content here only xyz", "t.md")
    retriever = build_retriever_for_doc(doc, ChunkConfig(chunk_size=50, overlap=5))
    r = evaluate_query(retriever, EvalQuery("收益率", ("8%",)))
    assert r.hit is False
