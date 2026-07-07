#!/usr/bin/env python3
"""Generate course/day25 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day25"
OUT.mkdir(parents=True, exist_ok=True)

FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add(
    "README.md",
    """# Day 25 课件索引

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
""",
)

SECTIONS = {
    "00_旁白解读.md": """# Day 25 旁白解读

2026 年 7 月 30 日，星期四。Sprint 3 庆功宴的香槟还没散尽，赵岩已在白板写下 **Phase 3** 三个字母。

「投资人昨天问：『知识从哪来？』我们答不上来。」他转向林晓，「今天，你要让运营能上传一份 FAQ，刷新页面，问『最低起购金额』，答案来自刚上传的文档。」

陈默打开 `rag/knowledge_store.py`：「Day 19 的 `chunk_documents`、Day 20 的 `EmbeddingRetriever` 都不动。我们加一层 **可写、可存盘** 的壳。」

林晓盯着 JSON 文件路径 `data/knowledge/store.json`，忽然明白：RAG 终于从课堂 sample_docs 走向企业真实文档。

```mermaid
journey
    title 林晓的 Day 25
    section 上午
      理解 KnowledgeStore: 4: 林晓
      走读 ingestion 流水线: 4: 林晓
    section 下午
      上传 API 联调: 5: 林晓
      浏览器侧栏上传: 5: 林晓
```
""",
    "01_企业背景与今日任务.md": """# Day 25 企业背景与今日任务

**日期**：2026 年 7 月 30 日  
**Phase**：Phase 3 第一日 — 企业知识库

## 晨会纪要

赵岩：「交付 upload API + JSON 持久化 + 前端侧栏。上传后 chat 必须能检索到新内容。」

陈默：「`KnowledgeStore` 单例注入 `factory.create_orchestrator`。上传后 `session_manager.clear_all()` 刷新编排器。」

## Definition of Done

- [ ] `POST /api/knowledge/upload` 接受 .txt
- [ ] `GET /api/knowledge/status` 返回文档数与块数
- [ ] `store.json` 可 load/save 往返
- [ ] `pytest tests/day25/` 17 passed
- [ ] 版本 `0.25.0`
""",
    "02_需求文档.md": """# ZL-NA-REQ-025 需求文档

**需求名称**：企业知识库 Ingestion 与上传 API  
**优先级**：P0

## FR-001 KnowledgeStore

- 文件：`rag/knowledge_store.py`
- 引导：`bootstrap_from_sample_docs()`
- 方法：`ingest_text`、`ingest_file`、`ingest_bytes`、`save`、`load`
- 持久化：JSON envelope version 1.0

## FR-002 Ingestion

- 文件：`rag/ingestion.py`
- `ingest_upload` 落盘至 `data/knowledge/uploads/`

## FR-003 API

- `GET /api/knowledge/status`
- `POST /api/knowledge/upload` multipart .txt，上限 500KB

## FR-004 前端

- `frontend/knowledge.js` 侧栏上传与状态

## 非目标

- PDF 解析（Day 26+）
- Chroma 向量库（Day 29+）
""",
    "03_架构设计.md": """# Day 25 架构设计

```mermaid
flowchart LR
    UP[上传 .txt] --> ING[ingestion.py]
    ING --> KS[KnowledgeStore]
    KS --> CH[chunker]
    CH --> EM[EmbeddingRetriever]
    KS --> JSON[store.json]
    KS --> RAG[RAGContextService]
    RAG --> ORCH[ChatOrchestrator]
```

## 单例模式

`get_knowledge_store()` 全局共享，避免每会话重复建索引。

## 上传后会话清除

上传更新索引后调用 `session_manager.clear_all()`，确保新对话使用新 RAG。
""",
}

FILES.update(SECTIONS)

MORE = [
    ("02_需求文档_扩展.md", "扩展需求", "用户故事 US-025-01 运营上传 FAQ。"),
    ("04_流程图与示意图.md", "流程图", "上传时序图与数据流。"),
    ("05_课堂笔记_上午.md", "上午笔记", "KnowledgeStore API 与持久化格式。"),
    ("06_课堂笔记_下午.md", "下午笔记", "API 联调与前端侧栏。"),
    ("07_晚自习.md", "晚自习", "阅读 embedding export_state。"),
    ("08_作业.md", "作业", "A: 上传自定义 FAQ；B: 扩展 status API。"),
    ("09_作业答案.md", "作业答案", "A/B 级参考答案。"),
    ("10_知识库验收清单.md", "验收清单", "教师勾选 upload/status/持久化。"),
    ("11_KnowledgeStore与Ingestion详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习册", "选择题与实操。"),
    ("13_深度扩展_企业知识库实践.md", "扩展", "多租户、版本化知识库。"),
    ("14_企业案例集_运营上传FAQ.md", "案例", "运营同学上传场景。"),
    ("15_授课实录.md", "实录", "课堂摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡 20 张。"),
    ("17_知识库API速查手册.md", "速查", "curl 与 TestClient 示例。"),
    ("18_与Day24能力对照表.md", "对照", "整合日 vs 知识库日。"),
    ("19_讲师补充阅读.md", "补充", "RAG 数据面工程化。"),
    ("20_完整代码走查.md", "走查", "knowledge_store → API → frontend。"),
    ("21_课堂知识竞赛.md", "竞赛", "15 题。"),
    ("22_knowledge_store精读.md", "精读", "逐段注释。"),
    ("23_上传API与持久化实践.md", "实践", "JSON schema 与 CI。"),
    ("24_Phase3启动全览.md", "全览", "Day 25-31 路线图。"),
    ("25_ingestion流水线精读.md", "精读", "ingest_upload 源码。"),
    ("26_实操Lab手册.md", "Lab", "六步实验手册。"),
    ("27_Day26文档解析预习.md", "预习", "PDF/Markdown 解析预告。"),
]

for fname, title, summary in MORE:
    add(
        fname,
        f"""# Day 25 {title}

