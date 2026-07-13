"""Content generators for the Phase 4 Agent-day narrative files that were
previously stale copies of the Day 37 (citation/rewrite) template. Each
function takes a :class:`phase4_topics.Phase4Day` and returns markdown that
is genuinely about that day's topic.
"""

from __future__ import annotations

from phase4_topics import Phase4Day


def readme(d: Phase4Day) -> str:
    mod_rows = "\n".join(f"| `{path}` | {desc} |" for path, desc in d.modules)
    extra_api = "\n".join(f"| POST {p} | 额外接口 |" for p in d.api_extra)
    demo_cmds = "\n".join(f"python3 src/{f}" for f in d.demo_files)
    return f"""# Day {d.day} 课件索引

**主题**：{d.topic} — {d.subtitle}
**需求**：{d.req}
**平台版本**：{d.ver}

## 今日交付

| 模块 | 说明 |
|------|------|
{mod_rows}

| API | 说明 |
|-----|------|
| GET/PUT {d.api_config} | 配置读写 |
| POST {d.api_preview} | 无状态预览，返回 `{d.trace_field}` |
{extra_api}

`POST /api/chat` + `{d.chat_flag}: true` → 响应含 `{d.trace_field}`{(" + " + " + ".join(d.trace_extra)) if d.trace_extra else ""}。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
{demo_cmds}
python3 -m pytest {d.tests_dir} -v
```

## 关键流程

{d.key_sentence}

## 验收

`{d.tests_dir}` {d.tests_count} 项全绿；`{d.review_file}` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day{d.day:02d}_course.py
```
"""


def narration(d: Phase4Day) -> str:
    return f"""# Day {d.day} 旁白解读

{d.prev_sentence}今天要解决的问题是：{d.story_problem}

赵岩在白板上画了一条演进线：

```
Day {d.prev_day} {d.prev_topic}  →  Day {d.day} {d.topic}
```

**今日目标**：{d.story_solution}

**行动**：Day{d.next_day} 预习 {d.next_topic}。

---

## 为什么是今天

{d.key_sentence}团队复盘上一轮迭代时发现，光靠 Day{d.prev_day} 的能力还不足以支撑运营的新需求，于是把「{d.topic}」排进了今天的 Sprint。

## 一句话总结

{d.key_sentence}
"""


def prd(d: Phase4Day) -> str:
    mod_rows = "\n".join(f"- `{path}` — {desc}" for path, desc in d.modules)
    fr_rows = "\n".join(
        f"### FR-{i + 1:03d} {desc}\n\n- 实现位置：`{path}`\n"
        for i, (path, desc) in enumerate(d.modules)
    )
    extra_api_lines = "\n".join(f"- `{p}` 额外接口" for p in d.api_extra)
    return f"""# {d.req} 产品需求文档（PRD）

**需求名称**：{d.topic}
**优先级**：P0
**平台版本**：{d.ver}

---

## 1. 背景

{d.story_problem} {d.story_solution}

## 2. 目标

{mod_rows}
- `GET/PUT {d.api_config}` 配置读写
- `POST {d.api_preview}` 无状态预览
{extra_api_lines}
- `POST /api/chat` + `{d.chat_flag}=true` → `{d.trace_field}`

## 3. 功能需求

{fr_rows}
### FR-{len(d.modules) + 1:03d} 持久化与 status

- `store.json` 新增对应 config 字段
- `GET /api/knowledge/status` 含该 config 字段
- `platform_version` 为 `{d.ver}`

### FR-{len(d.modules) + 2:03d} Chat 集成

- `api/chat.py` 在 `{d.chat_flag}=true` 且配置 `enabled` 时走本日管线
- `ChatResponse` 新增 `{d.trace_field}` 字段（及 {", ".join(d.trace_extra) if d.trace_extra else "无额外字段"}）

### FR-{len(d.modules) + 3:03d} 演示与测试

- `{d.demo_files[0]}` 打印决策/委派轨迹
- `{d.demo_files[1]}` 演示 REST API
- `{d.tests_dir}` {d.tests_count} 项覆盖单元 + API + chat

## 4. 非功能需求

### NFR-001 可观测性

每次调用都返回结构化 `{d.trace_field}`，可用于审计与教学演示。

### NFR-002 兼容性

`{d.chat_flag}=false`（默认）时行为与之前完全一致，不影响既有回归。

### NFR-003 可测试性

核心类可脱离 FastAPI 直接单测（构造 `ToolExecutor` 后 `invoke`/`run`）。

## 5. 非目标

- 接入真实大模型 function-calling（当前仍为规则/mock 决策）
- 跨 session 的长期记忆持久化

---

## 5.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
{chr(10).join(f"| FR-{i + 1:03d} | {path} | {d.tests_dir} |" for i, (path, _) in enumerate(d.modules))}

## 5.2 验收标准

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 默认配置 GET {d.api_config} | enabled=true |
| AC-02 | chat {d.chat_flag}=true | 响应含 `{d.trace_field}` |
| AC-03 | chat {d.chat_flag}=false（默认） | 行为与之前一致 |
| AC-04 | {d.tests_dir} | 全绿 |

---

## 6. 详细验收步骤

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 pytest {d.tests_dir} -v
PYTHONPATH=src python3 src/{d.demo_files[0]}
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/{d.demo_files[1]}
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| mock 决策与真实模型行为不一致 | 文档标注 mock_routing，预留切换真实模型的接口 |
| 新增字段影响既有前端解析 | `{d.trace_field}` 默认 null，向后兼容 |

---

## 8. 发布说明 {d.ver}

**新增**：{"、".join(path for path, _ in d.modules)}
**变更**：`ChatResponse` 扩展 `{d.trace_field}` 字段
**注意**：{d.chat_flag} 默认关闭，需显式开启才走新管线

---

## 9. 需求变更记录

| 版本 | 变更 |
|------|------|
| {d.ver}-draft | 仅核心类 |
| {d.ver} | API + chat 集成 + {d.tests_count} tests |

---

## 10. PRD 签字页

产品：________  研发：________  测试：________
"""


