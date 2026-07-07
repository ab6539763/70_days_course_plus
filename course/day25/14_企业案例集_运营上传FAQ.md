# Day 25 案例

**需求**：ZL-NA-REQ-025  
**主题**：企业知识库与文档 Ingestion

## 概述

运营同学上传场景。

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
{
  "version": "1.0",
  "platform_version": "0.25.0",
  "documents": [{"name": "raw_faq.txt", "chunk_count": 5}],
  "chunks": [{"chunk_id": "...", "text": "...", "source": "..."}],
  "embedding": {"vocab": {}, "idf": [], "fitted": true}
}
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
