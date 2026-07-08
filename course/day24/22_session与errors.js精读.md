# session.js 与 errors.js 精读

**需求**：ZL-NA-REQ-024  
**版本**：0.24.0

本文对 `frontend/session.js` 与 `frontend/errors.js` 进行**逐行**解读。请对照仓库源码阅读。

---

## 第一部分：session.js

### 源文件 `frontend/session.js`

**L1** `/**`
  → 文件头注释：标明 Day 24 职责与需求编号，便于 frontend_audit 检索。

**L2** ` * NexusAgent Day 24 — 浏览器会话 ID 持久化`
  → 空行分隔注释与实现，符合团队 JS 风格指南。

**L3** ` *`
  → 说明 localStorage 用途：刷新不丢 session_id，避免多用户串话。

**L4** ` * 使用 localStorage 保存 session_id，供 POST /api/chat 携带，避免刷新后串话。`
  → 再次强调需求编号，与 Python 模块 docstring 对齐。

**L5** ` *`
  → 空行。

**L6** ` * 需求：ZL-NA-REQ-024`
  → 需求追溯行。

**L7** ` */`
  → 结束块注释。

**L8** `(function (global) {`
  → IIFE 包裹，避免全局污染；参数 `global` 在浏览器即 `window`。

**L9** `  "use strict";`
  → `use strict` 启用严格模式，禁止隐式全局变量。

**L10** ``
  → 空行。

**L11** `  const STORAGE_KEY = "nexus_session_id";`
  → 常量：localStorage 键名，全小写+下划线，与后端无耦合。

**L12** ``
  → 空行。

**L13** `  function generateId() {`
  → 内部函数：生成新 session_id，不直接导出。

**L14** `    if (global.crypto && crypto.randomUUID) {`
  → 优先 Web Crypto API 的 randomUUID，密码学安全、格式标准。

**L15** `      return crypto.randomUUID();`
  → 返回 UUID 字符串。

**L16** `    }`
  → 闭合 if 分支。

**L17** `    return "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);`
  → 降级路径：旧浏览器无 crypto.randomUUID 时使用时间戳+随机串。

**L18** `  }`
  → 闭合 generateId。

**L19** ``
  → 空行。

**L20** `  function getSessionId() {`
  → 对外语义：获取当前会话 ID，懒创建。

**L21** `    let id = localStorage.getItem(STORAGE_KEY);`
  → 尝试从 localStorage 读取已有 ID。

**L22** `    if (!id) {`
  → 若不存在则进入创建分支。

**L23** `      id = generateId();`
  → 调用 generateId 生成新 ID。

**L24** `      localStorage.setItem(STORAGE_KEY, id);`
  → 持久化到 localStorage，同源策略下仅本站点可读。

**L25** `    }`
  → 闭合 if。

**L26** `    return id;`
  → 返回有效 ID（已有或新建）。

**L27** `  }`
  → 闭合 getSessionId。

**L28** ``
  → 空行。

**L29** `  function resetSession() {`
  → 新对话：强制轮换 ID，与 app.js 新对话按钮联动。

**L30** `    const id = generateId();`
  → 总是生成全新 ID，不复用旧值。

**L31** `    localStorage.setItem(STORAGE_KEY, id);`
  → 覆盖写入 localStorage。

**L32** `    return id;`
  → 返回新 ID，供调用方可选使用。

**L33** `  }`
  → 闭合 resetSession。

**L34** ``
  → 空行。

**L35** `  function shortId(id) {`
  → UI 辅助：长 UUID 截断显示，保护隐私又便于辨认。

**L36** `    if (!id || id.length <= 12) return id || "";`
  → 空 ID 安全返回空串。

**L37** `    return id.slice(0, 8) + "…";`
  → 短 ID 原样显示。

**L38** `  }`
  → 长 ID 取前 8 位 + 省略号，对应 index.html #session-label。

**L39** ``
  → 闭合 shortId。

**L40** `  global.NexusSession = {`
  → 空行。

**L41** `    getSessionId,`
  → 公开 API 对象，挂载到 global（window）。

