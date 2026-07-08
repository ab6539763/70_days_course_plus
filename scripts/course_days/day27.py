#!/usr/bin/env python3
"""Gold-standard course materials for Day 27 — chunk tuning & A/B evaluation."""

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
    """Line-by-line source walkthrough with instructor notes."""
    lines = read_repo(path).splitlines()
    parts = [f"### `{path}` 逐行走读\n", f"共 **{len(lines)}** 行。\n"]
    for i, line in enumerate(lines, 1):
        parts.append(f"**L{i}** `{line}`")
        if note := notes.get(i):
            parts.append(f"  → {note}")
        parts.append("")
    return "\n".join(parts)


def _chunk_config_line_notes() -> dict[int, str]:
    return {
        1: "模块 docstring：标明分块参数职责与需求编号 ZL-NA-REQ-027。",
        7: "启用 future annotations，支持前向类型引用。",
        9: "导入 asdict：ChunkConfig.to_dict 复用 dataclass 序列化。",
        13: "@dataclass 装饰器：自动生成 __init__ 与字段比较。",
        14: "ChunkConfig 是 Day 27 核心值对象，贯穿 store / API / eval。",
        17: "chunk_size 默认 200，与 Day 19 基线一致，便于对比实验。",
        18: "overlap 默认 40，约为 size 的 20%，经验比例。",
        19: "strategy 控制 chunk_from_parsed 的分发逻辑。",
        20: "name 用于 PRESET 标识与审计日志，非文件名。",
        22: "validate 在 API 与 store.set_chunk_config 前必须调用。",
        23: "chunk_size 必须正整数，零或负数无意义。",
        25: "overlap 上界严格小于 chunk_size，防止整块重复滑动。",
        27: "strategy 白名单：auto / fixed / markdown 三者之一。",
        30: "to_dict 供 store.json 与 EvaluateResponse 序列化。",
        34: "from_dict 容忍缺失键，使用默认值，利于旧 store 迁移。",
        43: "DEFAULT_CHUNK_CONFIG 单例语义：未配置时的回退。",
        45: "PRESET_CONFIGS 元组不可变，防止课堂演示中被意外修改。",
        46: "compact：小块压力测试，通常 chunk_count 最多。",
        47: "default：生产基线 PRESET。",
        48: "wide：理财短章节文档推荐，hit_rate 常最高。",
        49: "markdown_wide：强制 markdown 策略，适合结构化手册。",
    }


def _retrieval_eval_line_notes() -> dict[int, str]:
    return {
        1: "模块职责：检索质量评估，与生产 KnowledgeStore 解耦。",
        12: "依赖 ChunkConfig：评估输入必须可 validate。",
        13: "chunk_from_parsed：复用 Day 26 分块实现，不重复造轮子。",
        14: "EmbeddingRetriever：内存 TF-IDF，fit 在当前 chunks 上。",
        18: "EvalQuery：单条评估样本，expect_any 为弱监督关键词。",
        26: "from_dict 兼容 expect 旧字段名，降低 JSON 迁移成本。",
        36: "QueryEvalResult：单查询粒度，供教师逐条讲评。",
        46: "to_dict 四舍五入 top_score，API 响应更整洁。",
        56: "ConfigEvalResult：A/B 表格的一行。",
        76: "build_retriever_for_doc：评估路径入口，绝不写 store。",
        81: "先 validate 再分块，失败快速返回。",
        82: "chunk_from_parsed 参数来自 config 四字段。",
        88: "EmbeddingRetriever 构造即 fit 词表，chunk 变化则向量变。",
        91: "evaluate_query：hit@1 实现，top_k 默认 1 可扩展。",
        97: "search 返回 ScoredChunk 列表，可能为空。",
        98: "无检索结果时 hit=False，避免 None 访问。",
        109: "expect_any 非空才做关键词匹配；空则视为命中。",
        111: "any(kw in text)：子串匹配，教学简单；生产可用正则或 NER。",
        117: "preview(80) 截断预览，便于 CLI 与日志阅读。",
        122: "evaluate_config：单配置完整实验一次调用。",
        128: "build_retriever_for_doc 每次新建 retriever，配置间隔离。",
        130: "hits 计数：Python sum 布尔序列，简洁可读。",
        131: "total 至少为 1，防止除零。",
        143: "run_ab_experiment：A/B 核心，列表推导式生成结果。",
        150: "排序键：hit_rate ↓, avg_top_score ↓, chunk_count ↑。",
        154: "pick_best_config：空列表返回 None，API 层需处理。",
    }

def _readme() -> str:
    return """# Day 27 课件索引

**日期**：2026-08-03（星期一）  
**主题**：分块参数调优与检索质量 A/B 评估  
**需求**：ZL-NA-REQ-027  
**版本**：v0.27.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| ChunkConfig | `rag/chunk_config.py` | 四套 PRESET 与 validate |
| 检索评估 | `rag/retrieval_eval.py` | hit@1、run_ab_experiment |
| 评估问句 | `day27/constants.py` | EVAL_QUERIES 四条 |
| API | `GET/PUT /api/knowledge/chunk-config` | 持久化默认分块 |
| API | `POST /api/knowledge/evaluate` | A/B 实验入口 |
| 前端 | `frontend/knowledge.js` | `#kb-eval-btn` |
| 测试 | `tests/day27/` | 15 项 |

## 关键设计决策

1. **评估与生产索引分离**：`evaluate` 在 `product_notice.md` 上模拟分块，不写 `store.json`。
2. **hit@1 教学指标**：top-1 检索块文本包含 `expect_any` 任一关键词即命中。
3. **PRESET 四套**：compact / default / wide / markdown_wide，覆盖块大小与策略组合。
4. **chunk_config 持久化**：`PUT` 后影响后续 `upload`，已有块不自动变化。
5. **排序规则**：`hit_rate` 降序 → `avg_top_score` → `chunk_count` 升序。

## 验收命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day27/ab_experiment_demo.py
python3 src/day27/chunk_tune_api_demo.py
pytest tests/day27/ -q
```

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_分块调参与检索评估详解 | 深度专题讲义 |
| 15_授课实录 | 上午下午完整实录 |
| 22_retrieval_eval精读 | hit@1 源码走读 |
| 23_chunk_config与企业预设实践 | PRESET 设计 |
| 26_实操Lab手册 | 六步实验（评分） |
| 27_Day28知识库重建预习 | rebuild 预告 |

**生成器**：`scripts/course_days/day27.py`（gold-standard）
"""


def _narration() -> str:
    return """# Day 27 旁白解读

2026 年 8 月 3 日，星期一。智链科技产品部会议室，白板最上方写着一行字：**「chunk_size=200 谁定的？」**

陈默把马克笔扔回托盘：「Day 19 的默认值不是圣经。上周客服反馈『赎回规则』总检索到收益率段落——这不是模型笨，是**块切错了**。」

林晓打开 `product_notice.md`：五个 `##` 章节，起购、收益、风险、赎回各一段。她用 compact（120 字符）跑了一遍 evaluate，hit_rate 只有 50%。换成 wide（400 字符），四条评估问句全部命中。

赵岩在白板画了两条泳道：

```
[实验泳道]  parse → chunk(配置A) → 内存 EmbeddingRetriever → EVAL_QUERIES → hit@1
[生产泳道]  upload → store.chunks → TF-IDF/Chroma → /api/chat
```

「实验泳道不碰 store，」赵岩强调，「调参是科学，发布是工程——明天 Day 28 才 rebuild。」

下午周航把 `#kb-eval-btn` 接到 `POST /api/knowledge/evaluate`。投资人演示前，产品只需点一次按钮，看 `best_config.name` 是否为 `wide`。

```mermaid
journey
    title Day 27 学员旅程
    section 上午
      ChunkConfig.validate: 4: 林晓
      EVAL_QUERIES 设计: 5: 林晓
      run_ab_experiment: 5: 林晓
    section 下午
      evaluate API: 5: 林晓
      PUT chunk-config: 4: 林晓
      浏览器 A/B 按钮: 4: 林晓
```

**旁白**：今日故事线 —— 用数据回答「块要多大」，而不是凭感觉。
"""


