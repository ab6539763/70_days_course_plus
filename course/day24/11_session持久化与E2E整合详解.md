# Day 24 专题

**需求**：ZL-NA-REQ-024  
**主题**：Sprint 3 收官整合

---

## 1. localStorage 语义

`Storage` API 在同源策略下按域名隔离。智链演示环境使用 `http://127.0.0.1:8000`，与 FastAPI 静态托管同源，`fetch('/api/chat')` 与 `localStorage` 共享源。

`getSessionId()` 逻辑：

```javascript
let id = localStorage.getItem(STORAGE_KEY);
if (!id) {
  id = generateId();
  localStorage.setItem(STORAGE_KEY, id);
}
return id;
```

`generateId()` 优先 `crypto.randomUUID()`，兼容旧浏览器时降级为 `sess-{timestamp}-{random}`。

## 2. 服务端 SessionManager

Day 23 引入的 `SessionManager` 使用 `threading.Lock` 保护 dict。`clear(session_id)` 在 Day 24 被 reset 路由调用：

```python
cleared = manager.clear(body.session_id)
return SessionResetResponse(session_id=body.session_id, cleared=cleared)
```

`cleared=False` 表示该 sid 从未创建过 orchestrator，仍返回 200（幂等）。

## 3. mock.js 联调

`sendMessageApi` 构造 body：

```javascript
const body = {
  message: text,
  session_id: NexusSession.getSessionId(),
};
```

错误分支调用 `NexusErrors.mapApiError(res.status, payload)`。

## 4. E2E 设计哲学

`e2e_smoke.py` 不用 Selenium 的原因：课堂 CI 要求稳定、无头、快速。`TestClient` 足够验证 HTTP 契约与静态资源可访问性。真正的浏览器 E2E 留作作业 C 级扩展。

## 概述

双端 session 深度讲义，含 localStorage 与线程安全。

本讲义属于 NexusAgent 七十天培训 Day 24 标准课件。学员应结合仓库代码阅读，并在 `nexus-agent-platform` 目录完成实操。

---

## 核心知识点

### 1. 整合思维

Sprint 3 最后一天不追求新算法，而是把 Day 15–23 的能力串成 **可演示、可测试、可交付** 的产品切片。赵岩在晨会强调：投资人关心的是「端到端」，不是「模块清单」。

### 2. session 双端模型

| 端 | 存储 | 生命周期 |
|----|------|----------|
| 浏览器 | localStorage `nexus_session_id` | 用户清除站点数据前持久 |
| 服务端 | SessionManager 内存 dict | 进程内；reset 或重启清除 |

前端每次 `POST /api/chat` 必须携带 `session_id`。服务端据此 `get_or_create` 独立 `ChatOrchestrator`，避免用户 A 与用户 B 串话。

### 3. 新对话正确顺序

1. 读取当前 `oldSid = NexusSession.getSessionId()`  
2. `POST /api/session/reset` 传 `oldSid`（API 模式）  
3. `NexusSession.resetSession()` 生成新 ID 写 localStorage  
4. 清空 `#messages` 并插入欢迎 bot 消息  

若跳过步骤 2，服务端仍保留旧 orchestrator 实例（直到被 GC 或 map 清除），在边界情况下可能造成上下文泄漏。

### 4. 错误文案契约

`errors.js` 将 HTTP 状态映射为中文产品句：

```javascript
422 → 输入无效，请检查消息后重试。
502 → 大模型服务繁忙，请稍后重试。
500 → 服务配置异常，请联系管理员。
```

与 Day 23 `chat.py` 中 `APIError→502`、`ConfigError→500` 对齐。演示时故意触发错误，是整合验收的一部分。

### 5. 发布门禁 sprint3_launch

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py
```

内部顺序：subprocess pytest `tests/day22|23|24` → `e2e_smoke.run_smoke()` → 打印访问 URL → 可选 `--serve`。

周航解释：「这不是多余步骤。是告诉学员，**能启动 ≠ 能交付**。」

### 6. E2E 冒烟三问句

`DEMO_QUERIES` 覆盖 FAQ、总结、RAG 三类意图，确保 `kind` 集合多样。冒烟用 `TestClient`，不依赖真实浏览器，适合 CI。

### 7. 投资人五分钟流程

| 分钟 | 动作 |
|------|------|
| 0–1 | 展示 health、`mock_llm`、session 标签 |
| 1–2 | FAQ 问句 |
| 2–3 | 总结要点 |
| 3–4 | RAG 收益问句 |
| 4–5 | 新对话 + Q&A |

### 8. 与 Phase 3 衔接

Day 25 将在现有聊天壳子上挂载 **知识库 ingestion** 与向量持久化。今日整合的 API 与 session 模型将继续复用，无需推倒重来。

---

## 实操检查

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/e2e_smoke.py
python3 -m pytest tests/day24/ -v
```

预期：冒烟打印 ✅ 行；pytest 12 passed。

---

## 思考题

1. 为何 `session.js` 使用 IIFE 挂载 `window.NexusSession`？  
2. Mock 模式下新对话为何可跳过 reset API？  
3. 若把 `SessionManager` 换成 Redis，前端契约要不要变？  

---

## 延伸阅读

- [03_架构设计.md](03_架构设计.md)  
- [22_session与errors.js精读.md](22_session与errors.js精读.md)  
- [27_Day25_RAG知识库预习.md](27_Day25_RAG知识库预习.md)
