# Day 38 课件索引

**日期**：2026-08-13（星期二）  
**主题**：多轮 Self-RAG 校验重试 — route → … → LLM → validate → 用户  
**需求**：ZL-NA-REQ-038  
**平台版本**：v0.38.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| ValidationRetry | `rag/answer_validator.py` | 引用-回复一致性打分 |
| ValidationConfig | `rag/validation_config.py` | enabled、min_score、refuse_on_fail |
| validation API | `api/knowledge.py` | GET/PUT validation-config + validation-preview |
| chat validation | `api/chat.py` | reply + validation + citations |
| 演示 | `day38/retry_demo.py` | 校验对比 |
| 测试 | `tests/day38/` | 21 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day38/retry_demo.py
python3 src/day38/retry_api_demo.py
python3 -m pytest tests/day38/ -v
```

## 关键流程

Day 36 让管线**更省** → Day 37 让回答**更准**：生成后校验 citations 是否支撑 reply。

## 验收

`test_validation_preview_fail` + `test_chat_refuses_on_fail` 全绿。

---

## 课件生成

```bash
python3 scripts/course_days/day37.py
```