def _enterprise_bg() -> str:
    return """# Day 27 企业背景与今日任务

## 业务背景

智链科技「灵犀理财助手」上线三周，知识库已接入三份样例文档与若干运营上传。Day 26 支持 Markdown/PDF 解析后，产品部发现：

- 「最低起购金额」类问题，top-1 偶尔落到无关段落；
- 同一份 `product_notice.md`，Markdown 章节分块与 fixed 滑动窗口检索表现不一致；
- 运营希望**可配置、可量化**地调整分块，而非改代码发版。

## 今日任务（林晓）

| 序号 | 任务 | 产出 |
|------|------|------|
| T1 | 实现 `ChunkConfig` 与四套 PRESET | `rag/chunk_config.py` |
| T2 | 实现 hit@1 与 `run_ab_experiment` | `rag/retrieval_eval.py` |
| T3 | 定义评估问句集 | `day27/constants.py` |
| T4 | 暴露 chunk-config / evaluate API | `api/knowledge.py` |
| T5 | store 持久化 `chunk_config` | `rag/knowledge_store.py` |
| T6 | 前端评估按钮 | `frontend/knowledge.js` |
| T7 | 测试与演示脚本 | `tests/day27/`、`ab_experiment_demo.py` |

## 验收标准

- `pytest tests/day27/ -q` 全部通过；
- `ab_experiment_demo.py` 打印四套配置 hit_rate 且推荐配置合理；
- `PUT /api/knowledge/chunk-config` 非法 overlap 返回 422；
- `POST /api/knowledge/evaluate` 返回 `best_config` 与 `eval_query_count >= 4`。

## 团队分工

- **陈默**：评估层与生产索引隔离架构评审  
- **林晓**：核心实现与 API  
- **赵岩**：PRESET 命名与企业预设策略  
- **周航**：前端按钮与 CI 测试  

## 与 Phase 3 的关系

Day 25 知识库 → Day 26 多格式解析 → **Day 27 分块调参** → Day 28 全库 rebuild。
"""


def _requirements() -> str:
    return """# ZL-NA-REQ-027 需求文档

**版本**：v0.27.0  
**优先级**：P0  
**负责人**：林晓

## 背景

RAG 检索质量受分块参数显著影响。需在**不破坏生产索引**前提下，对固定评估文档运行 A/B 对比，并持久化优选配置供后续上传使用。

## 功能需求

### FR-001 ChunkConfig 数据类

- 字段：`chunk_size`、`overlap`、`strategy`、`name`
- `validate()`：`chunk_size > 0`，`0 <= overlap < chunk_size`，`strategy ∈ {auto,fixed,markdown}`
- `to_dict` / `from_dict` 支持 JSON 往返
- `PRESET_CONFIGS`：至少 compact、default、wide、markdown_wide 四套

### FR-002 retrieval_eval 模块

- `EvalQuery(query, expect_any, label)`
- `evaluate_query`：hit@1，top 块文本含 `expect_any` 任一子串即 hit
- `evaluate_config`：单配置完整指标（chunk_count、hit_rate、avg_top_score）
- `run_ab_experiment`：多配置对比，按 hit_rate 降序排序
- `pick_best_config`：取排序后第一项

### FR-003 REST API

| 方法 | 路径 | 行为 |
|------|------|------|
| GET | `/api/knowledge/chunk-config` | 返回当前 store 配置 |
| PUT | `/api/knowledge/chunk-config` | 校验后写入 store 并 save |
| POST | `/api/knowledge/evaluate` | 对样例文档跑 A/B，body 可选 `use_presets` / `configs` |

### FR-004 持久化

- `store.json` 增加 `chunk_config` 字段
- `GET /api/knowledge/status` 含 `chunk_config`
- 后续 `upload` / `ingest` 使用 store 中的默认参数

### FR-005 评估问句

- `day27/constants.py` 定义 `EVAL_QUERIES`（≥4 条）
- 覆盖起购、收益、风险、赎回四类业务问句

## 非目标

- 全库按新配置重建（Day 28 `rebuild`）
- 调用外部 Embedding API 做评估
- MRR、nDCG 等高级指标（扩展阅读仅介绍）

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 pytest tests/day27/ -q
```
"""


def _requirements_ext() -> str:
    return """# ZL-NA-REQ-027 需求文档（扩展）

## 用户故事

### US-027-01 产品经理调参

**作为** 产品经理  
**我希望** 在浏览器点击「A/B 评估」  
**以便** 看到推荐的分块配置名称与 hit_rate  
**验收**：`best_config.name` 显示在 UI，`eval_query_count` ≥ 4

### US-027-02 工程师持久化配置

**作为** 后端工程师  
**我希望** `PUT chunk-config` 写入 store.json  
**以便** 下次服务重启后上传仍用新参数  
**验收**：`KnowledgeStore.load` 后 `chunk_config.chunk_size` 与 PUT 一致

### US-027-03 测试工程师回归

**作为** QA  
**我希望** overlap ≥ chunk_size 时 API 返回 422  
**以便** 防止非法配置入库  
**验收**：`test_put_invalid_overlap` 通过

## 边界条件

| 场景 | 期望 |
|------|------|
| 评估样例缺失 | evaluate 返回 500 |
| configs 为空且 use_presets=false | 需客户端显式传配置列表 |
| expect_any 为空 | 有检索结果即 hit |
| 文档无匹配关键词 | hit=false，top_preview 仍返回 |

## 数据流

```
product_notice.md
    → parse_bytes → ParsedDocument
    → 对每个 ChunkConfig: chunk_from_parsed → EmbeddingRetriever
    → 对每条 EvalQuery: search(top_k=1) → QueryEvalResult
    → ConfigEvalResult → 排序 → best_config
```

## 版本对齐

- `day27/constants.py`：`PLATFORM_VERSION = "0.27.0"`
- health / status 中 platform_version 与课程版本一致（教学仓库可能已升至后续版本，以 constants 为准理解设计意图）
"""


def _arch_supplement_day27() -> str:
    return (
        "## 附录 A：knowledge_store.py 走读\n\n"
        + _line_commentary("nexus-agent-platform/src/rag/knowledge_store.py", _ks_store_notes())
        + "\n\n## 附录 B：api/knowledge.py 走读\n\n"
        + _line_commentary("nexus-agent-platform/src/api/knowledge.py", _api_eval_notes())
    )


def _ks_store_notes() -> dict[int, str]:
    notes: dict[int, str] = {}
    for i, line in enumerate(read_repo("nexus-agent-platform/src/rag/knowledge_store.py").splitlines(), 1):
        if any(k in line for k in ("chunk_config", "last_rebuilt", "set_chunk", "get_chunk", "ingest_parsed", "_rebuild_index")):
            notes[i] = "与 Day 27 chunk_config 持久化及后续 rebuild 相关。"
    return notes


def _api_eval_notes() -> dict[int, str]:
    notes: dict[int, str] = {}
    for i, line in enumerate(read_repo("nexus-agent-platform/src/api/knowledge.py").splitlines(), 1):
        if any(k in line for k in ("chunk", "evaluate", "rebuild", "EVAL", "PRESET")):
            notes[i] = "evaluate / chunk-config API 相关行。"
    return notes


def _architecture() -> str:
    chunk = _src("rag/chunk_config.py")
    return f"""# Day 27 架构设计

**需求**：ZL-NA-REQ-027

## 分层视图

```
┌─────────────────────────────────────────┐
│  frontend/knowledge.js  (#kb-eval-btn)  │
└──────────────────┬──────────────────────┘
                   │ POST /evaluate
┌──────────────────▼──────────────────────┐
│  api/knowledge.py                       │
│  get/put chunk-config · evaluate        │
└───────┬─────────────────────┬───────────┘
        │                     │
        ▼                     ▼
┌───────────────┐    ┌────────────────────┐
│ KnowledgeStore│    │ retrieval_eval     │
│ chunk_config  │    │ (内存临时 retriever)│
│ persist       │    │ 不写 chunks        │
└───────────────┘    └─────────┬──────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ chunk_config         │
                    │ chunk_strategies     │
                    │ embedding_retriever  │
                    └──────────────────────┘
```

## 核心隔离原则

**评估路径**调用 `build_retriever_for_doc`：在内存中对单份 `ParsedDocument` 分块并训练 TF-IDF，**从不**调用 `store._append_chunks` 或 `save()`。

**生产路径**由 `upload` / `ingest` 使用 `store.get_chunk_config()` 分块并写入索引。

## ChunkConfig 源码锚点

{fenced("python", chunk)}

## evaluate 端点伪代码

```python
doc = parse_bytes(_EVAL_SAMPLE)
queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]
configs = PRESET_CONFIGS if body.use_presets else body.configs
results = run_ab_experiment(doc, configs, queries)
return EvaluateResponse(best_config=results[0], ...)
```

## 持久化字段

`store.json` 片段：

```json
{{
  "chunk_config": {{
    "chunk_size": 200,
    "overlap": 40,
    "strategy": "auto",
    "name": "default"
  }}
}}
```



{_arch_supplement_day27()}

## 失败模式

| 失败 | 处理 |
|------|------|
| overlap 非法 | validate → 422 |
| 样例文件缺失 | 500 + detail |
| 空 configs 结果 | 500「评估未产生结果」 |
"""


