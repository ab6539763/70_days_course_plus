# Day 16 课件索引

**日期**：2026-07-21（星期二）  
**主题**：API 参数详解 — 流式输出模块（SSE）  
**需求**：ZL-NA-REQ-016  
**里程碑**：Phase 2 / Sprint 3 第二日（Day 15–24）

## Sprint 3 进度

昨日完成 Token 计量，今日从「等整段回复」迈向「边生成边看见」：

- Day 15 Token 计数 → **Day 16 流式输出（`stream=True` + SSE）**
- Day 17 Prompt 模板与系统提示词工程
- Day 18–24 检索、工具调用、Agent 编排……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# SSE 行解析演示
python3 src/day16/sse_parse_demos.py

# Mock 流式打字机效果
NEXUS_LLM_MOCK=1 python3 src/day16/streaming_demo.py

# asyncio 消费预习
python3 src/day16/async_stream_demos.py

# 单元测试
python3 -m pytest tests/day16/ -v
```

## 今日交付物

- [x] `llm/streaming.py` — `StreamingLLMClient`、`parse_sse_line`、`StreamAccumulator`、`stream_complete`、`on_delta`
- [x] `llm/sample_data/stream_mock.sse` — Mock SSE 样本
- [x] `build_stream_request_body` — `stream=True` 请求体
- [x] `src/day16/*` 演示脚本
- [x] `tests/day16/test_streaming.py`
- [x] Day 16 全套课件（29 篇）

## 上下文链

```
Day 5 parse_stream_chunk / parse_chat_completion → chunk 与 usage 字段
Day 12 urllib 阻塞 complete → Day 16 逐行 SSE 读取
Day 15 TokenUsage → 流式最后一 chunk 汇总 usage
Day 16 流式输出 → Day 17 Prompt 模板
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | 流式输出详解 | 深度专题 |
| 12-14 | 练习册 / SSE 异步扩展 / 流式体验案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day12 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | SSE 协议讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **标准库优先**：`urllib.request.urlopen` + `for raw_line in resp` 逐行读 SSE，与 Day 12 阻塞 `read()` 形成对照  
2. **协议兼容**：OpenAI `chat.completion.chunk` + `data: [DONE]` 终止信号  
3. **回调分离**：`on_delta` 负责 UI 打字机；`StreamAccumulator` 负责完整文本汇总  
4. **Transport 可注入**：`default_stream_transport` / `mock_stream_from_sse_file` 便于单测与离线演示  
5. **Usage 时机**：与 Day 15 一致，仅在**最后一个含 `usage` 的 chunk** 读取 token 统计

## Day 17 预告

明日引入 **Prompt 模板**：`system` 角色、变量插值、多场景提示词版本管理，为 RAG 与工具调用铺垫结构化输入。
