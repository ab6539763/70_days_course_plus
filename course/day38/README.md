# Day 38 课件索引

**主题**：多轮 Self-RAG 校验重试 — validate 失败 → rag_wide 重检索 → 再校验
**需求**：ZL-NA-REQ-038
**平台版本**：v0.38.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `rag/validation_retry.py` | apply_validation_retry — 校验失败后 rag_wide 重检索再校验 |

| API | 说明 |
|-----|------|
| GET/PUT /api/knowledge/validation-config | 配置读写 |
| POST /api/knowledge/validation-retry-preview | 无状态预览 |

`POST /api/chat` 响应体在管线经过本日模块处理后附带相应审计字段。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day38/retry_demo.py
python3 src/day38/retry_api_demo.py
python3 -m pytest tests/day38/ -v
```

## 关键流程

Day 37 让回答更准；Day 38 让校验失败后还能自动补救 — 强制 rag_wide 重检索再校验一次。

## 验收

`tests/day38/` 15 项全绿。

---

## 课件生成

```bash
python3 scripts/generate_day38_course.py
```
