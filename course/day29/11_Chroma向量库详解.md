# Chroma 向量库详解（Day 29 专题讲义）

**需求**：ZL-NA-REQ-029 | **建议学时**：90 分钟

## 1. 向量数据库在 RAG 中的位置

检索增强生成（RAG）链路：`query → embed → ANN search → top-k chunks → LLM`。Day 19–28 用内存列表存向量；Day 29 起向量落盘 Chroma，使 API 进程重启后**无需重算全库 embed**。

## 2. Chroma 核心概念

| 概念 | 说明 |
|------|------|
| Client | `PersistentClient(path=...)` 或 HTTP Client |
| Collection | 命名空间，类似 SQL 表 |
| Document | 可选文本，便于调试 |
| Embedding | float 向量 |
| Metadata | 过滤用键值，如 source |
| ID | 唯一字符串，我们用 chunk_id |

## 3. PersistentClient 落盘机制

Chroma 在 `path` 下创建 SQLite 元数据 + 二进制向量段。重启后 `get_or_create_collection` 恢复同一 collection。

```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="data/knowledge/chroma",
    settings=Settings(anonymized_telemetry=False),
)
col = client.get_or_create_collection(
    name="nexus_knowledge",
    metadata={"hnsw:space": "cosine"},
)
```

## 4. cosine 空间

`hnsw:space: cosine` 表示用 cosine 距离。返回的 `distance` 越小越相似。项目统一：

```
score = 1 - distance  （clamp 到 [0,1]）
```

与 `EmbeddingRetriever` 内积+归一化教学实现排序一致。

## 5. upsert 语义

`upsert` = insert or update。同一 `chunk_id` 重复写入会覆盖向量与 metadata，**不会**产生 duplicate id。全量 rebuild 前先 `reset()` 是为清空已删除 chunk 的残留 id。

## 6. metadata 设计权衡

我们存 `source/index/start_char/end_char`，不存全文（全文在 JSON chunks）。好处：metadata 体积小；过滤可按文档删（Day 30）。坏处：Chroma 单独无法重建完整 KnowledgeStore——**必须以 JSON 为权威源**。

## 7. 教学规模 vs 生产规模

本课程 chunk 数 < 100，Chroma 内部 HNSW 与暴力扫描差异不明显。`test_chroma_matches_in_memory_retriever_top1` 保证语义一致。生产上万 chunk 时，ANN 优势才显著。

## 8. 常见错误

| 错误 | 后果 |
|------|------|
| 忘记 reset 就全量 rebuild | 残留已删 chunk 的向量 |
| 词表更新但向量未重算 | top-1 错乱（Day 30 处理增量） |
| 多进程写同一 persist 目录 | SQLite 锁冲突 |

## 9. 与 OpenAI Embedding 路线对比

| 方案 | 优点 | 本项目阶段 |
|------|------|------------|
| TF-IDF + Chroma | 无外部 API、可离线 | ✅ 当前 |
| ada-002 + Chroma | 语义更强 | 后续 Phase |

词表仍在 JSON，换 Embedding 模型只需改 `EmbeddingClient`，`ChromaVectorIndex` 接口不变。

## 10. 课堂演示 checklist

- [ ] `collection.count()` 与 `len(chunks)` 一致  
- [ ] `query` 返回的 metadata.source 正确  
- [ ] 删除 persist 目录后 load 自动恢复  

## 11. Chroma 与 SQLite 事务（深入）

PersistentClient 在 `path` 下维护 `chroma.sqlite3`。每次 `upsert` 或 `delete` 会更新 SQLite 中的 id 索引，向量数据写入伴生段文件。理解这一点有助于解释：

- 为何**多进程同时写**同一 `persist_path` 可能触发 `database is locked`  
- 为何复制 `chroma/` 目录时建议先停写（或接受快照一致性）  
- 为何「只删 sqlite 不删段文件」会导致 collection 损坏  

教学环境单进程 API 不会遇到锁问题；周航在 CI 中为每个 `tmp_path` 分配独立 chroma 目录正是为了避免并行测试争用。

