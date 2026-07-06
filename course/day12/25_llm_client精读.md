# Day 12 llm/client 精读

**模块**：`nexus-agent-platform/src/llm/client.py`  
**行数**：约 156 行  
**建议时长**：45 分钟

---

## 文件头与导入

```python
"""
使用标准库 urllib 发送 OpenAI 兼容 Chat Completions 请求。
支持 Mock 离线模式（CI / 无 Key 环境）与可注入 transport（单元测试）。
"""
```

导入分层：

- 标准库：`json`, `urllib`, `pathlib`  
- 项目：`core.exceptions`, `core.paths`, `llm.env`, `llm.response`, `models`

**无第三方 HTTP 库** — 设计声明。

---

## TransportFunc 类型别名

```python
TransportFunc = Callable[[str, dict[str, str], dict[str, Any]], dict]
```

这是整个可测试性架构的**锚点**。任何符合签名的 callable 都可替换网络。

---

## build_request_body（36-49 行）

```python
for msg in messages:
    msg.ensure_valid()
body = config.to_api_params()
body["messages"] = [m.to_api_message() for m in messages]
return body
```

精读要点：

1. **先校验后序列化** — `ensure_valid` 抛 `ValidationError`  
2. **浅拷贝语义** — `to_api_params` 新 dict，再塞 messages  
3. **不 mutate** 入参 messages/config  

课堂提问：若 messages 为空，API 行为？→ 由服务端校验；我们未禁止空列表。

---

## default_transport（52-70 行）

### 编码链

`dict` → `json.dumps` → `str` → `.encode("utf-8")` → `bytes`

urllib body 必须是 bytes。

### HTTPError 处理

```python
body = exc.read().decode("utf-8", errors="replace")
```

`errors="replace"` 防止非 UTF-8 错误页解码崩溃。

### 超时 60s

大模型生成可能较慢；过短易误杀。Day 13 可对 504 重试。

---

## mock_transport_from_file（73-81 行）

闭包模式：

```python
def mock_transport_from_file(sample_path: Path) -> TransportFunc:
    def _transport(url, headers, payload):
        ...
    return _transport
```

注意：Mock **忽略** url/headers/payload，始终返回同一文件——适合 CI，不适合测试「不同输入不同输出」（那种用 lambda 注入）。

---

## LLMClient.__init__（93-111 行）

默认值链：

| 属性 | 默认 |
|------|------|
| config | `ModelConfig()` + ensure_valid |
| env | `load_llm_env()` |
| sample_path | `get_path("chat_completion_sample")` |

transport 优先级：**显式 > mock > default**

---

## _headers（118-126 行）

Mock 分支不要求 Key — 这是 `load_llm_env` 允许 Mock 无 Key 的配套设计。

Live 分支 `Bearer {api_key}` — 前缀 `Bearer ` 含空格，符合 RFC 6750。

---

## complete（128-140 行）

三步管道，无分支 — **单一职责**，利于 Day 13 整体装饰 retry。

---

## chat（142-155 行）

语法糖：

```python
messages = []
if system_prompt:
    messages.append(ChatMessage("system", system_prompt))
messages.append(ChatMessage("user", user_content))
```

多轮对话应直接用 `complete`，勿扩展 `chat` 参数爆炸。

---

## from_env 类方法

```python
@classmethod
def from_env(cls, **kwargs) -> LLMClient:
    return cls(env=load_llm_env(), **kwargs)
```

显式 `env=load_llm_env()` 避免构造时默认值被覆盖的歧义。

---

## 与 Day 13 装饰器接入点

推荐装饰 **complete**：

```python
# Day 13 预览
@retry(max_attempts=3)
def complete(self, messages):
    ...
```

原因：Mock/Live 共用；parse 错误不应重试（在 complete 内区分可重试异常）。

---

## 精读习题

1. 画出 `__init__` 中 transport 选择流程图  
2. 为何 `HTTPError` 用 `from exc` 链式抛出？  
3. 写一个 3 行 lambda transport 返回固定 content  
4. `chat` 方法适合加 retry 吗？为什么？  

---

*走查：[20_完整代码走查.md](20_完整代码走查.md)*
