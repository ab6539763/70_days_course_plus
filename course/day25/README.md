# Day 25 课件索引

**日期**：2026-07-30（星期四）  
**主题**：Phase 3 启动 — 企业知识库与文档 Ingestion  
**需求**：ZL-NA-REQ-025  
**里程碑**：Phase 3 第一日

## 进度

Sprint 3 收官后，产品提出：**知识从哪来？** 今日在 `rag/knowledge_store.py` 交付可写入、可落盘、可上传的企业知识库 MVP，并暴露 `POST /api/knowledge/upload` 与 `GET /api/knowledge/status`，前端增加知识库侧栏。

- Day 19 分块 → Day 20 Embedding → Day 24 网页整合 → **Day 25 知识库 ingestion**
- Day 26+ 文档解析增强、分块调优……

## 配套代码

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1

python3 src/day25/ingestion_demo.py
python3 src/day25/knowledge_api_demo.py
python3 -m pytest tests/day25/ -v

# 启动服务后浏览器「知识库」上传 .txt
python3 src/day24/sprint3_launch.py --serve --skip-pytest
```

## 今日交付物

- [x] `rag/knowledge_store.py` — JSON 持久化、TF-IDF 索引重建
- [x] `rag/ingestion.py` — 上传落盘 + 入库流水线
- [x] `api/knowledge.py` — upload / status 路由
- [x] `frontend/knowledge.js` — 知识库侧栏
- [x] `src/day25/*` 演示与 Phase 3 回顾
- [x] `tests/day25/`（17 tests）
- [x] Day 25 全套课件（30 篇）

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | 旁白解读 | Phase 3 故事线 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 设计 |
| 10 | 知识库验收清单 | 教师检查表 |
| 11 | KnowledgeStore 详解 | 深度专题 |
| 22 | knowledge_store 精读 | 源码走读 |
| 27 | Day26 预习 | 明日预告 |

## 验收命令

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 -m pytest tests/day25/ -q
```
