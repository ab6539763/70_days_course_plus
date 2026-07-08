# IntentRouter 速查手册

**模块**：`prompts/intent.py` + `ChatAssistant`  
**需求**：ZL-NA-REQ-018

---

## 快速开始

```python
from prompts import IntentRouter, RuleBasedIntentClassifier
from chat import ChatAssistant

router = IntentRouter(
    context_provider=lambda: "上下文文本",
    company="智链科技",
    default_product="稳健增值系列产品",
)

assistant = ChatAssistant(
    client=client,
    intent_router=router,
    auto_route=True,
)
```

---

## RuleBasedIntentClassifier

```python
clf = RuleBasedIntentClassifier(
    rules=None,          # 默认 DEFAULT_KEYWORD_RULES
    template_map=None,   # 默认 INTENT_TEMPLATE_MAP
    priority=INTENT_PRIORITY,
)
match = clf.classify("请总结要点")
print(match.summary())
```

### IntentMatch 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| intent | str | 业务意图名 |
| template_name | str | 注册表模板名 |
| confidence | float | 0.5–0.95 |
| matched_keywords | list[str] | 命中词 |
| user_text | str | 原始输入 |

---

## IntentRouter

| 方法 | 签名 | 作用 |
|------|------|------|
| classify | `(text) -> IntentMatch` | 委托 classifier |
| build_variables | `(match) -> dict[str,str]` | 模板变量 |
| route_and_apply | `(assistant, user_text) -> IntentMatch` | 分类+切换模板 |

### build_variables 速查

```python
# rag_qa → company, context
# doc_summary → company, max_points, document
# compliance_review → company, text
# product_faq → company, product_name
# default → company
```

---

## 默认关键词（节选）

| intent | 关键词示例 |
|--------|------------|
| compliance_review | 合规、审阅、宣传语 |
| doc_summary | 总结、摘要、要点 |
| product_faq | 理财、收益、基金 |
| rag_qa | 文档、资料、根据 |

完整表见 `DEFAULT_KEYWORD_RULES` 源码。

---

## INTENT_TEMPLATE_MAP

```python
{
    "rag_qa": "rag_qa",
    "doc_summary": "doc_summary",
    "compliance_review": "compliance_review",
    "product_faq": "product_faq",
    "general": "default_assistant",
}
```

---

## INTENT_PRIORITY

```
compliance_review > doc_summary > product_faq > rag_qa > general
```

---

## ChatAssistant API

### 构造参数

```python
intent_router: IntentRouter | None = None
auto_route: bool = False
```

### 斜杠命令

```
/route [用户话术]   # 预览分类，默认样例句
```

### chat_turn 行为

`auto_route=True` 时：

1. `route_and_apply`  
2. `add_user`  
3. `complete`  
4. 回复前缀 `[路由: template_name]`  

---

## CLI 演示

```bash
cd nexus-agent-platform
export PYTHONPATH=src

python3 src/day18/intent_demos.py
python3 src/day18/router_demos.py
NEXUS_LLM_MOCK=1 python3 src/day18/routed_assistant_demo.py
```

---

## 测试

```bash
python3 -m pytest tests/day18/test_intent.py -v
```

| 测试 | 断言要点 |
|------|----------|
| test_classify_* | template_name |
| test_priority_* | compliance 优先 |
| test_assistant_auto_route | product_faq + 路由前缀 |

---

## 自定义规则模板

```python
custom_rules = {
    **DEFAULT_KEYWORD_RULES,
    "my_intent": ["词1", "词2"],
}
custom_map = {**INTENT_TEMPLATE_MAP, "my_intent": "some_template"}
clf = RuleBasedIntentClassifier(rules=custom_rules, template_map=custom_map)
```

---

## 错误处理

| 现象 | 处理 |
|------|------|
| ConfigError on route | 检查 build_variables 与模板 required_vars |
| /route 未启用 | 传入 intent_router |
| 分类不符预期 | /route 看 matched_keywords，调 rules/priority |

---

## 相关文件

- `src/prompts/intent.py`  
- `src/chat/cli_assistant.py`  
- `src/day18/*.py`  
- `tests/day18/test_intent.py`  
