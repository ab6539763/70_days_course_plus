# Day 37 课件索引

**主题**：Self-RAG 答案校验 — route → expand? → rewrite → hybrid → rerank → citations → LLM → validate
**需求**：ZL-NA-REQ-037
**平台版本**：v0.37.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `rag/answer_validator.py` | RuleBasedAnswerValidator — 引用-回复一致性打分 |
| `rag/validation_config.py` | ValidationConfig — enabled / min_score / refuse_on_fail |

| API | 说明 |
|-----|------|
| GET/PUT /api/knowledge/validation-config | 配置读写 |
| POST /api/knowledge/validation-preview | 无状态预览 |

`POST /api/chat` 响应体在管线经过本日模块处理后附带相应审计字段。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day37/validation_demo.py
python3 src/day37/validation_api_demo.py
python3 -m pytest tests/day37/ -v
```

## 关键流程

Day 36 让管线更省；Day 37 让回答更准 — 生成后校验 citations 是否真的支撑 reply。

## 验收

`tests/day37/` 21 项全绿。

---

## 课件生成

```bash
python3 scripts/generate_day37_course.py
```
