"""Per-day diagram and architecture snippets for course/day31–37."""

from __future__ import annotations


def file04(day: int) -> str:
    """Return corrected 04_流程图与示意图.md body for the given day."""
    builders = {
        31: _file04_day31,
        32: _file04_day32,
        33: _file04_day33,
        34: _file04_day34,
        35: _file04_day35,
        36: _file04_day36,
        37: _file04_day37,
        38: _file04_day38,
        39: _file04_day39,
        40: _file04_day40,
        41: _file04_day41,
        42: _file04_day42,
    }
    return builders[day]()


def _file04_day31() -> str:
    return """# Day 31 流程图与示意图

## hybrid search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant H as HybridRetriever
    participant K as KeywordRetriever
    participant V as ChromaEmbeddingRetriever
    U->>H: "search query top_k=3"
    H->>H: "pool = max(12, 8)"
    par 双路召回
        H->>K: "search pool"
        H->>V: "search pool"
    end
    K-->>H: kw_hits
    V-->>H: vec_hits
    H->>H: "rrf or weighted merge"
    H-->>U: top 3 results
```

## weighted 融合数据流

```mermaid
sequenceDiagram
    participant W as weighted_merge
    participant N as normalize_scores
    W->>N: kw_hits
    W->>N: vec_hits
    N-->>W: normalized scores
    W->>W: "combine kw_w and vec_w"
    W->>W: sort desc
```

## ASCII：模式选择

```
query ──► mode?
            ├─ vector  ──► vector.search ──► return
            ├─ keyword ──► keyword.search ──► return
            └─ hybrid  ──► dual pool ──► fuse ──► top_k
```

## API 配置流

```
GET  /retrieval-config  ◄── store.get_retrieval_config()
PUT  /retrieval-config  ──► validate ──► set ──► save()
POST /api/chat          ──► HybridRetriever
```
"""


def _file04_day32() -> str:
    return """# Day 32 流程图与示意图

## rerank search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant R as RerankingRetriever
    participant H as HybridRetriever
    participant C as MockCrossEncoder
    U->>R: "search top_k=3"
    R->>R: "pool = max(20, 3)"
    R->>H: "search pool"
    H-->>R: 20 candidates
    R->>C: "rerank candidates"
    loop each candidate
        C->>C: score_pair
    end
    C-->>R: sorted top 3
    R-->>U: RetrievalResult list
```

## score_pair 数据流

```mermaid
sequenceDiagram
    participant S as score_pair
    S->>S: "check query in text"
    S->>S: token coverage
    S->>S: bigram overlap bonus
    S->>S: length penalty
    S-->>S: clamp 0 to 1
```

## ASCII：两阶段漏斗

```
query ──► HybridRetriever ──► top-20 ──► CrossEncoder ──► top-3 ──► LLM
              (宽召回)                      (精排)
```

## API 配置流

```
GET  /rerank-config  ◄── store.get_rerank_config()
PUT  /rerank-config  ──► validate ──► set ──► save()
POST /api/chat       ──► RerankingRetriever
```
"""


def _file04_day33() -> str:
    return """# Day 33 流程图与示意图

## rewrite search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant W as RewritingRetriever
    participant Q as QueryRewriter
    participant I as InnerRetriever
    U->>W: "search top_k=3"
    W->>Q: "rewrite query"
    Q-->>W: rewritten query
    W->>I: "search rewritten"
    I-->>W: hits
    W-->>U: RetrievalResult list
```

## RuleBasedQueryRewriter 数据流

```mermaid
sequenceDiagram
    participant R as QueryRewriter
    R->>R: "match rule regex"
    R->>R: "apply template"
    R->>R: "fallback original if disabled"
    R-->>R: RewriteResult
```

## ASCII：三阶段漏斗

```
query ──► Rewrite ──► Hybrid+Rerank ──► top-k ──► LLM
           (规范化)      (检索栈)
```

## API 配置流

```
GET  /rewrite-config  ◄── store.get_rewrite_config()
PUT  /rewrite-config  ──► validate ──► set ──► save()
POST /api/chat       ──► RewritingRetriever
```
"""


