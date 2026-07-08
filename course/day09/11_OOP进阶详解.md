# Day 9 OOP 进阶详解（扩展讲义）

本讲义系统梳理继承、抽象类与 NexusAgent 模型体系。

---

## 第一章：继承的内存模型

创建 `ChatMessage("user", "hi")` 时，Python 分配实例字典，存储 role/content/created_at。方法查找走 **MRO**：

```python
ChatMessage.__mro__
# (ChatMessage, BaseModel, ABC, object)
```

`msg.is_valid()` 在 ChatMessage 未找到时，沿 MRO 在 BaseModel 找到。

---

## 第二章：抽象类 vs 普通父类

| 特性 | 普通父类 | ABC |
|------|----------|-----|
| 能否实例化 | 能 | 抽象类本身不能 |
| 未实现方法 | 运行时报错 | 实例化时 TypeError |
| 用途 | 代码复用 | 定义接口契约 |

```python
class Incomplete(BaseModel):
    def validate(self): return None
    def to_dict(self): return {}
    # 缺少 from_dict — 仍无法实例化
```

---

## 第三章：里氏替换原则（LSP）

子类对象应能替换父类对象而不破坏程序。

```python
def persist(model: BaseModel, path: Path) -> None:
    save_json(path, model.to_json_ready())
```

`ChatMessage`、`Contact`、`ModelConfig` 均可传入。若子类 `to_dict` 返回不可 JSON 化对象，则违反 LSP。

---

## 第四章：接口统一的三件套

| 方法 | 职责 | ChatMessage 示例 |
|------|------|------------------|
| validate | 业务规则 | role 合法、content 非空 |
| to_dict | 出站序列化 | 含 created_at |
| from_dict | 入站反序列化 | 容忍缺字段 |

Pydantic 的 `model_validate` / `model_dump` 是工业级实现；今日为手工版以理解原理。

---

## 第五章：ensure_valid vs from_dict_safe

| 场景 | 推荐 API | 原因 |
|------|----------|------|
| 服务层写库 | ensure_valid | 快速失败 |
| CLI 交互 | from_dict_safe | 打印友好 |
| 批量导入 | from_dict_safe 逐条 | 收集全部错误 |
| HTTP API Day23 | ensure_valid → 400 | 统一错误响应 |

---

## 第六章：开闭原则实战

新增 `Tag(BaseModel)` 时：

- ✅ 继承 BaseModel，实现三方法，加入 Registry
- ❌ 修改 BaseModel 源码加 tag 字段
- ❌ 在 Registry 写 `if isinstance(m, Tag)`

**对扩展开放，对修改关闭。**

---

## 第七章：ModelConfig 深度说明

### 7.1 temperature 语义

- 0.0 — 确定性高，适合分类、抽取
- 0.7 — 默认，平衡创意与稳定
- 1.5+ — 创意写作，风险幻觉增加

### 7.2 max_tokens 与计费

`max_tokens` 限制**生成** token 数，非输入。Day 15 token 计算器将关联此字段。

### 7.3 与配置文件

```yaml
# 未来 config.yaml
llm:
  model: deepseek-chat
  temperature: 0.7
  max_tokens: 2048
```

Day 11 文件读取后 `ModelConfig.from_dict(yaml_dict["llm"])`。

---

## 第八章：多态在 Python 中的实现

Python **鸭子类型**：不强制继承，只要有 validate 方法即可调用。但我们**显式继承 BaseModel** 以获得：

1. ABC 强制实现
2. isinstance 检查
3. 团队代码规范统一

---

## 第九章：测试策略

| 层级 | 测什么 |
|------|--------|
| 子类 | 特有 validate 规则 |
| BaseModel | ensure_valid、from_dict_safe |
| 集成 | Registry + 多子类混合 |
| 回归 | Day 8 ChatMessage 测试仍绿 |

---

## 第十章：自测题与答案

1. 抽象类能否有具体方法？**能**  
2. 为何 from_dict 是类方法？**各子类字段不同，多态构造**  
3. ModelRegistry 为何用 BaseModel 类型？**开闭原则 + 多态**  
4. ModelValidationError 父类？**ValueError**  
5. Contact 迁 models 的好处？**统一模型包，与 ChatMessage 并列**  

---

*本讲义约 2200 字，配合课堂笔记使用。*