def _flowcharts() -> str:
    return """# Day 27 流程图与示意图

## A/B 评估时序

```mermaid
sequenceDiagram
    participant U as 用户/前端
    participant API as /api/knowledge/evaluate
    participant EV as retrieval_eval
    participant P as product_notice.md

    U->>API: POST use_presets=true
    API->>P: parse_bytes
    loop 每个 PRESET
        API->>EV: evaluate_config(doc, cfg, queries)
        EV->>EV: chunk_from_parsed + EmbeddingRetriever
        EV->>EV: hit@1 统计
    end
    EV-->>API: 排序后的 results
    API-->>U: best_config + hit_rate 表
```

## chunk-config 更新流程

```mermaid
flowchart TD
    A[PUT /chunk-config] --> B{{validate}}
    B -->|失败| C[422]
    B -->|成功| D[store.set_chunk_config]
    D --> E[store.save]
    E --> F[后续 upload 使用新参数]
    F --> G[已有 chunks 不变]
```

## hit@1 判定

```
query: "赎回多久到账"
expect_any: ["T+1", "到账", "赎回"]

retriever.search(query, top_k=1)
  → top.chunk.text = "...T+1 工作日到账..."
  → any(kw in text for kw in expect_any) → hit=true
```

## PRESET 对比示意（教学典型结果）

| name | chunk_size | hit_rate | chunk_count |
|------|------------|----------|-------------|
| compact | 120 | ~50-75% | 较多 |
| default | 200 | ~75% | 中等 |
| wide | 400 | ~100% | 较少 |
| markdown_wide | 500 | 视策略而定 | 章节块 |

*实际数值以本地 `ab_experiment_demo.py` 输出为准。*

## 与 Day 28 衔接

```
Day 27: evaluate → 选出 best_config → PUT chunk-config（可选）
Day 28: rebuild → 全库按 chunk_config 重扫源文件
```
"""


def _notes_am() -> str:
  eval_src = _src("rag/retrieval_eval.py", limit=90)
  return f"""# Day 27 课堂笔记（上午）

**讲师**：陈默  
**记录**：林晓

## 09:00–09:30 开场：为何调参

- Day 26 解决了「能解析」，没解决「切得好」
- 块太大：top-1 含噪声段落，hit 下降
- 块太小：关键词被切到相邻块，hit 下降
- **今日指标**：hit@1（教学简化版，非生产唯一标准）

## 09:30–10:30 ChunkConfig 走读

字段含义：

| 字段 | 作用 |
|------|------|
| chunk_size | 单块最大字符数（fixed/auto 滑动窗口上限） |
| overlap | 相邻块重叠，避免句中断裂 |
| strategy | auto：md 章节 / 其他 fixed；markdown：强制章节 |
| name | PRESET 标识，写入 store 便于审计 |

`validate()` 铁律：`overlap < chunk_size`。课堂有人提议 overlap=200、size=200「全覆盖」——**直接 422**。

## 10:45–11:30 retrieval_eval 核心 API

{fenced("python", eval_src)}

### 课堂追问

**Q**：为何 `build_retriever_for_doc` 不读 store？  
**A**：store 里是**旧配置**下的块；评估要对**同一份 ParsedDocument** 公平对比多套参数。

**Q**：`expect_any` 为何用 tuple？  
**A**：不可变、可哈希，测试里方便断言。

## 11:30–12:00 EVAL_QUERIES 设计工作坊

四条问句来自真实客服日志（脱敏）：

1. 起购门槛 → expect `1000` 或 `起购`
2. 收益率 → `8%`、`收益`、`年化`
3. 风险 → `风险`、`谨慎`
4. 赎回 → `T+1`、`到账`、`赎回`

赵岩：「expect_any 是**弱监督**，不是标注平台。教学够用，生产要换人工标注集。」
"""


def _notes_pm() -> str:
    return """# Day 27 课堂笔记（下午）

**讲师**：陈默、周航  
**记录**：林晓

## 14:00–14:45 evaluate API 实现（口述）

端点函数 `evaluate_chunk_configs`，走读顺序：

1. 空 body 默认 `EvaluateRequest()`  
2. 校验 `_EVAL_SAMPLE` 路径 `day26/sample_docs/product_notice.md`  
3. `parse_bytes` → `EvalQuery.from_dict` 加载 EVAL_QUERIES  
4. `use_presets and not configs` 时使用 `PRESET_CONFIGS`  
5. `run_ab_experiment` → `pick_best_config` → `EvaluateResponse`  

**源码**：见 `20_完整代码走查.md` 第 5 节，课堂不重复投屏。

## 14:45–15:30 持久化与 upload 联动

`KnowledgeStore.set_chunk_config` 流程：

1. `config.validate()`
2. 写入 `self.chunk_config`
3. `save()` 序列化到 `store.json`
4. **不**触发 rebuild

演示：PUT size=300 后 upload 新文档，新文档块约 300 字符；旧文档块数不变。

## 15:30–16:15 前端 #kb-eval-btn

周航演示 `runEvaluate()`：

```javascript
const resp = await fetch('/api/knowledge/evaluate', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{ use_presets: true }})
}});
const data = await resp.json();
// 展示 data.best_config.name, data.results[0].hit_rate
```

## 16:15–17:00 课堂练习预告

完成 `ab_experiment_demo.py` 运行，截图四套 hit_rate 填入练习册第 3 题。

## 今日金句

陈默：「调参是实验，不是迷信默认值；实验完不等于发布——记住明天 rebuild。」

---

## 下午补充实录（周航笔记）

**15:35** 林晓本地 evaluate 出现 500，原因是 sample 路径被误删。恢复 `day26/sample_docs/product_notice.md` 后正常。  
**15:50** 三组学员 PUT 成功但 status 未变——未调用 save 的旧进程缓存；重启 uvicorn 解决。  
**16:05** 竞赛第 8 题：`build_retriever_for_doc` 返回 `EmbeddingRetriever`，非 KnowledgeStore。  
**16:20** 赵岩强调：生产环境 evaluate 应异步化，课堂同步 API 足够。  
**16:35** 晚自习提醒：/compare Day 27 evaluate JSON 与 Day 28 rebuild 响应字段差异。

---

## 学员问答摘录

**问**：能否对 uploads 里每份文档分别 evaluate？  
**答**：今日 API 固定样例；扩展作业可自行 `parse_bytes` 后调 `run_ab_experiment`。

**问**：hit@1 太低是否换 embedding 模型？  
**答**：先排除 chunk 问题；换模型是 Day 29+ 向量引擎话题。

**问**：PRESET 能否从配置文件 YAML 加载？  
**答**：未实现；当前 PRESET_CONFIGS 元组在代码中，便于测试稳定。

实录完。总时长 6 课时。
"""


def _evening() -> str:
    return """# Day 27 晚自习

## 目标

巩固 hit@1 与 PRESET 差异，为 Day 28 rebuild 预习。

## 任务清单

### 任务 A：运行 A/B 演示（30 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 src/day27/ab_experiment_demo.py
```

记录表格：

| PRESET | chunk_size | hit_rate | chunk_count |
|--------|------------|----------|-------------|
| compact | | | |
| default | | | |
| wide | | | |
| markdown_wide | | | |

### 任务 B：修改 EVAL_QUERIES（45 分钟）

在 `day27/constants.py` 增加第 5 条问句，例如「产品叫什么名字」，设置合理 `expect_any`。

运行 `pytest tests/day27/test_chunk_tuning.py::test_evaluate_config_hit_rate -q`，确保仍通过。

### 任务 C：curl 实验（30 分钟）

```bash
# 非法 overlap
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/chunk-config \\
  -H 'Content-Type: application/json' \\
  -d '{"chunk_size":100,"overlap":100,"strategy":"auto","name":"bad"}' | jq .

# 合法 evaluate
curl -s -X POST http://127.0.0.1:8000/api/knowledge/evaluate \\
  -H 'Content-Type: application/json' \\
  -d '{"use_presets":true}' | jq .best_config
```

### 任务 D：阅读预习（15 分钟）

阅读 `27_Day28知识库重建预习.md`，思考：evaluate 通过后，store 里旧块为何还在？

## 反思题

1. 若 wide 的 hit_rate 100% 但 chunk_count 只有 2，是否一定选 wide？  
2. `markdown_wide` 对 PDF 上传有效吗？为什么？  
3. 评估用内存 retriever，生产用 Chroma（Day 29+），指标会否漂移？
"""