**L42** `    resetSession,`
  → 导出 getSessionId。

**L43** `    shortId,`
  → 导出 resetSession。

**L44** `    STORAGE_KEY,`
  → 导出 shortId。

**L45** `  };`
  → 导出 STORAGE_KEY 供测试或调试读取。

**L46** `})(window);`
  → 闭合 NexusSession 对象字面量。


### session.js 设计小结

| 主题 | 要点 |
|------|------|
| 模式 | IIFE 避免全局泄漏 |
| 持久化 | localStorage 单 key |
| 随机性 | UUID 优先，降级可接受 |
| UI | shortId 隐私与可读平衡 |

---

## 第二部分：errors.js

### 源文件 `frontend/errors.js`

**L1** `/**`
  → 模块说明：Day 24 专职 HTTP 错误 → 用户可读中文。

**L2** ` * NexusAgent Day 24 — API 错误文案映射`
  → 空行。

**L3** ` */`
  → 需求隐含：与 chat.py 状态码契约一致。

**L4** `(function (global) {`
  → IIFE 开始。

**L5** `  "use strict";`
  → 严格模式。

**L6** ``
  → 空行。

**L7** `  function mapApiError(status, payload) {`
  → 核心映射函数：status + JSON body → 展示字符串。

**L8** `    const detail =`
  → 从 payload 提取 detail 或 message，兼容 FastAPI 与自定义格式。

**L9** `      (payload && (payload.detail || payload.message)) ||`
  → payload.detail 常见于 HTTPException。

**L10** `      (typeof payload === "string" ? payload : "");`
  → 若 payload 本身是字符串则直接使用。

**L11** ``
  → 空行。

**L12** `    if (status === 422) {`
  → 422：Pydantic 校验失败，统一产品句，不暴露字段名给终端用户。

**L13** `      return "输入无效，请检查消息后重试。";`
  → 返回固定文案。

**L14** `    }`
  → 闭合 422 分支。

**L15** `    if (status === 502) {`
  → 502：对应 APIError / 上游 LLM 失败。

**L16** `      return "大模型服务繁忙，请稍后重试。";`
  → 友好提示「繁忙」而非技术术语。

**L17** `    }`
  → 闭合 502。

**L18** `    if (status === 500) {`
  → 500：ConfigError 或未分类 NexusError。

**L19** `      return detail ? `服务异常：${detail}` : "服务配置异常，请联系管理员。";`
  → 有 detail 时适度透传，便于管理员排障。

**L20** `    }`
  → 无 detail 时通用配置异常句。

**L21** `    if (status === 404) {`
  → 闭合 500。

**L22** `      return "接口不存在，请确认 API 服务已启动。";`
  → 404：常见于 API 未启动或路径错误。

**L23** `    }`
  → 引导用户确认服务状态。

**L24** `    return detail ? `请求失败（${status}）：${detail}` : `请求失败（${status}）`;`
  → 闭合 404。

**L25** `  }`
  → 兜底：其他状态码，尽量带 detail。

**L26** ``
  → 闭合 mapApiError。

**L27** `  async function parseErrorResponse(res) {`
  → 空行。

**L28** `    try {`
  → 异步解析错误响应体，避免重复 JSON 解析逻辑。

**L29** `      return await res.json();`
  → 标准 json() 解析。

**L30** `    } catch (_e) {`
  → 非 JSON 响应（如 nginx HTML）降级为 statusText。

**L31** `      return { detail: res.statusText };`
  → 忽略解析异常，保证 mapApiError 总能被调用。

**L32** `    }`
  → 返回最小 payload 对象。

**L33** `  }`
  → 闭合 parseErrorResponse。

**L34** ``
  → 空行。

**L35** `  global.NexusErrors = {`
  → 导出 NexusErrors 命名空间。

**L36** `    mapApiError,`
  → 导出 mapApiError。

**L37** `    parseErrorResponse,`
  → 导出 parseErrorResponse 供 mock.js 使用。

**L38** `  };`
  → 闭合对象。

**L39** `})(window);`
  → IIFE 结束。


### errors.js 设计小结

