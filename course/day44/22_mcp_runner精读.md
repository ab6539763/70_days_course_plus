# Day 44 精读：mcp_runner 与 MCP 工具桥接管线

**需求**：ZL-NA-REQ-044 | **学时**：120 min

---

## 一、mcp_runner.py 全文

```python
"""
McpRunner — MCP 工具发现 → 路由 → 调用 → 汇总

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST
from agent.mcp_server import NexusMcpServer
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class McpStep:
    """MCP 级 trace — 对齐 mcp_trace 并扩展 mcp_method"""

    step: int
    phase: str
    thought: str
    mcp_method: str | None = None
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "phase": self.phase,
            "thought": self.thought,
            "mcp_method": self.mcp_method,
            "tool": self.tool,
            "arguments": dict(self.arguments or {}),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class McpRunOutcome:
    query: str
    reply: str
    steps: tuple[McpStep, ...]
    tools_used: tuple[str, ...]
    mcp_tools: tuple[str, ...]
    server_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "mcp_tools": list(self.mcp_tools),
            "server_name": self.server_name,
        }


class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> McpRunOutcome:
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=(),
            tools_used=(),
            mcp_tools=(),
            server_name=self._config.server_name,
        )

    def _route_tool(
        self,
        query: str,
        available: tuple[str, ...],
    ) -> tuple[str, dict[str, Any], str]:
        q = query.lower()
        if self._config.mock_routing:
            if any(k in q for k in ("总结", "归纳", "概括", "分类")):
                tool = "intent_classify" if "intent_classify" in available else available[0]
                return tool, {"query": query}, "路由到意图 MCP 工具 intent_classify。"
            if any(k in q for k in ("电话", "客服", "139", "联系")):
                tool = "faq_lookup" if "faq_lookup" in available else available[0]
                return tool, {"query": query}, "路由到 FAQ MCP 工具 faq_lookup。"
            if any(k in q for k in ("收益", "年化", "风险", "理财", "产品")):
                tool = "rag_search" if "rag_search" in available else available[0]
                return tool, {"query": query}, "路由到 RAG MCP 工具 rag_search。"
        if re.search(r"\d{7,}", q):
            tool = "faq_lookup" if "faq_lookup" in available else available[0]
            return tool, {"query": query}, "检测到号码模式，路由 faq_lookup。"
        tool = "rag_search" if "rag_search" in available else available[0]
        return tool, {"query": query}, "默认路由到 rag_search。"

    def _synthesize(self, query: str, observation: str, tool: str) -> str:
        obs = (observation or "").strip()
        if not obs:
            return f"已通过 MCP 调用 {tool}，但未获得有效结果。"
        if len(obs) > 280:
            obs = obs[:277] + "..."
        return f"【MCP:{tool}】{obs}"
```


---

## 二、行级注释：QueryRouter 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rewrite(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、RuleBasedQueryRouter.route（L33–L68）

```python
"""
MCP 配置 — 自研 MCP Server 暴露 Nexus 工具链

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class McpConfig:
    """MCP 协议桥接策略"""

    enabled: bool = True
    server_name: str = "nexus-tools"
    expose_external_tools: bool = True
    mock_routing: bool = True
    use_session_history: bool = True
    return_mcp_trace: bool = True
    max_tool_calls: int = 2

    def validate(self) -> None:
        if self.max_tool_calls < 1 or self.max_tool_calls > 4:
            raise ValueError(f"max_tool_calls 须在 1~4，收到 {self.max_tool_calls}")
        if not (self.server_name or "").strip():
            raise ValueError("server_name 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "server_name": self.server_name,
            "expose_external_tools": self.expose_external_tools,
            "mock_routing": self.mock_routing,
            "use_session_history": self.use_session_history,
            "return_mcp_trace": self.return_mcp_trace,
            "max_tool_calls": self.max_tool_calls,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> McpConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            server_name=str(data.get("server_name", "nexus-tools")),
            expose_external_tools=bool(data.get("expose_external_tools", True)),
            mock_routing=bool(data.get("mock_routing", True)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_mcp_trace=bool(data.get("return_mcp_trace", True)),
            max_tool_calls=int(data.get("max_tool_calls", 2)),
        )
```


| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `rewrite`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、rewrite 全文

```python
class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )
```


| 行 | 讲解 |
|----|------|
| 子串分支 | `q in t` → 1.0，电话/SKU 金路径 |
| coverage | matched tokens / query tokens |
| bigram_bonus | 连续二字共现比例 |
| length_penalty | 抑制长文噪声 |
| clamp | [0, 1] 便于 UI 展示 sim=% |

---

## 五、_bigram_overlap

```python
class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )
```


中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、context.py 全文

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 七、search 主流程

```python
def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )
```


| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rewrite 开销 |
| pool 计算 | `max(max_citations, top_k)` |
| candidates | inner hybrid 宽召回 |
| rewrite 调用 | MockCrossEncoder 改写截断 |

---

## 八、citation_config.py 全文

```python
"""
MCP 配置 — 自研 MCP Server 暴露 Nexus 工具链

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class McpConfig:
    """MCP 协议桥接策略"""

    enabled: bool = True
    server_name: str = "nexus-tools"
    expose_external_tools: bool = True
    mock_routing: bool = True
    use_session_history: bool = True
    return_mcp_trace: bool = True
    max_tool_calls: int = 2

    def validate(self) -> None:
        if self.max_tool_calls < 1 or self.max_tool_calls > 4:
            raise ValueError(f"max_tool_calls 须在 1~4，收到 {self.max_tool_calls}")
        if not (self.server_name or "").strip():
            raise ValueError("server_name 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "server_name": self.server_name,
            "expose_external_tools": self.expose_external_tools,
            "mock_routing": self.mock_routing,
            "use_session_history": self.use_session_history,
            "return_mcp_trace": self.return_mcp_trace,
            "max_tool_calls": self.max_tool_calls,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> McpConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            server_name=str(data.get("server_name", "nexus-tools")),
            expose_external_tools=bool(data.get("expose_external_tools", True)),
            mock_routing=bool(data.get("mock_routing", True)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_mcp_trace=bool(data.get("return_mcp_trace", True)),
            max_tool_calls=int(data.get("max_tool_calls", 2)),
        )
```


