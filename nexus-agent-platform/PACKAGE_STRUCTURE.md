# NexusAgent 包结构说明

**版本**：v0.13.0（Day 13 retry）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-013

## 生产层目录（长期演进）

```
src/
├── core/           # 异常、路径、引导 — 全平台基础设施
├── models/         # 领域模型（ChatMessage, Contact, ModelConfig）
├── services/       # 业务服务（MessageHistoryService）
├── utils/          # 横切工具函数
├── llm/            # 大模型接入（client, retry, resilient_client）
├── chat/           # 对话应用（Day 14+）
├── tools/          # 文档/工具（Day 11 doc_reader）
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
