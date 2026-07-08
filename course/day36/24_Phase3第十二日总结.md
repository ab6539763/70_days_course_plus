# Phase 3 第十二日总结（Day 37）

## 本周进度

| Day | 主题 | 版本 |
|-----|------|------|
| 29 | Chroma | 0.29.x |
| 30 | 增量索引 | 0.30.x |
| 31 | 混合检索 | 0.31.x |
| 32 | Rerank | 0.32.x |
| 33 | Query Rewrite | 0.33.x |
| **34** | **Citation** | **v0.36.0** |

## Day 36 交付物

- QueryRouter + RouteConfig  
- route-config / citation-preview API  
- chat 响应 expansion.queries + merged citations + rewrite  
- 前端引用展示  
- 20 tests  
- 30 篇课件  

## 核心能力

**可解释性**：每条 RAG 回答可附带可追溯引用列表。

## 与 Phase 3 目标对齐

完整管线：rewrite → hybrid → rerank → **citations** → LLM。

## 学员自评 Rubric

| 等级 | 标准 |
|------|------|
| A | 能设计 Citation JSON + 写 chat 单测 |
| B | 能跑 route_demo 解释字段 |
| C | 能复述 citations 与 rewrite 关系 |
| D | 仅会 pytest -q |

## 下周预告

Day 37：HyDE / 自适应路由 — 一条问句变多条检索 query。

---

## Phase3 能力雷达（Day34 更新）

| 能力 | 等级 |
|------|------|
| 入库 | ★★★★★ |
| 召回 | ★★★★☆ |
| 精排 | ★★★★☆ |
| 改写 | ★★★★☆ |
| 溯源 | ★★★★☆ |
| 扩展 | ★★☆☆☆（Day35） |

---

## 团队复盘

1. citations 是否默认开启？  
2. preview 长度是否够用？  
3. 合规是否要求每条回答至少 1 条引用？  

---

## 金句墙

- 「有据可查」——陈默  
- 「chunk_id 是审计锚点」——林晓  
- 「reply 是面子，citations 是里子」——周航  

---

## 项目经理一页纸

ZL-NA-REQ-036 已交付：QueryRouter、citation API、chat citations、前端展示、20 测试。下一步：Day35 多 query 扩展。