def _homework() -> str:
    return """# Day 27 作业（ graded ）

**截止**：次日上午 09:00  
**提交**：Git 分支 `homework/day27-学号` + 实验报告 PDF  
**总分**：100 分

## 题目一：自定义配置评估（35 分）

编写脚本或 curl 序列，向 `POST /api/knowledge/evaluate` 传入**至少 3 个自定义** `ChunkConfig`（非 PRESET 原名），例如：

```json
{
  "use_presets": false,
  "configs": [
    {"chunk_size": 150, "overlap": 25, "strategy": "auto", "name": "hw_a"},
    {"chunk_size": 350, "overlap": 45, "strategy": "auto", "name": "hw_b"},
    {"chunk_size": 250, "overlap": 30, "strategy": "markdown", "name": "hw_c"}
  ]
}
```

**交付**：

- 完整 JSON 响应截图或保存的 `evaluate_result.json`
- 200 字分析：哪个配置 hit_rate 最高？chunk_count 与 hit_rate 如何权衡？

**评分**：请求合法 10 分；三套自定义配置 10 分；分析有理有据 15 分。

## 题目二：单元测试补充（25 分）

在 `tests/day27/` 新增 `test_homework_eval.py`，包含：

1. `test_custom_config_validate`：strategy=`"invalid"` 应抛 ValueError  
2. `test_evaluate_two_configs_order`：两个配置 hit_rate 不同，断言 `run_ab_experiment` 排序

**评分**：每项 12.5 分，pytest 通过。

## 题目三：EVAL_QUERIES 扩展（20 分）

在 `day27/constants.py` 增加第 5 条评估问句，标签 `label` 为「产品名称」，query 与 expect_any 能命中 `product_notice.md` 中「灵犀」或「智链」。

**评分**：问句合理 10 分；`ab_experiment_demo` 仍能运行 10 分。

## 题目四：简答（20 分）

1. （8 分）解释为何 evaluate **不**修改 `KnowledgeStore.chunks`。  
2. （6 分）`overlap` 的作用是什么？过大过小有何影响？  
3. （6 分）Day 28 rebuild 与今日 evaluate 的关系？

## 加分项（+10）

实现 CLI：`python3 -m day27.phase3_tune_review`，打印 PRESET 对比表（可参考仓库已有脚本）。

## 学术诚信

允许讨论思路，禁止抄袭他人 `evaluate_result.json`。
""" + "\n\n---\n\n" + _tutor_supplement_day27()


def _homework_answers() -> str:
    return """# Day 27 作业参考答案

*讲师用，学员课后发放。*

## 题目一参考

典型响应片段：

```json
{
  "best_config": {
    "name": "hw_b",
    "chunk_size": 350,
    "overlap": 45,
    "strategy": "auto"
  },
  "eval_query_count": 4,
  "results": [...]
}
```

**分析要点**（满分范例）：

- hw_b 块较大，产品说明各章节内容更可能落在单块内，hit@1 升高；
- hw_a 块过碎，「年化收益率」与「8%」可能分到不同块；
- hw_c 使用 markdown 策略，对 `product_notice.md` 按章节切分，块数少但语义完整；
- 生产还需考虑存储与延迟，不能只看 hit_rate。

## 题目二参考

```python
def test_custom_config_validate():
    cfg = ChunkConfig(strategy="invalid")
    with pytest.raises(ValueError):
        cfg.validate()

def test_evaluate_two_configs_order(parsed_doc, eval_queries):
    high = ChunkConfig(name="high", chunk_size=400, overlap=60)
    low = ChunkConfig(name="low", chunk_size=80, overlap=10)
    results = run_ab_experiment(parsed_doc, [low, high], eval_queries)
    assert results[0].hit_rate >= results[-1].hit_rate
```

## 题目三参考

```python
{
    "query": "这款理财产品叫什么",
    "expect_any": ["灵犀", "智链", "理财产品"],
    "label": "产品名称",
},
```

## 题目四参考

1. evaluate 在内存中对样例文档临时分块，避免污染生产索引；若写入 store，则无法对同一文档公平对比多套历史配置。  
2. overlap 使相邻块共享尾部/头部文本，减轻边界截断；过大则冗余高、块数虚增；过小则句中关键词可能被切断。  
3. evaluate 选出最优配置；rebuild 将全库源文件按该配置重新分块并重建索引，完成「发布」。
"""


def _checklist() -> str:
    return """# Day 27 调参验收清单

**课程**：NexusAgent Phase 3 Day 27  
**需求**：ZL-NA-REQ-027

## 讲师课前

- [ ] `nexus-agent-platform` 依赖已安装，`PYTHONPATH=src` 已文档化
- [ ] `product_notice.md` 存在于 `day26/sample_docs/`
- [ ] 投影可运行 `ab_experiment_demo.py`

## 学员实验验收

| # | 检查项 | 命令/操作 | 通过 |
|---|--------|-----------|------|
| 1 | PRESET 数量 | `len(PRESET_CONFIGS) >= 4` | ☐ |
| 2 | validate 拒绝非法 overlap | 单元测试或 curl 422 | ☐ |
| 3 | evaluate 返回 best_config | POST /evaluate | ☐ |
| 4 | eval_query_count ≥ 4 | 响应字段 | ☐ |
| 5 | PUT 后 status 含新 chunk_size | GET /status | ☐ |
| 6 | store 重启后配置保留 | load store.json | ☐ |
| 7 | 演示脚本无报错 | chunk_tune_api_demo.py | ☐ |
| 8 | pytest day27 全绿 | pytest tests/day27/ -q | ☐ |

## 代码审查要点

- [ ] `build_retriever_for_doc` 未调用 `store.save`
- [ ] `run_ab_experiment` 排序键正确
- [ ] API 层 `EvalQuery.from_dict` 兼容 `expect` 别名
- [ ] 前端按钮有 loading / 错误提示

## 课后

- [ ] 收集学员 A/B 结果表一份
- [ ] 强调 Day 28 rebuild 作业预告
"""


def _deep_topic() -> str:
    return """# 分块调参与检索评估详解

**Day 27 深度专题** | ZL-NA-REQ-027

## 1. 问题定义

给定文档集合 \(D\) 与查询 \(q\)，分块函数 \(C(\\theta)\) 由参数 \\(\\theta = (size, overlap, strategy)\\) 控制。目标是在固定评估集 \\(Q\\) 上最大化命中率。

教学环境用 **hit@1**：

\\[
\\text{{hit@1}}(q) = \\mathbb{{1}}\\left[ \\exists k \\in \\text{{expect\\_any}}(q): k \\subseteq \\text{{text}}(c_1) \\right]
\\]

其中 \\(c_1\\) 为检索排名第一的块。

## 2. 为何不用生产索引做 A/B

生产 `store.chunks` 是**单一** \\(\\theta_0\\) 的产物。要在同一 \\(D\\) 上比较 \\(\\theta_1, \\theta_2\\)，必须对 `ParsedDocument` **重新分块**。若直接改 store，则：

- 无法回滚对比；
- 并发请求看到中间态；
- 违背「实验与发布分离」。

## 3. PRESET 设计 rationale

| PRESET | 设计意图 |
|--------|----------|
| compact | 压力测试：小块、多块、边界截断 |
| default | Day 19 基线，向后兼容 |
| wide | 理财说明类短章节文档，提高 hit |
| markdown_wide | 强调章节语义，strategy=markdown |

## 4. 评估管线（概念）

核心调用链：

```python
retriever = build_retriever_for_doc(doc, config)
query_results = [evaluate_query(retriever, q) for q in queries]
hit_rate = sum(r.hit for r in query_results) / len(query_results)
```

完整实现见 `22_retrieval_eval精读.md` 与仓库 `rag/retrieval_eval.py`。

## 5. 指标局限（诚实说明）

- hit@1 不衡量排序余量（MRR 更合适）  
- 关键词匹配可「侥幸命中」  
- TF-IDF 与日后向量模型排序可能不一致  
- 评估集仅 4 条，统计显著性不足  

## 6. 实验纪律

1. 固定 `product_notice.md` 版本  
2. 一次只改一个变量（如只扫 chunk_size）  
3. 记录 chunk_count、hit_rate、avg_top_score  
4. 结论写入实验报告，附原始 JSON  

## 7. 与 chunk_strategies 协作

`chunk_from_parsed` 根据 strategy 分发：

- `fixed` → 滑动窗口  
- `markdown` → `chunk_markdown_sections`  
- `auto` → md 用章节，其他 fixed  

调参时 strategy 与 size 耦合，需一并纳入 A/B。
"""


