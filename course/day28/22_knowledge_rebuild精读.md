# knowledge_rebuild 精读

**路径**：`nexus-agent-platform/src/rag/knowledge_rebuild.py`

## RebuildReport

不可变报告对象，`to_dict` 供 API。`rebuilt_at` 与 `store.last_rebuilt_at` 一致。

## collect_source_files 算法

1. 解析默认 uploads / sample 路径（`get_path`）  
2. `by_name: dict[str, Path]`  
3. 若 `include_sample_docs`：glob 填入 sample  
4. uploads glob **覆盖**同名  
5. 返回排序后的 Path 列表  

## rebuild_store 逐步说明

| 步骤 | 代码意图 |
|------|----------|
| 快照 | documents_before, chunks_before |
| 取配置 | cfg = store.get_chunk_config() |
| 收集源 | collect_source_files(...) |
| 清空 | documents/chunks clear + invalidate_cache |
| 入库 | parse → clean → chunk → _append_chunks |
| 索引 | _rebuild_index() |
| 持久化 | last_rebuilt_at + save() |

## rebuild_with_best_config

延迟 import Day 27 的 `EVAL_QUERIES` 与 `run_ab_experiment`，避免模块循环依赖。

## 逐行走读（讲师批注）

### `nexus-agent-platform/src/rag/knowledge_rebuild.py` 逐行走读

共 **168** 行。

**L1** `"""`
  → 模块 docstring：全量重建，需求 ZL-NA-REQ-028。

**L2** `知识库全量重建 — 按当前 chunk_config 重扫源文件`

**L3** ``

**L4** `需求：ZL-NA-REQ-028`

**L5** `"""`

**L6** ``

**L7** `from __future__ import annotations`

**L8** ``

**L9** `from dataclasses import dataclass, field`

**L10** `from datetime import datetime, timezone`

**L11** `from pathlib import Path`

**L12** `from typing import Any`

**L13** ``

**L14** `from core.paths import get_path`
  → get_path：统一路径解析，sample_docs 与 uploads 位置由 core.paths 管理。

**L15** `from rag.chunk_config import ChunkConfig`

**L16** `from rag.chunk_strategies import chunk_from_parsed`

**L17** `from rag.knowledge_store import KnowledgeDocument, KnowledgeStore`

**L18** `from tools.doc_parser import SUPPORTED_EXTENSIONS, parse_bytes`

**L19** `from utils.text_utils import clean_text`

**L20** ``

**L21** `_SOURCE_GLOBS = tuple(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))`

**L22** ``

**L23** ``

**L24** `@dataclass`
  → RebuildReport：API 与 CLI 共用的重建报告 dataclass。

**L25** `class RebuildReport:`

**L26** `    """全量重建结果报告"""`

**L27** ``

**L28** `    documents_before: int`

**L29** `    chunks_before: int`

**L30** `    documents_after: int`

**L31** `    chunks_after: int`

**L32** `    sources_processed: int`

**L33** `    chunk_config: ChunkConfig`

**L34** `    source_files: list[str] = field(default_factory=list)`

**L35** `    rebuilt_at: str = ""`

**L36** `    message: str = ""`

**L37** ``

**L38** `    def to_dict(self) -> dict[str, Any]:`

**L39** `        return {`

**L40** `            "documents_before": self.documents_before,`

**L41** `            "chunks_before": self.chunks_before,`

**L42** `            "documents_after": self.documents_after,`

**L43** `            "chunks_after": self.chunks_after,`

**L44** `            "sources_processed": self.sources_processed,`

**L45** `            "chunk_config": self.chunk_config.to_dict(),`

**L46** `            "source_files": self.source_files,`

**L47** `            "rebuilt_at": self.rebuilt_at,`

**L48** `            "message": self.message,`

**L49** `        }`

**L50** ``

**L51** ``

**L52** `def collect_source_files(`
  → collect_source_files：双源扫描入口，测试可注入临时目录。

**L53** `    *,`

