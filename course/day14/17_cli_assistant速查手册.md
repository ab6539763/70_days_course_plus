# cli_assistant 速查手册

快速查阅 Day 14 命令、API 与运行方式。

---

## 运行命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 交互
NEXUS_LLM_MOCK=1 python3 src/chat/cli_assistant.py

# 验收
NEXUS_LLM_MOCK=1 python3 src/day14/cli_assistant_demo.py

# 测试
python3 -m pytest tests/day14/ -v
```

---

## 斜杠命令速查

| 命令 | 效果 |
|------|------|
| `/help` | 帮助列表 |
| `/exit` `/quit` | 退出 |
| `/clear` | 清空（留 system） |
| `/history` | 显示消息 |
| `/save` | 写 JSON |
| `/system 文本` | 追加 system |

---

## ChatAssistant API

```python
from chat import ChatAssistant

a = ChatAssistant(
    client=None,           # 默认 ResilientLLMClient
    history=None,          # 默认 MessageHistory()
    system_prompt="...",   # 默认 DEFAULT_SYSTEM_PROMPT
    history_path=None,     # 默认 get_path("chat_session")
    on_retry_log=False,
)

a.is_command("/help")           # True
a.handle_command("/help")       # (True, msg, False)
a.chat_turn("你好")             # str
a.run_scripted(["/exit"])       # list[str]
a.run_interactive()             # None
a.save_history() / a.load_history()
```

---

## _process_line 返回

```python
output: str      # 展示文本，可能为空
should_exit: bool
```

---

## 文件路径

| 路径 | 说明 |
|------|------|
| `src/chat/cli_assistant.py` | 核心 |
| `src/day14/cli_assistant_demo.py` | 验收 |
| `tests/day14/test_cli_assistant.py` | 测试 |

---

## 环境变量

| 变量 | 作用 |
|------|------|
| `NEXUS_LLM_MOCK=1` | Mock 模式 |
| `NEXUS_LLM_API_KEY` | 真实 API Key |
| `PYTHONPATH=src` | 导入路径 |

---

## 常见错误码

| 现象 | 检查 |
|------|------|
| ModuleNotFoundError | PYTHONPATH |
| ConfigError | Mock 或 Key |
| 无输出 | 空行或纯命令无反馈 |

---

## 与 Day 13 衔接

```python
from llm.resilient_client import ResilientLLMClient
# ChatAssistant 默认 client
```

---

## Day 15 预习

关注 `complete` 返回：

```python
result.usage  # prompt_tokens, completion_tokens, total_tokens
```

---

*对照表见 [18_模块整合对照表.md](18_模块整合对照表.md)*
