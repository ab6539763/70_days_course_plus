# retrieval_eval 精读

**文件**：`nexus-agent-platform/src/rag/retrieval_eval.py`  
**需求**：ZL-NA-REQ-027

## 模块职责

在**单份 ParsedDocument** 上，对多套 ChunkConfig 构建临时检索器并计算 hit@1。  
本文件是 Day 27 的「实验引擎」，与 `api/knowledge.py` 的 evaluate 端点直接对接。

## 数据类速览

| 类 | 用途 |
|----|------|
| EvalQuery | 评估输入：问句 + expect_any |
| QueryEvalResult | 单条 query 的 hit / score / preview |
| ConfigEvalResult | 单套配置的 hit_rate 与明细列表 |

## 核心算法

### hit@1

1. `retriever.search(query, top_k=1)`  
2. 取 `results[0].chunk.text`  
3. 若 `expect_any` 非空：`any(kw in text for kw in expect_any)`  
4. 否则有结果即 hit  

### A/B 排序

```python
results.sort(key=lambda r: (-r.hit_rate, -r.avg_top_score, r.chunk_count))
```

第三键 `chunk_count` 升序：hit 相同时偏好更粗粒度（更少块）。

## 逐行走读（带讲师批注）

### `nexus-agent-platform/src/rag/retrieval_eval.py` 逐行走读

共 **155** 行。

**L1** `"""`
  → 模块职责：检索质量评估，与生产 KnowledgeStore 解耦。

**L2** `检索质量评估 — hit@1 与 A/B 分块对比`

**L3** ``

**L4** `需求：ZL-NA-REQ-027`

**L5** `"""`

**L6** ``

**L7** `from __future__ import annotations`

**L8** ``

**L9** `from dataclasses import dataclass, field`

**L10** `from typing import Any`

**L11** ``

**L12** `from rag.chunk_config import ChunkConfig`
  → 依赖 ChunkConfig：评估输入必须可 validate。

**L13** `from rag.chunk_strategies import chunk_from_parsed`
  → chunk_from_parsed：复用 Day 26 分块实现，不重复造轮子。

**L14** `from rag.embedding_retriever import EmbeddingRetriever`
  → EmbeddingRetriever：内存 TF-IDF，fit 在当前 chunks 上。

**L15** `from tools.parsers.base import ParsedDocument`

**L16** ``

**L17** ``

**L18** `@dataclass`
  → EvalQuery：单条评估样本，expect_any 为弱监督关键词。

**L19** `class EvalQuery:`

**L20** `    """单条评估查询"""`

**L21** ``

**L22** `    query: str`

**L23** `    expect_any: tuple[str, ...] = ()`

**L24** `    label: str = ""`

**L25** ``

**L26** `    @classmethod`
  → from_dict 兼容 expect 旧字段名，降低 JSON 迁移成本。

**L27** `    def from_dict(cls, data: dict[str, Any]) -> EvalQuery:`

**L28** `        expect = data.get("expect_any") or data.get("expect") or []`

**L29** `        return cls(`

**L30** `            query=str(data["query"]),`

**L31** `            expect_any=tuple(str(x) for x in expect),`

**L32** `            label=str(data.get("label", "")),`

**L33** `        )`

**L34** ``

**L35** ``

**L36** `@dataclass`
  → QueryEvalResult：单查询粒度，供教师逐条讲评。

**L37** `class QueryEvalResult:`

**L38** `    """单查询评估结果"""`

**L39** ``

**L40** `    query: str`

**L41** `    hit: bool`

**L42** `    top_score: float`

**L43** `    top_preview: str`

**L44** `    expect_any: tuple[str, ...] = ()`

**L45** ``

**L46** `    def to_dict(self) -> dict[str, Any]:`
  → to_dict 四舍五入 top_score，API 响应更整洁。

**L47** `        return {`

**L48** `            "query": self.query,`

**L49** `            "hit": self.hit,`

**L50** `            "top_score": round(self.top_score, 4),`

**L51** `            "top_preview": self.top_preview,`

**L52** `            "expect_any": list(self.expect_any),`

**L53** `        }`

**L54** ``

**L55** ``

**L56** `@dataclass`
  → ConfigEvalResult：A/B 表格的一行。

**L57** `class ConfigEvalResult:`

**L58** `    """单配置完整评估"""`

**L59** ``

**L60** `    config: ChunkConfig`

**L61** `    chunk_count: int`

**L62** `    hit_rate: float`

**L63** `    avg_top_score: float`

**L64** `    queries: list[QueryEvalResult] = field(default_factory=list)`

**L65** ``

**L66** `    def to_dict(self) -> dict[str, Any]:`

**L67** `        return {`

**L68** `            "config": self.config.to_dict(),`

**L69** `            "chunk_count": self.chunk_count,`

**L70** `            "hit_rate": round(self.hit_rate, 4),`

**L71** `            "avg_top_score": round(self.avg_top_score, 4),`

**L72** `            "queries": [q.to_dict() for q in self.queries],`

**L73** `        }`

**L74** ``

**L75** ``

**L76** `def build_retriever_for_doc(`
  → build_retriever_for_doc：评估路径入口，绝不写 store。

**L77** `    doc: ParsedDocument,`

**L78** `    config: ChunkConfig,`

**L79** `) -> EmbeddingRetriever:`

**L80** `    """用指定配置对单文档分块并构建临时检索器"""`

**L81** `    config.validate()`
  → 先 validate 再分块，失败快速返回。

**L82** `    chunks = chunk_from_parsed(`
  → chunk_from_parsed 参数来自 config 四字段。

**L83** `        doc,`

