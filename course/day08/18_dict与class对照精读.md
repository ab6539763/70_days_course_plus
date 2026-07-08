# Day 8 dict 与 class 对照精读

本文档帮助从 Day 7 函数式代码平滑过渡到 Day 8 面向对象。

---

## 一、联系人：dict vs Contact

### dict 写法（Day 7）

```python
contact = {
    "id": 1,
    "name": "张三",
    "phone": "13800138000",
    "email": "a@b.com",
    "group": "研发部",
}
err = validate_contact_fields(contact["name"], contact["phone"], contact["email"])
```

### class 写法（Day 8 选修）

```python
from day08.contact_class import Contact

c = Contact(1, "张三", "13800138000", "a@b.com", "研发部")
err = c.validate()
line = c.format_line()
```

**优势**：IDE 自动补全 `c.name`；拼写错误即时提示；行为内聚。

---

## 二、消息：dict vs ChatMessage

### dict 写法（Day 5 解析后）

```python
message = choices[0]["message"]
role = message.get("role", "")
content = message.get("content", "")
```

### class 写法（Day 8）

```python
from models.message import ChatMessage

msg = ChatMessage.from_dict(choices[0]["message"])
if msg.validate() is None:
    print(msg.format_line())
api_payload = msg.to_api_message()
```

---

## 三、历史记录：list[dict] vs MessageHistory

```python
# dict 时代
messages = []
messages.append({"role": "user", "content": "hi"})

# class 时代
history = MessageHistory()
history.add_user("hi")
api = history.to_api_messages()
```

---

## 四、何时仍用 dict

1. JSON 反序列化**瞬间**的中间态（立即 `from_dict`）
2. 与外部系统交互且对方只认 JSON
3. 快速原型脚本（`dayXX` 实验代码）

**主代码路径**：尽快转为 class。

---

## 五、迁移检查清单

- [ ] 所有 `message["role"]` 改为 `msg.role`
- [ ] 校验函数改为 `msg.validate()`
- [ ] 格式化改为 `msg.format_line()` 或 `format_chat_line`
- [ ] 单测构造 `ChatMessage(...)` 而非 dict
- [ ] API 导出用 `to_api_messages()`

---

## 六、自测题

1. `ChatMessage` 放在哪个包？**models**
2. `MessageHistory` 当前在哪个目录？**day08**（Day 10 可能迁移）
3. `to_api_message` 含几个字段？**2**

---

*配合 [05_课堂笔记_上午.md](05_课堂笔记_上午.md) 阅读。*
