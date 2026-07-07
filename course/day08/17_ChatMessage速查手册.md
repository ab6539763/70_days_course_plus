# Day 8 ChatMessage 与 OOP 速查手册

## 一、最小可用示例

```python
from models.message import ChatMessage

msg = ChatMessage("user", "你好")
assert msg.validate() is None
print(msg.format_line())
print(msg.to_api_message())
```

## 二、ChatMessage API

| 方法 | 说明 |
|------|------|
| `__init__(role, content, *, created_at=None)` | 构造 |
| `validate()` | → str\|None |
| `to_dict()` | 含 created_at |
| `from_dict(d)` | 类方法 |
| `from_api_response(parsed)` | 从 Day5 解析结果 |
| `to_api_message()` | 仅 role+content |
| `format_line(max_content_len=60)` | 终端行 |
| `is_system/user/assistant()` | bool |

## 三、MessageHistory API

| 方法 | 说明 |
|------|------|
| `add(msg)` | 校验后追加 |
| `add_user/assistant/system(text)` | 快捷 |
| `to_api_messages()` | API 数组 |
| `save_json(path)` / `load_json(path)` | 持久化 |
| `len(history)` | 消息条数 |

## 四、运行命令

```bash
cd nexus-agent-platform
python3 src/day08/oop_demos.py
python3 src/day08/message_cli.py
python3 -m pytest tests/day08/ -v
```

## 五、VALID_ROLES

`system` | `user` | `assistant`

## 六、数据文件

`src/day08/data/messages.json`

## 七、与 Day 5 对照

```python
# Day 5 嵌套
content = data["choices"][0]["message"]["content"]

# Day 8
msg = ChatMessage.from_dict(data["choices"][0]["message"])
content = msg.content
```

## 八、魔术方法

| 调用 | 方法 |
|------|------|
| print(msg) | __str__ |
| repr(msg) | __repr__ |
| msg1 == msg2 | __eq__ |
| len(history) | MessageHistory.__len__ |

## 九、反模式

1. 在业务代码中手写 `{"role":...}` 而不经 ChatMessage  
2. 把 created_at 放进 API 请求  
3. 在 models 里 import day08  
4. 绕过 `history.add()` 直接改 `_messages`  

## 十、Sprint 2 进度

```
Day 8  ChatMessage     ← 今日
Day 9  BaseModel
Day 10 包重组
Day 12 首次 API
Day 14 阶段项目一
```

---

*打印贴显示器旁，编码时查阅。*
