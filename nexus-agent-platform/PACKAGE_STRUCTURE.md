# NexusAgent 包结构说明

**版本**：v0.27.0（Day 27 分块调参）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-027

## Day 27 新增

```
src/rag/
  chunk_config.py      # ChunkConfig 与 PRESET_CONFIGS
  retrieval_eval.py    # hit@1 评估、run_ab_experiment
src/day27/
  ab_experiment_demo.py
  chunk_tune_api_demo.py
  constants.py         # EVAL_QUERIES
```

## API v0.27.0

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/chunk-config` | 当前默认分块参数 |
| PUT | `/api/knowledge/chunk-config` | 更新后续上传使用的参数 |
| POST | `/api/knowledge/evaluate` | A/B 预设评估，返回 best_config |

`store.json` 新增 `chunk_config` 字段持久化。

## 评估指标

- **hit_rate**：评估问句 top-1 块命中 `expect_any` 关键词的比例  
- **avg_top_score**：top-1 余弦相似度均值  
- **chunk_count**：该配置下的块数  
