# Day 15 深度扩展：tiktoken 与 BPE

> **定位**：MVP 不依赖本模块；生产与精确计费建议阅读并实验。

---

## 1. 为何 MVP 不用 tiktoken？

| 因素 | 说明 |
|------|------|
| 教学环境 | 学员机器网络不一，`pip install tiktoken` 可能失败 |
| 模型绑定 | 不同模型 encoding 不同，需 `encoding_for_model` |
| 课程目标 | 理解「计量存在」比「精确到个位」更重要 |
| 可替换性 | `TokenCounter.estimate_text` 可注入替代实现 |

课件与代码均注明：**生产环境可替换为 tiktoken**。

---

## 2. BPE（Byte Pair Encoding）直觉

1. 从字符/字节序列开始  
2. 统计最高频相邻对，合并为新 symbol  
3. 重复直到词表大小达到目标（如 50k）

效果：

- 常见词整词一个 token：`「 the」`  
- 罕见词拆开：`「unbelievable」→ 多个子词`

---

## 3. tiktoken 快速上手

```bash
pip install tiktoken
```

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")  # 或 get_encoding("cl100k_base")
text = "你好世界 Hello"
tokens = enc.encode(text)
print(len(tokens), tokens)
print(enc.decode(tokens))
```

---

## 4. 与 estimate_tokens 对比实验

```python
from llm.token_counter import estimate_tokens
import tiktoken

def compare(text: str) -> None:
    est = estimate_tokens(text)
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        exact = len(enc.encode(text))
    except Exception:
        exact = -1
    print(f"{text!r}: estimate={est}, tiktoken={exact}, diff={est-exact}")
```

预期：纯英文启发式常**高估**；含特殊符号时偏差更大。

---

## 5. 接入 TokenCounter 的扩展设计

```python
class TiktokenCounter(TokenCounter):
    def __init__(self, model: str = "gpt-4", **kwargs):
        super().__init__(**kwargs)
        self._enc = tiktoken.encoding_for_model(model)

    def estimate_text(self, text: str) -> int:
        if not text:
            return 0
        return len(self._enc.encode(text))
```

保持 `usage_from_result` / `estimate_cost` 不变，仅替换估算路径。

---

## 6. DeepSeek 与 OpenAI 词表

教学项目默认 `deepseek-chat`，其 BPE 与 `cl100k_base` 不完全相同。企业应对：

- 使用厂商提供的 tokenizer  
- 或以 API `usage` 为唯一计费依据，本地仅粗估

---

## 7. 特殊内容 token 陷阱

| 内容类型 | 风险 |
|----------|------|
| JSON / 代码 | 符号多，token 密度高 |
| Base64 | 极差压缩，token 爆炸 |
| 重复空格 | 可能每空格单独 token |
| Emoji | 常 1–3 tokens/个 |

---

## 8. 字节级 BPE

部分新模型使用字节级输入，任意 UTF-8 可编码，罕见字不会 UNK。理解即可，NexusAgent MVP 不涉及。

---

## 9. 学习资源

- OpenAI cookbook：token counting  
- tiktoken GitHub README  
- Hugging Face `tokenizers` 库（训练自定义 BPE）

---

## 10. 自测

1. 解释 BPE 合并高频对的目的是什么？  
2. 为何财务对账应以 API usage 为准？  
3. 写出将 tiktoken 接入而不改 `ChatAssistant` 的类名。

<details>
<summary>参考答案</summary>

1. 在有限词表下平衡词表大小与序列长度  
2. 本地估算有偏差，厂商按实际 inference 计量  
3. `TiktokenCounter` 或注入自定义 `TokenCounter`

</details>