`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

```python
def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config
```


`RAGContextService(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_query_router.py

```python
"""Day 44 MCP Server/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.mcp_bridge import structured_tools_from_mcp
from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST, McpJsonRpcRequest
from agent.mcp_runner import McpRunner
from agent.mcp_server import NexusMcpServer
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return McpRunner.from_executor(orch.tool_executor, config=McpConfig())


def test_mcp_config_validate():
    McpConfig().validate()
    with pytest.raises(ValueError):
        McpConfig(max_tool_calls=0).validate()
    with pytest.raises(ValueError):
        McpConfig(server_name="  ").validate()


def test_mcp_server_list_tools(runner):
    server = runner._server  # noqa: SLF001
    tools = server.list_tools()
    names = {t.name for t in tools}
    assert "faq_lookup" in names
    assert "rag_search" in names


def test_mcp_server_handle_list(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(McpJsonRpcRequest(method=MCP_METHOD_LIST))
    assert resp.ok
    assert len(resp.result["tools"]) >= 3


def test_mcp_server_handle_call_faq(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(
        McpJsonRpcRequest(
            method=MCP_METHOD_CALL,
            params={"name": "faq_lookup", "arguments": {"query": "客服电话"}},
        )
    )
    assert resp.ok
    text = resp.result["content"][0]["text"]
    assert text


def test_mcp_client_list_and_call(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    tools = client.list_tools()
    assert any(t.name == "rag_search" for t in tools)
    obs = client.call_tool("rag_search", {"query": "年化收益"})
    assert obs


def test_mcp_bridge_structured_tools(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    structured = structured_tools_from_mcp(client)
    names = {t.name for t in structured}
    assert "intent_classify" in names
    out = structured[0].run({"query": "测试"})
    assert isinstance(out, str)


def test_mcp_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "faq_lookup" in outcome.mcp_tools
    assert any(s.phase == "call" for s in outcome.steps)


def test_mcp_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_mcp_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_mcp_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_mcp_config(McpConfig(server_name="custom-mcp", max_tool_calls=3))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_mcp_config()
    assert cfg.server_name == "custom-mcp"
    assert cfg.max_tool_calls == 3
```


| 测试 | 要点 |
|------|------|
| test_RuleBasedQueryRouter.route_from_results_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_citation_preview_with_rewrite | 业务号码 |
| test_context_disabled | 降级路径 |
| test_fetch_citations_with_hits_accessible | inner 类型 |
| test_knowledge_store_persists_citation_config | 持久化 |

---

## 十一、API 测试 test_route_api.py

```python
"""Day 44 MCP API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_get_mcp_config_default(client):
    data = client.get("/api/agent/mcp-config").json()
    assert data["enabled"] is True
    assert data["server_name"] == "nexus-tools"


def test_put_mcp_config(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_tool_calls"] == 3


def test_mcp_list_tools(client):
    resp = client.post("/api/agent/mcp-list-tools", json={})
    assert resp.status_code == 200
    data = resp.json()
    names = {t["name"] for t in data["tools"]}
    assert "faq_lookup" in names
    assert data["server_name"] == "nexus-tools"


def test_mcp_preview_rag(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "rag_search" in data["mcp_tools"]


def test_mcp_preview_with_history(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_mcp_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["mcp_config"]["enabled"] is True


def test_chat_mcp_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace")
    assert body.get("mcp_tools")
    assert body["kind"] == "mcp"


def test_chat_mcp_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace") is None
    assert body["kind"] == "faq"


def test_invalid_mcp_max_tool_calls_422(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 99,
        },
    )
    assert resp.status_code == 422
```


`test_health_version` 锁版本 `v0.44.0`；`test_chat_includes_citations` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rewrite 后前 3 的 rewrite  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json citation_config  

---

## 十三、自检

1. 手绘三阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rewrite 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 口语命中 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day33 衔接

HybridRetriever 仍是 inner；关 rewrite 即回 Day33 行为。retrieval_config 与 citation_config 正交。

---

## 十六、knowledge_store rewrite 方法

```python
def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config
```


`set_citation_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rewrite 是什么。  
2. 1 分钟对比召回与改写。  
3. 白板画 RAGContextService.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q citations 与 context 重复吗？** 可优化；当前同步教学实现。  
**Q matched_tokens 来源？** 来自 RetrievalResult，展示在 Citation 中。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RuleBasedQueryRouter.route` 与 `RoutingRetriever.search`，并映射到 ZL-NA-REQ-044 的 FR-001–FR-003。

---

## 二十一、mcp_runner 完整源码（重复嵌入便于打印）

```python
"""
McpRunner — MCP 工具发现 → 路由 → 调用 → 汇总

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST
from agent.mcp_server import NexusMcpServer
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class McpStep:
    """MCP 级 trace — 对齐 mcp_trace 并扩展 mcp_method"""

    step: int
    phase: str
    thought: str
    mcp_method: str | None = None
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "phase": self.phase,
            "thought": self.thought,
            "mcp_method": self.mcp_method,
            "tool": self.tool,
            "arguments": dict(self.arguments or {}),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class McpRunOutcome:
    query: str
    reply: str
    steps: tuple[McpStep, ...]
    tools_used: tuple[str, ...]
    mcp_tools: tuple[str, ...]
    server_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "mcp_tools": list(self.mcp_tools),
            "server_name": self.server_name,
        }


class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> McpRunOutcome:
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=(),
            tools_used=(),
            mcp_tools=(),
            server_name=self._config.server_name,
        )

    def _route_tool(
        self,
        query: str,
        available: tuple[str, ...],
    ) -> tuple[str, dict[str, Any], str]:
        q = query.lower()
        if self._config.mock_routing:
            if any(k in q for k in ("总结", "归纳", "概括", "分类")):
                tool = "intent_classify" if "intent_classify" in available else available[0]
                return tool, {"query": query}, "路由到意图 MCP 工具 intent_classify。"
            if any(k in q for k in ("电话", "客服", "139", "联系")):
                tool = "faq_lookup" if "faq_lookup" in available else available[0]
                return tool, {"query": query}, "路由到 FAQ MCP 工具 faq_lookup。"
            if any(k in q for k in ("收益", "年化", "风险", "理财", "产品")):
                tool = "rag_search" if "rag_search" in available else available[0]
                return tool, {"query": query}, "路由到 RAG MCP 工具 rag_search。"
        if re.search(r"\d{7,}", q):
            tool = "faq_lookup" if "faq_lookup" in available else available[0]
            return tool, {"query": query}, "检测到号码模式，路由 faq_lookup。"
        tool = "rag_search" if "rag_search" in available else available[0]
        return tool, {"query": query}, "默认路由到 rag_search。"

    def _synthesize(self, query: str, observation: str, tool: str) -> str:
        obs = (observation or "").strip()
        if not obs:
            return f"已通过 MCP 调用 {tool}，但未获得有效结果。"
        if len(obs) > 280:
            obs = obs[:277] + "..."
        return f"【MCP:{tool}】{obs}"
```


---

## 二十二、自适应路由伪代码

```
function FETCH_CITATIONS(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(max_citations, top_k)
    C = INNER(q, P)          # HybridRetriever
    return build_citation_bundle(q, C)
```

---

## 二十三、ROUTE_QUERIES 业务解读

| query | 业务意图 | citation 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_citation_config_validate | FR-004 |
| test_RuleBasedQueryRouter.route_from_results_candidates | FR-002 |
| test_context_enabled | FR-003 |
| test_citation_preview_with_rewrite | AC-03 |
| test_knowledge_store_persists_citation_config | FR-005 |
| test_health_version | FR-008 |
| test_put_citation_config_disable | AC-02 |
| test_chat_includes_citations | AC-05 |

---

## 二十五、knowledge API 节选（citation 上下文）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-035 / ZL-NA-REQ-036 / ZL-NA-REQ-037 / ZL-NA-REQ-038
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    CitationConfigRequest,
    CitationConfigResponse,
    CitationPreviewRequest,
    CitationPreviewResponse,
    ExpansionConfigRequest,
    ExpansionConfigResponse,
    ExpansionPreviewRequest,
    ExpansionPreviewResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
    RerankConfigRequest,
    RerankConfigResponse,
    RewriteConfigRequest,
    RewriteConfigResponse,
    RewritePreviewRequest,
    RewritePreviewResponse,
    RouteConfigRequest,
    RouteConfigResponse,
    RoutePreviewRequest,
    RoutePreviewResponse,
    ValidationConfigRequest,
    ValidationConfigResponse,
    ValidationPreviewRequest,
    ValidationPreviewResponse,
    ValidationRetryPreviewRequest,
    ValidationRetryPreviewResponse,
    RetrievalConfigRequest,
    RetrievalConfigResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import CitationConfig
from rag.expansion_config import ExpansionConfig
from rag.query_expander import build_expander
from rag.query_rewriter import RuleBasedQueryRewriter
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import RouteConfig
from rag.validation_config import ValidationConfig
from rag.rerank_config import RerankConfig
from rag.rewrite_config import RewriteConfig
from rag.retrieval_config import RetrievalConfig
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
def get_retrieval_config() -> RetrievalConfigResponse:
    """返回当前检索模式（vector / keyword / hybrid）与融合参数"""
    cfg = get_knowledge_store().get_retrieval_config()
    return RetrievalConfigResponse(**cfg.to_dict())


@router.put("/retrieval-config", response_model=RetrievalConfigResponse)
def update_retrieval_config(body: RetrievalConfigRequest) -> RetrievalConfigResponse:
    """更新检索策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RetrievalConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_retrieval_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RetrievalConfigResponse(**cfg.to_dict())


@router.get("/rerank-config", response_model=RerankConfigResponse)
def get_rerank_config() -> RerankConfigResponse:
    """返回 rerank 开关、候选池大小与模型标识"""
    cfg = get_knowledge_store().get_rerank_config()
    return RerankConfigResponse(**cfg.to_dict())


@router.put("/rerank-config", response_model=RerankConfigResponse)
def update_rerank_config(body: RerankConfigRequest) -> RerankConfigResponse:
    """更新 rerank 策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RerankConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rerank_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RerankConfigResponse(**cfg.to_dict())


@router.get("/rewrite-config", response_model=RewriteConfigResponse)
def get_rewrite_config() -> RewriteConfigResponse:
    """返回查询改写开关与规则模式"""
    cfg = get_knowledge_store().get_rewrite_config()
    return RewriteConfigResponse(**cfg.to_dict())


@router.put("/rewrite-config", response_model=RewriteConfigResponse)
def update_rewrite_config(body: RewriteConfigRequest) -> RewriteConfigResponse:
    """更新查询改写策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RewriteConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rewrite_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RewriteConfigResponse(**cfg.to_dict())


@router.post("/rewrite-preview", response_model=RewritePreviewResponse)
def rewrite_preview(body: RewritePreviewRequest) -> RewritePreviewResponse:
    """预览单条 query 的规则改写结果（不触发检索）"""
    store = get_knowledge_store()
    cfg = store.get_rewrite_config()
    rewriter = RuleBasedQueryRewriter(config=cfg)
    result = rewriter.rewrite(body.query)
    return RewritePreviewResponse(**result.to_dict())


@router.get("/citation-config", response_model=CitationConfigResponse)
def get_citation_config() -> CitationConfigResponse:
    """返回引用溯源开关与展示参数"""
    cfg = get_knowledge_store().get_citation_config()
    return CitationConfigResponse(**cfg.to_dict())


@router.put("/citation-config", response_model=CitationConfigResponse)
def update_citation_config(body: CitationConfigRequest) -> CitationConfigResponse:
    """更新引用溯源策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = CitationConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_citation_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CitationConfigResponse(**cfg.to_dict())


@ro
```


---

## 二十六、phase3_route_review 建议

课后运行 `src/day37/phase3_route_review.py` 串联 Day25–34。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| citations 替代检索 | 展示层 |
| preview 与全文 | 截断展示 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 rewrite 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET route-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 route_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 20 tests  
10. 能解释翻牌测试  
11. 能对比 Day33  
12. 能预告 Day36 HyDE  
13. 能读 validate 源码  
14. 能解释 include_route_meta  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_citations 上限 10  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-044 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`fetch_citations` 是 **Facade**：对外返回 dict，对内调用 RoutingRetriever.search。与 Day33 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 44 MCP API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_get_mcp_config_default(client):
    data = client.get("/api/agent/mcp-config").json()
    assert data["enabled"] is True
    assert data["server_name"] == "nexus-tools"


def test_put_mcp_config(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_tool_calls"] == 3


def test_mcp_list_tools(client):
    resp = client.post("/api/agent/mcp-list-tools", json={})
    assert resp.status_code == 200
    data = resp.json()
    names = {t["name"] for t in data["tools"]}
    assert "faq_lookup" in names
    assert data["server_name"] == "nexus-tools"


def test_mcp_preview_rag(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "rag_search" in data["mcp_tools"]


def test_mcp_preview_with_history(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_mcp_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["mcp_config"]["enabled"] is True


def test_chat_mcp_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace")
    assert body.get("mcp_tools")
    assert body["kind"] == "mcp"


def test_chat_mcp_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace") is None
    assert body["kind"] == "faq"


def test_invalid_mcp_max_tool_calls_422(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 99,
        },
    )
    assert resp.status_code == 422
```


---

## 三十一、课堂录音稿（8 min）

「打开 mcp_runner，看四阶段管线。先 tools/list 发现工具；再路由选工具，tools/call 执行，最后汇总成回复。这就是 ZL-NA-REQ-044 的执行路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RAGContextService + RouteConfig
- GET/PUT /api/knowledge/route-config
- tests/day37 (20 cases)
```

---

## 三十三、context 二次嵌入

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 三十四、route_demo 全文

```python
"""
MCP 工具桥接演示

运行：PYTHONPATH=src python3 src/day44/mcp_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from api.factory import create_orchestrator
from day44.constants import MCP_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 44 MCP 工具桥接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = McpRunner.from_executor(
        orchestrator.tool_executor,
        config=McpConfig(enabled=True),
    )

    tools = runner.list_tools()
    print(f"\n  MCP Server 工具: {tools}")
    for item in MCP_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    mcp_tools={list(outcome.mcp_tools)} tools_used={list(outcome.tools_used)} {flag}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ MCP 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 三十五、延迟估算习题

pool=20，单次 rewrite 0.5ms → rewrite 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、口语命中 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rewrite 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_citations_count`、`rag_citation_enabled`、`chat_with_citations_rate`。

---

## 三十九、Citation JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | int | 1-based 排序 |
| chunk_id | str | 可追溯分块 |
| source | str | 文档名 |
| score | float | rerank 后分数 |
| preview | str | 截断正文 |
| matched_tokens | list | 命中 token |

---

## 四十、mcp_runner 全文嵌入

```python
"""
McpRunner — MCP 工具发现 → 路由 → 调用 → 汇总

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST
from agent.mcp_server import NexusMcpServer
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class McpStep:
    """MCP 级 trace — 对齐 mcp_trace 并扩展 mcp_method"""

    step: int
    phase: str
    thought: str
    mcp_method: str | None = None
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "phase": self.phase,
            "thought": self.thought,
            "mcp_method": self.mcp_method,
            "tool": self.tool,
            "arguments": dict(self.arguments or {}),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class McpRunOutcome:
    query: str
    reply: str
    steps: tuple[McpStep, ...]
    tools_used: tuple[str, ...]
    mcp_tools: tuple[str, ...]
    server_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "mcp_tools": list(self.mcp_tools),
            "server_name": self.server_name,
        }


