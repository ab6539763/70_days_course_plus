# Day 27 课件索引

**日期**：2026-08-03（星期一）  
**主题**：分块参数调优与检索质量 A/B 评估  
**需求**：ZL-NA-REQ-027  
**版本**：v0.27.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| ChunkConfig | `rag/chunk_config.py` | 四套 PRESET 与 validate |
| 检索评估 | `rag/retrieval_eval.py` | hit@1、run_ab_experiment |
| 评估问句 | `day27/constants.py` | EVAL_QUERIES 四条 |
| API | `GET/PUT /api/knowledge/chunk-config` | 持久化默认分块 |
| API | `POST /api/knowledge/evaluate` | A/B 实验入口 |
| 前端 | `frontend/knowledge.js` | `#kb-eval-btn` |
| 测试 | `tests/day27/` | 15 项 |

## 关键设计决策

1. **评估与生产索引分离**：`evaluate` 在 `product_notice.md` 上模拟分块，不写 `store.json`。
2. **hit@1 教学指标**：top-1 检索块文本包含 `expect_any` 任一关键词即命中。
3. **PRESET 四套**：compact / default / wide / markdown_wide，覆盖块大小与策略组合。
4. **chunk_config 持久化**：`PUT` 后影响后续 `upload`，已有块不自动变化。
5. **排序规则**：`hit_rate` 降序 → `avg_top_score` → `chunk_count` 升序。

## 验收命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day27/ab_experiment_demo.py
python3 src/day27/chunk_tune_api_demo.py
pytest tests/day27/ -q
```

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_分块调参与检索评估详解 | 深度专题讲义 |
| 15_授课实录 | 上午下午完整实录 |
| 22_retrieval_eval精读 | hit@1 源码走读 |
| 23_chunk_config与企业预设实践 | PRESET 设计 |
| 26_实操Lab手册 | 六步实验（评分） |
| 27_Day28知识库重建预习 | rebuild 预告 |

**生成器**：`scripts/course_days/day27.py`（gold-standard）