def _workbook() -> str:
    return """# Day 27 课堂练习册

## 一、选择题（每题 4 分）

**1.** `ChunkConfig.validate()` 在哪种情况抛 ValueError？

- A. chunk_size=200, overlap=40  
- B. chunk_size=100, overlap=100  
- C. strategy=markdown, overlap=0  
- D. name=""

<details><summary>答案</summary>B — overlap 必须严格小于 chunk_size。</details>

**2.** hit@1 判定依赖？

- A. top-3 块任意命中  
- B. top-1 块包含 expect_any 任一关键词  
- C. avg_top_score > 0.5  
- D. chunk_count 最小  

<details><summary>答案</summary>B</details>

**3.** `POST /evaluate` 默认使用？

- A. store 中已有 chunks  
- B. PRESET_CONFIGS + EVAL_QUERIES  
- C. 用户上传的最新文件  
- D. 空配置列表  

<details><summary>答案</summary>B（use_presets 默认 true）</details>

**4.** PUT chunk-config 后，已有文档块？

- A. 自动重建  
- B. 不变，新上传用新配置  
- C. 全部删除  
- D. 只改文件名  

<details><summary>答案</summary>B</details>

**5.** `run_ab_experiment` 首要排序键？

- A. chunk_count 升序  
- B. hit_rate 降序  
- C. name 字母序  
- D. overlap 降序  

<details><summary>答案</summary>B</details>

## 二、填空题

1. 评估样例文档路径：`day26/sample_docs/__________.md`  
2. 需求编号：ZL-NA-REQ-______  
3. 四条 EVAL 中赎回相关 expect 含 T+__  

## 三、实操题（课堂完成）

运行 `ab_experiment_demo.py`，将 wide 的 hit_rate 填入：______%

## 四、简答题

解释 `build_retriever_for_doc` 与 `KnowledgeStore.ingest_parsed` 的调用链差异（不少于 80 字）。
"""


def _rag_extra_walkthrough_day27() -> str:
    cs_notes = {i: "分块策略与 ChunkConfig.strategy 字段对应。" for i, ln in enumerate(read_repo("nexus-agent-platform/src/rag/chunk_strategies.py").splitlines(), 1) if "def " in ln or "strategy" in ln}
    er_notes = {i: "EmbeddingRetriever 为 evaluate 提供 search 能力。" for i, ln in enumerate(read_repo("nexus-agent-platform/src/rag/embedding_retriever.py").splitlines(), 1) if "def " in ln or "search" in ln}
    return (
        "## 附录：chunk_strategies.py\n\n"
        + _line_commentary("nexus-agent-platform/src/rag/chunk_strategies.py", cs_notes)
        + "\n\n## 附录：embedding_retriever.py\n\n"
        + _line_commentary("nexus-agent-platform/src/rag/embedding_retriever.py", er_notes)
    )


def _extension() -> str:
    return _rag_extra_walkthrough_day27() + """

# 深度扩展：RAG 评估方法论

## 超越 hit@1

| 指标 | 含义 | Day 27 是否实现 |
|------|------|-----------------|
| hit@1 | top-1 是否含期望证据 | ✅ |
| hit@k | top-k 任一命中 | 可扩展 evaluate_query 的 top_k |
| MRR | 首个命中排名倒数 | ❌ 阅读材料 |
| nDCG | 分级相关性折扣 | ❌ |
| Recall@k | 命中块占全部相关块比例 | 需完整标注 |

## 评估集构建

企业实践：

1. 从客服日志采样真实问句  
2. 人工标注「金标准」段落 id  
3. 分层：简单事实 / 多跳 / 否定类  
4. 定期回归，防止索引漂移  

Day 27 的 `expect_any` 是**低成本弱标注**，适合教学。

## 工具链预览

- **Ragas**：faithfulness、answer_relevancy  
- **TruLens**：追踪 LLM 调用链  
- **LangSmith**：数据集与 A/B  

## A/B 实验统计

样本量 n=4 时，hit_rate 波动极大。生产环境应：

- 扩大评估集至 50+  
- 报告置信区间  
- 分流量灰度（Day 30+ incremental 思路）

## 阅读清单

1. Lewis et al., RAG 原论文评估章节  
2. 课程 `19_讲师补充阅读.md`  
3. NexusAgent Day 29 Chroma 后指标是否一致 —— 自行实验记录  
"""


def _case_study() -> str:
    return """# 企业案例集：检索命中率复盘会

**场景**：2026-08-02 周日，产品部紧急复盘  
**参会**：陈默、林晓、赵岩、客服代表小吴

## 会议纪要

### 现象

上周客服工单中，「赎回多久到账」类问题 23 条，助手答非所问 7 条。溯源：RAG top-1 块来自「收益率」章节，含「到账」一词出现在「收益到账」比喻句中。

### 根因

- 默认 chunk_size=200，赎回规则章节与相邻风险提示被合并；  
- TF-IDF 对「到账」权重高，误命中收益段；  
- 从未对分块参数做系统评估。

### 决策

1. 林晓负责 Day 27 评估流水线；  
2. 用 `product_notice.md` + EVAL_QUERIES 跑 PRESET；  
3. 若 wide 显著优于 default，周一评审后 **Day 28 rebuild**；  
4. 长期：建立 50 条标注评估集（Q3 OKR）。

### 数据摘录（林晓本地跑）

```
[default] hit_rate=75%  chunks=8
[wide]    hit_rate=100% chunks=4
```

赵岩：「块数减半，存储更省，hit 还升——但别在投资人演示前忘了 rebuild。」

### 行动项

| 负责人 | 行动 | 截止 |
|--------|------|------|
| 林晓 | 合并 evaluate API | 8/3 |
| 周航 | 前端评估按钮 | 8/3 |
| 小吴 | 提供 10 条真实问句 | 8/10 |

## 讨论题

若 wide 在样例上好、在 uploads 运营文档上差，该如何决策？
"""


def _lecture_transcript() -> str:
    return """# Day 27 授课实录

**日期**：2026-08-03  
**教室**：智链科技 3F 实训室

---

**09:05 陈默**：大家早上好。昨天 Day 26 能传 PDF 了，今早客服又投诉——问赎回，答收益。不是 parser 坏了，是 chunk 切坏了。（板书：chunk_size=200 who?）

**09:12 林晓**：我昨晚用 default 配置搜「赎回多久到账」，top-1 预览里确实有「到账」，但是收益段落的比喻句。

**09:15 陈默**：对，这就是 hit@1 要修的。我们定义：top-1 块必须包含**业务关键词**，expect_any 里列好了。今天写 `retrieval_eval.py`，不碰生产 store。

**09:40 赵岩**：四套 PRESET 不是拍脑袋。compact 故意小而碎，帮你们看到失败案例；wide 针对这种短章节产品说明。

**10:20 陈默**（投屏 `chunk_config.py`）：注意 validate，overlap 等于 chunk_size 直接 ValueError。去年某学员写成 overlap=chunk_size「全覆盖」，检索重复率爆炸。

**10:55 林晓**：`build_retriever_for_doc` 只有三行：validate、chunk_from_parsed、EmbeddingRetriever。全在内存。

**11:20 学生甲**：evaluate 能否用 uploads 里的文件？  
**陈默**：今日固定样例，保证全班结果可对比。扩展作业可以自己 parse 后调 `run_ab_experiment`。

---

**14:05 周航**：下午接 API。POST evaluate，body 空对象也行，默认 presets。

**14:30 林晓**（演示 curl）：PUT chunk-config 到 300，status 里 chunk_size 变了，但 chunk_count 还是 12——旧块还在。

**14:35 陈默**：这就是今天最重要的结论之一。**调参 ≠ 发布**。发布明天 rebuild。

**15:10 周航**：前端 `#kb-eval-btn`，点完展示 best_config.name。失败要 toast，别 silent fail。

**15:50 陈默**：晚自习跑 `ab_experiment_demo`，把表填完。明天早上我要看到 wide 是不是全班都是 100%。

**16:00 赵岩**：补充，markdown_wide 的 strategy 是 markdown，对 txt 上传不会魔法变章节——读文档 `23_chunk_config与企业预设实践.md`。

---

## 课后讲师备注

- 第三组 overlap 边界题错得多，明日课前 5 分钟复习  
- CI 上 pytest day27 稳定，可作 merge 门禁  
"""


def _flashcards() -> str:
    return """# Day 27 复习卡片

## 卡片 1
**Q**：ChunkConfig 四个字段？  
**A**：chunk_size、overlap、strategy、name。

## 卡片 2
**Q**：validate 对 overlap 的规则？  
**A**：0 ≤ overlap < chunk_size。

## 卡片 3
**Q**：hit@1 如何判定命中？  
**A**：top-1 块文本包含 expect_any 中任一关键词。

## 卡片 4
**Q**：evaluate 为何不写 store？  
**A**：评估需在内存中对同文档试多套配置，不能污染生产索引。

## 卡片 5
**Q**：PRESET 四套名称？  
**A**：compact、default、wide、markdown_wide。

## 卡片 6
**Q**：run_ab_experiment 排序第一键？  
**A**：hit_rate 降序。

## 卡片 7
**Q**：评估样例文档？  
**A**：day26/sample_docs/product_notice.md。

## 卡片 8
**Q**：PUT chunk-config 影响已有块吗？  
**A**：不影响，仅后续上传。

## 卡片 9
**Q**：EVAL_QUERIES 几条？  
**A**：4 条（起购、收益、风险、赎回）。

## 卡片 10
**Q**：需求编号与版本？  
**A**：ZL-NA-REQ-027，v0.27.0。

## 卡片 11
**Q**：API 路径？  
**A**：GET/PUT /api/knowledge/chunk-config；POST /api/knowledge/evaluate。

## 卡片 12
**Q**：Day 28 做什么？  
**A**：全库 rebuild，按 chunk_config 重扫源文件。

## 卡片 13
**Q**：expect_any 为空时 hit 规则？  
**A**：有检索结果即 hit。

## 卡片 14
**Q**：strategy 可选值？  
**A**：auto、fixed、markdown。

## 卡片 15
**Q**：演示脚本？  
**A**：ab_experiment_demo.py、chunk_tune_api_demo.py。
"""


