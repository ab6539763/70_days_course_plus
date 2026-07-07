# Day 15 实操 Lab 手册

**实验环境**：`nexus-agent-platform` + `PYTHONPATH=src`  
**建议时长**：120 分钟  
**角色**：学员独立完成，助教巡场

---

## Lab 0：环境自检（10 min）

```bash
cd /path/to/nexus-agent-platform
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 -m pytest tests/day15/ -v --tb=short
```

**通过标准**：全部 PASSED。

---

## Lab 1：Token 原理肉眼观察（15 min）

### 步骤

```bash
python3 src/day15/token_principle_demos.py
```

### 记录表

| 文本 | 字符数 | 程序 tokens | 你的心算 |
|------|--------|-------------|----------|
| Hello world | | | |
| 你好世界 | | | |
| NexusAgent 智链科技平台 | | | |
| 理财产品年化收益率约为 3.5%-4.2% | | | |

### 思考题

哪两条中文样本 token/字符 比最高？为什么？

---

## Lab 2：API usage 与本地估算（20 min）

```bash
python3 src/day15/token_counter_demo.py
```

### 任务

1. 抄写「本地估算 prompt tokens」数值  
2. 抄写 API 回报的 `prompt_tokens`  
3. 抄写 `compare_estimate` 一行  
4. 抄写 `format_yuan()` 费用

### 扩展

修改 `token_counter_demo.py` 中 `messages`，加一条长 system，观察估算变化（不提交，本地玩）。

---

## Lab 3：CLI `/tokens` 集成（25 min）

```bash
NEXUS_LLM_MOCK=1 python3 src/day15/assistant_token_demo.py
```

### 观察

- 第一轮对话回复内容  
- `/tokens` 报表三行结构

### 交互扩展

```bash
NEXUS_LLM_MOCK=1 python3 src/chat/cli_assistant.py
```

操作序列：

```
/help
你好
再问一句
/tokens
/clear
/tokens
/exit
```

**记录**：`/clear` 前后 `/tokens` 差异。

---

## Lab 4：多轮膨胀模拟（25 min）

创建 `lab_growth.py`（个人实验）：

```python
"""Lab 4: 模拟多轮 prompt 增长"""
from chat import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig

n = {"v": 0}

def transport(*_):
    n["v"] += 1
    v = n["v"]
    base = 100 + v * 50
    return {
        "model": "deepseek-chat",
        "choices": [{"message": {"role": "assistant", "content": f"r{v}"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": base, "completion_tokens": 20, "total_tokens": base + 20},
    }

env = LLMEnvConfig(api_key="x", base_url="https://x/v1", mock=True)
client = LLMClient(ModelConfig(), env=env, transport=transport)
a = ChatAssistant(client=client, track_tokens=True)

for i in range(1, 6):
    a.chat_turn(f"question {i}")
    u = a.token_tracker.stats.last_usage()
    print(f"轮{i}: prompt={u.prompt_tokens}")

print(a.token_tracker.report())
```

### 交付

手绘或 Excel 折线图：轮次 vs prompt_tokens。

---

## Lab 5：单元测试解剖（15 min）

```bash
python3 -m pytest tests/day15/test_token_counter.py -v -k "estimate"
python3 -m pytest tests/day15/test_token_counter.py::test_assistant_tokens_command -v
```

阅读 `test_assistant_shows_token_in_output`，回答：`run_scripted` 输出里何处含 `tokens`？

---

## Lab 6：费用沙盘（10 min）

用计算器（或 Python）：

| 场景 | prompt | completion | 费用(¥) |
|------|--------|------------|---------|
| 短问答 | 500 | 100 | |
| 长文档 | 20000 | 2000 | |
| 百万压测 | 1000000 | 500000 | |

单价：输入 1/M，输出 2/M。与 `TokenCounter.estimate_cost` 交叉验证。

---

## Lab 7：排错演练（10 min）

助教发放「坏代码」片段（见 [10_常见问题与排错指南.md](10_常见问题与排错指南.md) 练习 4），学员指出 `messages_snapshot` 错误并口述正确顺序。

---

## Lab 验收清单

| Lab | 完成 | 助教签 |
|-----|------|--------|
| 0 环境 | ☐ | |
| 1 原理 | ☐ | |
| 2 API 对比 | ☐ | |
| 3 /tokens | ☐ | |
| 4 膨胀 | ☐ | |
| 5 测试 | ☐ | |
| 6 费用 | ☐ | |
| 7 排错 | ☐ | |

---

## 实验报告模板

```markdown
# Day 15 Lab 报告 - 姓名

## Lab 1 四组数据
（粘贴表格）

## Lab 3 /clear 观察
（前后 /tokens 对比）

## Lab 4 曲线结论
（200 字说明 prompt 增长原因）

## 今日收获与疑问
```

---

## 清理

实验脚本 `lab_growth.py` 可不提交；若提交请放个人分支。

---

## 下一步

完成 Lab 后预习 Day 16：搜索 `stream` 关键字于 `nexus-agent-platform`（若已发布），阅读流式设计草案。