def prd_extended(d: Phase4Day) -> str:
    cases = "\n\n".join(
        f"## US-{d.day:02d}-{i + 1:02d} {title}\n\n"
        f"**场景**：{query}\n\n"
        f"**期望**：{outcome}"
        for i, (title, query, outcome) in enumerate(d.case_studies)
    )
    return f"""# {d.req} 需求扩展 — 用户故事

{cases}

---

## 边界：空 query

`invoke("")` / `run("")` → 返回「请输入有效问题。」，不进入决策循环。

## 与上一日关系

{d.key_sentence}

## 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| mock 决策命中率不足 | 中 | 演示效果打折 | 文档标注局限，预留真实模型接口 |
| 配置项过多导致运维困惑 | 低 | 排障变慢 | status 接口统一暴露当前配置 |

## 发布检查清单（扩展）

- [ ] `{d.tests_dir}` 全绿
- [ ] `{d.demo_files[0]}` / `{d.demo_files[1]}` 输出正常
- [ ] PACKAGE_STRUCTURE.md 更新
- [ ] CI Day {d.day} job 添加
- [ ] 课件 regenerate ≥100k
- [ ] PR 关联 {d.req}
"""


def file05(d: Phase4Day) -> str:
    path0, desc0 = d.modules[0]
    path1, desc1 = d.modules[-1]
    return f"""# Day {d.day} 课堂笔记（上午）

**09:00–09:40** 第一节：{d.story_problem[:30]}...
**09:40–10:30** 第二节：{path0}
**10:30–11:20** 第三节：{d.core_class} 核心循环
**11:20–12:00** 第四节：与 Day {d.prev_day} 对比走读

---

## 第一节：问题背景（40 min）

{d.story_problem}

{d.story_solution}

---

## 第二节：{desc0}（50 min）

`{path0}` 是本日配置的单一真相源，字段随日递增但结构一致：`enabled`、若干阈值/开关、`validate()` 校验。

**10:15** 课堂练习：写出三组非法配置，预测 `validate()` 抛出的异常信息。

---

## 第三节：{d.core_class}（50 min）

`{d.core_class}` 是今天的核心调度类，负责把「输入 query → 决策 → 调用工具 → 汇总」串起来，并把每一步记录进 `{d.trace_field}`，便于教学演示与审计。

**10:55** 板书：{d.key_sentence}

---

## 第四节：与 Day {d.prev_day} 对比（40 min）

{path1} — {desc1}

**11:40** 强调：Day {d.prev_day}（{d.prev_topic}）的能力仍然保留，今天是在其基础上新增一层。
"""