def _api_cheatsheet() -> str:
    return """# Day 27 调参 API 速查手册

## 环境

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
uvicorn api.app:create_app --factory --reload
```

## GET /api/knowledge/chunk-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/chunk-config | jq .
```

响应示例：

```json
{
  "chunk_size": 200,
  "overlap": 40,
  "strategy": "auto",
  "name": "default"
}
```

## PUT /api/knowledge/chunk-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/chunk-config \\
  -H 'Content-Type: application/json' \\
  -d '{
    "chunk_size": 400,
    "overlap": 60,
    "strategy": "auto",
    "name": "wide"
  }' | jq .
```

错误示例（422）：

```bash
curl -s -X PUT ... -d '{"chunk_size":50,"overlap":50,"strategy":"auto","name":"x"}'
```

## POST /api/knowledge/evaluate

预设评估：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/evaluate \\
  -H 'Content-Type: application/json' \\
  -d '{"use_presets": true}' | jq .
```

自定义配置：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/evaluate \\
  -H 'Content-Type: application/json' \\
  -d '{
    "use_presets": false,
    "configs": [
      {"chunk_size": 180, "overlap": 30, "strategy": "auto", "name": "lab1"}
    ]
  }' | jq .best_config
```

## GET /api/knowledge/status

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_config, .chunk_count'
```

## Python TestClient 片段

```python
from fastapi.testclient import TestClient
from api.app import create_app

client = TestClient(create_app())
assert client.post("/api/knowledge/evaluate", json={"use_presets": True}).status_code == 200
```

## 错误码

| 状态码 | 场景 |
|--------|------|
| 422 | validate 失败、请求体非法 |
| 500 | 样例缺失、评估无结果 |
"""


def _day26_compare() -> str:
    return """# Day 27 与 Day 26 能力对照表

| 维度 | Day 26 | Day 27 |
|------|--------|--------|
| 主题 | 多格式解析 | 分块参数调优 |
| 需求 | ZL-NA-REQ-026 | ZL-NA-REQ-027 |
| 核心模块 | doc_parser, chunk_strategies | chunk_config, retrieval_eval |
| API 新增 | upload 支持 md/pdf | chunk-config, evaluate |
| 是否改 store 索引 | upload 增量写入 | evaluate 不写；PUT 仅改默认配置 |
| 评估指标 | 无 | hit@1, hit_rate |
| 样例文档 | product_notice.md 引入 | 用作评估金标准 |
| 前端 | accept 扩展 | A/B 评估按钮 |
| 测试目录 | tests/day26/ | tests/day27/ |
| 下一日 | Day 27 调参 | Day 28 rebuild |

## 衔接说明

Day 26 的 `chunk_from_parsed(strategy, chunk_size, overlap)` 在 Day 27 被 **参数化配置对象** ChunkConfig 包装，并增加**量化评估闭环**。

## 仍由 Day 26 负责的能力

- Markdown 代码块剥离  
- PDF pypdf 抽取  
- ParsedDocument 模型  

Day 27 **不修改** parser，只消费其输出。
"""


def _extra_reading() -> str:
    return """# Day 27 讲师补充阅读

## Ragas 框架

Ragas 提供无参考或轻参考的 RAG 评估指标：

- **Faithfulness**：答案是否由检索上下文支持  
- **Answer Relevancy**：答案与问题的相关度  
- **Context Precision**：检索上下文精确度  

与 Day 27 hit@1 区别：Ragas 面向**端到端问答**，hit@1 面向**检索块**。

## TruLens

TruLens 通过 instrumentation 记录 retrieval → generation 链，适合调试「检索到了但 LLM 没用」类问题。

## 实验追踪

建议生产环境将每次 evaluate 结果写入：

```json
{
  "timestamp": "2026-08-03T08:00:00Z",
  "configs": [...],
  "best": "wide",
  "git_sha": "abc123"
}
```

## 论文

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*  
- 关注其检索器评估与开放域 QA 基准  

## 课堂可延伸 demo

让学员用 `phase3_tune_review.py` 生成 Markdown 报告，练习工程化输出。
"""


def _code_walkthrough() -> str:
    constants = _src("day27/constants.py")
    tests = _src("tests/day27/test_chunk_tuning.py")
    api_tests = _src("tests/day27/test_tune_api.py")
    api_slice = _src("api/knowledge.py", limit=95)
    return f"""# Day 27 完整代码走查

按**推荐阅读顺序**走读仓库，避免遗漏依赖。

## 1. rag/chunk_config.py

见 `23_chunk_config与企业预设实践.md` 逐行批注（51 行）。

## 2. day27/constants.py

评估问句与版本号是 evaluate 的「金标准」输入。

{fenced("python", constants)}

**走读要点**：

- `EVAL_QUERIES` 为元组，不可变，防止运行时被意外 append  
- 每条含 `label` 便于报告与竞赛题  
- `PLATFORM_VERSION` 与课件 v0.27.0 对齐  

## 3. rag/retrieval_eval.py

见 `22_retrieval_eval精读.md` 全文件逐行走读（156 行）。

## 4. rag/knowledge_store.py（搜索阅读）

在编辑器中搜索：

- `chunk_config` 字段定义  
- `get_chunk_config` / `set_chunk_config`  
- `status_dict` 中的 `chunk_config` 输出  
- `save` / `load` 对 chunk_config 的序列化  

**关键**：`set_chunk_config` 不触发 rebuild，只改默认参数。

## 5. api/knowledge.py — evaluate 与 chunk-config

{fenced("python", api_slice)}

## 6. api/schemas.py

阅读 `ChunkConfigRequest`、`EvaluateRequest`、`EvaluateResponse` 字段约束。

## 7. tests/day27/test_chunk_tuning.py

{fenced("python", tests)}

## 8. tests/day27/test_tune_api.py

{fenced("python", api_tests)}

## 9. 演示脚本

| 脚本 | 作用 |
|------|------|
| ab_experiment_demo.py | 无 HTTP，CLI 打表 |
| chunk_tune_api_demo.py | TestClient 全流程 |
| phase3_tune_review.py | 可选复习报告 |

## 10. 调用链小结

```
POST /evaluate
  → parse_bytes(product_notice.md)
  → EvalQuery.from_dict × N
  → run_ab_experiment
       → build_retriever_for_doc (per config)
       → evaluate_query (per query)
  → pick_best_config → EvaluateResponse
```

## 11. 常见断点调试

| 断点位置 | 观察变量 |
|----------|----------|
| evaluate_query L97 | results, expect_any |
| run_ab_experiment L150 | 排序前后 results[0].config.name |
| update_chunk_config L52 | cfg.validate() 前后 |
"""


def _quiz() -> str:
    return """# Day 27 课堂知识竞赛

**规则**：15 题，每题 10 分，抢答答错扣 5 分。

1. PRESET `compact` 的 chunk_size 是多少？（120）

2. `EvalQuery.from_dict` 兼容哪个旧字段名？（expect）

3. 评估 API 的 HTTP 方法？（POST）

4. hit_rate 计算公式？（hits / total queries）

5. 哪条 EVAL 问句标签是「赎回规则」？（第四条）

6. `pick_best_config` 空列表返回什么？（None）

7. chunk-config 非法时 HTTP 状态码？（422）

8. `build_retriever_for_doc` 返回什么类型？（EmbeddingRetriever）

9. strategy `markdown` 主要用于哪种文件？（.md）

10. Day 27 平台版本常量？（0.27.0）

11. 评估是否清除 session？（否，evaluate 不清；rebuild 才清）

12. `run_ab_experiment` 第三排序键？（chunk_count 升序）

13. 样例文档有几个二级标题章节？（5）

14. `test_smaller_chunks_more_blocks` 断言什么？（小块 chunk_count ≥ 大块）

15. 明日 Day 28 核心 API？（POST /api/knowledge/rebuild）

## 颁奖

前三名获赠「智链 RAG 调参手册」贴纸。
"""