class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> McpRunOutcome:
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=(),
            tools_used=(),
            mcp_tools=(),
            server_name=self._config.server_name,
        )

    def _route_tool(
        self,
        query: str,
        available: tuple[str, ...],
    ) -> tuple[str, dict[str, Any], str]:
        q = query.lower()
        if self._config.mock_routing:
            if any(k in q for k in ("总结", "归纳", "概括", "分类")):
                tool = "intent_classify" if "intent_classify" in available else available[0]
                return tool, {"query": query}, "路由到意图 MCP 工具 intent_classify。"
            if any(k in q for k in ("电话", "客服", "139", "联系")):
                tool = "faq_lookup" if "faq_lookup" in available else available[0]
                return tool, {"query": query}, "路由到 FAQ MCP 工具 faq_lookup。"
            if any(k in q for k in ("收益", "年化", "风险", "理财", "产品")):
                tool = "rag_search" if "rag_search" in available else available[0]
                return tool, {"query": query}, "路由到 RAG MCP 工具 rag_search。"
        if re.search(r"\d{7,}", q):
            tool = "faq_lookup" if "faq_lookup" in available else available[0]
            return tool, {"query": query}, "检测到号码模式，路由 faq_lookup。"
        tool = "rag_search" if "rag_search" in available else available[0]
        return tool, {"query": query}, "默认路由到 rag_search。"

    def _synthesize(self, query: str, observation: str, tool: str) -> str:
        obs = (observation or "").strip()
        if not obs:
            return f"已通过 MCP 调用 {tool}，但未获得有效结果。"
        if len(obs) > 280:
            obs = obs[:277] + "..."
        return f"【MCP:{tool}】{obs}"