def file06(d: Phase4Day) -> str:
    api_curl_extra = "\n".join(
        f"curl -s -X POST http://127.0.0.1:8000{p}" for p in d.api_extra
    )
    return f"""# Day {d.day} 课堂笔记（下午）

**14:00–14:30** 第五节：{d.demo_files[0]} 现场
**14:30–15:20** 第六节：{d.core_class} 决策逻辑源码
**15:20–16:00** 第七节：{d.api_config} API
**16:00–16:45** 第八节：pytest + chat 回归

---

## 第五节：demo 现场（30 min）

```bash
PYTHONPATH=src python3 src/{d.demo_files[0]}
```

记录每个案例的委派/决策路径是否符合预期。

---

## 第六节：核心决策逻辑（50 min）

课堂上逐行读 `{d.core_class}` 的主循环，重点讲：何时判定「已经拿到答案」、何时继续下一步、`{d.trace_field}` 每一步记录哪些字段。

---

## 第七节：API（40 min）

```bash
curl -s http://127.0.0.1:8000{d.api_config} | jq .
curl -s -X PUT http://127.0.0.1:8000{d.api_config} \\
  -H 'Content-Type: application/json' -d '{{"enabled": true}}' | jq .
curl -s -X POST http://127.0.0.1:8000{d.api_preview} \\
  -H 'Content-Type: application/json' -d '{{"query": "测试问题"}}' | jq .
{api_curl_extra}
```

---

## 第八节：测试与 chat（45 min）

```bash
pytest {d.tests_dir} -v
```

**16:30** 里程碑：{d.tests_count} passed。

**16:40** 现场跑一次 `POST /api/chat` + `{d.chat_flag}: true`，对照响应里的 `{d.trace_field}`。
"""


def file07(d: Phase4Day) -> str:
    return f"""# Day {d.day} 晚自习

## 讨论（19:00–19:45）

1. {d.core_class} 与 Day {d.prev_day}（{d.prev_topic}）的边界在哪里？
2. 今天新增的 config 项，哪个字段最容易配错？
3. `{d.trace_field}` 除了教学演示，在生产环境还能用来做什么？

## 阅读（19:45–20:30）

`13_深度扩展_{d.topic.replace(' ', '')}方法论.md`

## 预习 Day {d.next_day}（20:30–21:00）

{d.next_topic}：{d.key_sentence}

---

## 深度讨论：配置项敏感性

| 配置项 | 调大/调小影响 |
|--------|----------------|
| 主开关（enabled） | 关闭后完全回退到旧行为 |
| 会话记忆（use_session_history） | 关闭后每次调用互不影响历史 |

---

## 自查清单

- [ ] 能默写 {d.core_class} 主循环三步
- [ ] 能解释 `{d.trace_field}` 每个字段含义
- [ ] 跑通两个 demo 脚本
- [ ] 读过 22 精读第一节
"""


def file08(d: Phase4Day) -> str:
    return f"""# Day {d.day} 作业

## A（35 分）：{d.core_class} 案例扩展脚本

编写脚本，对以下 query 逐条打印 `{d.trace_field}` 摘要：

{chr(10).join(f'- {q}' for _, q, _ in d.case_studies)}

**评分**：可运行 20 分；输出含每步 thought/observation 10 分；结论 5 分。

## B（25 分）：问答

1. `{d.core_class}` 主循环的终止条件是什么？
2. `{d.api_config}` 与 `{d.api_preview}` 的区别？
3. `{d.chat_flag}=false` 时 chat 行为与之前有何不同？

## C（25 分）：Lab 报告

完成 `26_实操Lab手册.md` 全部 Lab，含至少一次真实 API 调用截图。

## D（15 分）：配置审计

读取 `store.json` 对应 config 字段，输出人类可读摘要。

## E（bonus 10 分）：单元测试

为 `{d.core_class}` 补一条边界测试（例如空 query 或配置关闭时的分支）。

## F（课堂参与 10 分）

知识竞赛或 demo 现场 1 分钟：解释「什么时候该关闭 `{d.chat_flag}`」。

---

## 评分 Rubric 汇总

| 题 | 满分 | 及格线 |
|----|------|--------|
| A | 35 | 25 |
| B | 25 | 15 |
| C | 25 | 18 |
| D | 15 | 10 |
| E bonus | 10 | — |
| F | 10 | 6 |

---

## 学术诚信

允许讨论思路，禁止抄袭 Lab 报告。相似度 >80% 扣该题满分。
"""