def _file04_day34() -> str:
    return """# Day 34 流程图与示意图

## citation 检索时序

```mermaid
sequenceDiagram
    participant U as Client
    participant S as KnowledgeStore
    participant R as RetrieverStack
    participant B as CitationBuilder
    U->>S: fetch_citations query
    S->>R: search top_k
    R-->>S: RetrievalResult list
    S->>B: build_citation_bundle
    B-->>S: CitationBundle
    S-->>U: "citations + rewrite meta"
```

## Citation 构建数据流

```mermaid
sequenceDiagram
    participant B as build_citations
    B->>B: "truncate preview"
    B->>B: "attach matched_tokens"
    B->>B: "rank 1..N"
    B-->>B: list Citation
```

## ASCII：引用溯源

```
query ──► retrieve ──► build_citations ──► chat citations[]
                              │
                              └── rewrite audit optional
```

## API 配置流

```
GET  /citation-config   ◄── store.get_citation_config()
PUT  /citation-config   ──► validate ──► set ──► save()
POST /citation-preview  ──► fetch_citations
POST /api/chat          ──► reply + citations[]
```
"""


def _file04_day35() -> str:
    return """# Day 35 流程图与示意图

## expansion search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant E as ExpandingRetriever
    participant X as QueryExpander
    participant I as InnerRetriever
    participant M as ResultMerger
    U->>E: search query
    E->>X: expand query
    X-->>E: queries list
    loop each expanded query
        E->>I: search per query
        I-->>E: partial hits
    end
    E->>M: merge by chunk_id
    M-->>E: deduped hits
    E-->>U: merged top_k
```

## HyDE 扩展数据流

```mermaid
sequenceDiagram
    participant H as HyDEMockExpander
    H->>H: "template or hyde mock"
    H->>H: "cap max_queries"
    H-->>H: ExpansionResult
```

## ASCII：多路召回

```
query ──► expand ──► q1,q2,q3 ──► parallel search ──► merge ──► top-k
```

## API 配置流

```
GET  /expansion-config   ◄── store.get_expansion_config()
PUT  /expansion-config   ──► validate ──► set ──► save()
POST /expansion-preview  ──► expand query
POST /api/chat           ──► expansion audit + citations
```
"""


def _file04_day36() -> str:
    return """# Day 36 流程图与示意图

## route search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant RT as RoutingRetriever
    participant Q as QueryRouter
    participant E as ExpandingRetriever
    participant I as InnerStack
    U->>RT: search query
    RT->>Q: route query
    Q-->>RT: "intent expand rewrite flags"
    RT->>E: "search with overrides"
    E->>I: inner search
    I-->>E: hits
    E-->>RT: hits
    RT-->>U: RetrievalResult list
```

## 意图路由数据流

```mermaid
sequenceDiagram
    participant R as RuleBasedQueryRouter
    R->>R: "match regex rules"
    R->>R: "faq_fast rag_standard rag_wide"
    R-->>R: RouteResult
```

## ASCII：快慢路径

```
query ──► route ──► expand? ──► rewrite? ──► hybrid ──► rerank
          faq_fast     off          off
          rag_wide     on           on
```

## API 配置流

```
GET  /route-config   ◄── store.get_route_config()
PUT  /route-config   ──► validate ──► set ──► save()
POST /route-preview  ──► intent preview
POST /api/chat       ──► route audit + citations
```
"""


