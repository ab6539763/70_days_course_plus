# Phase 3 第十一日总结（Day 35）

## Day 35 交付物

- QueryExpander + ExpandingRetriever + ResultMerger
- expansion-config / expansion-preview API
- chat 响应 `expansion.queries` + merged citations
- tests/day35/ 20 项全绿
- 30 篇课件

## 核心能力

**宽召回**：一条问句变多条检索 query，merge 去重后进入 hybrid/rerank。

## 下一日

Day 36：自适应路由 — 按意图动态 expand/rewrite。