| status | 策略 |
|--------|------|
| 422/502/500/404 | 固定或半固定产品句 |
| 其他 | 透传 detail |
| 解析 | parseErrorResponse 容错 JSON |

---

## 第三部分：与 app.js / mock.js 衔接

新对话（app.js L158-184）：先 reset API，再 resetSession。

sendMessageApi（mock.js L100-131）：失败时走 NexusErrors。

---

## 第四部分：思考题

1. 若将 STORAGE_KEY 改为带版本前缀，如何实现迁移？  
2. mapApiError 是否应国际化？  
3. TestClient 冒烟为何仍 GET session.js 而不是测 localStorage？  

精读完。

---

## 第五部分：app.js 新对话相关行（精读）

**L132-135** `updateSessionLabel` — 读 NexusSession.shortId 更新 #session-label。  
**L158-184** `newChatBtn` 监听器 — 整合日核心：reset API → resetSession → 清空 DOM → 欢迎语。  
**L163-172** API 模式才 fetch reset；Mock 跳过。  
**L170-171** catch 空块：服务端失败不阻塞 UI 换 ID。  

## 第六部分：mock.js sendMessageApi 错误路径

**L113-122** 非 ok 时 parseErrorResponse + mapApiError + throw。保证 app.js catch 收到用户可读 message。

精讲扩展完。

---

## 第七部分：app.js 新对话逐行

**app.js L130** `  async function handleSubmit(event) {`

**app.js L131** `    event.preventDefault();`

**app.js L132** `    const text = inputEl.value.trim();`
  → updateSessionLabel 定义开始

**app.js L133** `    if (!text) return;`
  → 守卫：无 sessionLabel 或无 NexusSession 则返回

**app.js L134** ``
  → shortId 显示到 #session-label

**app.js L135** `    appendMessage("user", text);`

**app.js L136** `    inputEl.value = "";`

**app.js L137** `    setLoading(true);`

**app.js L138** ``

**app.js L139** `    try {`

**app.js L140** `      const result = await dispatchMessage(text);`

**app.js L141** `      let parsed;`

**app.js L142** `      if (result.kind && result.kind !== "api" && result.kind !== "mock") {`

**app.js L143** `        parsed =`

**app.js L144** `          result.kind === "faq"`

**app.js L145** `            ? { kind: "faq", text: result.reply }`

**app.js L146** `            : result.kind === "route"`

**app.js L147** `              ? parseReply(result.reply)`

**app.js L148** `              : { kind: "bot", text: result.reply };`

**app.js L149** `      } else {`

**app.js L150** `        parsed = parseReply(result.reply);`

**app.js L151** `      }`

**app.js L152** `      appendMessage("bot", parsed, result.meta, {`

**app.js L153** `        citations: result.citations,`

**app.js L154** `        rewrite: result.rewrite,`

**app.js L155** `        expansion: result.expansion,`

**app.js L156** `      });`

**app.js L157** `    } catch (err) {`

**app.js L158** `      appendMessage("bot", `错误：${err.message}`, "请求失败");`
  → newChatBtn 存在才绑定

**app.js L159** `    } finally {`
  → click 异步处理器开始

**app.js L160** `      setLoading(false);`
  → 确认 NexusSession 可用

**app.js L161** `      inputEl.focus();`
  → 保存 oldSid 供 reset API

**app.js L162** `    }`
  → 取 apiBase，默认同源空串

**app.js L163** `  }`
  → 非 Mock 才调服务端 reset

**app.js L164** ``
  → try 开始

**app.js L165** `  formEl.addEventListener("submit", handleSubmit);`
  → POST reset 端点

**app.js L166** ``
  → method POST

**app.js L167** `  function updateSessionLabel() {`
  → Content-Type json

**app.js L168** `    if (!sessionLabel || !window.NexusSession) return;`
  → body 含 old session_id

**app.js L169** `    sessionLabel.textContent = NexusSession.shortId(NexusSession.getSessionId());`
  → 闭合 fetch 选项

**app.js L170** `  }`
  → catch 空：失败不阻塞 UI

**app.js L171** ``
  → 注释说明不阻塞