**L84** `        strategy=config.strategy,`

**L85** `        chunk_size=config.chunk_size,`

**L86** `        overlap=config.overlap,`

**L87** `    )`

**L88** `    return EmbeddingRetriever(chunks)`
  → EmbeddingRetriever 构造即 fit 词表，chunk 变化则向量变。

**L89** ``

**L90** ``

**L91** `def evaluate_query(`
  → evaluate_query：hit@1 实现，top_k 默认 1 可扩展。

**L92** `    retriever: EmbeddingRetriever,`

**L93** `    eval_query: EvalQuery,`

**L94** `    *,`

**L95** `    top_k: int = 1,`

**L96** `) -> QueryEvalResult:`

**L97** `    results = retriever.search(eval_query.query, top_k=top_k)`
  → search 返回 ScoredChunk 列表，可能为空。

**L98** `    if not results:`
  → 无检索结果时 hit=False，避免 None 访问。

**L99** `        return QueryEvalResult(`

**L100** `            query=eval_query.query,`

**L101** `            hit=False,`

**L102** `            top_score=0.0,`

**L103** `            top_preview="",`

**L104** `            expect_any=eval_query.expect_any,`

**L105** `        )`

**L106** ``

**L107** `    top = results[0]`

**L108** `    text = top.chunk.text`

**L109** `    hit = True`
  → expect_any 非空才做关键词匹配；空则视为命中。

**L110** `    if eval_query.expect_any:`

**L111** `        hit = any(kw in text for kw in eval_query.expect_any)`
  → any(kw in text)：子串匹配，教学简单；生产可用正则或 NER。

**L112** ``

**L113** `    return QueryEvalResult(`

**L114** `        query=eval_query.query,`

**L115** `        hit=hit,`

**L116** `        top_score=top.score,`

**L117** `        top_preview=top.preview(80),`
  → preview(80) 截断预览，便于 CLI 与日志阅读。

**L118** `        expect_any=eval_query.expect_any,`

**L119** `    )`

**L120** ``

**L121** ``

**L122** `def evaluate_config(`
  → evaluate_config：单配置完整实验一次调用。

**L123** `    doc: ParsedDocument,`

**L124** `    config: ChunkConfig,`

**L125** `    queries: list[EvalQuery],`

**L126** `) -> ConfigEvalResult:`

**L127** `    """对一份 ParsedDocument 评估分块配置"""`

**L128** `    retriever = build_retriever_for_doc(doc, config)`
  → build_retriever_for_doc 每次新建 retriever，配置间隔离。

**L129** `    query_results = [evaluate_query(retriever, q) for q in queries]`

**L130** `    hits = sum(1 for r in query_results if r.hit)`
  → hits 计数：Python sum 布尔序列，简洁可读。

**L131** `    total = len(query_results) or 1`
  → total 至少为 1，防止除零。

**L132** `    avg_score = sum(r.top_score for r in query_results) / total`

**L133** ``

**L134** `    return ConfigEvalResult(`

**L135** `        config=config,`

**L136** `        chunk_count=retriever.chunk_count,`

**L137** `        hit_rate=hits / total,`

**L138** `        avg_top_score=avg_score,`

**L139** `        queries=query_results,`

**L140** `    )`

**L141** ``

**L142** ``

**L143** `def run_ab_experiment(`
  → run_ab_experiment：A/B 核心，列表推导式生成结果。

**L144** `    doc: ParsedDocument,`

**L145** `    configs: list[ChunkConfig],`

**L146** `    queries: list[EvalQuery],`

**L147** `) -> list[ConfigEvalResult]:`

**L148** `    """多配置 A/B 对比，按 hit_rate 降序"""`

**L149** `    results = [evaluate_config(doc, cfg, queries) for cfg in configs]`

**L150** `    results.sort(key=lambda r: (-r.hit_rate, -r.avg_top_score, r.chunk_count))`
  → 排序键：hit_rate ↓, avg_top_score ↓, chunk_count ↑。

**L151** `    return results`

**L152** ``

**L153** ``

**L154** `def pick_best_config(results: list[ConfigEvalResult]) -> ConfigEvalResult | None:`
  → pick_best_config：空列表返回 None，API 层需处理。

**L155** `    return results[0] if results else None`


## 与测试的对应关系

| 测试函数 | 覆盖行 |
|----------|--------|
| test_evaluate_config_hit_rate | evaluate_config |
| test_run_ab_experiment_sorted | run_ab_experiment 排序 |
| test_eval_query_miss | evaluate_query 未命中 |
| test_smaller_chunks_more_blocks | chunk_count 随 size 变化 |

## 练习题

1. 修改 `evaluate_query` 支持 hit@3，写出伪代码。  
2. 为何 avg_top_score 作第二排序键？  
3. 若两个配置 hit_rate 都是 1.0，你会选 chunk_count 少还是多？说明业务理由。  
4. 在 L111 改用大小写不敏感匹配，会如何影响「收益率」类 query？

---

## 源码测试映射（扩展）

| 测试 | 断言意图 |
|------|----------|
| test_evaluate_config_hit_rate | hit_rate 区间合法 |
| test_run_ab_experiment_sorted | 排序单调性 |
| test_smaller_chunks_more_blocks | size↓ → chunk_count↑ |
| test_knowledge_store_chunk_config_roundtrip | 持久化 |
| test_put_invalid_overlap | API 422 |
| test_evaluate_presets | 集成 evaluate |

## 代码阅读作业

用 `grep -n` 在仓库搜索 `run_ab_experiment` 调用点，列出文件与行号，说明每条调用链属于「实验」还是「生产」。