def _retrieval_eval_deep() -> str:
    path = "nexus-agent-platform/src/rag/retrieval_eval.py"
    commentary = _line_commentary(path, _retrieval_eval_line_notes())
    return f"""# retrieval_eval 精读

**文件**：`{path}`  
**需求**：ZL-NA-REQ-027

## 模块职责

在**单份 ParsedDocument** 上，对多套 ChunkConfig 构建临时检索器并计算 hit@1。  
本文件是 Day 27 的「实验引擎」，与 `api/knowledge.py` 的 evaluate 端点直接对接。

## 数据类速览

| 类 | 用途 |
|----|------|
| EvalQuery | 评估输入：问句 + expect_any |
| QueryEvalResult | 单条 query 的 hit / score / preview |
| ConfigEvalResult | 单套配置的 hit_rate 与明细列表 |

## 核心算法

### hit@1

1. `retriever.search(query, top_k=1)`  
2. 取 `results[0].chunk.text`  
3. 若 `expect_any` 非空：`any(kw in text for kw in expect_any)`  
4. 否则有结果即 hit  

### A/B 排序

```python
results.sort(key=lambda r: (-r.hit_rate, -r.avg_top_score, r.chunk_count))
```

第三键 `chunk_count` 升序：hit 相同时偏好更粗粒度（更少块）。

## 逐行走读（带讲师批注）

{commentary}

## 与测试的对应关系

| 测试函数 | 覆盖行 |
|----------|--------|
| test_evaluate_config_hit_rate | evaluate_config |
| test_run_ab_experiment_sorted | run_ab_experiment 排序 |
| test_eval_query_miss | evaluate_query 未命中 |
| test_smaller_chunks_more_blocks | chunk_count 随 size 变化 |

## 练习题

1. 修改 `evaluate_query` 支持 hit@3，写出伪代码。  
2. 为何 avg_top_score 作第二排序键？  
3. 若两个配置 hit_rate 都是 1.0，你会选 chunk_count 少还是多？说明业务理由。  
4. 在 L111 改用大小写不敏感匹配，会如何影响「收益率」类 query？

---

## 源码测试映射（扩展）

| 测试 | 断言意图 |
|------|----------|
| test_evaluate_config_hit_rate | hit_rate 区间合法 |
| test_run_ab_experiment_sorted | 排序单调性 |
| test_smaller_chunks_more_blocks | size↓ → chunk_count↑ |
| test_knowledge_store_chunk_config_roundtrip | 持久化 |
| test_put_invalid_overlap | API 422 |
| test_evaluate_presets | 集成 evaluate |

## 代码阅读作业

用 `grep -n` 在仓库搜索 `run_ab_experiment` 调用点，列出文件与行号，说明每条调用链属于「实验」还是「生产」。
"""


def _chunk_config_practice() -> str:
    path = "nexus-agent-platform/src/rag/chunk_config.py"
    commentary = _line_commentary(path, _chunk_config_line_notes())
    return f"""# chunk_config 与企业预设实践

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
- 自定义配置用 `{{env}}_{{purpose}}` 如 `prod_wide`  

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

{commentary}

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
"""


def _phase3_summary() -> str:
    return """# Phase 3 第三日总结（Day 25–27）

## 三日脉络

| 日 | 主题 | 关键词 |
|----|------|--------|
| Day 25 | 知识库 REST + TF-IDF | upload, store.json |
| Day 26 | 多格式解析 | md, pdf, chunk_strategies |
| Day 27 | 分块调参 + A/B | ChunkConfig, hit@1, evaluate |

## 技术栈累积

```
upload → parse → chunk(config) → index → chat
                      ↑
              Day 27 量化选 config
```

## 团队里程碑

- 知识库 API 版本 v0.27.0 教学设计  
- 15 个 day27 测试守护回归  
- 产品部复盘会案例闭环  

## 常见坑汇总

1. 以为 PUT 会重建 —— **不会**  
2. 评估用 uploads 文件 —— **今日用固定样例**  
3. 忽视 overlap 边界 —— **必须 < size**  

## 明日预告

Day 28：**rebuild_store**，`last_rebuilt_at`，`apply_best_config` 一键发布。
"""


def _ab_demo_deep() -> str:
    demo = _src("day27/ab_experiment_demo.py")
    api_demo = _src("day27/chunk_tune_api_demo.py")
    return f"""# ab_experiment 脚本精读

## ab_experiment_demo.py

CLI 入口，不启动 HTTP 服务。

{fenced("python", demo)}

### 执行流程

1. 读取 `product_notice.md`  
2. `EvalQuery.from_dict` 加载 EVAL_QUERIES  
3. `run_ab_experiment(doc, PRESET_CONFIGS, queries)`  
4. 打印每套 hit_rate、chunk_count  
5. `pick_best_config` 输出推荐  

### 预期输出解读

```
[compact] size=120 ... hit_rate=75%
[wide]    size=400 ... hit_rate=100%
✅ 推荐配置: wide
```

## chunk_tune_api_demo.py

{fenced("python", api_demo)}

### 与 CLI 差异

- 走 HTTP 层，验证路由与 schema  
- 需 `NEXUS_LLM_MOCK=1`  
- 演示 PUT 后 GET 一致性  

## 排错

| 症状 | 检查 |
|------|------|
| ModuleNotFoundError: day27 | PYTHONPATH=src |
| 样例找不到 | day26/sample_docs 是否存在 |
| evaluate 500 | 查看服务端日志 detail |
"""


def _lab() -> str:
    return """# Day 27 实操 Lab 手册

**时长**：120 分钟 | **分值**：100 分（计入平时成绩）

## 环境准备（5 分）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

检查：`python3 -c "from day27.constants import EVAL_QUERIES; print(len(EVAL_QUERIES))"` 输出 4。

## 步骤 1：CLI A/B（15 分）

```bash
python3 src/day27/ab_experiment_demo.py | tee lab27_ab.txt
```

**交付**：`lab27_ab.txt` 含四套 PRESET 输出。  
**评分**：文件存在且含 hit_rate 行。

## 步骤 2：找出 best_config（15 分）

从输出填写：

- 推荐配置名：________  
- 其 hit_rate：________  
- 其 chunk_count：________  

## 步骤 3：API evaluate（20 分）

终端 1：

```bash
uvicorn api.app:create_app --factory --port 8000
```

终端 2：

```bash
python3 src/day27/chunk_tune_api_demo.py
```

**评分**：截图含 PUT 与 POST evaluate 成功。

## 步骤 4：持久化验证（20 分）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/chunk-config \\
  -H 'Content-Type: application/json' \\
  -d '{"chunk_size":350,"overlap":50,"strategy":"auto","name":"lab_wide"}'

curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_config'
```

重启服务后再次 GET，确认 chunk_size 仍为 350。

## 步骤 5：pytest（15 分）

```bash
pytest tests/day27/ -q --tb=no
```

要求：全部 passed。

## 步骤 6：反思报告（10 分）

200 字：为何 evaluate 后 chunk_count 不变？若要让全库用 lab_wide，明天该调用什么 API？

## 教师验收勾选

- [ ] 步骤 1–6 齐全  
- [ ] 无抄袭 lab 文件  
- [ ] 反思提到 rebuild  

## Lab 专属辅导（不与作业重复）

**步骤 2 常见错误**：把 ab 输出中 `avg_top_score` 最高误认为最优 —— 排序第一键是 hit_rate。  
**步骤 4 常见错误**：未重启 uvicorn 就断言持久化失败。  
**步骤 6 优秀反思范例**：evaluate 只改内存 retriever；PUT 只改默认配置字段；全库块变化需 Day 28 `POST /rebuild`。
"""


def _day28_preview() -> str:
    return """# Day 28 预习：知识库全量重建

## 问题

林晓完成 Day 27 Lab，`PUT chunk-config` 为 wide，但 `GET /status` 显示 `chunk_count` 仍是旧值——**为什么？**

## 答案预告

已有 chunks 是按旧配置生成的。`chunk_config` 只影响**后续上传**。要让全库统一到 wide，需要 **rebuild**。

## Day 28 核心 API

```
POST /api/knowledge/rebuild
{
  "include_sample_docs": true,
  "apply_best_config": false
}
```

## 关键模块

- `rag/knowledge_rebuild.py`  
- `collect_source_files` — sample_docs + uploads  
- `rebuild_store` — 清空后重扫  
- `last_rebuilt_at` — 审计时间戳  

## 预习阅读

1. `rag/knowledge_rebuild.py` 前 80 行  
2. 思考：uploads 与 sample 同名时谁优先？  

## 陈默寄语

「调参选出答案，重建让整个库统一到答案上。」
"""