**app.js L172** `  async function checkHealth() {`
  → 闭合 catch

**app.js L173** `    if (!badgeEl || (window.NexusConfig && window.NexusConfig.useMock)) return;`
  → 闭合 if 非 Mock

**app.js L174** `    try {`
  → 客户端 resetSession 新 UUID

**app.js L175** `      const base = (window.NexusConfig && window.NexusConfig.apiBase) || "";`
  → 更新标签

**app.js L176** `      const res = await fetch(`${base}/api/health`);`
  → 闭合 if NexusSession

**app.js L177** `      if (res.ok) {`
  → 清空消息 DOM

**app.js L178** `        badgeEl.textContent = "API 在线";`
  → appendMessage 欢迎 bot

**app.js L179** `        badgeEl.style.background = "#d1fae5";`
  → role bot

**app.js L180** `        badgeEl.style.color = "#065f46";`
  → 欢迎文案

**app.js L181** `      } else {`
  → meta 系统

**app.js L182** `        badgeEl.textContent = "API 异常";`
  → 闭合 appendMessage

**app.js L183** `        badgeEl.style.background = "#fee2e2";`
  → 闭合 click 处理器

**app.js L184** `        badgeEl.style.color = "#991b1b";`
  → 闭合 if newChatBtn

**app.js L185** `      }`

**app.js L186** `    } catch (_e) {`

**app.js L187** `      badgeEl.textContent = "API 离线";`

**app.js L188** `      badgeEl.style.background = "#fee2e2";`

**app.js L189** `      badgeEl.style.color = "#991b1b";`

**app.js L190** `    }`

**app.js L191** `  }`

**app.js L192** ``

**app.js L193** `  if (newChatBtn) {`

**app.js L194** `    newChatBtn.addEventListener("click", async () => {`

**app.js L195** `      if (window.NexusSession) {`

**app.js L196** `        const oldSid = NexusSession.getSessionId();`

**app.js L197** `        const base = (window.NexusConfig && window.NexusConfig.apiBase) || "";`

**app.js L198** `        if (!(window.NexusConfig && window.NexusConfig.useMock)) {`

**app.js L199** `          try {`

**app.js L200** `            await fetch(`${base}/api/session/reset`, {`

**app.js L201** `              method: "POST",`

**app.js L202** `              headers: { "Content-Type": "application/json" },`

**app.js L203** `              body: JSON.stringify({ session_id: oldSid }),`

**app.js L204** `            });`

**app.js L205** `          } catch (_e) {`

**app.js L206** `            /* 服务端重置失败不阻塞 UI */`

**app.js L207** `          }`

**app.js L208** `        }`

**app.js L209** `        NexusSession.resetSession();`

**app.js L210** `        updateSessionLabel();`

**app.js L211** `      }`

**app.js L212** `      messagesEl.innerHTML = "";`

**app.js L213** `      appendMessage(`

**app.js L214** `        "bot",`

**app.js L215** `        "已开始新对话。可继续提问。",`

**app.js L216** `        "系统"`

**app.js L217** `      );`

**app.js L218** `    });`

**app.js L219** `  }`

**app.js L220** ``

**app.js L221** `  const badge = badgeEl;`

**app.js L222** `  if (badge && window.NexusConfig && !window.NexusConfig.useMock) {`

**app.js L223** `    badge.textContent = "API 模式";`

**app.js L224** `    badge.style.background = "#d1fae5";`

**app.js L225** `    badge.style.color = "#065f46";`

**app.js L226** `    checkHealth();`

**app.js L227** `  }`

**app.js L228** ``

**app.js L229** `  updateSessionLabel();`

**app.js L230** ``

**app.js L231** `  inputEl.addEventListener("keydown", (e) => {`

**app.js L232** `    if (e.key === "Enter" && !e.shiftKey) {`

**app.js L233** `      e.preventDefault();`

**app.js L234** `      formEl.requestSubmit();`

**app.js L235** `    }`

**app.js L236** `  });`

**app.js L237** ``

**app.js L238** `  inputEl.focus();`

**app.js L239** `})();`
