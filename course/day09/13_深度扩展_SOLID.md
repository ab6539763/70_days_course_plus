# Day 9 深度扩展：SOLID 与模型设计

## 单一职责（S）

每个模型类只描述一种业务实体：ChatMessage 不含 temperature。

## 开闭原则（O）

新增 `Tag` 模型：继承 BaseModel 即可加入 Registry，无需改 BaseModel 源码。

## 里氏替换（L）

凡接受 `BaseModel` 的函数，任意子类传入不应破坏逻辑。

## 接口隔离（I）

`to_api_message` 仅 ChatMessage 需要，不强行放进 BaseModel。

## 依赖倒置（D）

`ModelRegistry` 依赖抽象 `BaseModel`，不依赖具体 `ChatMessage`。

---

*企业开发常用 SOLID 指导类设计，今日实践 OCP 与 LSP。*
