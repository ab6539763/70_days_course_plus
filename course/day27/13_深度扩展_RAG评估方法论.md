## 附录：chunk_strategies.py

### `nexus-agent-platform/src/rag/chunk_strategies.py` 逐行走读

共 **132** 行。

**L1** `"""`

**L2** `分块策略 — 固定窗口 vs Markdown 章节`

**L3** ``

**L4** `需求：ZL-NA-REQ-026`

**L5** `"""`

**L6** ``

**L7** `from __future__ import annotations`

**L8** ``

**L9** `from dataclasses import dataclass`

**L10** ``

**L11** `from rag.chunker import TextChunk, chunk_text`

**L12** `from tools.parsers.base import DocumentSection, ParsedDocument`

**L13** ``

**L14** ``

**L15** `@dataclass`

**L16** `class ChunkStrategyResult:`

**L17** `    """策略对比结果"""`

**L18** ``

**L19** `    strategy: str`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L20** `    chunk_count: int`

**L21** `    chunks: list[TextChunk]`

**L22** `    preview: str`

**L23** ``

**L24** ``

**L25** `def chunk_fixed_window(`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L26** `    text: str,`

**L27** `    *,`

**L28** `    source: str,`

**L29** `    chunk_size: int = 200,`

**L30** `    overlap: int = 40,`

**L31** `) -> list[TextChunk]:`

**L32** `    """Day 19 默认滑动窗口策略"""`

**L33** `    return chunk_text(text, chunk_size=chunk_size, overlap=overlap, source=source)`

**L34** ``

**L35** ``

**L36** `def chunk_markdown_sections(`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L37** `    doc: ParsedDocument,`

**L38** `    *,`

**L39** `    max_chars: int = 400,`

**L40** `    overlap: int = 40,`

**L41** `) -> list[TextChunk]:`

**L42** `    """`

**L43** `    按 Markdown 章节分块：每节独立成块，过长再滑动切分。`

**L44** `    """`

**L45** `    if not doc.sections:`

**L46** `        return chunk_fixed_window(doc.plain_text, source=doc.filename)`

**L47** ``

**L48** `    chunks: list[TextChunk] = []`

**L49** `    global_index = 0`

**L50** ``

**L51** `    for section in doc.sections:`

**L52** `        header = f"[{section.title}] "`

**L53** `        body = section.body.strip()`

**L54** `        piece = f"{header}{body}" if body else section.title`

**L55** ``

**L56** `        if len(piece) <= max_chars:`

**L57** `            chunks.append(`

**L58** `                TextChunk(`

**L59** `                    chunk_id=f"{doc.filename}:sec:{section.index}",`

**L60** `                    text=piece,`

**L61** `                    source=doc.filename,`

**L62** `                    index=global_index,`

**L63** `                    start_char=0,`

**L64** `                    end_char=len(piece),`

**L65** `                )`

**L66** `            )`

**L67** `            global_index += 1`

**L68** `            continue`

**L69** ``

**L70** `        sub_chunks = chunk_text(`

**L71** `            piece,`

**L72** `            chunk_size=max_chars,`

**L73** `            overlap=overlap,`

**L74** `            source=doc.filename,`

**L75** `        )`

**L76** `        for sub in sub_chunks:`

**L77** `            chunks.append(`

**L78** `                TextChunk(`

**L79** `                    chunk_id=f"{doc.filename}:sec:{section.index}:{sub.index}",`

**L80** `                    text=sub.text,`

**L81** `                    source=doc.filename,`

**L82** `                    index=global_index,`

**L83** `                    start_char=sub.start_char,`

**L84** `                    end_char=sub.end_char,`

**L85** `                )`

**L86** `            )`

**L87** `            global_index += 1`

**L88** ``

**L89** `    return chunks`

**L90** ``

**L91** ``

**L92** `def chunk_from_parsed(`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L93** `    doc: ParsedDocument,`

**L94** `    *,`

**L95** `    strategy: str = "auto",`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L96** `    chunk_size: int = 200,`

**L97** `    overlap: int = 40,`

**L98** `) -> list[TextChunk]:`

**L99** `    """根据文档类型与策略选择分块方式"""`

**L100** `    chosen = strategy`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L101** `    if strategy == "auto":`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L102** `        chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"`

**L103** ``

**L104** `    if chosen == "markdown":`

**L105** `        return chunk_markdown_sections(doc, max_chars=chunk_size, overlap=overlap)`

**L106** `    return chunk_fixed_window(`

**L107** `        doc.plain_text,`

**L108** `        source=doc.filename,`

**L109** `        chunk_size=chunk_size,`

**L110** `        overlap=overlap,`

**L111** `    )`

**L112** ``

**L113** ``

**L114** `def compare_strategies(doc: ParsedDocument) -> list[ChunkStrategyResult]:`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L115** `    """对比固定窗口与章节策略（教学演示用）"""`

**L116** `    fixed = chunk_fixed_window(doc.plain_text, source=doc.filename)`

**L117** `    section = chunk_markdown_sections(doc) if doc.sections else fixed`

**L118** ``

**L119** `    return [`

**L120** `        ChunkStrategyResult(`

**L121** `            strategy="fixed",`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L122** `            chunk_count=len(fixed),`

**L123** `            chunks=fixed,`

**L124** `            preview=fixed[0].text[:80] if fixed else "",`

**L125** `        ),`

**L126** `        ChunkStrategyResult(`

**L127** `            strategy="markdown",`
  → 分块策略与 ChunkConfig.strategy 字段对应。

**L128** `            chunk_count=len(section),`

**L129** `            chunks=section,`

**L130** `            preview=section[0].text[:80] if section else "",`

**L131** `        ),`

**L132** `    ]`


## 附录：embedding_retriever.py

