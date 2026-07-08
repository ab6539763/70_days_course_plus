# Day 12 实操 Lab 手册（Step-by-Step）

按步骤完成全天实验，约 3500 字。  
**环境**：`cd nexus-agent-platform` · `export PYTHONPATH=src`

---

## Lab 0：环境自检（5 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 -c "from llm import LLMClient; print('OK')"
```

预期：打印 `OK`。

若失败：检查目录与 PYTHONPATH。

---

## Lab 1：HTTP 基础（15 分钟）

```bash
python3 src/day12/http_demos.py
```

### 记录表

| 输出段 | 你观察到的值 |
|--------|--------------|
| args.demo | |
| 离线跳过？ | 是/否 |

### 追问

`urllib.request.Request` 与直接 `urlopen(url)` 的区别？

<details><summary>提示</summary>Request 可自定义 headers、method、body</details>

---

## Lab 2：请求体预览（15 分钟）

```bash
python3 src/day12/api_demos.py
```

手填 JSON 顶层 key：

- model = ____  
- temperature = ____  
- max_tokens = ____  
- messages 条数 = ____  

### 扩展

在 REPL 增加一条 `assistant` 历史消息，再 `build_request_body`，观察 messages 数组。

---

## Lab 3：环境变量（20 分钟）

```bash
cp .env.example .env
echo "NEXUS_LLM_MOCK=1" >> .env
```

```python
from llm.env import load_llm_env
c = load_llm_env()
print(c.mock, c.chat_completions_url)
```

### 实验：优先级

```bash
export DEEPSEEK_API_KEY=from-shell
python3 -c "from llm.env import load_llm_env; print(load_llm_env().api_key)"
```

---

## Lab 4：Mock 端到端（20 分钟）

```bash
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
```

记录：

| 字段 | 值 |
|------|-----|
| 模式 | |
| finish_reason | |
| total_tokens | |
| assistant 前 30 字 | |

对照 `src/day05/sample_data/chat_completion.json` 是否一致。

---

## Lab 5：单元测试（15 分钟）

```bash
NEXUS_LLM_MOCK=1 python3 -m pytest tests/day12/ -v
```

全绿后，打开 `tests/day12/test_llm_client.py`，找一个使用 **custom transport** 的用例，解释其意图。

---

## Lab 6：ConfigError（10 分钟）

```bash
unset NEXUS_LLM_MOCK DEEPSEEK_API_KEY
python3 -c "
from llm.client import LLMClient
from llm.env import LLMEnvConfig
LLMClient(env=LLMEnvConfig(api_key='', base_url='https://x/v1', mock=False))
"
```

预期异常：__________

---

## Lab 7：自定义 transport（25 分钟，选做）

创建 `/tmp/day12_echo_transport.py`：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nexus-agent-platform" / "src"))

from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig

def echo_transport(url, headers, payload):
    user = next(
        (m["content"] for m in reversed(payload["messages"]) if m["role"] == "user"),
        "",
    )
    return {
        "model": "echo",
        "choices": [{
            "message": {"role": "assistant", "content": f"Echo: {user}"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }

env = LLMEnvConfig(api_key="", base_url="https://local/v1", mock=False)
client = LLMClient(ModelConfig(), env=env, transport=echo_transport)
print(client.chat("Lab7 成功").content)
```

预期：`Echo: Lab7 成功`

---

## Lab 8：Live 调用（15 分钟，可选）

`.env` 配置真实 Key，`NEXUS_LLM_MOCK=0`。

```bash
python3 src/day12/llm_client_demo.py
```

对比 Mock：content 是否与问题相关？记录 usage。

---

## Lab 9：Day 13 预习（10 分钟）

阅读 `25_llm_client精读.md` 末尾「Day 13 装饰器接入点」。

写下你认为应重试的 2 种 `APIError` 场景：

1. __________  
2. __________  

---

## 实验报告模板

```markdown
# Day 12 实验报告 — 姓名

## 环境
- Python 版本：
- Mock/Live：

## Lab 4 输出摘要
（粘贴 assistant 回复）

## 收获
1.
2.

## 问题
1.
```

---

## 故障速查

| 现象 | 检查 |
|------|------|
| ModuleNotFoundError | PYTHONPATH=src |
| ConfigError | NEXUS_LLM_MOCK 或 Key |
| pytest 红 | 先单独跑 demo |
| Live 401 | Key 有效性 |

---

*FAQ：[10_常见问题与排错指南.md](10_常见问题与排错指南.md)*