**L54** `    uploads_dir: Path | None = None,`

**L55** `    sample_docs_dir: Path | None = None,`

**L56** `    include_sample_docs: bool = True,`

**L57** `) -> list[Path]:`

**L58** `    """`

**L59** `    收集可重建的源文件。`

**L60** ``

**L61** `    uploads 与 sample_docs 同名时，uploads 优先覆盖。`
  → uploads 优先覆盖 sample 的注释，业务语义核心。

**L62** `    """`

**L63** `    uploads = uploads_dir or get_path("knowledge_uploads")`
  → uploads 默认路径：运营上传目录。

**L64** `    sample = sample_docs_dir or get_path("sample_docs")`
  → sample 默认路径：教学样例目录。

**L65** `    by_name: dict[str, Path] = {}`

**L66** ``

**L67** `    if include_sample_docs and sample.is_dir():`
  → include_sample_docs=false 时仅扫 uploads，运维场景。

**L68** `        for pattern in _SOURCE_GLOBS:`

**L69** `            for path in sorted(sample.glob(pattern)):`

**L70** `                if path.is_file():`

**L71** `                    by_name[path.name] = path`

**L72** ``

**L73** `    if uploads.is_dir():`

**L74** `        for pattern in _SOURCE_GLOBS:`

**L75** `            for path in sorted(uploads.glob(pattern)):`

**L76** `                if path.is_file():`

**L77** `                    by_name[path.name] = path`

**L78** ``

**L79** `    return [by_name[name] for name in sorted(by_name)]`
  → sorted(by_name) 保证跨机器确定性。

**L80** ``

**L81** ``

**L82** `def rebuild_store(`
  → rebuild_store：清空后全量重建主函数。

**L83** `    store: KnowledgeStore,`

**L84** `    *,`

**L85** `    include_sample_docs: bool = True,`

**L86** `    uploads_dir: Path | None = None,`

**L87** `    sample_docs_dir: Path | None = None,`

**L88** `) -> RebuildReport:`

**L89** `    """`

**L90** `    清空索引并按当前 chunk_config 从源文件全量重建。`

**L91** ``

**L92** `    流程：收集源文件 → 清空 chunks/documents → 逐文件 parse+chunk → 重建 embedding → save`

**L93** `    """`

**L94** `    docs_before = store.document_count`
  → 快照 before 计数，写入 RebuildReport 供 UI 展示。

**L95** `    chunks_before = store.chunk_count`

**L96** `    cfg = store.get_chunk_config()`
  → 使用 store 当前 chunk_config，而非全局常量。

**L97** ``

**L98** `    sources = collect_source_files(`

**L99** `        uploads_dir=uploads_dir,`

**L100** `        sample_docs_dir=sample_docs_dir,`

**L101** `        include_sample_docs=include_sample_docs,`

**L102** `    )`

**L103** ``

**L104** `    store.documents.clear()`
  → clear documents/chunks：破坏性操作，生产需备份。

**L105** `    store.chunks.clear()`

**L106** `    store.invalidate_cache()`
  → invalidate_cache：防止 DocumentIndex 持有旧 chunk 引用。

**L107** ``

**L108** `    for path in sources:`
  → 逐文件循环：与 upload 单文件 ingest 不同，这是批处理。

**L109** `        parsed = parse_bytes(path.read_bytes(), path.name)`
  → parse_bytes 复用 Day 26 解析层。

**L110** `        text = parsed.plain_text.strip()`

**L111** `        if not text:`
  → 空文本跳过，避免空文档。

**L112** `            continue`

**L113** `        text, _ = clean_text(text)`

**L114** `        parsed.plain_text = text`

**L115** `        for section in parsed.sections:`

**L116** `            section.body, _ = clean_text(section.body)`

**L117** ``

**L118** `        new_chunks = chunk_from_parsed(`
  → chunk_from_parsed 使用 store 配置四参数。

**L119** `            parsed,`

**L120** `            strategy=cfg.strategy,`

