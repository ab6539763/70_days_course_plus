# Day 10 Sprint 2 阶段回顾（Day 8-10）

Sprint 2 前三天完成 OOP 与架构整理，本文档串联三日产出，约 3500 字。

---

## Day 8：ChatMessage 类

**核心**：从 dict 升级到 class，数据与行为封装。

| 产出 | 路径 |
|------|------|
| ChatMessage | models/message.py |
| MessageHistory | day08（后迁 services） |
| message_cli | day08 |

**关键方法**：validate, to_dict, from_dict, to_api_message

---

## Day 9：BaseModel 抽象体系

**核心**：为所有模型立法，抽象方法强制实现。

| 产出 | 路径 |
|------|------|
| BaseModel | models/llm_base.py |
| ModelConfig | models/model_config.py |
| Contact | models/contact.py |
| ModelRegistry | day09 演示 |

**关键方法**：ensure_valid, from_dict_safe, is_valid

---

## Day 10：包结构重组

**核心**：分层目录 + 统一异常 + 服务层。

| 产出 | 路径 |
|------|------|
| NexusError 体系 | core/exceptions.py |
| 路径注册 | core/paths.py |
| bootstrap | core/bootstrap.py |
| MessageHistoryService | services/ |
| 骨架包 | llm, chat, tools |

---

## 三日后架构图

```
应用(dayXX/chat/llm)
        ↓
    services
        ↓
     models
        ↓
   core + utils
```

---

## 代码量与测试

| Day | 新增测试约 | 累计 pytest |
|-----|------------|-------------|
| 8 | 13 | 87 |
| 9 | 11 | 98 |
| 10 | 10 | 108 |

---

## 常见面试题串联

1. dict 和 class 区别？— Day 8  
2. 抽象类作用？— Day 9  
3. 如何组织 Python 项目目录？— Day 10  
4. 自定义异常为何分层？— Day 10  

---

## 明日 Day 11 预告

**文件与标准库**：`pathlib`、`glob`、批量读取企业文档，产出 `tools/doc_reader.py`。为 Day 28 RAG 文档处理铺路。

---

## 自查清单

- [ ] 能默写 BaseModel 三个抽象方法  
- [ ] 能说出 core/models/services 职责  
- [ ] 能运行 structure_audit 并解释输出  
- [ ] 能捕获 ModelValidationError 并读取 code  

---

*Sprint 2 继续：Day 11-14 对话能力冲刺。*
