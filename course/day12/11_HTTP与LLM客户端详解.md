# Day 12 HTTP 与 LLM 客户端详解

**篇幅**：深度专题 · 约 4500 字  
**代码锚点**：`nexus-agent-platform/src/llm/client.py`、`env.py`、`response.py`

---

## 一、HTTP 客户端在 NexusAgent 中的战略位置

智链科技知识库 MVP 的「智能」层依赖外部大模型 API。Day 12 实现的 `llm/` 包是平台**第一个出站网络模块**，承担：

```
业务 Prompt（ChatMessage）→ HTTP → 远程 GPU 推理 → 结构化回复（ChatCompletionResult）
```

陈默在架构评审中划定四条红线：

1. **OpenAI 兼容**：请求/响应字段与业界标准一致，便于切换 DeepSeek / OpenAI / 私有网关  
2. **标准库传输**：`urllib.request`，不引入 `requests`  
3. **Mock 一等公民**：`NEXUS_LLM_MOCK=1`，CI 零 Key、零外网  
4. **异常统一**：出站错误全部 `APIError`，配置错误 `ConfigError`

---

## 二、urllib 传输层详解

### 2.1 POST JSON 的标准步骤

```python
# 1. Python dict → JSON 字符串 → UTF-8 bytes
data = json.dumps(payload).encode("utf-8")

# 2. 构造 Request（method 显式 POST）
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

# 3. 发送并读取响应
with urllib.request.urlopen(req, timeout=60) as resp:
    raw = resp.read().decode("utf-8")
    return json.loads(raw)
```

与 `http_demos.py` GET 的区别：**有 body**、**Content-Type: application/json**、通常 **Authorization**。

### 2.2 异常分层

| 层级 | 异常 | 处理 |
|------|------|------|
| TCP/TLS | `URLError` | 转 `APIError("网络连接失败")` |
| HTTP 语义 | `HTTPError`（仍是 response） | 读 body，`APIError` + code |
| 解析 | `JSONDecodeError` | `APIError("响应非合法 JSON")` |

`HTTPError` 可 `exc.read()` 获取错误 body（如 `{"error":{"message":"Invalid API Key"}}`）。

### 2.3 为何不用 Session / 连接池

课程 MVP 单次 `complete` 一次连接足够。高 QPS 场景（Day 30+）可考虑 `httpx` 连接池；今日重点是**正确性**与**可测性**。

---

## 三、build_request_body：边界校验

```python
def build_request_body(messages, config):
    for msg in messages:
        msg.ensure_valid()  # BaseModel → ValidationError
    body = config.to_api_params()
    body["messages"] = [m.to_api_message() for m in messages]
    return body
```

设计要点：

- **先校验后组装**：避免发出非法请求浪费 token  
- `to_api_message()` 仅 `role`+`content`，不泄露 `created_at` 等内部字段  
- `ModelConfig.to_api_params()` 经 `ensure_valid()` 保证 temperature 范围

OpenAI 兼容 body 示例见 `api_demos.py` 输出。

---

## 四、LLMEnvConfig 与 URL 拼接

```python
@property
def chat_completions_url(self) -> str:
    base = self.base_url.rstrip("/")
    return f"{base}/chat/completions"
```

`rstrip("/")` 防止 `https://x/v1/` + `/chat/completions` 出现双斜杠。

`parse_env_file` 规则：

- 跳过空行、`#` 注释  
- `KEY=VALUE`，value 去首尾引号  
- **不覆盖**已存在于 `os.environ` 的键（12-factor 原则）

Mock 判定：`1`、`true`、`yes`、`on`（大小写不敏感）均为真。

---

## 五、Transport 抽象与依赖注入

```python
TransportFunc = Callable[[str, dict[str, str], dict[str, Any]], dict]
```

三种实现：

| 实现 | 场景 |
|------|------|
| `default_transport` | 生产 Live |
| `mock_transport_from_file` | Mock / CI |
| 测试 lambda | 单元测试 |

`LLMClient.__init__` 决策树见 `03_架构设计.md`。

**测试示例**：

```python
def fake_t(url, h, p):
    return {"choices": [{"message": {"role": "assistant", "content": "ok"}}], "usage": {}}

client = LLMClient(env=mock_env, transport=fake_t)
```

无需 monkeypatch `urllib`。

---

## 六、parse_chat_completion 与 Day 5 传承

生产版 `llm/response.py` 相比 Day 5 教学脚本：

- 返回类型化 `ChatCompletionResult`  
- `ChatMessage.from_api_response` 复用模型层  
- 错误抛 `APIError` 而非 `print`+`exit`  
- 保留 `raw` 字段供调试（`repr=False`）

检查顺序：

1. `response.get("error")` — API 业务错误  
2. `choices` 非空  
3. `message.content` 非空  

与 Day 5 `.get()` 链思想一致，失败时**快速明确**。

---

## 七、Mock 模式深度说明

### 7.1 激活条件

`NEXUS_LLM_MOCK=1` 或 `.env` 中等价值。

### 7.2 行为差异

| 维度 | Mock | Live |
|------|------|------|
| HTTP | 无 | urllib POST |
| Key | 不需要 | 必须 |
| 响应 | 固定 JSON 文件 | 模型实时生成 |
| headers | 仅 Content-Type | + Authorization |

### 7.3 样本路径

`get_path("chat_completion_sample")` → `day05/sample_data/chat_completion.json`

**与 Day 5 同源**：教学解析与生产 Mock 字段一致，降低认知负担。

### 7.4 CI 实践

`llm_client_demo.py` 内：

```python
os.environ.setdefault("NEXUS_LLM_MOCK", "1")
```

保证直接运行 demo 不依赖 Key。pytest 通过 `monkeypatch` 或环境变量同样策略。

---

## 八、APIError 与上层集成

```python
class APIError(NexusError):
    def __init__(self, message, *, status_code=None, response_body=None):
        self.status_code = status_code
        self.response_body = response_body
```

Day 13 重试装饰器将检查：

- `status_code in (429, 500, 502, 503, 504)` → 可重试  
- `ConfigError` / 401 → 不重试

Day 14 `cli_assistant` 捕获 `APIError` 向用户展示友好消息。

---

## 九、完整调用示例

```python
from llm import LLMClient
from models import ChatMessage, ModelConfig

client = LLMClient(ModelConfig(temperature=0.3, max_tokens=256))
messages = [
    ChatMessage("system", "你是企业知识库助手。"),
    ChatMessage("user", "NexusAgent 是什么？"),
]
result = client.complete(messages)
print(result.message.content)
print(result.usage_summary())
```

Mock：

```bash
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
```

---

## 十、与后续课程衔接

| 日程 | 扩展 |
|------|------|
| Day 13 | `@retry` 装饰 `complete` |
| Day 14 | CLI 交互调用 `chat()` |
| Day 16 | 流式 chunk 解析 |
| Day 28 | RAG：doc_reader 文本作 user 上下文 |

---

*速查：[17_LLMClient速查手册.md](17_LLMClient速查手册.md) · 精读：[25_llm_client精读.md](25_llm_client精读.md)*