```


---

## 四十一、chat citations 代码

```python
if body.mcp_mode and store.get_mcp_config().enabled:
            mcfg = store.get_mcp_config()
            runner = McpRunner.from_executor(
                orchestrator.tool_executor,
                config=mcfg,
            )
            history = _session_history(orchestrator, enabled=mcfg.use_session_history)
            mcp_outcome = runner.invoke(message, history=history)
            reply = mcp_outcome.reply
            mcp_trace = [s.to_dict() for s in mcp_outcome.steps]
            mcp_tools = list(mcp_outcome.mcp_tools)
            tools_used = list(mcp_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.mcp_mode and store.get_supervisor_config().enabled:
            scfg = store.get_supervisor_config()
            supervisor = McpRunner.from_executor(
                orchestrator.tool_executor,
                config=scfg,
            )
            history = _session_history(orchestrator, enabled=scfg.use_session_history)
            sup_outcome = supervisor.invoke(message, history=history)
            reply = sup_outcome.reply
            mcp_trace = [s.to_dict() for s in sup_outcome.steps]
            mcp_tools = list(sup_outcome.mcp_tools)
            tools_used = list(sup_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.approval_mode and store.get_approval_config().enabled:
            gcfg = store.get_graph_config()
            acfg = store.get_approval_config()
            workflow = ApprovalWorkflowGraph.from_executor(
                orchestrator.tool_executor,
                graph_config=gcfg,
                approval_config=acfg,
            )
            history = _session_history(orchestrator, enabled=gcfg.use_session_history)
            approval_outcome = workflow.invoke(message, history=history)
            reply = approval_outcome.reply
            graph_trace = [s.to_dict() for s in approval_outcome.steps]
            tools_used = list(approval_outcome.tools_used)
            approval_payload = approval_outcome.approval
            orchestrator.assistant.history.add_user(message)
            if not approval_outcome.interrupted:
                orchestrator.assistant.history.add_assistant(reply)
        elif body.graph_mode and store.get_graph_config().enabled:
            cfg = store.get_graph_config()
            graph = RAGAgentGraph.from_executor(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            graph_outcome = graph.invoke(message, history=history)
            reply = graph_outcome.reply
            graph_trace = [s.to_dict() for s in graph_outcome.steps]
            tools_used = list(graph_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.executor_mode and store.get_executor_config().enabled:
            cfg = store.get_executor_config()
            agent = AgentExecutor.from_executor(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            exec_outcome = agent.invoke(message, history=history)
            reply = exec_outcome.reply
            executor_trace = [s.to_dict() for s in exec_outcome.steps]
            tools_used = list(exec_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.agent_mode and store.get_react_config().enabled:
            cfg = store.get_react_config()
            agent = ReActAgent(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            react_outcome = agent.run(message, history=history)
            reply = react_outcome.reply
            agent_trace = [s.to_dict() for s in react_outcome.steps]
            tools_used = list(react_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        else:
            reply = orchestrator.handle_message(message)
    except ConfigError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc
    except APIError as exc:
        raise _http_from_nexus(exc, status_code=502) from exc
    except NexusError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc

    kind, meta = classify_reply(reply)
    if mcp_trace is not None:
        kind = "mcp"
        meta = "MCP Tool Bridge"
    elif mcp_trace is not None:
        kind = "supervisor"
        meta = "Supervisor Multi-Agent"
    elif approval_payload is not None:
        kind = "approval"
        meta = "Approval Workflow"
    elif graph_trace and kind != "approval":
        kind = "graph"
        meta = "StateGraph"
    elif executor_trace:
        kind = "executor"
        meta = "AgentExecutor"
    elif agent_trace:
        kind = "agent"
        meta = "ReAct Agent"
```


---

## 四十二、fetch_citations 代码

```python
def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )
```


---

## 四十三、前端展示要点

`app.js` 的 `msg__route` 渲染 rank/source/score/preview；`msg__rewrite` 展示改写链。

---

## 四十四、合规场景

理财回答必须带风险提示引用 — citations 第一条应来自风险揭示 chunk。

---

## 四十五、测试与 FR 映射

| 测试 | FR |
|------|-----|
| test_RuleBasedQueryRouter.route_from_results | FR-002 |
| test_fetch_citations_with_hits | FR-003 |
| test_chat_includes_citations | FR-006 |
| test_citation_preview_with_rewrite | FR-005 |

---

## 四十六、完整 context.py 引用段

```python
def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )
```


---

## 四十七、完整测试文件

```python
"""Day 44 MCP Server/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.mcp_bridge import structured_tools_from_mcp
from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST, McpJsonRpcRequest
from agent.mcp_runner import McpRunner
from agent.mcp_server import NexusMcpServer
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return McpRunner.from_executor(orch.tool_executor, config=McpConfig())


def test_mcp_config_validate():
    McpConfig().validate()
    with pytest.raises(ValueError):
        McpConfig(max_tool_calls=0).validate()
    with pytest.raises(ValueError):
        McpConfig(server_name="  ").validate()


def test_mcp_server_list_tools(runner):
    server = runner._server  # noqa: SLF001
    tools = server.list_tools()
    names = {t.name for t in tools}
    assert "faq_lookup" in names
    assert "rag_search" in names


def test_mcp_server_handle_list(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(McpJsonRpcRequest(method=MCP_METHOD_LIST))
    assert resp.ok
    assert len(resp.result["tools"]) >= 3


def test_mcp_server_handle_call_faq(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(
        McpJsonRpcRequest(
            method=MCP_METHOD_CALL,
            params={"name": "faq_lookup", "arguments": {"query": "客服电话"}},
        )
    )
    assert resp.ok
    text = resp.result["content"][0]["text"]
    assert text


def test_mcp_client_list_and_call(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    tools = client.list_tools()
    assert any(t.name == "rag_search" for t in tools)
    obs = client.call_tool("rag_search", {"query": "年化收益"})
    assert obs


def test_mcp_bridge_structured_tools(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    structured = structured_tools_from_mcp(client)
    names = {t.name for t in structured}
    assert "intent_classify" in names
    out = structured[0].run({"query": "测试"})
    assert isinstance(out, str)


def test_mcp_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "faq_lookup" in outcome.mcp_tools
    assert any(s.phase == "call" for s in outcome.steps)


def test_mcp_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_mcp_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_mcp_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_mcp_config(McpConfig(server_name="custom-mcp", max_tool_calls=3))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_mcp_config()
    assert cfg.server_name == "custom-mcp"
    assert cfg.max_tool_calls == 3
```


---

## 四十八、完整 API 测试

```python
"""Day 44 MCP API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_get_mcp_config_default(client):
    data = client.get("/api/agent/mcp-config").json()
    assert data["enabled"] is True
    assert data["server_name"] == "nexus-tools"


def test_put_mcp_config(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_tool_calls"] == 3


def test_mcp_list_tools(client):
    resp = client.post("/api/agent/mcp-list-tools", json={})
    assert resp.status_code == 200
    data = resp.json()
    names = {t["name"] for t in data["tools"]}
    assert "faq_lookup" in names
    assert data["server_name"] == "nexus-tools"


def test_mcp_preview_rag(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "rag_search" in data["mcp_tools"]


def test_mcp_preview_with_history(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_mcp_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["mcp_config"]["enabled"] is True


def test_chat_mcp_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace")
    assert body.get("mcp_tools")
    assert body["kind"] == "mcp"


def test_chat_mcp_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace") is None
    assert body["kind"] == "faq"


def test_invalid_mcp_max_tool_calls_422(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 99,
        },
    )
    assert resp.status_code == 422
```


---

## 四十九、课堂 8 分钟录音稿

「打开 mcp_runner，McpStep 记录 phase 与 mcp_method。chat 里 mcp_trace 挂在 reply 后面。这就是 ZL-NA-REQ-044。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 4 · Day 44 · MCP · ZL-NA-REQ-044 · mcp_runner 精读完**
