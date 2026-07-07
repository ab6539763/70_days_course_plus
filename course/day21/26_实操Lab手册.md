# Day 21 实操 Lab 手册

**时长**：90 分钟  
**环境**：`nexus-agent-platform` + `PYTHONPATH=src` + `NEXUS_LLM_MOCK=1`

---

## Lab 0：环境自检（5 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 -m pytest tests/day21/test_sprint3.py -v
```

**通过标准**：12 passed

---

## Lab 1：Sprint 3 周测（15 分钟）

```bash
python3 src/day21/sprint3_quiz.py
```

记录得分于实验报告。低于 60 查阅 [10_Sprint3周测题库.md](10_Sprint3周测题库.md) 后重测。

```bash
python3 src/day21/sprint3_review.py
```

对照打印的 Day 15–21 里程碑，勾选已理解项。

---

## Lab 2：工具注册表（20 分钟）

### 2.1 运行演示

```bash
python3 src/day21/tool_demos.py
```

**任务**：在报告中抄写四段 `[tool_name]` 输出的第一行。

### 2.2 REPL 实验

```python
from tools import build_nexus_tools, ToolExecutor
from services import SimilarQuestionMatcher

reg = build_nexus_tools(faq_matcher=SimilarQuestionMatcher())
print(reg.list_names())
ex = ToolExecutor(reg)
print(ex.execute("faq_lookup", {"query": "客服电话"}).summary())
```

**任务**：故意 `execute("typo", {})` 观察失败格式。

---

## Lab 3：/tool 命令（20 分钟）

编写 `lab21_tool_commands.py`：

```python
from chat import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig
from tools import build_nexus_tools
from services import SimilarQuestionMatcher

registry = build_nexus_tools(faq_matcher=SimilarQuestionMatcher())
env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
client = LLMClient(ModelConfig(), env=env)
assistant = ChatAssistant(client=client, tool_registry=registry, track_tokens=False)

for cmd in [
    "/tool list",
    "/tool faq_lookup 投资回报率",
    "/tool estimate_tokens lab test",
]:
    handled, msg, _ = assistant.handle_command(cmd)
    print(cmd, "->", msg[:80])
```

**通过标准**：三条均有合理输出。

---

## Lab 4：ChatOrchestrator 整合（25 分钟）

```bash
python3 src/day21/integrated_assistant_demo.py
```

**观察清单**：

| 步骤 | 输入 | 检查点 |
|------|------|--------|
| 1 | /tool list | 四工具 |
| 2 | /tool faq_lookup ... | [faq_lookup] |
| 3 | 有没有风险啊？ | FAQ 直答 |
| 4 | 根据资料，年化收益率？ | LLM 或路由 |

### 阈值实验

修改 demo 中 `faq_direct_threshold` 为 `0.99`，重跑步骤 3，记录是否仍直答。

---

## Lab 5：读测试（5 分钟）

```bash
python3 -m pytest tests/day21/test_sprint3.py -v -k "orchestrator"
```

阅读 `test_orchestrator_faq_direct` 与 `test_orchestrator_fallback_to_llm` 源码。

---

## 实验报告模板

```markdown
# Day 21 Lab 报告 — 姓名

## 周测得分
## tool_demos 四工具输出摘要
## /tool 实验截图或日志
## integrated_assistant_demo 观察
## 阈值实验结论（2 句话）
## 今日最大收获
```

---

## 故障排除

| 问题 | 解决 |
|------|------|
| ModuleNotFoundError | export PYTHONPATH=src |
| 工具调用未启用 | 传 tool_registry |
| FAQ 不直答 | 降 faq_direct_threshold |
| pytest 失败 | 先 git pull 最新代码 |

---

## 拓展挑战（+10 分）

在 Lab 4 基础上新增脚本步骤：对「请审阅宣传语」先 `/tool intent_classify` 再自然语言问同一句话，对比意图是否一致。

```mermaid
flowchart LR
    L0[自检] --> L1[周测]
    L1 --> L2[工具]
    L2 --> L3[/tool]
    L3 --> L4[编排器]
    L4 --> L5[测试]
```

---

## Lab 6：结对编程编排器（20 分钟，选做）

两人一组，一人写测试一人写代码（伪）：给定 `user_text="今天天气"`，断言**不**含 FAQ 直答。使用 `SimilarQuestionMatcher()` 默认配置与 `OrchestratorConfig()` 默认阈值。运行 mindset 同 `test_orchestrator_fallback_to_llm`。

---

## Lab 7：文档化你的工具（15 分钟）

为你设计的「第五工具」chunk_count 写一段 `description`（中文，50 字内），说明适用场景与不应使用的场景。交换给同伴 peer review。

---

## Lab 8：晨会三分钟演讲

每人用三分钟向假想「智链科技全员」说明：Day 21 我们交付了什么、为什么 FAQ 直答重要、明天 Day 22 做什么。讲师随机点名 3 人。

---

## 安全与合规提醒

- 实验勿用真实客户 PII 作为 /tool 参数  
- mock LLM 环境下勿误以为已接生产密钥  
- 截图发群时打码 API key  

---

## Lab 成绩 rubric

| 项 | 分值 |
|----|------|
| 环境 12 passed | 30 |
| 周测记录 | 15 |
| tool_demos 报告 | 20 |
| integrated 观察 | 25 |
| 报告格式 | 10 |

---

## 讲师巡场 checkpoints

- [ ] 50% 学员完成 Lab 2  
- [ ] 17:00 前 80% 跑通 integrated_assistant_demo  
- [ ] 收集 FAQ 直答阈值实验至少 5 份  

---

## 延伸：与 Day 22 衔接作业

在 Lab 报告末尾用 100 字描述你期望的聊天页面长什么样。优秀作业将贴到 Day 22 教室墙报。
