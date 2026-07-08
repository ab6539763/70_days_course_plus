#!/usr/bin/env python3
"""Gold-standard course materials for Day 28 — knowledge base full rebuild."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from course_builder import fenced, read_repo, write_course  # noqa: E402

_REPO = "nexus-agent-platform/src"


def _src(rel: str, *, limit: int | None = None) -> str:
    return read_repo(f"{_REPO}/{rel}", limit=limit)


def _line_commentary(path: str, notes: dict[int, str]) -> str:
    lines = read_repo(path).splitlines()
    parts = [f"### `{path}` 逐行走读\n", f"共 **{len(lines)}** 行。\n"]
    for i, line in enumerate(lines, 1):
        parts.append(f"**L{i}** `{line}`")
        if note := notes.get(i):
            parts.append(f"  → {note}")
        parts.append("")
    return "\n".join(parts)


def _knowledge_rebuild_line_notes() -> dict[int, str]:
    return {
        1: "模块 docstring：全量重建，需求 ZL-NA-REQ-028。",
        14: "get_path：统一路径解析，sample_docs 与 uploads 位置由 core.paths 管理。",
        24: "RebuildReport：API 与 CLI 共用的重建报告 dataclass。",
        52: "collect_source_files：双源扫描入口，测试可注入临时目录。",
        61: "uploads 优先覆盖 sample 的注释，业务语义核心。",
        63: "uploads 默认路径：运营上传目录。",
        64: "sample 默认路径：教学样例目录。",
        67: "include_sample_docs=false 时仅扫 uploads，运维场景。",
        79: "sorted(by_name) 保证跨机器确定性。",
        82: "rebuild_store：清空后全量重建主函数。",
        94: "快照 before 计数，写入 RebuildReport 供 UI 展示。",
        96: "使用 store 当前 chunk_config，而非全局常量。",
        104: "clear documents/chunks：破坏性操作，生产需备份。",
        106: "invalidate_cache：防止 DocumentIndex 持有旧 chunk 引用。",
        108: "逐文件循环：与 upload 单文件 ingest 不同，这是批处理。",
        109: "parse_bytes 复用 Day 26 解析层。",
        111: "空文本跳过，避免空文档。",
        118: "chunk_from_parsed 使用 store 配置四参数。",
        125: "_append_chunks 内部方法：写入 documents 与 chunks 列表。",
        132: "_rebuild_index：重建 TF-IDF + Chroma（Day 29+）。",
        133: "UTC 时间戳，ISO8601 格式，写入 last_rebuilt_at。",
        146: "store.last_rebuilt_at 持久化字段，status API 暴露。",
        151: "rebuild_with_best_config：evaluate + rebuild 编排。",
        158: "延迟 import Day 27 模块，避免 import 环。",
        164: "run_ab_experiment 在 product_notice 上选最优 PRESET。",
        167: "set_chunk_config 后立刻 rebuild_store 完成发布。",
    }

def _readme() -> str:
    return """# Day 28 课件索引

**日期**：2026-08-04（星期二）  
**主题**：知识库全量重建（rebuild）  
**需求**：ZL-NA-REQ-028  
**版本**：v0.28.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| 重建核心 | `rag/knowledge_rebuild.py` | collect_source_files / rebuild_store |
| 最优配置发布 | `rebuild_with_best_config` | evaluate + rebuild 一键 |
| API | `POST /api/knowledge/rebuild` | 全量重建入口 |
| 状态字段 | `last_rebuilt_at` | store.json 审计时间戳 |
| 前端 | `frontend/knowledge.js` | `#kb-rebuild-btn` |
| 测试 | `tests/day28/` | 14 项 |

## 关键设计决策

1. **双源扫描**：`sample_docs` 开箱即用 + `knowledge_uploads` 运营文档。  
2. **uploads 优先**：同名文件 uploads 覆盖 sample。  
3. **清空重建**：`documents.clear()` + `chunks.clear()` 后逐文件 parse+chunk。  
4. **apply_best_config**：先 `run_ab_experiment` 再 `set_chunk_config` 再 rebuild。  
5. **sessions_cleared**：重建后 `session_manager.clear_all()`，编排器用新索引。

## 验收命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day28/rebuild_demo.py
python3 src/day28/rebuild_api_demo.py
pytest tests/day28/ -q
```

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_知识库重建详解 | 重建专题 |
| 15_授课实录 | 发布夜实录 |
| 22_knowledge_rebuild精读 | 源码走读 |
| 23_双源扫描与覆盖策略 | uploads 优先 |
| 26_实操Lab手册 | 六步发布实验 |
| 27_Day29向量库预习 | Chroma 预告 |

**生成器**：`scripts/course_days/day28.py`（gold-standard）

**运行生成**：`python3 scripts/course_days/day28.py` → 写入 `course/day28/`（30 文件，≥110k 字符）

**前置课程**：Day 27 分块调优与 `POST /api/knowledge/evaluate` 已完成。
"""


def _narration() -> str:
    return """# Day 28 旁白解读

2026 年 8 月 4 日，星期二。林晓把 Day 27 的评估报告贴在显示器边：**wide, hit_rate=100%**。她点开知识库状态页，`chunk_count` 仍是 12。

陈默路过：「调参是实验，重建是发布。你改了默认配置，旧块还在仓库里睡觉。」

上午十点，`rebuild_demo.py` 跑通。终端打印：

```
重建前: 3 篇 / 12 块
配置: size=400 overlap=60
重建后: 3 篇 / 8 块
```

赵岩：「块数下降，说明全库按 wide 重新切了。看 `last_rebuilt_at`，这就是运维要的审计点。」

下午投资人演示彩排。周航点击「全量重建」，勾选 `apply_best_config`。API 先 evaluate 四套 PRESET，自动 `set_chunk_config(wide)`，再 `rebuild_store`。聊天接口立刻引用新块。

```mermaid
journey
    title Day 28 发布旅程
    section 上午
      collect_source_files: 5: 林晓
      rebuild_store 走读: 5: 林晓
    section 下午
      apply_best_config: 5: 林晓
      浏览器 rebuild 按钮: 4: 周航