def file09(d: Phase4Day) -> str:
    case_rows = "\n".join(
        f"| {q} | {outcome} |" for _, q, outcome in d.case_studies
    )
    return f"""# Day {d.day} 作业答案

## A 参考答案要点

| query | 预期委派/决策结果 |
|-------|-------------------|
{case_rows}

## B 答案

1. 拿到 Final Answer，或达到 `max_iterations`/`max_steps` 上限。
2. `{d.api_config}` 读写持久化配置；`{d.api_preview}` 是无状态一次性预览，不落盘。
3. 行为与升级前完全一致——新逻辑默认不介入。

## C Lab 要点

必须体现一次真实 curl/TestClient 调用与其响应截图。

## D 示例输出

```
{d.chat_flag.replace('_mode', '')}: enabled=true
```

## E bonus

```python
def test_empty_query_returns_placeholder():
    outcome = runner.invoke("")
    assert "请输入有效问题" in outcome.reply
```

---

## F 参考答案

关闭 `{d.chat_flag}` 的场景：新逻辑出现异常、需要临时回退、A/B 测试对照组。

---

## 讲评要点（讲师用）

作业 A 最常见错误：忘记结合 `history` 参数测试多轮场景。
作业 B 第 2 问：容易把 preview 和 config 接口混淆，需要强调「预览不落盘」。
"""


def file12(d: Phase4Day) -> str:
    return f"""# Day {d.day} 课堂练习册

## 练习 1：概念匹配（10 min）

将术语与定义连线：`{d.core_class}`、`{d.trace_field}`、`{d.api_config}`、`{d.chat_flag}`。

## 练习 2：判题（15 min）

判断对错：

1. `{d.chat_flag}=false`（默认）时，{d.topic} 的新逻辑不会被触发。
2. `{d.trace_field}` 只在演示脚本里出现，chat 接口不会返回。
3. `{d.tests_dir}` 全绿是今日交付的硬性验收标准之一。

**答案**：对、错（chat 响应也会带上）、对。

## 练习 3：读代码（20 min）

在 `{d.modules[-1][0]}` 中标出：配置校验行、核心决策分支、trace 记录行。

## 练习 4：手算决策（25 min）

针对 case study 「{d.case_studies[0][1]}」，写出预期的调用路径。

## 练习 5：API 填空（15 min）

补全 curl PUT 关闭 `{d.chat_flag}` 对应主开关的 JSON body。

## 练习 6：测试阅读（20 min）

读 `{d.tests_dir}` 中任意一个 API 测试，写 Given-When-Then。

## 练习 7：画时序图（15 min）

手绘今日核心流程的时序图（对照 `04_流程图与示意图.md`）。

## 练习 8：与 Day {d.prev_day} 对比表（15 min）

填三行：核心类、API 前缀、chat 开关字段。

## 练习 9：口述 60 秒（课堂）

「向产品经理解释为何要 Day {d.day}」。
"""


def file13(d: Phase4Day) -> str:
    return f"""# 深度扩展：{d.topic}方法论

## 1. 问题定义

{d.story_problem}

## 2. 设计取舍

{d.story_solution}

## 3. 与上一日的关系

{d.key_sentence}

## 4. 可观测性设计

每一步决策都落进 `{d.trace_field}`，字段设计遵循「thought（为什么）+ 动作（做什么）+ observation（结果）」三元组，方便审计与教学复盘。

## 5. 失败模式

| 现象 | 诊断 |
|------|------|
| 决策总是选同一个工具 | mock 路由规则过于粗糙，需要更细的关键词表 |
| 步数经常打满上限 | 上限设置过低，或工具返回信息不足以收敛 |
| chat 开启后行为无变化 | 忘记同时把配置 `enabled` 打开 |

## 6. 与真实大模型 function-calling 的差异

生产环境通常让大模型自己决定调用哪个工具（true function-calling）；本课在 `NEXUS_LLM_MOCK=1` 下用规则/关键词模拟这一决策，保证测试确定性，同时保留切换到真实模型的接口形状。

## 7. 推荐阅读

- ReAct: Synergizing Reasoning and Acting in Language Models
- LangChain AgentExecutor 官方文档

## 8. 实验设计模板

固定输入集合，对比 `{d.chat_flag}` 开/关两种模式下的响应差异，记录延迟与结果准确率。

## 9. 案例：企业级 Agent 平台的分层

```
Stage0: 工具注册（本课 ToolRegistry/StructuredTool）
Stage1: 决策/路由（本课 {d.core_class}）
Stage2: 可观测 trace（本课 {d.trace_field}）
Stage3: 人工干预 / 多 Agent 协作（Day42/43）
Stage4: 协议化外部工具接入（Day44 MCP）
```

## 10. 数学/工程小结

配置项数量与可维护性成反比，建议每个新配置字段都要有明确的默认值与 `validate()` 边界，避免运维猜测。
"""


