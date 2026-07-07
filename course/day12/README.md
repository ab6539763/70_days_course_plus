# Day 12 课件索引

**日期**：2026-07-17（星期五）  
**主题**：网络与 API — 首次 LLM API 调用  
**需求**：ZL-NA-REQ-012  
**Sprint**：Sprint 2 第 5 天

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# HTTP 基础（urllib GET）
python3 src/day12/http_demos.py

# 请求体组装预览
python3 src/day12/api_demos.py

# LLM 客户端（Mock 模式，无需 Key）
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py

# 单元测试
python3 -m pytest tests/day12/ -v
```

## 今日交付物

- [x] `llm/client.py` — `LLMClient`、`build_request_body`、`default_transport`（urllib）
- [x] `llm/env.py` — `load_llm_env`、`NEXUS_LLM_MOCK`、简易 `.env` 解析
- [x] `llm/response.py` — `parse_chat_completion`、`ChatCompletionResult`
- [x] `core/exceptions.py` — `APIError` 扩展字段
- [x] Day 12 演示脚本与单元测试

## 上下文链

```
Day 5  api_response_parser（离线 JSON）→ Day 12 llm/client（真实 HTTP）  ← 今日
Day 11 doc_reader 读文档 → Day 15+ 作为 Prompt 上下文
Day 13 装饰器与重试 → 包装 LLMClient.complete
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | HTTP 与 LLM 客户端详解 | 深度专题 |
| 12-14 | 练习册 / urllib 扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | REST 讲义 / 密钥实践 / Sprint2 回顾 / 精读 / Lab | 进阶实操 |

## 关键设计决策

1. **标准库 urllib**：不引入 `requests`，与课程「先标准库后生态」一致  
2. **OpenAI 兼容格式**：`POST /v1/chat/completions`，DeepSeek 等厂商通用  
3. **Mock 模式**：`NEXUS_LLM_MOCK=1` + 本地 JSON 样本，CI 无需真实 Key  
4. **可注入 transport**：单元测试与离线开发不依赖网络

## Day 13 预告

明日学习**装饰器（decorator）**与**重试（retry）**，将为 `LLMClient.complete` 增加指数退避重试，处理 429/5xx 等瞬时故障。
