# chunk_config 与企业预设实践

## PRESET 参数表

| name | chunk_size | overlap | strategy | 适用场景 |
|------|------------|---------|----------|----------|
| compact | 120 | 20 | auto | 压力测试、长文档 |
| default | 200 | 40 | auto | 基线兼容 |
| wide | 400 | 60 | auto | 短章节 FAQ/产品说明 |
| markdown_wide | 500 | 50 | markdown | 结构化 Markdown 手册 |

## 企业命名规范

赵岩建议：

- `name` 最长 32 字符，写入 audit log  
- 禁止使用 `test1` 在生产 store  
- 自定义配置用 `{env}_{purpose}` 如 `prod_wide`  

## validate 陷阱

| 错误配置 | 后果 |
|----------|------|
| overlap ≥ size | validate 拒绝 |
| size < 50（API schema） | FastAPI 422 |
| strategy=invalid | validate 拒绝 |

## 与 API schema 双重校验

`ChunkConfigRequest` 用 Pydantic：`chunk_size` ge=50 le=2000。  
`ChunkConfig.validate()` 在业务层再次校验 strategy。

## 逐行走读 chunk_config.py

### `nexus-agent-platform/src/rag/chunk_config.py` 逐行走读

共 **50** 行。

**L1** `"""`
  → 模块 docstring：标明分块参数职责与需求编号 ZL-NA-REQ-027。

**L2** `分块参数配置 — chunk_size / overlap / strategy`

**L3** ``

**L4** `需求：ZL-NA-REQ-027`

**L5** `"""`

**L6** ``

**L7** `from __future__ import annotations`
  → 启用 future annotations，支持前向类型引用。

**L8** ``

**L9** `from dataclasses import asdict, dataclass, field`
  → 导入 asdict：ChunkConfig.to_dict 复用 dataclass 序列化。

**L10** `from typing import Any`

**L11** ``

**L12** ``

**L13** `@dataclass`
  → @dataclass 装饰器：自动生成 __init__ 与字段比较。

**L14** `class ChunkConfig:`
  → ChunkConfig 是 Day 27 核心值对象，贯穿 store / API / eval。

**L15** `    """知识库分块参数（可持久化、可 A/B 对比）"""`

**L16** ``

**L17** `    chunk_size: int = 200`
  → chunk_size 默认 200，与 Day 19 基线一致，便于对比实验。

**L18** `    overlap: int = 40`
  → overlap 默认 40，约为 size 的 20%，经验比例。

**L19** `    strategy: str = "auto"  # auto | fixed | markdown`
  → strategy 控制 chunk_from_parsed 的分发逻辑。

**L20** `    name: str = "default"`
  → name 用于 PRESET 标识与审计日志，非文件名。

**L21** ``

**L22** `    def validate(self) -> None:`
  → validate 在 API 与 store.set_chunk_config 前必须调用。

**L23** `        if self.chunk_size <= 0:`
  → chunk_size 必须正整数，零或负数无意义。

**L24** `            raise ValueError("chunk_size 必须为正整数")`

**L25** `        if self.overlap < 0 or self.overlap >= self.chunk_size:`
  → overlap 上界严格小于 chunk_size，防止整块重复滑动。

**L26** `            raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")`

**L27** `        if self.strategy not in ("auto", "fixed", "markdown"):`
  → strategy 白名单：auto / fixed / markdown 三者之一。

**L28** `            raise ValueError("strategy 须为 auto / fixed / markdown")`

**L29** ``

**L30** `    def to_dict(self) -> dict[str, Any]:`
  → to_dict 供 store.json 与 EvaluateResponse 序列化。

**L31** `        return asdict(self)`

**L32** ``

**L33** `    @classmethod`

**L34** `    def from_dict(cls, data: dict[str, Any]) -> ChunkConfig:`
  → from_dict 容忍缺失键，使用默认值，利于旧 store 迁移。

**L35** `        return cls(`

**L36** `            chunk_size=int(data.get("chunk_size", 200)),`

**L37** `            overlap=int(data.get("overlap", 40)),`

**L38** `            strategy=str(data.get("strategy", "auto")),`

**L39** `            name=str(data.get("name", "default")),`

**L40** `        )`

**L41** ``

**L42** ``

**L43** `DEFAULT_CHUNK_CONFIG = ChunkConfig()`
  → DEFAULT_CHUNK_CONFIG 单例语义：未配置时的回退。

**L44** ``

**L45** `PRESET_CONFIGS: tuple[ChunkConfig, ...] = (`
  → PRESET_CONFIGS 元组不可变，防止课堂演示中被意外修改。

**L46** `    ChunkConfig(name="compact", chunk_size=120, overlap=20, strategy="auto"),`
  → compact：小块压力测试，通常 chunk_count 最多。

**L47** `    ChunkConfig(name="default", chunk_size=200, overlap=40, strategy="auto"),`
  → default：生产基线 PRESET。

**L48** `    ChunkConfig(name="wide", chunk_size=400, overlap=60, strategy="auto"),`
  → wide：理财短章节文档推荐，hit_rate 常最高。

**L49** `    ChunkConfig(name="markdown_wide", chunk_size=500, overlap=50, strategy="markdown"),`
  → markdown_wide：强制 markdown 策略，适合结构化手册。

**L50** `)`


## 实践 Lab 片段

```python
from rag.chunk_config import ChunkConfig, PRESET_CONFIGS

for p in PRESET_CONFIGS:
    p.validate()
    print(p.name, p.chunk_size)
```

## 选型决策树

```
文档是否 Markdown 且章节清晰？
  ├─ 是 → 试 markdown_wide + wide
  └─ 否 → 试 default + wide
hit_rate 达标？
  ├─ 否 → 增 size 或改 strategy
  └─ 是 → 比较 chunk_count → PUT → Day 28 rebuild
```

## 企业预设扩展讨论

**陈默**：PRESET 不是越多越好。每增一套，CI 的 evaluate 时间就线性增长。  
**林晓**：建议生产环境 3–5 套，用 `name` 区分环境：`staging_wide`、`prod_wide`。  
**赵岩**：变更 PRESET 默认值需走变更评审，因为 `apply_best_config`（Day 28）会直接采纳 evaluate 排序。