def file14(d: Phase4Day) -> str:
    cases = "\n\n".join(
        f"## 案例 {i + 1}：{title}\n\n"
        f"**场景**：{query}\n"
        f"**处理**：{outcome}"
        for i, (title, query, outcome) in enumerate(d.case_studies)
    )
    return f"""# 企业案例集：{d.topic}

{cases}

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 {d.chat_flag} | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `{d.trace_field}` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT {d.api_config}` 将 `enabled` 置为 `false`，立即回退到 Day {d.prev_day} 行为。
"""


def file15(d: Phase4Day) -> str:
    return f"""# Day {d.day} 授课实录

**09:05** 讲师展示上一轮 Sprint 遗留问题：{d.story_problem}
**09:30** 白板画出核心方案：{d.story_solution}
**10:10** `{d.core_class}` live coding。
**10:55** 走读 `{d.modules[0][0]}` 配置类。
**11:20** 第一次跑通 demo，全班确认 `{d.trace_field}` 输出正常。

**14:05** demo 案例逐条讲解：{d.case_studies[0][1]}。
**14:50** 讲 `{d.chat_flag}=false` 时的兼容路径。
**15:15** `PUT {d.api_config}` 现场演示配置变更。
**15:58** pytest 第 {d.tests_count} 个全绿。
**16:42** 预告 Day {d.next_day}：{d.next_topic}。

---

## 问答实录

**15:30 学员**：`{d.trace_field}` 会不会让响应体过大？
**讲师**：默认返回，但可以通过配置关闭详细 trace，只保留最终 reply。

**16:05 学员**：关闭 `{d.chat_flag}` 最快的方式？
**讲师**：`PUT {d.api_config}` 把 `enabled` 设为 `false`，无需改代码。

---

## 讲师自评

- {d.core_class} live coding 时间刚好
- Lab 环节学员普遍能独立完成
- Day {d.next_day} 预告已铺垫

---

## 课后作业布置原话

「{d.tests_dir} 必须全绿再提交，作业 A 的案例脚本周日 23:59 前 push。」
"""


def file16(d: Phase4Day) -> str:
    return f"""# Day {d.day} 复习卡片（10 张）

**Q1** 今日核心类？ → `{d.core_class}`
**Q2** 需求号？ → {d.req}
**Q3** 平台版本？ → {d.ver}
**Q4** chat 开关字段？ → `{d.chat_flag}`
**Q5** trace 字段名？ → `{d.trace_field}`
**Q6** 配置 API 路径？ → `{d.api_config}`
**Q7** 预览 API 路径？ → `{d.api_preview}`
**Q8** 测试目录？ → `{d.tests_dir}`
**Q9** 测试数量？ → {d.tests_count}
**Q10** 与上一日的关系？ → {d.key_sentence}
"""


def file19(d: Phase4Day) -> str:
    return f"""# 讲师补充阅读

## 1. 学术脉络

{d.core_class} 所体现的「决策-执行-观察」循环，与 ReAct 论文（Yao et al.）的思路一致：让模型在自然语言里穿插推理与行动。

## 2. 与商用 Agent 框架的对照

LangChain 的 `AgentExecutor`、LangGraph 的 `StateGraph`、以及各家的 Function Calling API，都是本课对应日子的工业界对应物；本课用无第三方依赖的教学实现让学员看清底层机制。

## 3. 延迟预算案例

某金融客服团队上线类似能力后，P50 延迟增加约 10-20ms（多一次决策判断），换来的是新增场景无需改代码即可支持。

## 4. 课堂彩蛋：可观测性优先

先把 `{d.trace_field}` 设计对，比先把决策准确率调高更重要——没有可观测性，线上问题排查会非常痛苦。

## 5. 伦理与合规

Agent 自主选择工具意味着更难预测的行为路径，生产环境务必配合审计日志（对照 Day42 人工审批）。

## 6. 推荐阅读顺序

1. `{d.modules[0][0]}`
2. `{d.modules[-1][0]}`
3. Day {d.next_day} 预习
"""


