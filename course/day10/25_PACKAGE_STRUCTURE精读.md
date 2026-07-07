# Day 10 PACKAGE_STRUCTURE 精读笔记

对照仓库根目录 `nexus-agent-platform/PACKAGE_STRUCTURE.md` 精读，约 2000 字。

---

## 一、生产层 vs 教学层

**生产层**：core, models, services, utils, llm, chat, tools — 平台长期演进代码。

**教学层**：day01-day70 — 按天课件配套实验，**保留不删**。

新同学常见误区：「day08 有了 MessageHistory，为何还要 services？」  
**答**：day08 是教材快照；services 是生产归宿；re-export 保兼容。

---

## 二、依赖方向详解

### 允许

- `day10.module_demos` → `core.bootstrap`  
- `services.message_history` → `models.message`  
- `models.llm_base` → `core.exceptions`  

### 禁止

- `core.exceptions` → `models.anything`  
- `models.message` → `services.anything`  
- `utils.json_utils` → `day05.anything`  

**口诀**：上层依赖下层，下层对上层无感知。

---

## 三、数据路径演进

当前 `PATHS` 仍指向 day05/day07/day08 数据目录，避免学员数据迁移阵痛。

**Phase 2**（Day 20+）：迁移至 `src/data/` 统一目录，PATHS 一键切换。

---

## 四、异常与 HTTP 映射表

| NexusError 子类 | 未来 HTTP |
|-----------------|-----------|
| ModelValidationError | 400 |
| JsonParseError | 400 |
| ConfigError | 500 |
| StorageError | 500 |
| ImportPathError | 500 |

---

## 五、骨架包何时填充

| 包 | 填充日 | 首个模块 |
|----|--------|----------|
| tools | 11 | doc_reader.py |
| llm | 12 | client.py |
| chat | 14 | cli_assistant.py |

今日 `__init__.py` 占位即可通过 structure_audit。

---

## 六、与团队 GIT 规范

包重组 commit message 示例：

```
refactor(core): add exception hierarchy and paths module

BREAKING CHANGE: none (re-exports preserve imports)
```

---

## 七、精读作业

打开 `PACKAGE_STRUCTURE.md`，在每项依赖规则旁手写一个本项目真实模块例子。

---

*架构师赵岩审定。*
