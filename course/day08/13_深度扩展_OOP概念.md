# Day 8 深度扩展：OOP 核心概念

## 封装

隐藏内部实现，对外暴露接口。`MessageHistory._messages` 是「私有约定」（单下划线），外部应通过 `add()` 修改。

## 继承（Day 9 预告）

```python
class BaseModel(ABC):
    @abstractmethod
    def validate(self) -> str | None: ...

class ChatMessage(BaseModel):
    def validate(self) -> str | None:
        ...
```

## 多态

同一接口 `validate()`，不同类有不同实现。Agent 工具返回统一「可校验对象」。

## 组合优于继承

`MessageHistory` **包含**多个 `ChatMessage`（has-a），而非继承 ChatMessage（is-a）。

## dataclass 对比

```python
from dataclasses import dataclass

@dataclass
class SimpleMessage:
    role: str
    content: str
```

`dataclass` 自动生成 `__init__`；企业项目常在此基础上加 `validate`。Day 9 讨论选型。

## 与 JSON Schema

`to_dict` / `from_dict` 是轻量序列化；大型项目可用 JSON Schema 或 Pydantic 校验。NexusAgent Day 23 引入 Pydantic。

---

*延伸阅读：Python data model — Special method names*