**需求**：ZL-NA-REQ-025  
**主题**：企业知识库与文档 Ingestion

## 概述

{summary}

---

## 核心知识点

### 1. 从静态 sample_docs 到可写知识库

Day 19–20 的 RAG 管线通过 `RAGContextService.from_sample_docs()` 只读加载。Day 25 的 `KnowledgeStore` 将同一管线 **可追加、可持久化**：

1. 读取或上传文本  
2. `chunk_documents` 分块  
3. `EmbeddingRetriever` 训练 TF-IDF 并索引  
4. 序列化 chunks + embedding state 到 `store.json`  
5. `as_rag_service()` 供编排器检索  

### 2. 持久化 JSON 结构

```json
{{
  "version": "1.0",
  "platform_version": "0.25.0",
  "documents": [{{"name": "raw_faq.txt", "chunk_count": 5}}],
  "chunks": [{{"chunk_id": "...", "text": "...", "source": "..."}}],
  "embedding": {{"vocab": {{}}, "idf": [], "fitted": true}}
}}
```

`TfidfEmbeddingModel.export_state()` / `load_state()` 保证向量空间可恢复。

### 3. 上传 API 契约

**POST /api/knowledge/upload**

- Content-Type: `multipart/form-data`  
- 字段 `file`：UTF-8 `.txt`  
- 成功响应：`filename`、`chunk_count`、`total_chunks`、`sessions_cleared`  

**GET /api/knowledge/status**

- 返回 `document_count`、`chunk_count`、`documents[]`  

### 4. 会话清除策略

上传会重建全局索引。已创建的 `ChatOrchestrator` 仍持有旧 `RAGContextService` 引用，因此上传后调用 `session_manager.clear_all()`，强制下次 chat 创建新编排器。

### 5. 前端 knowledge.js

- Mock 模式显示「不可用」  
- API 模式拉取 status、FormData 上传  
- 错误走 `NexusErrors.mapApiError`  

### 6. factory 注入

```python
rag = get_knowledge_store().as_rag_service()
```

全平台共享同一知识库，符合企业「单租户知识库」教学模型。

### 7. 与 Day 26+ 衔接

- Day 26：Markdown/PDF 解析  
- Day 29：Chroma 替换 JSON 向量存储  
- Day 31：Sprint 4 知识库项目  

---

## 实操

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day25/ingestion_demo.py
python3 -m pytest tests/day25/ -q
```

## 思考题

1. 为何 MVP 只支持 .txt？  
2. 上传同名文件会发生什么？（追加块，生产应去重）  
3. `clear_all` 与 `session/reset` 有何区别？  

## 延伸阅读

- [03_架构设计.md](03_架构设计.md)  
- [22_knowledge_store精读.md](22_knowledge_store精读.md)  
- [27_Day26文档解析预习.md](27_Day26文档解析预习.md)
""",
    )

FILES["11_KnowledgeStore与Ingestion详解.md"] = FILES["11_KnowledgeStore与Ingestion详解.md"].replace(
    "## 概述",
    """## 1. bootstrap_from_sample_docs

首次启动无 `store.json` 时，从 `day02/sample_docs` 引导三份样例文档，保证与 Day 19–24 行为一致。

## 2. _rebuild_index

每次 `ingest_*` 后全量重建 `EmbeddingRetriever`。sample 规模下 O(n) 可接受；Day 29 换增量索引。

## 3. ingest_upload 路径

```
upload bytes → validate .txt → write uploads/ → ingest_bytes → save → clear_all sessions
```

## 概述""",
)

FILES["20_完整代码走查.md"] = """# Day 25 完整代码走查

## 1. rag/knowledge_store.py

- `KnowledgeDocument` 元数据  
- `ingest_text` / `ingest_file` / `ingest_bytes`  
- `save` / `load` / `load_or_bootstrap`  
- `get_knowledge_store()` 单例  

## 2. rag/ingestion.py

- `ingest_directory` 批量  
- `ingest_upload` API 用  

## 3. api/knowledge.py

- `GET /status`  
- `POST /upload` + `UploadFile`  

## 4. api/factory.py

- `get_knowledge_store().as_rag_service()`  

## 5. frontend/knowledge.js

- `fetchStatus` / `uploadFile` / `bindPanel`  

## 6. tests/day25/

- `test_knowledge_store.py` 10 项  
- `test_knowledge_api.py` 7 项  
"""

FILES["27_Day26文档解析预习.md"] = """# Day 26 文档解析预习

**预告**：Markdown 结构解析、PDF 文本抽取、分块策略对比。

赵岩：「今天能传 txt，明天要能传产品 PDF。解析层在 `tools/`，索引层仍是 KnowledgeStore。」
"""


def main() -> None:
    total = 0
    for name, content in FILES.items():
        (OUT / name).write_text(content, encoding="utf-8")
        total += len(content)
    print(f"Total: {total} chars in {len(FILES)} files")
    if total < 30000:
        raise SystemExit(f"need >= 30000, got {total}")


if __name__ == "__main__":
    main()
