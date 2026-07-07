# Phase 3 第三日总结（Day 25–27）

## 三日脉络

| 日 | 主题 | 关键词 |
|----|------|--------|
| Day 25 | 知识库 REST + TF-IDF | upload, store.json |
| Day 26 | 多格式解析 | md, pdf, chunk_strategies |
| Day 27 | 分块调参 + A/B | ChunkConfig, hit@1, evaluate |

## 技术栈累积

```
upload → parse → chunk(config) → index → chat
                      ↑
              Day 27 量化选 config
```

## 团队里程碑

- 知识库 API 版本 v0.27.0 教学设计  
- 15 个 day27 测试守护回归  
- 产品部复盘会案例闭环  

## 常见坑汇总

1. 以为 PUT 会重建 —— **不会**  
2. 评估用 uploads 文件 —— **今日用固定样例**  
3. 忽视 overlap 边界 —— **必须 < size**  

## 明日预告

Day 28：**rebuild_store**，`last_rebuilt_at`，`apply_best_config` 一键发布。