### `nexus-agent-platform/src/rag/embedding_retriever.py` 逐行走读

共 **89** 行。

**L1** `"""`

**L2** `向量检索器 — 基于 Embedding 余弦相似度`

**L3** ``

**L4** `与 KeywordRetriever 接口一致，可注入 DocumentIndex.retriever。`

**L5** ``

**L6** `需求：ZL-NA-REQ-020`

**L7** `"""`

**L8** ``

**L9** `from __future__ import annotations`

**L10** ``

**L11** `from dataclasses import dataclass`

**L12** ``

**L13** `from rag.chunker import TextChunk`

**L14** `from rag.embedding import EmbeddingClient, EmbeddingVector, TfidfEmbeddingModel`

**L15** `from rag.retriever import RetrievalResult`

**L16** ``

**L17** ``

**L18** `@dataclass`

**L19** `class IndexedChunk:`

**L20** `    """带向量的文本块"""`

**L21** ``

**L22** `    chunk: TextChunk`

**L23** `    vector: EmbeddingVector`

**L24** ``

**L25** ``

**L26** `class EmbeddingRetriever:`

**L27** `    """Embedding 向量检索器"""`

**L28** ``

**L29** `    def __init__(`
  → EmbeddingRetriever 为 evaluate 提供 search 能力。

**L30** `        self,`

**L31** `        chunks: list[TextChunk] | None = None,`

**L32** `        *,`

**L33** `        client: EmbeddingClient | None = None,`

**L34** `        min_score: float = 0.05,`

**L35** `    ) -> None:`

**L36** `        self._client = client or EmbeddingClient()`

**L37** `        self._indexed: list[IndexedChunk] = []`

**L38** `        self._min_score = min_score`

**L39** `        if chunks:`

**L40** `            self.index(chunks)`

**L41** ``

**L42** `    @property`

**L43** `    def chunk_count(self) -> int:`
  → EmbeddingRetriever 为 evaluate 提供 search 能力。

**L44** `        return len(self._indexed)`

**L45** ``

**L46** `    def index(self, chunks: list[TextChunk]) -> None:`
  → EmbeddingRetriever 为 evaluate 提供 search 能力。

**L47** `        """在文本块上训练 TF-IDF 并预计算向量"""`

**L48** `        texts = [c.text for c in chunks]`

**L49** `        self._client.fit_corpus(texts)`

**L50** `        vectors = self._client.embed_batch(texts)`

**L51** `        self._indexed = [`

**L52** `            IndexedChunk(chunk=chunk, vector=vec)`

**L53** `            for chunk, vec in zip(chunks, vectors)`

**L54** `        ]`

**L55** ``

**L56** `    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:`
  → EmbeddingRetriever 为 evaluate 提供 search 能力。

**L57** `        query = (query or "").strip()`

**L58** `        if not query or not self._indexed:`

**L59** `            return []`

**L60** ``

**L61** `        query_vec = self._client.embed(query)`

**L62** `        scored: list[RetrievalResult] = []`

**L63** ``

**L64** `        for item in self._indexed:`

**L65** `            score = query_vec.similarity_to(item.vector)`

**L66** `            if score >= self._min_score:`

**L67** `                matched = _overlap_terms(query, item.chunk.text)`

**L68** `                scored.append(`

**L69** `                    RetrievalResult(`

**L70** `                        chunk=item.chunk,`

**L71** `                        score=score,`

**L72** `                        matched_tokens=matched,`

**L73** `                    )`

**L74** `                )`

**L75** ``

**L76** `        scored.sort(key=lambda r: (-r.score, r.chunk.index))`

**L77** `        if not scored:`

**L78** `            return []`

**L79** `        return scored[: max(1, top_k)]`

**L80** ``

**L81** ``

**L82** `def _overlap_terms(query: str, text: str, limit: int = 5) -> tuple[str, ...]:`
  → EmbeddingRetriever 为 evaluate 提供 search 能力。

**L83** `    """提取查询与文档共现词（可解释性）"""`

**L84** `    from rag.synonyms import expand_tokens, tokenize`

**L85** ``

**L86** `    q_set = set(expand_tokens(tokenize(query), query))`

**L87** `    t_set = set(expand_tokens(tokenize(text), text))`

**L88** `    common = [t for t in q_set if t in t_set]`

**L89** `    return tuple(common[:limit])`


# 深度扩展：RAG 评估方法论

## 超越 hit@1

| 指标 | 含义 | Day 27 是否实现 |
|------|------|-----------------|
| hit@1 | top-1 是否含期望证据 | ✅ |
| hit@k | top-k 任一命中 | 可扩展 evaluate_query 的 top_k |
| MRR | 首个命中排名倒数 | ❌ 阅读材料 |
| nDCG | 分级相关性折扣 | ❌ |
| Recall@k | 命中块占全部相关块比例 | 需完整标注 |

## 评估集构建

企业实践：

1. 从客服日志采样真实问句  
2. 人工标注「金标准」段落 id  
3. 分层：简单事实 / 多跳 / 否定类  
4. 定期回归，防止索引漂移  

Day 27 的 `expect_any` 是**低成本弱标注**，适合教学。

## 工具链预览

- **Ragas**：faithfulness、answer_relevancy  
- **TruLens**：追踪 LLM 调用链  
- **LangSmith**：数据集与 A/B  

## A/B 实验统计

样本量 n=4 时，hit_rate 波动极大。生产环境应：

- 扩大评估集至 50+  
- 报告置信区间  
- 分流量灰度（Day 30+ incremental 思路）

## 阅读清单

1. Lewis et al., RAG 原论文评估章节  
2. 课程 `19_讲师补充阅读.md`  
3. NexusAgent Day 29 Chroma 后指标是否一致 —— 自行实验记录
