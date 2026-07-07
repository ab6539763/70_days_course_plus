# Day 23 config.js 与 chat 路由精读

**需求**：ZL-NA-REQ-023  
**对标**：Day 22 `25_mock.js精读.md`

---

## 1. config.js 全文逻辑

```javascript
(function (global) {
  "use strict";
  const params = new URLSearchParams(global.location.search);
  global.NexusConfig = {
    useMock: params.get("mock") === "1",
    apiBase: "",
  };
})(window);
```

### 1.1 IIFE

避免污染全局，仅导出 `NexusConfig`。

### 1.2 useMock 真值

| URL | useMock |
|-----|---------|
| `/` | false |
| `/?mock=1` | true |

**设计意图**：FastAPI 托管默认 API；纯静态教学用 `?mock=1` 回退。

### 1.3 apiBase

空字符串 → `fetch(\`${base}/api/chat\`)` 即 `/api/chat` 相对当前 origin。将来分离部署设为 `https://api.example.com`。

---

## 2. mock.js 与 config 联动

```javascript
global.NexusMock = {
  sendMessage,
  sendMessageApi,
  useMock: !(global.NexusConfig && global.NexusConfig.useMock === false),
};
```

**真值表**：

| NexusConfig | useMock (NexusMock) | 调用 |
|-------------|---------------------|------|
| 未定义 | true | sendMessage |
| useMock: false | false | sendMessageApi |
| useMock: true (?mock=1) | true | sendMessage |

林晓：「config 是开关，mock 是执行者。」

---

## 3. sendMessageApi 精读

```javascript
async function sendMessageApi(text) {
  const base = (window.NexusConfig && window.NexusConfig.apiBase) || "";
  const res = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  if (!res.ok) {
    throw new Error(`API 错误: ${res.status}`);
  }
  const data = await res.json();
  return {
    reply: data.reply || "",
    meta: data.meta || "API",
    kind: data.kind || "api",
  };
}
```

**要点**：

- 仅传 `message`，未传 `session_id`（Day 24 扩展）  
- 非 ok 抛错，app.js catch 渲染  
- 默认值兜底空字段  

---

## 4. chat.py 路由精读

```python
router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, manager: SessionManager = Depends(get_session_manager)) -> ChatResponse:
```

### 4.1 prefix

完整路径 `/api` + `/chat` = `/api/chat`，与 mock fetch 一致。

### 4.2 response_model

过滤未声明字段；生成 OpenAPI schema 供 `/docs`。

### 4.3 同步 def

匹配同步 `handle_message`；uvicorn 在线程池运行，不阻塞事件循环过久（教学负载可接受）。

---

## 5. 两端对照表

| 步骤 | 前端 | 后端 |
|------|------|------|
| 校验 | trim（mock） | Pydantic + strip |
| 业务 | — | handle_message |
| 分类 | parseReply（降级） | classify_reply |
| 会话 | 未传 | get_or_create |

---

## 6. 调试练习

1. 在 sendMessageApi 内 `console.log(data)`  
2. 对比 Swagger 同 body 响应  
3. 故意传 `?mock=1` 看差异  

精读完。

---

## 7. 逐行注释：sendMessageApi 错误路径

当 `res.ok` 为 false，抛出 `Error(\`API 错误: ${res.status}\`)`。app.js catch 渲染为 bot 气泡。Day 24 将映射：502→服务繁忙，500→配置异常，422→输入无效（通常前端已拦）。林晓建议在 sendMessageApi 内读 `res.json().detail`，作业 E 可扩展。

## 8. 逐行注释：chat 依赖注入

`Depends(get_session_manager)` 在 FastAPI 中每请求调用 get_session_manager，返回同一 session_manager 单例。orchestrator 实例按 sid 懒创建。第一次 POST 创建 default orchestrator，进程重启后丢失——教学 MVP 可接受。

## 9. 与 Day 22 mock.js useMock 逻辑对比

Day 22：`useMock: true` 硬编码在 NexusMock 对象。Day 23：由 config 驱动，表达式 `!(NexusConfig && NexusConfig.useMock === false)` 实现「仅显式 false 走 API」。这是更安全的默认：无 config 时仍 Mock，避免纯静态打开 8080 时 fetch 报错刷屏。

## 10. 精读测验（自测）

不看代码回答：sendMessageApi 的 Content-Type？chat router 的 prefix？config 的 apiBase 默认值？三题全对方可进入 Day 24 Lab。

精读扩展完。智链科技培训部。
