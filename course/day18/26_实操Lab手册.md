# Day 18 实操 Lab 手册

**实验环境**：`nexus-agent-platform`  
**预计时长**：90 分钟  
**角色**：林晓（学员）— 智链科技实训

---

## Lab 0：环境准备（10 分钟）

```bash
cd /workspace/nexus-agent-platform
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1

python3 --version   # 建议 3.11+
python3 -m pytest tests/day18/test_intent.py -v
```

**验收**：12 passed。

---

## Lab 1：意图分类观察（15 分钟）

### 步骤

1. 打开 `src/day18/intent_demos.py`  
2. 在 `SAMPLES` 末尾添加你的姓名 + 「请审查合规」  
3. 运行：

```bash
python3 src/day18/intent_demos.py
```

### 记录表

| 输入 | intent | template_name | confidence | 命中词 |
|------|--------|---------------|------------|--------|
| （填写） | | | | |

### 思考题

为何「请审查合规」几乎总是 `compliance_review`？

---

## Lab 2：变量构建（15 分钟）

```bash
python3 src/day18/router_demos.py
```

### 任务

修改 `router_demos.py` 的 `context_provider` 返回你自己的学号字符串，重新运行。

确认 `rag_qa` 分支输出含你的学号。

### 扩展

添加第四条 query：`理财产品文档总结` — 预测 intent 并运行验证。

---

## Lab 3：/route 与 auto_route 对比（20 分钟）

创建 `lab18_route_compare.py`（可放 `/tmp`）：

```python
import sys
from pathlib import Path
SRC = Path("src").resolve()
sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig
from prompts import IntentRouter

SAMPLE = {
    "model": "mock",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}

env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
router = IntentRouter()

# A: 仅 /route
a1 = ChatAssistant(client=client, intent_router=router, auto_route=False, track_tokens=False)
h, msg, _ = a1.handle_command("/route 总结要点")
print("A /route:", msg)
print("A template:", a1.prompt_template)

# B: auto_route
a2 = ChatAssistant(client=client, intent_router=router, auto_route=True, track_tokens=False)
a2.chat_turn("总结要点")
print("B template:", a2.prompt_template.name if a2.prompt_template else None)
```

运行并回答：

- A 的 `prompt_template` 为何是 `None`？  
- B 的模板名是什么？  

---

## Lab 4：端到端演示（15 分钟）

```bash
NEXUS_LLM_MOCK=1 python3 src/day18/routed_assistant_demo.py
```

### 观察点

1. `/route` 行是否只打印分类  
2. 普通输入是否含 `[路由: ...]`  
3. `context_provider` 是否加载 `raw_notice.txt`  

### 修改实验

将脚本中一条改为「理财产品收益如何」，预测路由模板。

---

## Lab 5：测试驱动理解（15 分钟）

```bash
python3 -m pytest tests/day18/test_intent.py::test_priority_compliance_over_rag -v
```

阅读该测试，在注释中手写各意图命中词与得分。

任选另一条失败测试（若故意改错 rules），观察 pytest 输出。

---

## Lab 6：自定义规则挑战（可选 +10 分）

1. 新建 `lab18_custom_rules.py`  
2. 增加意图 `tech_support`，关键词：「断网」「登录失败」「报错」  
3. 映射到 `default_assistant` 或自定义模板  
4. 断言 `classify("登录失败怎么办").intent == "tech_support"`  

---

## Lab 提交清单

| 产物 | 必须 |
|------|------|
| Lab 1 记录表 | ✓ |
| Lab 3 两问答案 | ✓ |
| Lab 4 预测与实测 | ✓ |
| Lab 6 代码 | 选做 |

提交路径：`homework/day18/lab/` 或学习平台。

---

## 故障排除

见 [10_常见问题与排错指南](10_常见问题与排错指南.md)。

---

## Lab 总结话术（填写）

「Day 18 我理解了 __________ 与 __________ 的区别，意图路由在 complete 之前调用 __________。」

参考答案：/route、auto_route、route_and_apply

---

## 讲师巡场要点

- Lab 3 是今日最高频误区  
- Lab 4 确保 `NEXUS_LLM_MOCK=1`  
- Lab 6 禁止直接改仓库 `DEFAULT_KEYWORD_RULES`  