def file21(d: Phase4Day) -> str:
    quiz_lines = "\n".join(f"{i + 1}. {q} → `{a}`" for i, (q, a) in enumerate(d.quiz))
    return f"""# Day {d.day} 课堂知识竞赛（10 题）

{quiz_lines}
{len(d.quiz) + 1}. 需求号？ → `{d.req}`
{len(d.quiz) + 2}. 平台版本？ → `{d.ver}`
{len(d.quiz) + 3}. 测试总数？ → `{d.tests_count}`
{len(d.quiz) + 4}. 核心类名？ → `{d.core_class}`
{len(d.quiz) + 5}. chat 开关字段？ → `{d.chat_flag}`

---

## 抢答加分题（讲师用）

**A** 写出 `{d.trace_field}` 的典型字段。
**答**：因日不同，但通常含 step/thought/observation/final_answer 之一或组合。

**B** `{d.chat_flag}=false` 时 chat 行为？
**答**：与升级前完全一致。

---

## 记分板模板

| 组 | 基础题 | 加分题 | 总分 |
|----|--------|--------|------|
| A | | | |
| B | | | |

---

## 赛后复盘（教研组）

正确率最低的题目通常是「配置项默认值」，下节课前抽查。
"""


def file23(d: Phase4Day) -> str:
    return f"""# {d.topic} 实验手册

## 实验 1：配置开关 A/B

同一批 query，分别在 `{d.chat_flag}=true/false` 下调用 `/api/chat`，对比响应差异。

## 实验 2：{d.trace_field} 逐步走读

任选一条 case study，逐步打印 `{d.trace_field}`，标注每一步对应源码行号。

## 实验 3：边界输入

测试空字符串、超长字符串、纯数字字符串三类输入，记录返回结果。

## 实验 4：降级演练

`PUT {d.api_config}` 将 `enabled` 设为 `false`，确认 chat 立即回退到旧行为。

## 实验 5：延迟测量

用 `time.perf_counter()` 测量 10 次调用的平均延迟，与 Day {d.prev_day} 对照。

---

## 报告模板

```markdown
# {d.topic} Lab
- query:
- {d.trace_field} 摘要:
- 结论:
```

---

## 常见实验坑

- 忘记 `store.save()` 导致配置未持久化
- 用旧 session_id 导致历史干扰对比结果
- 混淆 preview（不落盘）与 config（落盘）两个 API
"""


def file26(d: Phase4Day) -> str:
    api_extra_curl = "\n".join(
        f"curl -s -X POST http://127.0.0.1:8000{p} -H 'Content-Type: application/json' -d '{{}}'"
        for p in d.api_extra
    )
    return f"""# Day {d.day} 实操 Lab 手册（Lab 0-6）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
pytest {d.tests_dir} --collect-only -q
```

**通过标准**：collect ≥{d.tests_count} tests。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.status_dict().get('{d.trace_field.split('_')[0]}_config'))
"
```

---

## Lab 2：核心 demo（25 min）

```bash
python3 src/{d.demo_files[0]}
```

**通过标准**：所有 case study 都打印出委派/决策结果与 `{d.trace_field}`。

---

## Lab 3：API demo（20 min）

```bash
python3 src/{d.demo_files[1]}
```

**通过标准**：health version 为 `{d.ver}`。

---

## Lab 4：chat 对比（35 min）——必做

对每条 case study query 分别发一次 `{d.chat_flag}=true` 与默认（不带该字段）的 chat 请求，记录 `{d.trace_field}` 是否出现。

| query | {d.chat_flag}=true | 默认 |
|-------|---------------------|------|
| | | |

---

## Lab 5：curl 全家桶（20 min）

```bash
curl -s http://127.0.0.1:8000{d.api_config} | jq .
curl -s -X POST http://127.0.0.1:8000{d.api_preview} -H 'Content-Type: application/json' -d '{{"query":"测试"}}' | jq .
{api_extra_curl}
```

---

## Lab 6：全量回归（20 min）

```bash
pytest {d.tests_dir} -v
```

**通过标准**：{d.tests_count} passed。

---

## 提交

`lab/day{d.day:02d}-<姓名>.md` 含 Lab 4 表格 + Lab 6 截图。

---

## 评分 Rubric

| Lab | 分值 |
|-----|------|
| 0-1 | 10 |
| 2-3 | 30 |
| 4 | 30 |
| 5-6 | 30 |

---

## 故障排查

| 症状 | 处理 |
|------|------|
| chat 无 `{d.trace_field}` | 检查 `{d.chat_flag}` 是否为 true 且配置 enabled |
| API 404 | 确认 uvicorn 已重启加载新路由 |
| 测试失败 | 检查 `PYTHONPATH=src` 是否设置 |
"""