**L121** `            chunk_size=cfg.chunk_size,`

**L122** `            overlap=cfg.overlap,`

**L123** `        )`

**L124** `        size_bytes = path.stat().st_size`

**L125** `        store._append_chunks(`
  → _append_chunks 内部方法：写入 documents 与 chunks 列表。

**L126** `            parsed.filename,`

**L127** `            new_chunks,`

**L128** `            size_bytes=size_bytes,`

**L129** `            doc_format=parsed.format,`

**L130** `        )`

**L131** ``

**L132** `    store._rebuild_index()`
  → _rebuild_index：重建 TF-IDF + Chroma（Day 29+）。

**L133** `    rebuilt_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`
  → UTC 时间戳，ISO8601 格式，写入 last_rebuilt_at。

**L134** ``

**L135** `    report = RebuildReport(`

**L136** `        documents_before=docs_before,`

**L137** `        chunks_before=chunks_before,`

**L138** `        documents_after=store.document_count,`

**L139** `        chunks_after=store.chunk_count,`

**L140** `        sources_processed=len(sources),`

**L141** `        chunk_config=cfg,`

**L142** `        source_files=[p.name for p in sources],`

**L143** `        rebuilt_at=rebuilt_at,`

**L144** `        message="知识库已按当前 chunk_config 全量重建",`

**L145** `    )`

**L146** `    store.last_rebuilt_at = rebuilt_at`
  → store.last_rebuilt_at 持久化字段，status API 暴露。

**L147** `    store.save()`

**L148** `    return report`

**L149** ``

**L150** ``

**L151** `def rebuild_with_best_config(`
  → rebuild_with_best_config：evaluate + rebuild 编排。

**L152** `    store: KnowledgeStore,`

**L153** `    *,`

**L154** `    eval_sample_path: Path,`

**L155** `    include_sample_docs: bool = True,`

**L156** `) -> RebuildReport:`

**L157** `    """先运行 A/B 评估选最优配置，再全量重建"""`

**L158** `    from day27.constants import EVAL_QUERIES`
  → 延迟 import Day 27 模块，避免 import 环。

**L159** `    from rag.chunk_config import PRESET_CONFIGS`

**L160** `    from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment`

**L161** ``

**L162** `    doc = parse_bytes(eval_sample_path.read_bytes(), eval_sample_path.name)`

**L163** `    queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]`

**L164** `    results = run_ab_experiment(doc, list(PRESET_CONFIGS), queries)`
  → run_ab_experiment 在 product_notice 上选最优 PRESET。

**L165** `    best = pick_best_config(results)`

**L166** `    if best:`

**L167** `        store.set_chunk_config(best.config)`
  → set_chunk_config 后立刻 rebuild_store 完成发布。

**L168** `    return rebuild_store(store, include_sample_docs=include_sample_docs)`


## 练习

1. 若要在 rebuild 中跳过 PDF，应改哪一层？  
2. 如何实现「dry-run rebuild」只报告不写入？（提示：不 save）  
3. 解释 uploads 优先对投资人演示的意义。  
4. 画出 rebuild_store 与 ingest_upload 的异同 Venn 图（文字描述即可）。

---

## 与测试用例对照精读

### test_collect_sources_uploads_override

构造临时 uploads/sample，验证 uploads 文本覆盖。阅读时对照 `collect_source_files` L61–77。

### test_rebuild_changes_chunk_count

修改 `chunk_config` 为 tiny 后 rebuild，块数应变化。说明 rebuild 确实用新配置重切。

### test_rebuild_persists_last_rebuilt_at

连续 load 验证持久化。联系 `status` API 的 `last_rebuilt_at` 字段。

### test_rebuild_api.py

`test_chat_after_rebuild` 证明发布后会话可用新索引回答。失败时先查 session 与 MOCK 环境。

## 设计思考题（提交可选）

若允许「仅重建 uploads 不改 sample」，API 应增加何参数？与现有 `include_sample_docs` 如何组合？