def _file04_day37() -> str:
    return """# Day 37 流程图与示意图

## validation 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant C as ChatAPI
    participant O as Orchestrator
    participant S as KnowledgeStore
    participant V as AnswerValidator
    U->>C: chat message
    C->>O: handle_message
    O-->>C: reply
    C->>S: fetch_citations
    S-->>C: citations
    C->>V: validate reply vs citations
    V-->>C: ValidationResult
    C-->>U: "reply + validation meta"
```

## RuleBasedAnswerValidator 数据流

```mermaid
sequenceDiagram
    participant V as AnswerValidator
    V->>V: "token overlap reply vs citations"
    V->>V: "citation coverage score"
    V->>V: "compare min_score"
    V-->>V: passed or refused
```

## ASCII：Self-RAG 后置校验

```
route ──► ... ──► citations ──► LLM ──► validate ──► user
                                      ↑ 今日
```

## API 配置流

```
GET  /validation-config   ◄── store.get_validation_config()
PUT  /validation-config   ──► validate ──► set ──► save()
POST /validation-preview  ──► score query+reply
POST /api/chat            ──► validation audit
```
"""


def _file04_day38() -> str:
    return """# Day 38 流程图与示意图

## validation retry 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant C as ChatAPI
    participant V as AnswerValidator
    participant S as KnowledgeStore
    U->>C: chat message
    C->>V: validate reply
    alt failed and retry_on_fail
        V-->>C: not passed
        C->>S: fetch_citations_retry rag_wide
        S-->>C: wider citations
        C->>V: re-validate
    end
    C-->>U: reply + validation.retries
```

## ASCII：重试决策

```
validate ──► passed? ──yes──► return
              │
              no + retry_on_fail
              ▼
         fetch_citations_retry
              ▼
         re-validate ──► refuse_on_fail?
```

## API 配置流

```
PUT  /validation-config      retry_on_fail max_retries
POST /validation-retry-preview  模拟重试
POST /api/chat               validation.retries retry_route
```
"""


def _file04_day39() -> str:
    return """# Day 39 流程图与示意图

## ReAct 时序

```mermaid
sequenceDiagram
    participant U as User
    participant A as ReActAgent
    participant T as ToolExecutor
    participant KB as KnowledgeStore
    U->>A: query
    A->>A: Thought
    A->>T: Action rag_search
    T->>KB: retrieve
    KB-->>T: Observation
    T-->>A: tool result
    A->>A: Final Answer
    A-->>U: reply + agent_trace
```

## API

```
GET/PUT /api/agent/react-config
POST    /api/agent/react-preview
POST    /api/chat  agent_mode=true
```
"""


def _file04_day40() -> str:
    return """# Day 40 流程图与示意图

## AgentExecutor 时序

```mermaid
sequenceDiagram
    participant U as User
    participant E as AgentExecutor
    participant S as StructuredTool
    participant KB as KnowledgeStore
    U->>E: query
    E->>E: plan tool
    E->>S: run rag_search
    S->>KB: retrieve
    KB-->>S: Observation
    S-->>E: tool result
    E->>E: Final Answer
    E-->>U: reply + executor_trace
```

## API

```
GET/PUT /api/agent/executor-config
POST    /api/agent/executor-preview
POST    /api/chat  executor_mode=true
```
"""


def _file04_day41() -> str:
    return """# Day 41 流程图与示意图

## StateGraph 时序

```mermaid
sequenceDiagram
    participant U as User
    participant G as RAGAgentGraph
    participant P as planner
    participant T as tool_runner
    participant A as answer
    U->>G: query
    G->>P: plan tool
    P->>T: run StructuredTool
    T-->>P: observation
    P->>A: finalize
    A-->>U: reply + graph_trace
```

## API

```
GET/PUT /api/agent/graph-config
POST    /api/agent/graph-preview
POST    /api/chat  graph_mode=true
```
"""


def _file04_day42() -> str:
    return """# Day 42 流程图与示意图

## 人工审批时序

```mermaid
sequenceDiagram
    participant U as User
    participant W as ApprovalWorkflow
    participant T as tool_runner
    participant H as human_approval
    participant R as Reviewer
    U->>W: query
    W->>T: rag_search
    T->>H: 需审批
    H-->>U: interrupted + checkpoint_id
    R->>W: approval-resume approved
    W-->>U: reply + approval
```

## API

```
GET/PUT /api/agent/approval-config
POST    /api/agent/approval-preview
POST    /api/agent/approval-resume
POST    /api/chat  approval_mode=true
```
"""