## 12. collection metadata 与距离空间

创建 collection 时传入 `metadata={"hnsw:space": "cosine"}`。此后该 collection 内所有向量按 cosine 空间建 HNSW 图。若误用 L2 collection 写入 TF-IDF 向量，排序会与 `EmbeddingRetriever` 不一致，`test_chroma_matches_in_memory_retriever_top1` 会失败。

**课堂实验**：不必真改空间；阅读 Chroma 文档对比 `cosine` 与 `l2` 返回 distance 量纲差异。

## 13. upsert 与 add 的区别

Chroma 提供 `add`（仅插入）与 `upsert`（插入或覆盖）。我们选择 upsert 因为：

1. 全量 rebuild 后 `reset()` 清空 collection，`add` 亦可；但增量路径（Day 30）需覆盖同 `chunk_id`  
2. 幂等重试：网络抖动重放 upsert 不会产生 duplicate id 错误  

## 14. query 参数 n_results 边界

```python
n_results = max(1, min(top_k, collection.count()))
```

当 `top_k=10` 但库中只有 3 条向量时，Chroma 只能返回 3 条。客户端不应假设永远返回 `top_k` 条。`ChromaEmbeddingRetriever` 末尾再 `[:max(1, top_k)]` 做二次截断。

## 15. min_score 过滤语义

`min_score=0.05` 过滤极低相似度 hit，减少 RAG 上下文噪声。TF-IDF 在短 query 上可能出现「有命中但分数低」的情况；过滤后 `search` 返回空列表，`RAGContextService` 应优雅降级（项目已有「未检索到」文案）。

调参建议：评估集上扫 `min_score` ∈ {0, 0.05, 0.1}，观察 hit_rate 与噪声率权衡——Day 27 评估脚本可复用。

## 16. delete_by_source 实现细节

Day 29 已实现供 Day 30 使用。逻辑分两步：

1. `collection.get(where={"source": source}, include=[])` 取出 ids  
2. `collection.delete(ids=ids)` 或 `delete(where=...)` 兜底  

不同 chromadb 版本 `where` 语法略有差异；项目用 try/except 兼容。生产升级 chromadb 时须跑 `tests/day30/test_chroma_delete_by_source`。

## 17. EmbeddingClient 与 Chroma 的分工

| 步骤 | 组件 | 输入/输出 |
|------|------|-----------|
| 训练词表 | EmbeddingRetriever / fit | chunks → vocab/idf |
| 导出状态 | export_state() | dict → JSON |
| 编码 query | EmbeddingClient.embed | str → EmbeddingVector |
| 编码 batch | embed_batch | list[str] → list[EmbeddingVector] |
| 存储向量 | ChromaVectorIndex | list[float] → 磁盘 |
| ANN 检索 | Chroma query | query_vector → ChromaHit |

Chroma **不负责** TF-IDF 训练；若 JSON 词表与 Chroma 向量来自不同 fit 轮次，检索必错。

## 18. 版本 pin 策略

`requirements-api.txt` 建议写 `chromadb>=0.4,<0.6`（示例）。大版本升级时关注：

- `PersistentClient` 构造函数参数  
- `collection.query` 返回字段名  
- `delete` 是否支持 `where`  

锁定版本后，在 README 注明「升级须全量 regression」。

## 19. 可观测性建议

生产可在 `status` 之外增加：

- `chroma_last_sync_at`（若实现异步 sync）  
- `chroma_disk_bytes`（`du -sb chroma/`）  
- 定时任务跑作业 A `chroma_health.py`  

教学项目以 `chroma_count == chunk_count` 为健康唯一硬指标。

## 20. 术语表

| 术语 | 定义 |
|------|------|
| ANN | 近似最近邻，HNSW 等算法 |
| collection | Chroma 内向量表 |
| chunk_id | 业务主键，贯穿 JSON 与 Chroma |
| embedding_state | TF-IDF vocab/idf 序列化 dict |
| persist_path | Chroma 数据目录 |
| dual storage | JSON 元数据 + Chroma 向量 |