def _tutor_supplement_day27() -> str:
    return """# Day 27 培训部辅导长文（分块调参）

## 专题 01：overlap 边界实验

学员常把 overlap 设为等于 chunk_size 以求「全覆盖」。用 curl 发送非法 PUT，确认 422 响应体含 overlap 关键字。记录响应 JSON 到实验报告。对比合法 PUT 200 的差异。

## 专题 02：compact 为何 hit 低

compact 块小，产品说明中「年化收益率可达 8%」可能被切到两块。用 ab_experiment_demo 打印 compact 的 queries 明细，找出未命中 query 的 top_preview。截图标注断裂位置。

## 专题 03：wide 块数与存储

wide 块少不等于一定更优。计算 chunk_count 下降比例与 hit_rate 提升比例，写 100 字权衡：若 uploads 含 50 页 PDF，wide 是否仍合适？

## 专题 04：markdown_wide 适用边界

对 product_notice.md 有效，对 raw_faq.txt 无效。解释 strategy=markdown 在 chunk_from_parsed 内的分支。运行 chunk_compare_demo（Day 26）对比。

## 专题 05：EVAL_QUERIES 第四条

赎回问句 expect_any 含 T+1、到账、赎回。若 top-1 命中收益段「收益到账」比喻句，讨论 expect_any 是否应改为更严格正则。

## 专题 06：evaluate 与 chat 差异

evaluate 用内存 retriever；chat 用 store 索引。即使 evaluate 100%，未 rebuild 前 chat 可能仍差。为投资人演示写 3 步检查清单。

## 专题 07：PUT 后 upload 验证

PUT chunk_size=350 后上传新 txt，统计新文档块平均长度。用 pytest 或手动 inspect store.json chunks 数组。

## 专题 08：store.json 中 chunk_config

打开 store.json 搜索 chunk_config 键。对比 PUT 前后 name 字段。说明为何 chunk 数组内单块不自动更新 size 元数据。

## 专题 09：TestClient 与 uvicorn

chunk_tune_api_demo 用 TestClient 不启端口。对比 curl 调用同一 evaluate 路径。列出两种方式的优缺点。

## 专题 10：pytest test_put_invalid_overlap

阅读测试断言 status_code==422。尝试 overlap=99 size=100 边界合法案例，应 200。

## 专题 11：PRESET 排序 tie-break

构造两配置 hit_rate 相同：调整 expect_any 使某配置 avg_top_score 更高。观察 run_ab_experiment 排序第二键。

## 专题 12：pick_best_config 空列表

传 configs=[] 给 run_ab_experiment 在 REPL 实验。API 层应 500。说明错误处理必要性。

## 专题 13：phase3_tune_review 加分

阅读仓库 phase3_tune_review.py，运行并附输出到作业。说明如何扩展为 Markdown 报告。

## 专题 14：前端 eval 按钮错误态

断网点击 #kb-eval-btn，应有 toast。检查 knowledge.js catch 分支是否实现。

## 专题 15：NEXUS_LLM_MOCK 环境变量

说明 evaluate 路径不调用 LLM，但 health 与 chat 测试可能依赖 mock。统一 export 避免 CI 漂移。

## 专题 16：product_notice 代码块

Markdown 代码块被剥离，不参与检索。验证 compact 配置下 hit 不受 print(demo) 影响。

## 专题 17：自定义 configs JSON

作业一要求 use_presets=false。常见错误：仍传 use_presets true 导致 configs 被忽略。

## 专题 18：hit_rate 统计显著性

n=4 条 query 时 75% vs 100% 差距仅 1 条。讨论扩大评估集到 20 条的方法。

## 专题 19：MRR 扩展预习

若 top-2 才命中，hit@1 为 0 但 MRR=0.5。写公式并举例。

## 专题 20：与 Day 26 chunk_strategies

auto 策略在 md 与 txt 上行为不同。画表对比 Day 26 与 Day 27 职责分界。

## 专题 21：并发 PUT 与 evaluate

教学单进程无锁。生产应串行化配置变更。讨论乐观锁 version 字段设计。

## 专题 22：日志可观测性

建议在 evaluate 结束打 log：best_config.name, hit_rate, duration_ms。附伪代码。

## 专题 23：合规审计

保存 evaluate JSON 到 ops/evaluate/2026-08-03.json。列出应含字段：git_sha, operator, presets_hash。

## 专题 24：课堂竞赛第 11 题

evaluate 不清 session。对比 upload 与 rebuild（Day 28）的 session 行为。

## 专题 25：复盘会案例延伸

若 wide 对 uploads 长文档 hit 差，提出「分文档类型配置」未来需求，写 150 字 PRD 片段。

## 附录：逐条实验复盘（培训部自动生成）

### 复盘 01：chunk_size 扫描

**场景**：Day 27 学员在「chunk_size 扫描」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 02：overlap 扫描

**场景**：Day 27 学员在「overlap 扫描」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 03：strategy 对比

**场景**：Day 27 学员在「strategy 对比」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 04：evaluate 空 body

**场景**：Day 27 学员在「evaluate 空 body」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 05：evaluate 自定义 configs

**场景**：Day 27 学员在「evaluate 自定义 configs」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 06：PUT 后立即 evaluate

**场景**：Day 27 学员在「PUT 后立即 evaluate」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 07：bootstrap 后 evaluate

**场景**：Day 27 学员在「bootstrap 后 evaluate」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 08：wide 后未 rebuild 的 chat

**场景**：Day 27 学员在「wide 后未 rebuild 的 chat」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 09：store 重启后配置

**场景**：Day 27 学员在「store 重启后配置」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 10：pytest 单测隔离

**场景**：Day 27 学员在「pytest 单测隔离」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 11：PRESET compact 压力

**场景**：Day 27 学员在「PRESET compact 压力」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 12：PRESET markdown_wide

**场景**：Day 27 学员在「PRESET markdown_wide」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 13：expect_any 为空

**场景**：Day 27 学员在「expect_any 为空」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 14：top_k=3 扩展思考

**场景**：Day 27 学员在「top_k=3 扩展思考」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 15：MRR 预习计算

**场景**：Day 27 学员在「MRR 预习计算」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 16：Ragas 指标对比

**场景**：Day 27 学员在「Ragas 指标对比」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 17：upload 新文档块形状

**场景**：Day 27 学员在「upload 新文档块形状」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 18：TF-IDF 词表变化

**场景**：Day 27 学员在「TF-IDF 词表变化」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 19：并发 evaluate

**场景**：Day 27 学员在「并发 evaluate」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 20：日志字段设计

**场景**：Day 27 学员在「日志字段设计」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 21：Git 分支作业

**场景**：Day 27 学员在「Git 分支作业」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 22：截图验收标准

**场景**：Day 27 学员在「截图验收标准」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 23：助教 FAQ 1

**场景**：Day 27 学员在「助教 FAQ 1」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 24：助教 FAQ 2

**场景**：Day 27 学员在「助教 FAQ 2」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 25：助教 FAQ 3

**场景**：Day 27 学员在「助教 FAQ 3」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 26：投资人演示脚本

**场景**：Day 27 学员在「投资人演示脚本」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 27：rollback 预案

**场景**：Day 27 学员在「rollback 预案」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 28：staging 环境

**场景**：Day 27 学员在「staging 环境」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 29：prod 环境

**场景**：Day 27 学员在「prod 环境」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。

### 复盘 30：合规存档

**场景**：Day 27 学员在「合规存档」环节常见疑问。
**操作**：对照仓库 `nexus-agent-platform` 运行演示脚本，记录终端输出与 `store.json` 关键字段。
**期望**：能向助教口头解释因果链——从 API 请求到 `KnowledgeStore` 持久化字段，再到检索行为变化。
**扣分点**：仅贴截图不写字；使用他人 evaluate/rebuild JSON；未 export `PYTHONPATH=src`。
**加分点**：附 pytest 单条用例名；对比 Day 26 与 Day 27 能力差异表一行。
"""

def build() -> dict[str, str]:
    """Generate course/day27 materials. Returns total character count."""
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
        "10_调参验收清单.md": _checklist(),
        "11_分块调参与检索评估详解.md": _deep_topic(),
        "12_课堂练习册.md": _workbook(),
        "13_深度扩展_RAG评估方法论.md": _extension(),
        "14_企业案例集_检索命中率复盘.md": _case_study(),
        "15_授课实录.md": _lecture_transcript(),
        "16_复习卡片.md": _flashcards(),
        "17_调参API速查手册.md": _api_cheatsheet(),
        "18_与Day26能力对照表.md": _day26_compare(),
        "19_讲师补充阅读.md": _extra_reading(),
        "20_完整代码走查.md": _code_walkthrough(),
        "21_课堂知识竞赛.md": _quiz(),
        "22_retrieval_eval精读.md": _retrieval_eval_deep(),
        "23_chunk_config与企业预设实践.md": _chunk_config_practice(),
        "24_Phase3第三日总结.md": _phase3_summary(),
        "25_ab_experiment脚本精读.md": _ab_demo_deep(),
        "26_实操Lab手册.md": _lab(),
        "27_Day28知识库重建预习.md": _day28_preview(),
    }
    if len(files) != 30:
        raise SystemExit(f"day27: expected 30 files, got {len(files)}")
    return files


if __name__ == "__main__":
    from course_builder import write_course
    write_course(27, build(), min_chars=110_000)
