# Day 28 课件索引

**日期**：2026-08-04（星期二）  
**主题**：知识库全量重建（rebuild）  
**需求**：ZL-NA-REQ-028  
**版本**：v0.28.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| 重建核心 | `rag/knowledge_rebuild.py` | collect_source_files / rebuild_store |
| 最优配置发布 | `rebuild_with_best_config` | evaluate + rebuild 一键 |
| API | `POST /api/knowledge/rebuild` | 全量重建入口 |
| 状态字段 | `last_rebuilt_at` | store.json 审计时间戳 |
| 前端 | `frontend/knowledge.js` | `#kb-rebuild-btn` |
| 测试 | `tests/day28/` | 14 项 |

## 关键设计决策

1. **双源扫描**：`sample_docs` 开箱即用 + `knowledge_uploads` 运营文档。  
2. **uploads 优先**：同名文件 uploads 覆盖 sample。  
3. **清空重建**：`documents.clear()` + `chunks.clear()` 后逐文件 parse+chunk。  
4. **apply_best_config**：先 `run_ab_experiment` 再 `set_chunk_config` 再 rebuild。  
5. **sessions_cleared**：重建后 `session_manager.clear_all()`，编排器用新索引。

## 验收命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day28/rebuild_demo.py
python3 src/day28/rebuild_api_demo.py
pytest tests/day28/ -q
```

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_知识库重建详解 | 重建专题 |
| 15_授课实录 | 发布夜实录 |
| 22_knowledge_rebuild精读 | 源码走读 |
| 23_双源扫描与覆盖策略 | uploads 优先 |
| 26_实操Lab手册 | 六步发布实验 |
| 27_Day29向量库预习 | Chroma 预告 |

**生成器**：`scripts/course_days/day28.py`（gold-standard）

**运行生成**：`python3 scripts/course_days/day28.py` → 写入 `course/day28/`（30 文件，≥110k 字符）

**前置课程**：Day 27 分块调优与 `POST /api/knowledge/evaluate` 已完成。
