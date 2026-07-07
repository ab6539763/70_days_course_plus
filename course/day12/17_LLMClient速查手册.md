# LLMClient 速查手册

**模块**：`nexus-agent-platform/src/llm/`  
**需求**：ZL-NA-REQ-012

---

## 快速开始

```python
from llm import LLMClient
from models import ChatMessage, ModelConfig

client = LLMClient.from_env()
result = client.complete([
    ChatMessage("user", "你好"),
])
print(result.message.content)
```

Mock（无需 Key）：

```bash
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
```

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | — | Bearer Token，Live 必填 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | API 根 |
| `NEXUS_LLM_MOCK` | `0` | `1` 启用 Mock |

---

## build_request_body

```python
def build_request_body(
    messages: list[ChatMessage],
    config: ModelConfig,
) -> dict[str, Any]
```

输出：`{model, temperature, max_tokens, messages: [{role, content}, ...]}`

---

## LLMClient

### 构造

```python
LLMClient(
    config: ModelConfig | None = None,
    *,
    env: LLMEnvConfig | None = None,
    transport: TransportFunc | None = None,
    sample_path: Path | None = None,
)
```

### 类方法

```python
LLMClient.from_env(**kwargs) -> LLMClient
```

### complete

```python
def complete(self, messages: list[ChatMessage]) -> ChatCompletionResult
```

### chat

```python
def chat(
    self,
    user_content: str,
    *,
    system_prompt: str | None = None,
) -> ChatMessage
```

---

## ChatCompletionResult

```python
@dataclass
class ChatCompletionResult:
    message: ChatMessage
    model: str
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw: dict  # repr=False

    def usage_summary(self) -> str: ...
```

---

## parse_chat_completion

```python
def parse_chat_completion(response: dict) -> ChatCompletionResult
```

**Raises**: `APIError`

---

## load_llm_env

```python
def load_llm_env(*, env_file: Path | None = None) -> LLMEnvConfig
```

**Raises**: `ConfigError`（非 Mock 且无 Key）

---

## Transport 类型

```python
TransportFunc = Callable[[str, dict[str, str], dict[str, Any]], dict]
```

| 函数 | 用途 |
|------|------|
| `default_transport` | urllib POST |
| `mock_transport_from_file` | 读本地 JSON |

---

## 异常

```python
from core.exceptions import APIError, ConfigError

except APIError as e:
    e.code            # "API_ERROR"
    e.status_code     # int | None
    e.response_body   # str | None

except ConfigError as e:
    e.code            # "CONFIG_ERROR"
```

---

## 路径键

| key | 指向 |
|-----|------|
| chat_completion_sample | src/day05/sample_data/chat_completion.json |

---

## 命令行

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 src/day12/http_demos.py
python3 src/day12/api_demos.py
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
python3 -m pytest tests/day12/ -v
```

---

*深度：[11_HTTP与LLM客户端详解.md](11_HTTP与LLM客户端详解.md) · 精读：[25_llm_client精读.md](25_llm_client精读.md)*
