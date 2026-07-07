# Day 8 OOP 核心概念详解（扩展讲义）

本讲义对上午课堂笔记的补充，适合需要更深入理解面向对象的学员。

---

## 第一章：对象模型直觉

Python 中**一切皆对象**：整数 `1` 是 `int` 类的实例，`"hello"` 是 `str` 的实例。`class ChatMessage` 是你**自定义类型**的工厂。

```python
type(42)        # <class 'int'>
type("hi")      # <class 'str'>
msg = ChatMessage("user", "hi")
type(msg)       # <class 'models.message.ChatMessage'>
```

当你写 `msg.role`，Python 在实例 `msg` 上查找属性；找不到则去类 `ChatMessage` 上找方法。

---

## 第二章：属性查找顺序

1. 实例 `__dict__`
2. 类 `__dict__`
3. 父类（Day 9 继承）
4. `__getattr__`（高级）

```python
msg = ChatMessage("user", "test")
msg.role          # 实例属性
msg.validate      # 类上的函数，绑定为 bound method
msg.validate()    # 自动传入 self=msg
```

---

## 第三章：构造与不变量

**不变量**（invariant）是对象应始终满足的条件。`ChatMessage` 的不变量：

- `role in VALID_ROLES`
- `content` 非空（校验后）
- `created_at` 为 ISO 字符串

`__init__` 负责**初始化**，`validate()` 负责**检查不变量**。部分团队在 `__init__` 末尾直接 `validate` 并 `raise`，我们选择延迟校验以支持「先构造再修复」的 CLI 流程。

---

## 第四章：序列化契约

| 方向 | 方法 | 契约 |
|------|------|------|
| 对象→dict | to_dict() | 信息完整，可还原 |
| dict→对象 | from_dict() | 容忍缺字段，用默认值 |
| 对象→API | to_api_message() | 严格最小字段集 |

**往返一致性**：

```python
original = ChatMessage("user", "往返测试", created_at="2026-01-01T00:00:00Z")
restored = ChatMessage.from_dict(original.to_dict())
assert original == restored
```

---

## 第五章：MessageHistory 设计模式

### 5.1 容器模式

`MessageHistory` 是 **Collection** 的薄封装，类似 `list` 的专用版：

- 单一职责：只管理 `ChatMessage`
- 统一入口：`add()` 强制校验
- 导出适配：`to_api_messages()` 对接外部 API

### 5.2 与 list 对比

| 操作 | list[dict] | MessageHistory |
|------|------------|----------------|
| 追加 | append | add（带校验） |
| 导出 API | 手写推导 | to_api_messages() |
| 持久化 | 自己 json | save_json |

---

## 第六章：错误处理哲学

OOP 中常见两种风格：

1. **异常型**：`validate` 失败 `raise ValidationError`
2. **消息型**：`validate` 返回 `str | None`（本项目 CLI 阶段）

Day 10 引入自定义异常后，`ChatMessage.validate` 可能增加 `raise_on_error=True` 参数——今日先掌握消息型。

---

## 第七章：测试类的方法

```python
def test_roundtrip():
    msg = ChatMessage("assistant", "回复")
    assert ChatMessage.from_dict(msg.to_dict()) == msg

def test_api_format_no_extra_keys():
    api = ChatMessage("user", "x").to_api_message()
    assert set(api.keys()) == {"role", "content"}
```

测试类与测试函数相同，都用 pytest；类放在 `models`，测试放在 `tests/day08`。

---

## 第八章：常见面试题（预习）

1. `__str__` 和 `__repr__` 区别？  
   **答**：str 给用户，repr 给开发者调试。

2. 类方法 vs 静态方法？  
   **答**：类方法接收 cls，常用于工厂；静态方法与类逻辑相关但不访问类状态。

3. 组合和继承如何选择？  
   **答**：History **has-a** Message；Day 9 Message **is-a** BaseModel。

---

## 第九章：与 TypeScript / Java 对照

| 概念 | Python | TypeScript |
|------|--------|------------|
| 类 | class | class |
| 构造 | __init__ | constructor |
| 接口 | Protocol/ABC | interface |
| 属性 | self.x | this.x |

有 OOP 其他语言经验的同学可据此快速映射。

---

## 第十章：今日代码阅读顺序

1. `models/message.py` — 核心，逐行读
2. `day08/message_history.py` — 容器
3. `day08/oop_demos.py` — 小例子
4. `day08/message_cli.py` — 完整应用
5. `tests/day08/test_chat_message.py` — 行为规格

---

*本讲义约 3500 字，配合课堂笔记使用。*
