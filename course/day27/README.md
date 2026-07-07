# Day 27 课件索引

**日期**：2026-08-03（星期一）  
**主题**：分块参数调优与检索质量 A/B 评估  
**需求**：ZL-NA-REQ-027

## 今日交付

- `rag/chunk_config.py` — ChunkConfig 与四套 PRESET
- `rag/retrieval_eval.py` — hit@1、run_ab_experiment
- `GET/PUT /api/knowledge/chunk-config`
- `POST /api/knowledge/evaluate`
- `KnowledgeStore` 持久化 `chunk_config`
- `frontend/knowledge.js` — A/B 评估按钮
- `tests/day27/` 15 项

## 关键设计

1. **评估与生产索引分离**：evaluate 在样例文档上模拟，不破坏 store  
2. **hit@1 教学指标**：top-1 块含 expect_any 任一关键词  
3. **PRESET 四套**：compact / default / wide / markdown_wide  
4. **chunk_config 持久化**：PUT 后影响后续 upload  
5. **版本 0.27.0**：health、status、PACKAGE_STRUCTURE 对齐  

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day27/chunk_tune_api_demo.py
PYTHONPATH=src pytest tests/day27/ -q
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 11 | 分块调参与检索评估详解 | 深度专题 |
| 22 | retrieval_eval 精读 | hit@1 源码 |
| 26 | 实操 Lab | 六步实验 |
| 27 | Day28 预习 | 全库 rebuild |
