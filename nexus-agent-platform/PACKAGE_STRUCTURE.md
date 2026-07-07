# NexusAgent 包结构说明

**版本**：v0.23.0（Day 23 api）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-023

## 仓库根目录（Day 22+）

```
frontend/           # 静态聊天页（HTML/CSS/JS，Day 22+）
  index.html
  config.js         # Day 23 API/Mock 切换
  ...
```

## 生产层目录（长期演进）

```
src/
├── api/            # FastAPI HTTP 层（Day 23+）
│   ├── app.py      # 应用入口、CORS、静态托管
│   ├── chat.py     # POST /api/chat
│   ├── schemas.py  # Pydantic 模型
│   └── sessions.py # 会话管理
├── core/           # 异常、路径、引导 — 全平台基础设施
├── models/         # 领域模型（ChatMessage, Contact, ModelConfig）
├── services/       # 业务服务（MessageHistoryService）
├── utils/          # 横切工具函数
├── llm/            # 大模型接入（client, retry, token_counter, streaming）
├── prompts/        # Prompt 模板库 + 意图路由（Day 17+）
│   ├── base.py     # PromptTemplate
│   ├── library.py  # 内置模板
│   ├── registry.py # 注册表
│   └── intent.py   # RuleBasedIntentClassifier, IntentRouter（Day 18）
├── rag/            # RAG 检索（Day 19+）
│   ├── chunker.py  # 文档分块
│   ├── retriever.py # 关键词检索
│   ├── embedding.py # TF-IDF Embedding（Day 20）
│   ├── embedding_retriever.py # 向量检索
│   ├── vector.py   # 余弦相似度
│   └── context.py  # RAGContextService
├── services/       # 业务服务
│   ├── message_history.py
│   └── faq_matcher.py # 相似问题匹配（Day 20）
├── chat/           # 对话应用（Day 14 cli_assistant, Day 21 orchestrator）
│   ├── cli_assistant.py
│   └── orchestrator.py  # ChatOrchestrator（Day 21）
├── tools/          # 文档/工具（Day 11 doc_reader, Day 21 tool_registry）
│   ├── doc_reader.py
│   ├── tool_registry.py
│   └── executor.py
└── day01..dayXX/   # 教学实验代码（保留，不删）
```

## 依赖方向

```
dayXX  →  services  →  models  →  core
              ↓           ↓
            utils  ←──────┘
llm/chat/tools  →  models, core, utils
```

**禁止**：`core` / `models` import `dayXX` 或 `services` 反向依赖 `dayXX`。

## 数据路径

统一在 `core/paths.py` 的 `PATHS` 字典注册，逐步替代各 day 内 constants。

## 异常映射（预告 Day 23）

| 异常 | HTTP |
|------|------|
| ModelValidationError | 400 |
| ConfigError | 500 |
| StorageError | 500 |
| JsonParseError | 400 |