```

**旁白**：Day 27 回答「块要多大」，Day 28 让整个库**统一到答案上**。

---

## 场景还原：投资人演示前 30 分钟

周航检查清单口述版：

1. `GET /api/knowledge/status` — `chunk_config.name` 是否目标 PRESET  
2. `POST /api/knowledge/evaluate` — 截图 `best_config` 与 `hit_rate`  
3. `POST /api/knowledge/rebuild` — `apply_best_config=true` 或手动 PUT 后 rebuild  
4. 确认 `last_rebuilt_at` 为今日 UTC  
5. 浏览器无痕窗口新开 chat，问「赎回多久到账」  

林晓补充：「第 5 步必须用新 session，否则陈默会当场抓旧上下文 bug。」

赵岩记录：发布决策不只技术，还有**审计时间戳**——`last_rebuilt_at` 是合规部第一周就会问的字段。

## 技术名词对照（中英）

| 中文 | English | Day 28 对应 |
|------|---------|-------------|
| 全量重建 | full rebuild | rebuild_store |
| 源文件扫描 | source collection | collect_source_files |
| 双源覆盖 | upload override | uploads 优先 |
| 评估驱动发布 | eval-driven release | apply_best_config |
| 审计时间 | audit timestamp | last_rebuilt_at |

## 课后一分钟

陈默：「记住三个词——**清、扫、建**。清了旧块，扫了源文件，建了新的索引。明天 Chroma 换引擎，这三个词不变。」

林晓在笔记本写下：`evaluate = 实验`，`rebuild = 发布`，`last_rebuilt_at = 审计`。周航补上第四行：`sessions_cleared = 用户重新对话`。

赵岩最后补充：「投资人问『你们知识库什么时候更新的』，别答『昨天调了参数』——答 `last_rebuilt_at` 里的 UTC 时间，并说明已与评估实验一致。」

旁白收束：Day 28 结束，知识库从「能调参」走向「能发布」。下一课，向量引擎换壳，流程不换。
"""


def _enterprise_bg() -> str:
    return """# Day 28 企业背景与今日任务

## 业务背景

Day 27 评估表明 `wide` 配置在 `product_notice.md` 上 hit_rate 优于 `default`。但生产 `store.json` 中的 chunks 仍按旧参数生成，客服助手检索行为未变。

运营部要求：

- 一键将全库切换到评估优选配置；  
- 合并 sample 与 uploads 全部源文件；  
- 记录最近重建时间供合规审计；  
- 重建后清理会话，避免旧上下文干扰。

## 今日任务

| 序号 | 任务 | 产出 |
|------|------|------|
| T1 | 源文件收集与覆盖策略 | `collect_source_files` |
| T2 | 全量重建主流程 | `rebuild_store` |
| T3 | evaluate + rebuild 编排 | `rebuild_with_best_config` |
| T4 | POST /api/knowledge/rebuild | `api/knowledge.py` |
| T5 | `last_rebuilt_at` 持久化 | `KnowledgeStore` |
| T6 | 前端重建按钮 | `frontend/knowledge.js` |
| T7 | 测试与演示 | `tests/day28/` |

## 验收

- `rebuild` 后 `chunks_after` 反映新配置；  
- `status.last_rebuilt_at` 非空；  
- uploads 同名覆盖 sample 有测试覆盖；  
- `apply_best_config=true` 端到端成功。

## 与 Day 27 关系

| 操作 | 作用域 | 写库 |
|------|--------|------|
| evaluate | 样例文档模拟 | 否 |
| PUT chunk-config | 默认参数 | 是（配置字段） |
| rebuild | 全库源文件 | 是（documents/chunks） |

---

## 干系人沟通话术

**对产品**：「evaluate 是实验报告，rebuild 才是上线按钮。」  
**对运维**：「发布前备份 store.json，发布后看 last_rebuilt_at。」  
**对客服**：「重建后请用户新开对话，旧会话可能引用旧知识。」  
**对合规**：「留存 evaluate JSON 与 rebuild 响应，含 source_files 列表。」

## 今日里程碑检查

- [ ] `rebuild_demo.py` 本地跑通  
- [ ] `rebuild_api_demo.py` 打印 chunks 变化  
- [ ] `pytest tests/day28/ -q` 全绿  
- [ ] 能口述双源覆盖规则  
- [ ] 能解释 apply_best_config 与 Day 27 关系  
"""


def _requirements() -> str:
    return """# ZL-NA-REQ-028 需求文档

**版本**：v0.28.0  
**优先级**：P0

## FR-001 源文件收集

- 扫描 `sample_docs/*.{txt,md,pdf}`（可 `include_sample_docs=false` 跳过）  
- 扫描 `knowledge_uploads/*` 同扩展名  
- **同名**：uploads 覆盖 sample  
- 返回排序后的 `list[Path]`

## FR-002 rebuild_store

1. 记录 `documents_before` / `chunks_before`  
2. 读取 `store.get_chunk_config()`  
3. `documents.clear()`、`chunks.clear()`、`invalidate_cache()`  
4. 逐源文件：`parse_bytes` → `clean_text` → `chunk_from_parsed` → `_append_chunks`  
5. `_rebuild_index()`  
6. 设置 `last_rebuilt_at`（UTC ISO8601）  
7. `save()`，返回 `RebuildReport`

## FR-003 API

`POST /api/knowledge/rebuild`

```json
{
  "include_sample_docs": true,
  "apply_best_config": false
}
```

响应含 `chunks_before/after`、`source_files`、`rebuilt_at`、`sessions_cleared`。

## FR-004 apply_best_config

为 true 时：

1. 对 `product_notice.md` 运行 `run_ab_experiment`  
2. `pick_best_config` → `store.set_chunk_config`  
3. 调用 `rebuild_store`

## FR-005 会话

重建成功后 `session_manager.clear_all()`。

## 非目标

- 单文档增量重建（Day 30 incremental）  
- 异步任务队列 / 进度条  
- 重建期间只读副本（教学单进程）
"""


def _requirements_ext() -> str:
    return """# ZL-NA-REQ-028 需求文档（扩展）

## 用户故事

### US-028-01 运维发布

**作为** 运维工程师  
**我希望** 调用 rebuild API  
**以便** 全库分块与当前 chunk_config 一致  
**验收**：`chunks_after` > 0，`last_rebuilt_at` 更新

### US-028-02 产品一键发布

**作为** 产品经理  
**我希望** `apply_best_config=true`  
**以便** 无需手动 PUT 评估最优配置  
**验收**：重建后 `chunk_config.name` 与 evaluate 一致

### US-028-03 QA 覆盖策略

**作为** QA  
**我希望** uploads 同名文件覆盖 sample  
**验收**：`test_collect_sources_uploads_override` 通过

## RebuildReport 字段

| 字段 | 说明 |
|------|------|
| documents_before/after | 文档篇数变化 |
| chunks_before/after | 块数变化 |
| sources_processed | 处理的源文件数 |
| chunk_config | 重建使用的配置快照 |
| source_files | 文件名列表 |
| rebuilt_at | UTC 时间戳 |
| message | 人类可读摘要 |

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 重建中查询不一致 | 教学环境可接受；生产加维护窗口 |
| 空 uploads 且 skip sample | 可能清空库 —— 测试需警示 |
| 大文件重建慢 | 500KB 上传上限仍适用 |

## 验收用例（Gherkin 风格）

```gherkin
Scenario: 标准全量重建
  Given 知识库已从 sample_docs bootstrap
  When POST /api/knowledge/rebuild with include_sample_docs=true
  Then 响应 chunks_after > 0
  And GET /status 的 last_rebuilt_at 非空

Scenario: uploads 覆盖 sample
  Given uploads 与 sample 存在同名 doc.txt 且内容不同
  When collect_source_files 被调用
  Then 返回路径内容为 uploads 版本

Scenario: apply_best_config 发布
  Given product_notice.md 存在
  When POST /rebuild apply_best_config=true
  Then chunk_config.name 等于 evaluate 最优 PRESET
  And sessions_cleared >= 0
```

## 与 Day 27 联合验收

1. 先 `POST /evaluate` 存档 `best_config`  
2. 再 `POST /rebuild` 带 `apply_best_config`  
3. 对比两次 `chunk_config` 一致  
4. spot-check 四条 EVAL 问句 chat  

## 数据保留策略

- evaluate JSON：保留 90 天  
- rebuild 响应：永久归档  
- store.json.bak：至少保留 7 天  
"""


def _architecture() -> str:
    rebuild = _src("rag/knowledge_rebuild.py", limit=45)
    return f"""# Day 28 架构设计

**需求**：ZL-NA-REQ-028

## 组件图

```
POST /rebuild
    │
    ├─ apply_best_config?
    │     └─ rebuild_with_best_config
    │           ├─ run_ab_experiment (Day 27)
    │           ├─ set_chunk_config
    │           └─ rebuild_store
    │
    └─ rebuild_store
          ├─ collect_source_files
          ├─ clear documents/chunks
          ├─ parse_bytes + chunk_from_parsed
          ├─ _rebuild_index (TF-IDF + Chroma)
          ├─ last_rebuilt_at
          └─ save
    │
    └─ session_manager.clear_all()
```

## 与 ingestion 层关系

Day 25 `ingest_upload` 处理**单文件增量**。Day 28 `rebuild_store` 是**批处理编排**，复用相同 parse/chunk 原语，但先清空索引。

## 核心源码（文件头 + RebuildReport）

{fenced("python", rebuild)}

完整 `rebuild_store` 实现见 `22_knowledge_rebuild精读.md`。

## 数据流

```
sample_docs ──┐
              ├──► by_name (uploads wins) ──► sorted paths
uploads ──────┘
                    │
                    ▼
              parse_bytes → ParsedDocument
                    │
                    ▼
              chunk_from_parsed(cfg)
                    │
                    ▼
              store._append_chunks
                    │
                    ▼
              _rebuild_index → save
```

## 状态字段

`KnowledgeStore.last_rebuilt_at` 写入 `store.json`，`status_dict` 对外暴露。
"""


def _flowcharts() -> str:
    return """# Day 28 流程图与示意图

## rebuild 时序

```mermaid
sequenceDiagram
    participant C as Client
    participant API as POST /rebuild
    participant KR as knowledge_rebuild
    participant KS as KnowledgeStore
    participant SM as session_manager

    C->>API: apply_best_config=true
    API->>KR: rebuild_with_best_config
    KR->>KR: run_ab_experiment → set_chunk_config
    KR->>KS: documents/chunks clear
    loop each source file
        KR->>KR: parse_bytes + chunk
        KR->>KS: _append_chunks
    end
    KR->>KS: _rebuild_index + save
    KR-->>API: RebuildReport
    API->>SM: clear_all()
    API-->>C: chunks_before/after, rebuilt_at
```

## 双源覆盖决策

```mermaid
flowchart LR
    S[sample_docs/doc.txt] --> M{{by_name}}
    U[uploads/doc.txt] --> M
    M -->|uploads 存在| W[选用 uploads]
    M -->|仅 sample| X[选用 sample]
```

## Day 27 → Day 28 发布流水线

```
evaluate → 人工确认 best_config
    ↓
方案 A: PUT chunk-config → POST rebuild (apply_best_config=false)
方案 B: POST rebuild (apply_best_config=true)
    ↓
spot-check EVAL_QUERIES + /api/chat
```

## 块数变化示意

| 阶段 | chunk_size | 典型 chunk_count |
|------|------------|------------------|
| 重建前 default | 200 | 12 |
| 重建后 wide | 400 | 8 |

*以 `rebuild_demo.py` 本地输出为准。*
"""


def _notes_am() -> str:
    return """# Day 28 课堂笔记（上午）

**讲师**：陈默  
**记录**：林晓

## 09:00 发布 vs 实验

复习 Day 27：evaluate 不写库。今日问题：**如何让已入库文档用新配置？**  
答案：只能重扫**源文件**，因为原始全文不在 store 里（仅存 chunks）。

## 09:30 collect_source_files 逻辑口述

陈默板书三步：

1. 建 `by_name: dict[str, Path]`  
2. 若 `include_sample_docs`：glob sample，按文件名填入  
3. glob uploads，**同名覆盖** sample  
4. `return sorted(by_name.values())`  

林晓提问：为何不用 list 直接拼接？  
答：字典覆盖语义清晰，且 sorted 保证 CI 确定性。

## 10:30 rebuild_store 七步

1. 快照 `documents_before` / `chunks_before`  
2. `cfg = store.get_chunk_config()` — 重建用的是**当前 store 配置**，不是环境变量  
3. `collect_source_files(...)`  
4. `documents.clear()`、`chunks.clear()`、`invalidate_cache()`  
5. 对每个 path：`parse_bytes` → `clean_text` → `chunk_from_parsed` → `_append_chunks`  
6. `store._rebuild_index()` — Day 29 起内部含 Chroma reset  
7. 写 `last_rebuilt_at`（UTC）、`save()`、构造 `RebuildReport`  

## 11:00 空文件与跳过策略

`plain_text.strip()` 为空则 `continue`，避免空文档占位导致 document_count 虚高。

## 11:30 clean_text 一致性

赵岩强调：rebuild 路径必须与 `ingest_upload` 使用相同清洗逻辑，否则「上传能搜到、重建后搜不到」的诡异 bug。

## 11:50 课堂演示观察点

运行 `rebuild_demo.py` 前先用 `set_chunk_config(wide)`，块数变化更明显（12→8 典型）。

## 金句

「rebuild 不是调参，是**运维发布**；发布完要看 last_rebuilt_at。」
"""


def _notes_pm() -> str:
    return """# Day 28 课堂笔记（下午）

**讲师**：陈默、周航

## 14:00 rebuild API 口述

`POST /api/knowledge/rebuild` 处理函数 `rebuild_knowledge_base`：

- `body = body or RebuildRequest()`  
- `apply_best_config` 为 true → `rebuild_with_best_config`（内部 Day 27 evaluate）  
- 否则 → `rebuild_store`  
- 成功后 `session_manager.clear_all()`  
- 返回 `RebuildResponse`，附加 `sessions_cleared`  

源码粘贴见 `20_完整代码走查.md`，此处不重复。

## 14:40 sessions_cleared

重建后 `session_manager.clear_all()`，返回清除数量。原因：旧 session 的 RAG 上下文引用旧 chunk 边界。

## 15:10 前端 #kb-rebuild-btn

`runRebuild(applyBest)` 调用 POST，展示：

- chunks N → M  
- source_files 列表  
- rebuilt_at  

## 15:40 apply_best_config 演示

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"include_sample_docs":true,"apply_best_config":true}' | jq .
```

观察 `chunk_config.name` 是否为 evaluate 最优。

## 16:00 投资人彩排 checklist

- [ ] evaluate 截图存档  
- [ ] rebuild 前后 chunk_count  
- [ ] 三条 chat 抽测  
- [ ] last_rebuilt_at 截图  

## 答疑

**Q**：rebuild 会删 uploads 目录吗？  
**A**：不会，只读源文件，重写 store.json 索引。

**Q**：能否只重建 uploads？  
**A**：`include_sample_docs=false` 且指定 `uploads_dir`（测试用）。
"""


def _evening() -> str:
    return """# Day 28 晚自习

## 任务 A：运行 rebuild_demo（30 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 src/day28/rebuild_demo.py
```

记录：重建前块数 ___，重建后块数 ___，`rebuilt_at` ___。

## 任务 B：阅读 store.json（20 分钟）

重建前后对比 `chunk_config`、`last_rebuilt_at`、`chunks` 数组长度。

## 任务 C：uploads 覆盖实验（40 分钟）

1. 在 `data/knowledge/uploads/` 放入与 sample 同名的 `raw_faq.txt`  
2. 修改首行内容为「上传覆盖测试」  
3. rebuild  
4. 检索验证 top 块含覆盖内容  

## 任务 D：pytest（20 分钟）

```bash
pytest tests/day28/test_knowledge_rebuild.py -v
```

## 预习 Day 29

阅读 `27_Day29向量库预习.md`：rebuild 后 Chroma 向量如何更新？（提示：`_rebuild_index`）

## 任务 E：运维台账模板（30 分钟）

填写下表并提交：

| 字段 | 你的记录 |
|------|----------|
| evaluate 时间 | |
| best_config.name | |
| rebuild 前 chunk_count | |
| rebuild 后 chunk_count | |
| last_rebuilt_at | |
| source_files | |
| chat 抽测 1/2/3 结果 | |
| 操作者 | |

## 任务 F：故障注入（20 分钟）

1. 将 store.json 临时改名  
2. 调用 rebuild，观察错误  
3. 恢复备份，再次 rebuild 成功  
4. 写 100 字事故报告  
"""


def _homework() -> str:
    return """# Day 28 作业（graded）

**总分**：100 分

## 题目一：重建报告（30 分）

运行 `rebuild_api_demo.py` 与一次手动 curl rebuild，合并为 `rebuild_report.md`，包含：

- `chunks_before` / `chunks_after`  
- `source_files` 完整列表  
- `chunk_config` 快照  
- `sessions_cleared`  

**评分**：数据完整 15 分；格式清晰 15 分。

## 题目二：apply_best_config 对比（25 分）

分别执行：

1. `apply_best_config: false`（事先手动 PUT wide）  
2. `apply_best_config: true`  

对比两次 `chunk_config.name` 与 `chunks_after` 是否一致。500 字分析。

## 题目三：测试补充（25 分）

新增 `tests/day28/test_homework_rebuild.py`：

- `test_rebuild_empty_uploads_skip_sample`：`include_sample_docs=false` 且空 uploads 时行为记录（允许 0 文档，须断言 report）  
- `test_last_rebuilt_at_monotonic`：连续两次 rebuild，`last_rebuilt_at` 字符串不递减（按时间解析）

## 题目四：简答（20 分）

1. （8 分）为何 rebuild 必须清空 chunks 而非原地改 size？  
2. （6 分）uploads 优先覆盖的业务含义？  
3. （6 分）rebuild 与 Day 30 incremental upload 的区别？

## 加分（+10）

绘制运维 runbook：evaluate → 审批 → rebuild → chat 抽测（一页 PDF）。
""" + "\n\n---\n\n" + _tutor_supplement_day28()


def _homework_answers() -> str:
    return """# Day 28 作业参考答案

## 题目一

范例片段：

```markdown
## Rebuild 执行记录
- chunks: 12 → 8
- sources: ["raw_faq.txt", "product_notice.md", ...]
- rebuilt_at: 2026-08-04T10:30:00Z
- sessions_cleared: 2
```

## 题目二

两次 `chunk_config.name` 应均为 evaluate 最优（通常 wide）。`chunks_after` 应接近；若不同，检查第一次 PUT 前是否已 rebuild。

## 题目三参考

```python
def test_last_rebuilt_at_monotonic(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
    rebuild_store(store)
    t1 = store.last_rebuilt_at
    rebuild_store(store)
    t2 = store.last_rebuilt_at
    assert t2 >= t1
```

## 题目四

1. chunk 边界依赖 size/overlap/strategy，原地改参无法保证旧块文本边界合法，必须重 parse 源文件。  
2. 运营上传的是线上权威版本，应覆盖内置样例避免演示数据误导。  
3. rebuild 全量清空重扫；incremental 仅 upsert 新文档 chunk，不 clear 全库。

---

## 教师评分 rubric（详细）

### 题目一（30 分）

| 分项 | 满分 | 要点 |
|------|------|------|
| rebuild_report.md 存在 | 5 | 文件名正确 |
| chunks 前后 | 8 | 数字与 API 一致 |
| source_files 列表 | 7 | 不遗漏 uploads |
| sessions_cleared | 5 | 有记录 |
| 排版可读 | 5 | 标题分级 |

### 题目二（25 分）

满分答案须对比两次请求的 JSON diff，并解释 `apply_best_config` 省掉的手动 PUT 步骤。

### 题目三（25 分）

测试须用 `tmp_path`，不得污染仓库 `data/knowledge/store.json`。

### 题目四（20 分）

每小题须举例：如「原地改 size 导致块边界非法」可画 before/after 示意图。

### 加分（10 分）

runbook 须含：备份、evaluate 存档、审批签名栏、rebuild、三条 chat 抽测、回滚。

---

## 常见失分答案点评

- **失分**：只说「rebuild 更新库」——未提 clear chunks 与重 parse。  
- **失分**：混淆 evaluate 与 rebuild 写库行为。  
- **失分**：忽略 uploads 优先导致 source_files 与 sample 不一致。  
- **优秀**：附 `rebuild_api_demo.py` 终端原始输出与 store.json 片段对照。
"""


def _checklist() -> str:
    return """# Day 28 重建验收清单

## 学员验收

| # | 项 | 验证 | ✓ |
|---|-----|------|---|
| 1 | rebuild API 200 | POST /rebuild | ☐ |
| 2 | chunks_after > 0 | 响应字段 | ☐ |
| 3 | sources_processed ≥ 1 | 响应字段 | ☐ |
| 4 | last_rebuilt_at 写入 | GET /status | ☐ |
| 5 | sessions_cleared 存在 | 响应字段 | ☐ |
| 6 | apply_best_config 成功 | POST body | ☐ |
| 7 | uploads 覆盖 | 单元测试 | ☐ |
| 8 | pytest day28 全绿 | pytest -q | ☐ |

## 讲师课前

- [ ] sample_docs 三份文件齐全  
- [ ] 演示 `rebuild_demo.py` 块数变化明显（可先 PUT wide）  
- [ ] 强调备份 store.json  

## 发布后 spot-check

- [ ] EVAL_QUERIES 任取 3 条 chat  
- [ ] `source_files` 含预期运营文档  
- [ ] 无 duplicate document 名  

## 教师课后归档

- 保存一份学员 `rebuild_report.md` 优秀范例  
- 记录本次课 `source_files` 基线列表  
- 统计 `apply_best_config` 与手动 PUT 两种路径各多少人完成  
- 提醒 Day 29 预习：rebuild 后 `_rebuild_index` 会操作 Chroma  

## 回归命令（Phase 3）

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day25/ tests/day26/ tests/day27/ tests/day28/ -q
python3 src/day28/rebuild_api_demo.py
```

## 异常处理速查

| 学员报错 | 助教第一响应 |
|----------|--------------|
| chunks_after=0 | 检查源目录是否有非空文件 |
| 500 sample 缺失 | 恢复 day26/sample_docs |
| chat 仍旧答案 | 新 session_id + 确认 rebuild 成功 |
| last_rebuilt_at null | 是否调用了 rebuild 而非仅 PUT config |
"""


def _deep_supplement_day28() -> str:
    return (
        "## 附录：knowledge_store 持久化走读\n\n"
        + _line_commentary("nexus-agent-platform/src/rag/knowledge_store.py", _ks_rebuild_notes())
        + "\n\n## 附录：api/knowledge.py 重建端点走读\n\n"
        + _line_commentary("nexus-agent-platform/src/api/knowledge.py", _api_rebuild_notes())
    )


def _ks_rebuild_notes() -> dict[int, str]:
    notes: dict[int, str] = {}
    for i, line in enumerate(read_repo("nexus-agent-platform/src/rag/knowledge_store.py").splitlines(), 1):
        if any(k in line for k in ("chunk_config", "last_rebuilt", "set_chunk", "get_chunk", "_rebuild_index", "save")):
            notes[i] = "与 Day 28 rebuild 及 last_rebuilt_at 相关。"
    return notes


def _api_rebuild_notes() -> dict[int, str]:
    notes: dict[int, str] = {}
    for i, line in enumerate(read_repo("nexus-agent-platform/src/api/knowledge.py").splitlines(), 1):
        if any(k in line for k in ("rebuild", "apply_best", "session_manager")):
            notes[i] = "rebuild API 相关行。"
    return notes


def _deep_topic() -> str:
    return f"""# 知识库重建详解

**Day 28 深度专题** | ZL-NA-REQ-028

## 1. 问题定义

设源文件集合 \(S\)，当前配置 \(\theta\)。生产索引 \(I = \text{{Index}}(\text{{Parse}}(S), \theta_{{\text{{old}}}})\)。配置更新为 \(\theta_{{\text{{new}}}}\) 后，需计算 \(I' = \text{{Index}}(\text{{Parse}}(S), \theta_{{\text{{new}}}})\)。

**无法**通过修改 \(\theta\) 元数据把 \(I\) 就地变为 \(I'\)，因 chunk 文本边界已固定。

## 2. rebuild_store 不变式

- 重建后 \(\forall d \in \text{{documents}}\)，\(d\) 来自 \(S\) 中某个源文件  
- \(\text{{chunk\_count}}\) 仅取决于 \(|S|\) 与 \(\theta_{{\text{{new}}}}\)  
- `last_rebuilt_at` 单调更新（同进程连续 rebuild）

## 3. 与 evaluate 协作

`rebuild_with_best_config`：

```python
results = run_ab_experiment(doc, PRESET_CONFIGS, queries)
best = pick_best_config(results)
store.set_chunk_config(best.config)
return rebuild_store(store, ...)
```

**注意**：evaluate 样例是 `product_notice.md`，全库 rebuild 包含所有源文件——最优配置未必对所有文档全局最优。

## 4. 清空顺序为何重要

必须先 `documents.clear()` 再逐文件 `_append_chunks`，最后单次 `_rebuild_index()`。若中途 `_rebuild_index()` 会导致空索引窗口内 chat 失败——教学单进程可接受。

## 5. 运维 Runbook（摘要）

1. 备份 `data/knowledge/store.json`  
2. 确认 uploads 文档版本  
3. POST evaluate 存档 JSON  
4. POST rebuild（或 apply_best_config）  
5. 检查 last_rebuilt_at、chunk_count  
6. chat 抽测 + 监控错误率  



{_deep_supplement_day28()}

## 6. 失败恢复

重建失败 mid-loop 可能导致空库——教学环境可重新 bootstrap；生产应事务化或先写临时 store。
"""


def _workbook() -> str:
    return """# Day 28 课堂练习册

## 选择题

**1.** uploads 与 sample 同名时？

- A. sample 优先  
- B. uploads 优先  
- C. 合并内容  
- D. 抛异常  

<details><summary>答案</summary>B</details>

**2.** rebuild 后哪个字段必更新？

- A. platform_version  
- B. last_rebuilt_at  
- C. chroma_path  
- D. index_mode 必为 incremental  

<details><summary>答案</summary>B</details>

**3.** `apply_best_config` 先做？

- A. rebuild_store  
- B. run_ab_experiment  
- C. clear_all sessions  
- D. delete uploads  

<details><summary>答案</summary>B</details>

**4.** rebuild 清空的是？

- A. uploads 目录  
- B. documents 与 chunks 内存列表  
- C. sample_docs  
- D. EVAL_QUERIES  

<details><summary>答案</summary>B</details>

**5.** `RebuildReport.sources_processed` 表示？

- A. 删除的文件数  
- B. 处理的源文件路径数  
- C. session 数  
- D. API 调用次数  

<details><summary>答案</summary>B</details>

## 填空

1. 重建 API 路径：`POST /api/knowledge/________`  
2. 需求编号：ZL-NA-REQ-______  
3. Day 28 版本：v0.____.0  

## 实操

运行 `rebuild_demo.py`，填写 chunks 变化：____ → ____

## 简答题

1. 为何 rebuild 必须 clear documents/chunks？（提示：块边界）  
2. `apply_best_config` 与 Day 27 evaluate 的关系？  
3. 重建后为何要 `sessions_cleared`？  

## 实操附加（教师选做）

| 步骤 | 操作 | 预期 |
|------|------|------|
| 1 | GET status 记录 chunk_count | 基线 |
| 2 | POST rebuild | 200 |
| 3 | GET status 的 last_rebuilt_at | 更新 |
| 4 | POST chat 赎回问句 | 含 T+1 或赎回 |
| 5 | 对比 source_files 与 ls uploads | 一致 |

## 评分参考

- 选择题全对：20 分  
- 填空正确：15 分  
- 实操题有数据：25 分  
- 简答每题 10 分  
"""


def _rag_extra_walkthrough_day28() -> str:
    dp_notes = {i: "rebuild 循环内 parse_bytes 入口。" for i, ln in enumerate(read_repo("nexus-agent-platform/src/tools/doc_parser.py").splitlines(), 1) if "parse" in ln or "def " in ln}
    cs_notes = {i: "rebuild 使用 chunk_from_parsed 应用 chunk_config。" for i, ln in enumerate(read_repo("nexus-agent-platform/src/rag/chunk_strategies.py").splitlines(), 1) if "chunk" in ln or "def " in ln}
    return (
        "## 附录：doc_parser.py（rebuild 解析链）\n\n"
        + _line_commentary("nexus-agent-platform/src/tools/doc_parser.py", dp_notes)
        + "\n\n## 附录：chunk_strategies.py\n\n"
        + _line_commentary("nexus-agent-platform/src/rag/chunk_strategies.py", cs_notes)
    )


def _extension() -> str:
    return _rag_extra_walkthrough_day28() + """

# 深度扩展：索引发布流程

## 蓝绿发布类比

| 蓝绿 | NexusAgent 教学 |
|------|-----------------|
| 绿环境新版本 | rebuild 后新 store |
| 切流量 | clear sessions + 新检索 |
| 回滚 | 恢复备份 store.json + rebuild |

## 变更窗口

企业实践常在低峰期 rebuild，配合：

- 只读模式 flag（未实现）  
- 双 store 切换（未实现）  

## 与 CI/CD

```yaml
- name: Knowledge rebuild smoke
  run: |
    PYTHONPATH=src pytest tests/day28/ -q
    python3 src/day28/rebuild_api_demo.py
```

## 审计

`last_rebuilt_at` + Git 中 uploads 版本 + evaluate JSON = 完整追溯链。

## Day 29 展望

rebuild 调用 `_rebuild_index` 会 reset Chroma；Day 29 学习向量落盘细节。
"""


def _case_study() -> str:
    return """# 企业案例集：运营发布夜

**时间**：2026-08-04 20:00–22:00  
**事件**：灵犀助手 v0.28 知识库发布

## 时间线

| 时刻 | 动作 | 负责人 |
|------|------|--------|
| 20:00 | 备份 store.json | 周航 |
| 20:15 | POST evaluate 存档 | 林晓 |
| 20:30 | 确认 uploads 含最新合规 PDF | 赵岩 |
| 20:45 | POST rebuild apply_best_config=true | 林晓 |
| 21:00 | chunks 12→8，last_rebuilt_at 更新 | 全员见证 |
| 21:15 | 客服三条抽测通过 | 小吴 |
| 21:30 | 投资人演示彩排 OK | 陈默 |

## 事故预演（ tabletop ）

**若 rebuild 中途断电？**  
答：可能空库；恢复备份后重跑。教学代码未做两阶段提交。

**若 wide 对 uploads 长 PDF 极差？**  
答：evaluate 仅覆盖 product_notice；需扩展评估集后再选配置。

## 经验

- 发布夜必须有 evaluate 截图  
- `source_files` 打印出来人工核对  
- 重建后第一时间看 session 是否清空  

## 讨论

是否应强制 rebuild 前 evaluate？如何在 API 层加 guard？

---

## 发布决策矩阵（培训部附录）

| 信号 | 建议 |
|------|------|
| evaluate hit_rate ≥ 90% 且 chunk_count 下降 | 可执行 apply_best_config |
| uploads 含 >20 页 PDF | 暂缓 wide，补评估问句 |
| chat 抽测 3/3 通过 | 发布 |
| last_rebuilt_at 未更新 | 禁止对外宣称已发布 |

## 角色演练台词

**小吴**：赎回类仍偶发偏。  
**林晓**：样例 md 与合规 PDF 结构不同，下周加 PDF 专用 EVAL。  
**陈默**：投资人演示只看「发布流程完整」，不是「一次调参通吃」。

## D+7 复盘

- 误答率下降 12%  
- 决定 Day 29 接 Chroma 前再 rebuild 一次  
- 建立 evaluate JSON 归档目录 `ops/evaluate/`  
"""


def _lecture_transcript() -> str:
    return """# Day 28 授课实录

**2026-08-04**

---

**09:05 陈默**：昨天大家 hit_rate 很漂亮，但客服说助手没变。谁说说为什么？

**09:08 林晓**：PUT 只改默认配置，旧 chunks 还在。

**09:10 陈默**：对。今天 **rebuild**。三个字：清、扫、建。清空 documents/chunks，重扫源文件，按当前配置建索引。

**09:25 赵岩**：源文件两处：sample 和 uploads。同名 uploads 赢，这是运营常识——线上文档覆盖教材样例。

**10:00 陈默**（投屏 collect_source_files）：先 dict 填 sample，再 uploads 覆盖。返回 sorted 保证 CI 稳定。

**10:40 林晓**：rebuild 里每文件都 `parse_bytes`，跟 Day 26 一样，然后 `chunk_from_parsed` 用 store 里的 config。

**11:15 学生乙**：last_rebuilt_at 有什么用？  
**陈默**：审计。合规问「你什么时候更新的知识库」，别回答「昨晚吧」。

---

**14:05 周航**：API 来了。POST rebuild，body 可以全默认。

**14:20 陈默**：`apply_best_config` 是懒人按钮——先 Day 27 评估再重建。投资人演示可以用，生产建议人工审批。

**14:50 林晓**（演示）：chunks_before 12，after 8。source_files 三个文件名。

**15:20 周航**：重建完 clear_all sessions。不然用户还在聊旧块组成的上下文。

**15:45 陈默**：明天 Day 29 Chroma。rebuild 已经会 `_rebuild_index`，向量也会重刷。

**16:00**：作业 rebuild_report.md，今晚交。

---

## 晚间答疑（陈默）

**20:10** 林晓：rebuild 后 chat 仍答旧内容——未 clear session 的浏览器标签页缓存了 session_id，新开标签解决。  
**20:25** 讨论：apply_best_config 是否应写审计表——赵岩建议记录 evaluate JSON hash。  
**20:40** 周航演示 store.json.bak 恢复，强调发布夜第一步永远是备份。

实录完。
"""


def _flashcards() -> str:
    return """# Day 28 复习卡片

**Q1**：rebuild 核心函数？  
**A1**：`rebuild_store`。

**Q2**：源文件收集函数？  
**A2**：`collect_source_files`。

**Q3**：同名覆盖规则？  
**A3**：uploads 优先于 sample_docs。

**Q4**：重建后审计时间字段？  
**A4**：`last_rebuilt_at`。

**Q5**：API 路径？  
**A5**：`POST /api/knowledge/rebuild`。

**Q6**：apply_best_config 先做什么？  
**A6**：run_ab_experiment 选最优配置。

**Q7**：重建是否删除 uploads 文件？  
**A7**：否，只读。

**Q8**：RebuildReport 中块数变化字段？  
**A8**：chunks_before / chunks_after。

**Q9**：重建后 session 如何处理？  
**A9**：clear_all。

**Q10**：需求编号？  
**A10**：ZL-NA-REQ-028。

**Q11**：版本号？  
**A11**：v0.28.0。

**Q12**：演示脚本？  
**A12**：rebuild_demo.py、rebuild_api_demo.py。

**Q13**：include_sample_docs=false 场景？  
**A13**：仅重建 uploads（测试/运营）。

**Q14**：rebuild 与 evaluate 谁写库？  
**A14**：rebuild 写；evaluate 不写。

**Q15**：Day 29 主题？  
**A15**：Chroma 向量库持久化。

## 闪卡使用说明（教师）

- 第 1–5 张：晨测  
- 第 6–10 张：Lab 前复习  
- 第 11–15 张：Day 29 预习抽查  

## 扩展问法

**Q16**：`RebuildReport.sources_processed` 与 `len(source_files)` 关系？  
**A16**：相等，每个源文件处理一次。

**Q17**：rebuild 是否调用 `ingest_upload`？  
**A17**：否，直接 parse + `_append_chunks`。

**Q18**：`include_sample_docs=false` 且 uploads 空会怎样？  
**A18**：可能得到空库，需谨慎。

**Q19**：`apply_best_config` 评估文档路径？  
**A19**：`day26/sample_docs/product_notice.md`（与 Day 27 相同）。

**Q20**：重建后 `index_mode` 通常为何？  
**A20**：`full`（全量重建后模式，Day 30 才强调 incremental）。
"""


def _api_cheatsheet() -> str:
    return """# Day 28 重建 API 速查手册

## POST /api/knowledge/rebuild

默认 body：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{}' | jq .
```

仅 uploads：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"include_sample_docs": false}' | jq .
```

评估 + 重建：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"include_sample_docs": true, "apply_best_config": true}' | jq .
```

## 响应字段

```json
{
  "documents_before": 3,
  "chunks_before": 12,
  "documents_after": 3,
  "chunks_after": 8,
  "sources_processed": 3,
  "chunk_config": {"name": "wide", "chunk_size": 400, ...},
  "source_files": ["raw_faq.txt", "..."],
  "rebuilt_at": "2026-08-04T12:00:00Z",
  "sessions_cleared": 0,
  "message": "知识库已按当前 chunk_config 全量重建"
}
```

## GET /api/knowledge/status

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.last_rebuilt_at, .chunk_count'
```

## Python 直接调用

```python
from rag.knowledge_store import KnowledgeStore
from rag.knowledge_rebuild import rebuild_store

store = KnowledgeStore.bootstrap_from_sample_docs()
report = rebuild_store(store)
print(report.chunks_before, "->", report.chunks_after)
```

## 错误排查

| 现象 | 可能原因 |
|------|----------|
| sources_processed=0 | 无 sample 且无 uploads |
| chunks_after=0 | 源文件全空 |
| 500 | store 路径不可写 |

---

## curl 完整示例集

```bash
# 1. 查看重建前状态
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_count,.last_rebuilt_at,.chunk_config'

# 2. 标准重建
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"include_sample_docs":true,"apply_best_config":false}' | jq .

# 3. 评估驱动重建
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"apply_best_config":true}' | jq '.chunk_config,.chunks_after,.rebuilt_at'

# 4. 重建后抽测 chat
curl -s -X POST http://127.0.0.1:8000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"message":"投资有风险吗","session_id":"post-rebuild-check"}' | jq .
```

## 响应字段详解

| 字段 | 教学关注点 |
|------|------------|
| chunks_before/after | 发布是否改变索引规模 |
| source_files | 与磁盘源是否一致 |
| sessions_cleared | 是否通知用户重新对话 |
| chunk_config | 实际生效的重建配置快照 |
| message | 人类可读摘要，可打日志 |
"""


def _day27_compare() -> str:
    return """# Day 28 与 Day 27 能力对照表

| 维度 | Day 27 | Day 28 |
|------|--------|--------|
| 主题 | 分块调参 A/B | 全库 rebuild |
| 核心模块 | retrieval_eval | knowledge_rebuild |
| 是否清空 chunks | 否 | 是 |
| 是否读源文件 | 仅评估样例 | sample + uploads |
| API | evaluate, chunk-config | rebuild |
| 新状态字段 | chunk_config 持久化 | last_rebuilt_at |
| 会话 | evaluate 不清 | rebuild 后 clear_all |
| 典型块数变化 | 无（不写库） | 12→8（wide 示例） |

## 联合工作流

```
Day 27 evaluate → 选定 wide
Day 28 rebuild → 全库 wide 块
Day 29+ → 向量引擎换 Chroma，rebuild 流程仍适用
```

## 仍由 Day 27 提供

- PRESET_CONFIGS  
- EVAL_QUERIES  
- run_ab_experiment（用于 apply_best_config）  
"""


def _extra_reading() -> str:
    return """# Day 28 讲师补充阅读

## Elasticsearch Reindex API

类比：rebuild ≈ reindex from source，而非 update mapping in place。

## Lucene 段合并

全文检索引擎中，段不可原地改 doc values；只能新段替换。教学 rebuild 同理。

## 数据湖批处理

Spark 批处理重算特征 vs 流式增量 —— 对应 Day 28 rebuild vs Day 30 incremental。

## 备份策略

- store.json 每次 rebuild 前复制  
- uploads 目录 Git LFS 或对象存储版本化  

## 扩展阅读

- Google *Site Reliability Engineering* 变更管理章节  
- 课程 Day 30 incremental 预习材料  

---

## 专题：变更窗口（Change Window）

企业发布 rebuild 的典型窗口：周二/周四 22:00–23:00 低峰期。  
步骤：公告维护 → 备份 → evaluate 存档 → rebuild → smoke test → 公告恢复。

## 专题：两阶段提交（未实现）

理想实现：

1. 写入 `store.rebuild.tmp.json` 完整新索引  
2. 原子 rename 替换 `store.json`  
3. 失败时保留旧文件  

教学代码单进程 `save()` 直接覆盖，学员需知晓风险。

## 专题：多区域部署

若 sample_docs 在 A 区、uploads 在 B 区对象存储，collect_source_files 需扩展为远程列举——本课仅本地 Path。

## 专题：与 Kubernetes Job 结合

将 rebuild 封装为 CronJob：  
`kubectl create job rebuild-kb --from=cronjob/kb-nightly-rebuild`  
环境变量：`APPLY_BEST_CONFIG=true`。

## 书单

1. Kleppmann, *Designing Data-Intensive Applications* — 衍生数据与批处理  
2. 课程 Day 29 Chroma 文档 — 向量持久化  
3. 课程 Day 27 evaluate 讲义 — 发布前实验  
"""


def _code_walkthrough() -> str:
    tests = _src("tests/day28/test_knowledge_rebuild.py")
    api_tests = _src("tests/day28/test_rebuild_api.py")
    api_slice = _src("api/knowledge.py", limit=125)
    schemas = read_repo("nexus-agent-platform/src/api/schemas.py", limit=140)
    return f"""# Day 28 完整代码走查

## 1. rag/knowledge_rebuild.py

**不重复粘贴全文**。请阅读 `22_knowledge_rebuild精读.md` 的 169 行逐行走读。

## 2. api/knowledge.py — rebuild 端点

{fenced("python", api_slice)}

关注 `rebuild_knowledge_base` 分支：`apply_best_config` vs 直接 `rebuild_store`。

## 3. api/schemas.py — Rebuild 相关

{fenced("python", schemas)}

## 4. rag/knowledge_store.py（搜索）

- `last_rebuilt_at` 字段  
- `status_dict` 暴露  
- load/save 序列化  

## 5. day28/constants.py

```python
DAY = 28
REQ_ID = "ZL-NA-REQ-028"
PLATFORM_VERSION = "0.28.0"
```

## 6. tests/day28/test_knowledge_rebuild.py

{fenced("python", tests)}

## 7. tests/day28/test_rebuild_api.py

{fenced("python", api_tests)}

## 8. 演示脚本

| 脚本 | 层次 |
|------|------|
| rebuild_demo.py | 纯 Python，无 HTTP |
| rebuild_api_demo.py | TestClient |
| phase3_rebuild_review.py | 复习报告（可选） |

## 9. 端到端调用顺序

```
POST /rebuild
  → rebuild_with_best_config? (Day 27 eval)
  → rebuild_store
       → collect_source_files
       → clear → parse loop → _rebuild_index
  → session_manager.clear_all()
  → RebuildResponse
```

## 10. 与 Day 27 衔接点

| Day 27 | Day 28 |
|--------|--------|
| run_ab_experiment | rebuild_with_best_config 内调用 |
| set_chunk_config | apply_best 分支自动调用 |
| evaluate 不写库 | rebuild 写库 |
"""


def _quiz() -> str:
    return """# Day 28 课堂知识竞赛

1. `collect_source_files` 同名时谁优先？（uploads）

2. rebuild 清空的数据结构？（documents 和 chunks）

3. `last_rebuilt_at` 格式？（UTC ISO8601 如 2026-08-04T12:00:00Z）

4. apply_best_config 依赖哪天的评估？（Day 27）

5. rebuild 后为何 clear sessions？（避免旧 RAG 上下文）

6. `sources_processed` 含义？（处理的源文件数量）

7. include_sample_docs 默认？（true）

8. rebuild 是否调用 parse_bytes？（是）

9. RebuildReport 转换字典方法？（to_dict）

10. 双源扫描第二源路径类型？（knowledge_uploads）

11. 需求编号？（ZL-NA-REQ-028）

12. 版本？（0.28.0）

13. 演示脚本之一？（rebuild_demo.py）

14. test_uploads_override 验证什么？（覆盖内容）

15. Day 29 主题？（Chroma 向量库）

## tie-break

`rebuild_with_best_config` 在何文件定义？（knowledge_rebuild.py）

---

## 竞赛答案解析（教师用）

| 题 | 解析 |
|----|------|
| 1 | uploads 覆盖是 Day 28 双源扫描核心语义 |
| 4 | evaluate 在 Day 27，rebuild 可选用其最优配置 |
| 5 | 旧 session 上下文基于旧 chunk 边界，必须 clear |
| 7 | 默认 true，课堂常漏测 false 分支 |
| 10 | 与 Day 27 evaluate 样例路径相同 |
| 15 | Day 29 主题，rebuild 已会 _rebuild_index |

## 加分题

用一句话向投资人解释「调参」与「发布」：  
**参考答案**：调参是实验室里选配置，发布是把全库文档按该配置重新切块并上线。
"""


def _knowledge_rebuild_deep() -> str:
    path = "nexus-agent-platform/src/rag/knowledge_rebuild.py"
    commentary = _line_commentary(path, _knowledge_rebuild_line_notes())
    return f"""# knowledge_rebuild 精读

**路径**：`{path}`

## RebuildReport

不可变报告对象，`to_dict` 供 API。`rebuilt_at` 与 `store.last_rebuilt_at` 一致。

## collect_source_files 算法

1. 解析默认 uploads / sample 路径（`get_path`）  
2. `by_name: dict[str, Path]`  
3. 若 `include_sample_docs`：glob 填入 sample  
4. uploads glob **覆盖**同名  
5. 返回排序后的 Path 列表  

## rebuild_store 逐步说明

| 步骤 | 代码意图 |
|------|----------|
| 快照 | documents_before, chunks_before |
| 取配置 | cfg = store.get_chunk_config() |
| 收集源 | collect_source_files(...) |
| 清空 | documents/chunks clear + invalidate_cache |
| 入库 | parse → clean → chunk → _append_chunks |
| 索引 | _rebuild_index() |
| 持久化 | last_rebuilt_at + save() |

## rebuild_with_best_config

延迟 import Day 27 的 `EVAL_QUERIES` 与 `run_ab_experiment`，避免模块循环依赖。

## 逐行走读（讲师批注）

{commentary}

## 练习

1. 若要在 rebuild 中跳过 PDF，应改哪一层？  
2. 如何实现「dry-run rebuild」只报告不写入？（提示：不 save）  
3. 解释 uploads 优先对投资人演示的意义。  
4. 画出 rebuild_store 与 ingest_upload 的异同 Venn 图（文字描述即可）。

---

## 与测试用例对照精读

### test_collect_sources_uploads_override

构造临时 uploads/sample，验证 uploads 文本覆盖。阅读时对照 `collect_source_files` L61–77。

### test_rebuild_changes_chunk_count

修改 `chunk_config` 为 tiny 后 rebuild，块数应变化。说明 rebuild 确实用新配置重切。

### test_rebuild_persists_last_rebuilt_at

连续 load 验证持久化。联系 `status` API 的 `last_rebuilt_at` 字段。

### test_rebuild_api.py

`test_chat_after_rebuild` 证明发布后会话可用新索引回答。失败时先查 session 与 MOCK 环境。

## 设计思考题（提交可选）

若允许「仅重建 uploads 不改 sample」，API 应增加何参数？与现有 `include_sample_docs` 如何组合？
"""


def _dual_source() -> str:
    return """# 双源扫描与覆盖策略

## 动机

| 源 | 角色 |
|----|------|
| sample_docs | 教学开箱即用，CI 可重复 |
| knowledge_uploads | 运营真实文档 |

仅靠 sample 无法演练「上传后发布」；仅靠 uploads 空目录时 CI 失败。

## 覆盖算法

```python
by_name: dict[str, Path] = {}
# 1. sample 填入
for path in sample.glob("*.txt"): by_name[path.name] = path
# 2. uploads 覆盖
for path in uploads.glob("*.txt"): by_name[path.name] = path
return [by_name[k] for k in sorted(by_name)]
```

## 场景表

| sample | uploads | 结果 |
|--------|---------|------|
| a.txt | — | a.txt (sample) |
| a.txt | a.txt (不同内容) | a.txt (uploads) |
| — | b.txt | b.txt |
| include_sample=false | b.txt | 仅 b.txt |

## 测试锚点

`test_collect_sources_uploads_override` 构造临时目录验证覆盖。

## 运维建议

- uploads 文件命名规范：`{{product}}_{{version}}.md`  
- 避免与 sample 同名除非有意覆盖  
- 发布前 `ls uploads` 对照 `source_files` 响应  

## 与 ingest_upload 关系

upload 单文件写入磁盘+索引；rebuild 批量**重读**磁盘上已有文件，不调用 ingest_upload。

## 双源扫描调试清单

1. `ls` 对比 uploads 与 sample_docs 文件名  
2. 同名文件 `diff` 首行确认 uploads 覆盖  
3. rebuild 响应 `source_files` 与磁盘一致  
4. 抽查 `parse_bytes` 块数与 rebuild 后 store 块分布  
5. 台账记录 `last_rebuilt_at` 与操作者  

## rebuild vs ingest 对照

| 维度 | ingest_upload | rebuild_store |
|------|---------------|----------------|
| 触发 | POST upload | POST /rebuild |
| 是否 clear 全库 | 否 | 是 |
| 数据源 | 请求体 | 磁盘路径 |
| 审计 | incremental（Day 30） | last_rebuilt_at |
"""


def _phase3_summary() -> str:
    return """# Phase 3 第四日总结（Day 25–28）

| 日 | 关键词 |
|----|--------|
| 25 | 知识库 REST |
| 26 | md/pdf 解析 |
| 27 | chunk A/B evaluate |
| 28 | rebuild 发布 |

## 发布闭环

```
evaluate (实验) → chunk-config (配置) → rebuild (发布) → chat (验证)
```

## 字段演进

store.json：

- Day 25: documents, chunks  
- Day 27: + chunk_config  
- Day 28: + last_rebuilt_at  

## 测试累计

day25 + day26 + day27 + day28 pytest 作为 Phase 3 回归套件。

## 明日

Day 29：向量从 JSON 迁至 Chroma，**rebuild 流程不变**，变的是 `_rebuild_index` 内部实现。

---

## Day 25–28 能力栈（详细）

### 知识入库

- Day 25：`ingest_upload` / `ingest_text`  
- Day 26：`parse_bytes` 支持 md/pdf  
- Day 27：默认分块可配置、可评估  
- Day 28：全库按配置重扫发布  

### 状态字段演进

```json
{
  "chunk_config": {"name": "wide", "chunk_size": 400},
  "last_rebuilt_at": "2026-08-04T12:00:00Z",
  "index_mode": "full"
}
```

### API 端点累积

| Day | 新端点 |
|-----|--------|
| 25 | POST upload, GET status |
| 27 | GET/PUT chunk-config, POST evaluate |
| 28 | POST rebuild |

### 团队能力验收

- 林晓：能独立跑通 evaluate → rebuild  
- 周航：能备份恢复 store.json  
- 赵岩：能评审 PRESET 选型报告  
- 小吴：能执行 chat 抽测并填表  

### 常见面试题

1. 为何 evaluate 不 rebuild？  
2. uploads 优先的业务含义？  
3. last_rebuilt_at 与 last_incremental_at 区别？（Day 30）  

### 下一阶段

Day 29 Chroma：rebuild 后检查 `chroma_count == chunk_count`。

## 学员自测 10 问（Day 28）

1. rebuild 是否删除 uploads？  
2. apply_best_config 依赖哪份评估样例？  
3. sessions_cleared 何时大于 0？  
4. include_sample_docs=false 的典型场景？  
5. RebuildReport 哪个字段用于审计？  
6. 与 evaluate 相比谁写入 chunks？  
7. collect_source_files 返回顺序？  
8. 重建失败如何回滚？  
9. Day 30 incremental 与 rebuild 区别？  
10. 投资人演示前三步 API 是什么？  

参考答案见 `21_课堂知识竞赛.md` 与 `09_作业答案.md`。
"""


def _rebuild_api_deep() -> str:
    demo = _src("day28/rebuild_demo.py")
    api_demo = _src("day28/rebuild_api_demo.py")
    return f"""# rebuild_api 脚本精读

## rebuild_demo.py

{fenced("python", demo)}

**流程**：

1. bootstrap store  
2. 可选 `set_chunk_config(wide)` 使前后块数差异明显  
3. `collect_source_files()` 打印源列表  
4. `rebuild_store(store)`  
5. 打印 RebuildReport 关键字段  

## rebuild_api_demo.py

{fenced("python", api_demo)}

**验证点**：

- HTTP 200  
- chunks_before → chunks_after  
- status.last_rebuilt_at  

## 与单元测试差异

| 层级 | 文件 |
|------|------|
| 纯函数 | test_knowledge_rebuild.py |
| HTTP | test_rebuild_api.py |
| 手动演示 | rebuild_api_demo.py |

## 常见错误

- 未设 PYTHONPATH  
- store 路径只读  
- 忘记 NEXUS_LLM_MOCK 导致 LLM 调用（部分环境）  
"""


def _lab() -> str:
    return """# Day 28 实操 Lab 手册

**分值**：100 分

## Step 0 环境（5 分）

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day28/ -q
```

## Step 1 观察重建前（10 分）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.chunk_count, s.chunk_config.name)
"
```

## Step 2 设置 wide 并 rebuild（25 分）

```bash
python3 src/day28/rebuild_demo.py | tee lab28_rebuild.txt
```

记录 chunks 变化：______ → ______

## Step 3 API rebuild（25 分）

```bash
python3 src/day28/rebuild_api_demo.py
```

截图含 `last_rebuilt_at`。

## Step 4 apply_best_config（20 分）

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{"apply_best_config":true}' | jq '.chunk_config.name, .chunks_after'
```

## Step 5 chat 抽测（10 分）

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"message":"赎回多久到账","session_id":"lab28"}' | jq .
```

## Step 6 反思（5 分）

100 字：rebuild 与 Day 27 evaluate 分工。

## 教师勾选

- [ ] lab28_rebuild.txt 已交  
- [ ] chat 回答含 T+1 或赎回关键词  

## Lab 专属辅导

**Step 2**：若 chunks 前后不变，检查是否忘记 `set_chunk_config(wide)`。  
**Step 4**：`apply_best_config` 响应中 `chunk_config.name` 应与 Day 27 evaluate 一致。  
**Step 5**：chat 失败先查 session 是否需新 `session_id`。  
**常见扣分**：未提交 `lab28_rebuild.txt`；反思未对比 evaluate vs rebuild 写库差异。
"""


def _day29_preview() -> str:
    return """# Day 29 预习：Chroma 向量库

## 问题

Day 28 rebuild 后，`store.json` 仍然很大——向量存在哪？

## 预告

Day 29 引入 `ChromaVectorIndex`，向量落盘 `data/knowledge/chroma/`。

## rebuild 不变

`rebuild_store` 仍调用 `_rebuild_index()`，内部变为：

1. fit TF-IDF  
2. chroma.reset()  
3. upsert_chunks  

## 预习任务

阅读 `rag/chroma_store.py` 前 60 行。

## 陈默寄语

「发布流程你们已经会了；明天换引擎，流程不换。」
"""



def _tutor_supplement_day28() -> str:
    return """# Day 28 培训部辅导长文（知识库重建）

## 专题 01：rebuild 前备份

复制 store.json 为 store.json.bak。说明恢复步骤：停服务、替换、重启。演练一次恢复。

## 专题 02：collect_source_files 实验

在 uploads 放与 sample 同名文件，打印 collect_source_files 路径与 read_text 首行。

## 专题 03：include_sample_docs=false

仅 uploads 有文件时重建。观察 sources_processed 与 documents_after。

## 专题 04：chunks_before 与 after

rebuild_demo 打印变化。若相同，检查是否未改 chunk_config 或源文件未变。

## 专题 05：last_rebuilt_at 时区

字段为 UTC。转换为北京时间写在实验报告。说明为何用 UTC 存储。

## 专题 06：apply_best_config 审批

投资人演示可用，生产需人工审批。写审批单模板：evaluate 截图、审批人、时间。

## 专题 07：sessions_cleared 含义

重建后所有会话 orchestrator 清空。用户需重新 chat。说明与 upload 后 clear 的一致性。

## 专题 08：rebuild 与 Chroma

Day 29 起 _rebuild_index 重置 Chroma。预习：重建后 chroma_count 应等于 chunk_count。

## 专题 09：空库风险

rebuild 中途失败可能空库。讨论两阶段提交：先写临时 store 再 rename。

## 专题 10：source_files 人工核对

发布夜 checklist：source_files 与 ls uploads 一致。缺文件则中止发布。

## 专题 11：parse 失败单文件

若某 PDF 损坏，当前实现 skip 或 fail？阅读 rebuild_store 循环，讨论 try/except 策略。

## 专题 12：clean_text 一致性

对比 ingest 与 rebuild 清洗结果。同一文件两种路径 chunk 应一致。

## 专题 13：rebuild_api_demo 输出

保存终端输出到 rebuild_report.md。助教对照 chunks 字段。

## 专题 14：test_uploads_override

阅读测试构造临时 uploads/sample。自己复现并截图 pytest -k override 通过。

## 专题 15：chat 抽测三条

重建后对 EVAL 问句各发一条 chat。记录 reply 是否引用正确段落。

## 专题 16：运维 runbook 一页

evaluate → 审批 → rebuild → spot-check。画流程图附作业。

## 专题 17：与 incremental 对比

Day 30 upload 不 reset。列表对比 rebuild 与 upload 索引行为。

## 专题 18：store 体积变化

wide 后 chunk 少，store.json 可能变小。记录重建前后文件大小 KB。

## 专题 19：双环境发布

staging rebuild 通过后 prod rebuild。描述配置 promote 流程。

## 专题 20：监控指标

建议记录 rebuild_duration_seconds。附 Prometheus 指标名伪代码。

## 专题 21：uploads 命名规范

避免无意覆盖 sample。使用 product_v2.md 而非 raw_faq.txt。

## 专题 22：合规 last_rebuilt_at

合规部问「何时更新知识库」，演示 GET status 字段。

## 专题 23：失败回滚演练

故意 PUT 非法 config 后 rebuild 应失败。记录 HTTP 状态。

## 专题 24：团队角色

发布夜：林晓执行、周航备份、赵岩审批、小吴抽测。写 RACI 表。

## 专题 25：Day 29 预习问题

_rebuild_index 内 chroma.reset 何时调用？阅读预习文档回答。

## 附录：逐条实验复盘（培训部自动生成）

### 复盘 01：rebuild 默认 body

**场景**：Day 28 学员在「rebuild 默认 body」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 02：apply_best 真

**场景**：Day 28 学员在「apply_best 真」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 03：apply_best 假

**场景**：Day 28 学员在「apply_best 假」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 04：skip sample

**场景**：Day 28 学员在「skip sample」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 05：uploads 覆盖

**场景**：Day 28 学员在「uploads 覆盖」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 06：空 uploads

**场景**：Day 28 学员在「空 uploads」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 07：last_rebuilt 两次

**场景**：Day 28 学员在「last_rebuilt 两次」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 08：sessions 清零验证

**场景**：Day 28 学员在「sessions 清零验证」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 09：chat 抽测 1

**场景**：Day 28 学员在「chat 抽测 1」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 10：chat 抽测 2

**场景**：Day 28 学员在「chat 抽测 2」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 11：store 备份恢复

**场景**：Day 28 学员在「store 备份恢复」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 12：chunks 前后对比

**场景**：Day 28 学员在「chunks 前后对比」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 13：source_files 核对

**场景**：Day 28 学员在「source_files 核对」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 14：PDF 源文件

**场景**：Day 28 学员在「PDF 源文件」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 15：md 源文件

**场景**：Day 28 学员在「md 源文件」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 16：txt 源文件

**场景**：Day 28 学员在「txt 源文件」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 17：clean_text 一致

**场景**：Day 28 学员在「clean_text 一致」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 18：invalidate_cache

**场景**：Day 28 学员在「invalidate_cache」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 19：_rebuild_index 耗时

**场景**：Day 28 学员在「_rebuild_index 耗时」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 20：Chroma 预习

**场景**：Day 28 学员在「Chroma 预习」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 21：incremental 对比

**场景**：Day 28 学员在「incremental 对比」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 22：运维窗口

**场景**：Day 28 学员在「运维窗口」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 23：审批流

**场景**：Day 28 学员在「审批流」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 24：监控指标

**场景**：Day 28 学员在「监控指标」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 25：失败注入

**场景**：Day 28 学员在「失败注入」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 26：pytest 全量

**场景**：Day 28 学员在「pytest 全量」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 27：API demo 输出

**场景**：Day 28 学员在「API demo 输出」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 28：团队 RACI

**场景**：Day 28 学员在「团队 RACI」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 29：发布夜 checklist

**场景**：Day 28 学员在「发布夜 checklist」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 30：投资人彩排

**场景**：Day 28 学员在「投资人彩排」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。

### 复盘 31：Day29 作业

**场景**：Day 28 学员在「Day29 作业」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 27 与 Day 28 能力差异表一行。
"""

def build() -> dict[str, str]:
    """Generate course/day28 materials. Returns total character count."""
    files = {
        "README.md": _readme(),
        "00_旁白解读.md": _narration(),
        "01_企业背景与今日任务.md": _enterprise_bg(),
        "02_需求文档.md": _requirements(),
        "02_需求文档_扩展.md": _requirements_ext(),
        "03_架构设计.md": _architecture(),
        "04_流程图与示意图.md": _flowcharts(),
        "05_课堂笔记_上午.md": _notes_am(),
        "06_课堂笔记_下午.md": _notes_pm(),
        "07_晚自习.md": _evening(),
        "08_作业.md": _homework(),
        "09_作业答案.md": _homework_answers(),
        "10_重建验收清单.md": _checklist(),
        "11_知识库重建详解.md": _deep_topic(),
        "12_课堂练习册.md": _workbook(),
        "13_深度扩展_索引发布流程.md": _extension(),
        "14_企业案例集_运营发布夜.md": _case_study(),
        "15_授课实录.md": _lecture_transcript(),
        "16_复习卡片.md": _flashcards(),
        "17_重建API速查手册.md": _api_cheatsheet(),
        "18_与Day27能力对照表.md": _day27_compare(),
        "19_讲师补充阅读.md": _extra_reading(),
        "20_完整代码走查.md": _code_walkthrough(),
        "21_课堂知识竞赛.md": _quiz(),
        "22_knowledge_rebuild精读.md": _knowledge_rebuild_deep(),
        "23_双源扫描与覆盖策略.md": _dual_source(),
        "24_Phase3第四日总结.md": _phase3_summary(),
        "25_rebuild_api脚本精读.md": _rebuild_api_deep(),
        "26_实操Lab手册.md": _lab(),
        "27_Day29向量库预习.md": _day29_preview(),
    }
    if len(files) != 30:
        raise SystemExit(f"day28: expected 30 files, got {len(files)}")
    return files


if __name__ == "__main__":
    build()
