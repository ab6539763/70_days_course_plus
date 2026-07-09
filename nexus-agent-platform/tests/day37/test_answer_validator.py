"""Day 37 答案校验单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.answer_validator import RuleBasedAnswerValidator
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import MODE_STRICT, ValidationConfig


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_validation_config_validate():
    ValidationConfig().validate()
    with pytest.raises(ValueError):
        ValidationConfig(mode="invalid").validate()
    with pytest.raises(ValueError):
        ValidationConfig(min_score=1.5).validate()


def test_validator_passes_when_reply_matches_citations():
    validator = RuleBasedAnswerValidator()
    citations = [
        {
            "rank": 1,
            "source": "faq.md",
            "preview": "客服热线 400-888-1234 工作日接听",
            "matched_tokens": ["客服", "400"],
            "score": 0.9,
            "chunk_id": "c1",
        }
    ]
    result = validator.validate(
        "客服电话多少",
        "请拨打客服热线 400-888-1234。",
        citations,
    )
    assert result.passed is True
    assert result.score >= 0.35
    assert 1 in result.matched_citation_ranks


def test_validator_fails_on_unrelated_reply():
    validator = RuleBasedAnswerValidator()
    citations = [
        {
            "rank": 1,
            "source": "product.md",
            "preview": "年化收益率约 3.5% 至 4.2%",
            "matched_tokens": ["年化", "收益"],
            "score": 0.8,
            "chunk_id": "c2",
        }
    ]
    result = validator.validate(
        "年化收益怎么样",
        "今天天气很好，适合出门散步。",
        citations,
    )
    assert result.passed is False
    assert result.score < 0.35


def test_validator_skips_faq_direct():
    validator = RuleBasedAnswerValidator()
    result = validator.validate(
        "客服电话",
        "[FAQ 直答·90%] 400-888-1234",
        [],
    )
    assert result.passed is True
    assert result.reason == "FAQ 直答跳过校验"


def test_strict_mode_requires_citation_coverage():
    validator = RuleBasedAnswerValidator(
        config=ValidationConfig(mode=MODE_STRICT, min_score=0.2)
    )
    citations = [
        {
            "rank": 1,
            "source": "risk.md",
            "preview": "完全不相关的段落内容",
            "matched_tokens": [],
            "score": 0.3,
            "chunk_id": "c4",
        },
        {
            "rank": 2,
            "source": "other.md",
            "preview": "另一段无关说明",
            "matched_tokens": [],
            "score": 0.2,
            "chunk_id": "c5",
        },
        {
            "rank": 3,
            "source": "misc.md",
            "preview": "其他信息",
            "matched_tokens": [],
            "score": 0.1,
            "chunk_id": "c6",
        },
    ]
    result = validator.validate(
        "理财安全吗",
        "投资有风险，请谨慎。",
        citations,
    )
    assert result.citation_coverage < 0.5
    assert result.passed is False


def test_store_validate_answer_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(ValidationConfig(enabled=False))
    result = store.validate_answer("q", "r", [])
    assert result is None


def test_store_validate_answer_enabled(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("客服电话多少")
    result = store.validate_answer(
        "客服电话多少",
        "客服热线 400-888-1234",
        data.get("citations") or [],
    )
    assert result is not None
    assert result.passed is True


def test_knowledge_store_persists_validation_config(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(ValidationConfig(min_score=0.5, refuse_on_fail=False))
    store.save()
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    assert loaded.get_validation_config().min_score == 0.5
    assert loaded.get_validation_config().refuse_on_fail is False


def test_status_includes_validation_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["platform_version"] == "0.40.0"
    assert status["validation_config"]["enabled"] is True


def test_validation_result_to_dict():
    validator = RuleBasedAnswerValidator()
    result = validator.validate("q", "r", [])
    data = result.to_dict()
    assert "passed" in data
    assert "score" in data
    assert "reason" in data


def test_validator_empty_citations_fails():
    validator = RuleBasedAnswerValidator()
    result = validator.validate("年化收益", "收益不错", [])
    assert result.passed is False
    assert result.reason == "无可用引用"
