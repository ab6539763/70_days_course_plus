# Day 9 BaseModel 速查手册

## 一、导入

```python
from models import BaseModel, ChatMessage, Contact, ModelConfig, ModelValidationError
```

## 二、BaseModel API 完整表

| 方法/属性 | 类型 | 说明 |
|-----------|------|------|
| validate()* | 实例 | → err\|None |
| to_dict()* | 实例 | → dict |
| from_dict()* | 类方法 | → 子类实例 |
| is_valid() | 实例 | bool |
| ensure_valid() | 实例 | 失败 raise |
| to_json_ready() | 实例 | 校验后 dict |
| from_dict_safe() | 类方法 | → (obj\|None, err\|None) |
| model_type | 属性 | 类名 str |

## 三、子类字段速查

### ChatMessage
role, content, created_at | to_api_message()

### Contact  
id, name, phone, email, group | format_line()

### ModelConfig
model, temperature, max_tokens | to_api_params()

## 四、校验规则速查

| 类 | 关键规则 |
|----|----------|
| ChatMessage | role ∈ system/user/assistant；content 非空 |
| Contact | 姓名手机邮箱合法；id>0 |
| ModelConfig | model 非空；0≤temp≤2；max_tokens>0 |

## 五、命令

```bash
cd nexus-agent-platform
python3 src/day09/inheritance_demos.py
python3 src/day09/polymorphism_demo.py
python3 -m pytest tests/day09/ tests/day08/ -v
```

## 六、异常处理模板

```python
try:
    model.ensure_valid()
except ModelValidationError as e:
    print(f"校验失败: {e}")
```

## 七、多态遍历模板

```python
def dump_all(models: list[BaseModel]) -> None:
    for m in models:
        print(m.model_type, m.to_dict())
```

## 八、迁移对照

| 旧 import | 新 import |
|-----------|-----------|
| day08.contact_class.Contact | models.Contact |
| （无） | models.ModelConfig |

## 九、文件路径

| 文件 | 路径 |
|------|------|
| BaseModel | src/models/llm_base.py |
| ChatMessage | src/models/message.py |
| Contact | src/models/contact.py |
| ModelConfig | src/models/model_config.py |

## 十、Sprint 2 进度

Day 8 ChatMessage → **Day 9 BaseModel** → Day 10 包重组 → Day 12 API

---

*打印本页备查。*
