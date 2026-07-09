# Day 23 深度扩展：FastAPI 与 REST 设计

**读者**：有余力的学员与内部晋升候选  
**需求**：ZL-NA-REQ-023

---

## 1. REST 成熟度与 NexusAgent

Richardson 成熟度模型：

| 级别 | 特征 | Day 23 位置 |
|------|------|-------------|
| 0 | 单一 URI POST | — |
| 1 | 资源 URI | `/api/chat` 单资源 |
| 2 | HTTP 动词 | GET health, POST chat |
| 3 | HATEOAS | 未实现 |

智链科技 Day 23 停在 **Level 2**：够用、可测、可文档化。HATEOAS 与版本化 `/v1/` 留 Sprint 5。

---

## 2. OpenAPI 即契约

FastAPI 自动生成 `/openapi.json`。周航建议：

- CI 对比 schema diff  
- 前端用 openapi-typescript 生成类型（选修）  

林晓在 `/docs` 点击「Try it out」发送 FAQ 问句，即完成零代码集成测试。

---

## 3. 同步 vs 异步路由

当前：

```python
def chat(...) -> ChatResponse:  # 同步
```

`handle_message` 为同步。若改为 `async def` 而无 await，反而误导。真正异步化需：

- `async` LLM client  
- `await` 流式 chunk  

Day 16 流式将在 Sprint 4 以 SSE 暴露。

---

## 4. 依赖注入进阶

可抽象接口：

```python
def get_orchestrator_factory() -> Callable[[], ChatOrchestrator]:
    return create_orchestrator
```

测试时替换为轻量 fake orchestrator，加速单元测试。当前教学用真实 `create_orchestrator` + Mock LLM 已足够快。

---

## 5. API 版本策略

| 策略 | 示例 | 适用 |
|------|------|------|
| URL 路径 | `/api/v1/chat` | 公开 API |
| Header | `Accept-Version: 1` | 内部 |
| 无版本 | `/api/chat` | Day 23 教学 |

赵岩倾向内测期无版本，避免前端频繁改路径。

---

## 6. 幂等性与重试

`POST /api/chat` **非幂等**：每次调用可能追加 history。客户端重试须谨慎。生产可引入：

- `Idempotency-Key` header  
- 客户端 message UUID  

Day 23 不实现，写入技术债 backlog。

---

## 7. 可观测性

扩展点：

- 中间件记录 `request_id`  
- Prometheus metrics：`chat_requests_total{kind}`  
- 结构化日志 JSON  

周航 Sprint 4 将接 OpenTelemetry。

---

## 8. 安全纵深

| 层 | Day 23 | 生产 |
|----|--------|------|
| 传输 | HTTP 教学 | HTTPS |
| 认证 | 无 | API Key / JWT |
| 授权 | 无 | RBAC |
| 输入 | Pydantic | + WAF |
| 限流 | 无 | token bucket |

---

## 9. 与 gRPC 对比

陈默架构备忘：内部微服务间可用 gRPC；**浏览器只认 HTTP**。Chat API 保持 REST JSON。

---

## 10. 阅读清单

1. FastAPI Tutorial — User Guide  
2. Pydantic V2 Migration  
3. RFC 9110 HTTP 语义（选修）  

扩展阅读完。

---

## 11. REST 与金融行业 API 治理（智链科技内参节选）

### 11.1 幂等与资金类 API 的对比

聊天 API 虽非资金划转，但监管科技对话中常并列讨论。智链科技支付网关要求 POST 带幂等键；`POST /api/chat` 教学版无此要求，但须在架构文档标明「非金融交易接口」，避免合规误分类。

### 11.2 审计日志字段草案

建议字段：timestamp、session_id_hash、message_len、kind、latency_ms、mock_llm。禁止落盘完整用户消息于未审批环境。林晓作业 F 可引用此草案。

### 11.3 国际化与 REST

未来英文界面时，`classify_reply` 前缀可能变为 `[FAQ Direct]`。版本化策略：Accept-Language 头或 reply 内嵌 locale 标记。Day 30 技术债已登记。

### 11.4 API 网关层预告

Sprint 5 可能在 Kong/nginx 加 rate limit、WAF。FastAPI 层保持薄，安全策略外置。陈默主张「边缘防护 + 应用校验」双轨。

### 11.5 学习成果自评 Rubric

| 等级 | 标准 |
|------|------|
| 入门 | 能 curl /api/chat |
| 合格 | 能解释 422/502 |
| 良好 | 能画 ASGI 栈 |
| 优秀 | 能评述 SessionManager 生产替代方案 |

内参节选完。

---

## 12. 智链科技 REST 成熟度工作坊（文字版）

### 12.1 工作坊目标

让学员在六十分钟内为虚构「转账 API」与「聊天 API」对比 REST 成熟度，从而感激 Day 23 chat 设计已具备 Level 2。

### 12.2 聊天 API 自检表

- 是否用名词路径？`/api/chat` 是动作化名词，内训容忍。  
- 是否用正确动词？POST 非 GET，避免缓存泄露 message。  
- 是否有状态码语义？422/500/502 已具备。  
- 是否有 schema？Pydantic 是。  
- 是否 idempotent？否，有意为之。  

### 12.3 与 GraphQL 对比口播

GraphQL 灵活但复杂；REST 够用于 MVP。NexusAgent 选 REST 降低全栈班认知负荷。

### 12.4 HATEOAS 幻想练习

「若响应含 links.next，会怎样？」——课堂笑谈，无人真想实现。

### 12.5 成熟度打分

学员自评 Day 23 API 成熟度：平均 2.3 级（Level 2 偏上）。陈默满意。

工作坊文字版完，2026-07-28。
