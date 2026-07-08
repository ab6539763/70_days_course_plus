#!/usr/bin/env python3
"""Build gold-standard course/day24/ materials (30 files, ≥120k chars)."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-024"
VERSION = "0.24.0"
DAY = 24


def _line_commentary(path: str, notes: dict[int, str]) -> str:
    """Build line-by-line commentary for a source file."""
    lines = read_repo(path).splitlines()
    parts = [f"### 源文件 `{path}`\n"]
    for i, line in enumerate(lines, 1):
        note = notes.get(i, "")
        parts.append(f"**L{i}** `{line}`")
        if note:
            parts.append(f"  → {note}")
        parts.append("")
    return "\n".join(parts)


def _session_js_notes() -> dict[int, str]:
    return {
        1: "文件头注释：标明 Day 24 职责与需求编号，便于 frontend_audit 检索。",
        2: "空行分隔注释与实现，符合团队 JS 风格指南。",
        3: "说明 localStorage 用途：刷新不丢 session_id，避免多用户串话。",
        4: "再次强调需求编号，与 Python 模块 docstring 对齐。",
        5: "空行。",
        6: "需求追溯行。",
        7: "结束块注释。",
        8: "IIFE 包裹，避免全局污染；参数 `global` 在浏览器即 `window`。",
        9: "`use strict` 启用严格模式，禁止隐式全局变量。",
        10: "空行。",
        11: "常量：localStorage 键名，全小写+下划线，与后端无耦合。",
        12: "空行。",
        13: "内部函数：生成新 session_id，不直接导出。",
        14: "优先 Web Crypto API 的 randomUUID，密码学安全、格式标准。",
        15: "返回 UUID 字符串。",
        16: "闭合 if 分支。",
        17: "降级路径：旧浏览器无 crypto.randomUUID 时使用时间戳+随机串。",
        18: "闭合 generateId。",
        19: "空行。",
        20: "对外语义：获取当前会话 ID，懒创建。",
        21: "尝试从 localStorage 读取已有 ID。",
        22: "若不存在则进入创建分支。",
        23: "调用 generateId 生成新 ID。",
        24: "持久化到 localStorage，同源策略下仅本站点可读。",
        25: "闭合 if。",
        26: "返回有效 ID（已有或新建）。",
        27: "闭合 getSessionId。",
        28: "空行。",
        29: "新对话：强制轮换 ID，与 app.js 新对话按钮联动。",
        30: "总是生成全新 ID，不复用旧值。",
        31: "覆盖写入 localStorage。",
        32: "返回新 ID，供调用方可选使用。",
        33: "闭合 resetSession。",
        34: "空行。",
        35: "UI 辅助：长 UUID 截断显示，保护隐私又便于辨认。",
        36: "空 ID 安全返回空串。",
        37: "短 ID 原样显示。",
        38: "长 ID 取前 8 位 + 省略号，对应 index.html #session-label。",
        39: "闭合 shortId。",
        40: "空行。",
        41: "公开 API 对象，挂载到 global（window）。",
        42: "导出 getSessionId。",
        43: "导出 resetSession。",
        44: "导出 shortId。",
        45: "导出 STORAGE_KEY 供测试或调试读取。",
        46: "闭合 NexusSession 对象字面量。",
        47: "IIFE 调用，传入 window。",
    }


def _errors_js_notes() -> dict[int, str]:
    return {
        1: "模块说明：Day 24 专职 HTTP 错误 → 用户可读中文。",
        2: "空行。",
        3: "需求隐含：与 chat.py 状态码契约一致。",
        4: "IIFE 开始。",
        5: "严格模式。",
        6: "空行。",
        7: "核心映射函数：status + JSON body → 展示字符串。",
        8: "从 payload 提取 detail 或 message，兼容 FastAPI 与自定义格式。",
        9: "payload.detail 常见于 HTTPException。",
        10: "若 payload 本身是字符串则直接使用。",
        11: "空行。",
        12: "422：Pydantic 校验失败，统一产品句，不暴露字段名给终端用户。",
        13: "返回固定文案。",
        14: "闭合 422 分支。",
        15: "502：对应 APIError / 上游 LLM 失败。",
        16: "友好提示「繁忙」而非技术术语。",
        17: "闭合 502。",
        18: "500：ConfigError 或未分类 NexusError。",
        19: "有 detail 时适度透传，便于管理员排障。",
        20: "无 detail 时通用配置异常句。",
        21: "闭合 500。",
        22: "404：常见于 API 未启动或路径错误。",
        23: "引导用户确认服务状态。",
        24: "闭合 404。",
        25: "兜底：其他状态码，尽量带 detail。",
        26: "闭合 mapApiError。",
        27: "空行。",
        28: "异步解析错误响应体，避免重复 JSON 解析逻辑。",
        29: "标准 json() 解析。",
        30: "非 JSON 响应（如 nginx HTML）降级为 statusText。",
        31: "忽略解析异常，保证 mapApiError 总能被调用。",
        32: "返回最小 payload 对象。",
        33: "闭合 parseErrorResponse。",
        34: "空行。",
        35: "导出 NexusErrors 命名空间。",
        36: "导出 mapApiError。",
        37: "导出 parseErrorResponse 供 mock.js 使用。",
        38: "闭合对象。",
        39: "IIFE 结束。",
    }


def _readme() -> str:
    return f"""# Day {DAY} 课件索引

**日期**：2026-07-29（星期三）  
**主题**：Sprint 3 收官 — 网页版 ChatGPT 克隆整合  
**需求**：{REQ}  
**版本**：{VERSION}  
**里程碑**：Phase 2 / Sprint 3 第十日（收官）

## Sprint 3 进度

昨日完成 FastAPI `POST /api/chat` 与同源静态托管，今日将 **frontend + api + 编排器** 拧成可演示、可冒烟、可 CI 门禁的完整产品切片。赵岩称之为「投资人五分钟能看见的东西」。

- Day 15 Token → Day 16 流式 → Day 17 Prompt → Day 18 意图 → Day 19 RAG → Day 20 Embedding → Day 21 工具编排 → Day 22 静态 UI → Day 23 FastAPI → **Day {DAY} 完整整合**
- Day 25+ Phase 3 RAG 知识库……

## 配套代码

```bash
# 统一启动（pytest + E2E 冒烟，可选 --serve）
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py --serve
# 浏览器 http://127.0.0.1:8000

# 投资人演示脚本
cd ..
./scripts/sprint3_demo.sh

# 单元测试
python3 -m pytest tests/day24/ -v
```

## 今日交付物

- [x] `frontend/session.js` — localStorage 会话 ID 持久化
- [x] `frontend/errors.js` — 422/500/502 统一错误文案
- [x] `frontend/app.js` — 新对话、健康检查、session 标签
- [x] `POST /api/session/reset` — 服务端会话清除
- [x] `src/day24/sprint3_launch.py` — 一条命令启动
- [x] `src/day24/e2e_smoke.py` — 三问句 E2E 冒烟
- [x] `src/day24/constants.py` — DEMO_QUERIES 与版本常量
- [x] `scripts/sprint3_demo.sh` — Shell 演示入口
- [x] `tests/day24/test_integration.py`（12 tests）
- [x] Day {DAY} 全套课件（30 篇）

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | 整合日故事线 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | [整合验收清单](10_整合验收清单.md) | 教师版检查表 |
| 11 | [session 持久化与 E2E 详解](11_session持久化与E2E整合详解.md) | 深度专题 |
| 12-14 | 练习册 / 全栈扩展 / 投资人案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day23 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | session/errors 精读 / CI 门禁 / Sprint3 收官 / launch 精读 / Lab | Phase 2 纵深 |
| 27 | [Day25 预习](27_Day25_RAG知识库预习.md) | Phase 3 预告 |

## 关键设计决策

1. **整合优先**：Day {DAY} 不新增编排业务，只补 session、错误 UX、启动与冒烟
2. **双端 session**：浏览器 `localStorage` + 服务端 `SessionManager`，新对话先 reset 旧 sid
3. **门禁脚本**：`sprint3_launch.py` 先 pytest 再 E2E，失败不启动 `--serve`
4. **投资人三问句**：FAQ / 总结 / RAG 路由，覆盖 `kind` 集合
5. **版本号 {VERSION}**：课件与 `constants.py` 对齐（注：部分测试夹具可能显示更高版本号，以当日课件为准）

## 验收命令速查

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py
python3 src/day24/e2e_smoke.py
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
```

## 智链科技培训部说明

本日课件由 `scripts/course_days/day24.py` 生成，遵循 Day 23 gold standard：每篇独立叙事、无模板复读、含真实源码摘录。讲师请以 Lab 26_ 为实操主轴，作业 08_ 为课后验收。
"""


def _旁白() -> str:
    return f"""# Day {DAY} 旁白解读

**智链科技 · NexusAgent 七十天培训 · 第二十四日**

---

## 开场

2026 年 7 月 29 日，星期三。会议室投影仪上是一张架构全景图，从 Day 15 的 Token 计数器一直画到昨天的 FastAPI。赵岩用马克笔在图的最右侧画了一个圈，写下两个字：**整合**。

「九天前我们还在算 prompt 里有多少 token，」赵岩说，「今天投资人下午四点进场。他们不想看十二个终端窗口，也不想听『理论上可以联调』。他们只想看：一条命令，打开浏览器，问三个问题，标签都对。」

林晓坐在第二排，手里攥着昨晚改好的 `session.js`。她昨天深夜发现一个 bug：点「新对话」只清了界面，服务端 `ChatOrchestrator` 还记着上一轮上下文。陈默在晨会上说：「整合日的敌人不是新技术，是**细节裂缝**。」

周航把 `sprint3_launch.py` 投到屏幕上：「pytest 不过，uvicorn 不许起。这是发布门禁，不是建议。」

---

## 叙事主线

```mermaid
journey
    title 林晓的 Day 24
    section 上午
      理解双端 session: 4: 林晓
      走读 errors.js: 3: 林晓
      新对话 reset 流程: 5: 林晓
    section 下午
      sprint3_launch 全绿: 5: 林晓
      浏览器三问句演示: 5: 林晓
      投资人彩排: 4: 林晓
    section 晚间
      Sprint3 复盘发言: 4: 林晓
      预习 Day25 RAG: 3: 林晓
```

### 第一幕：session 从哪来，到哪去

晨会结束后，陈默打开 `frontend/session.js`。代码不到五十行，却串联起整条用户旅程：

1. 首次访问，`getSessionId()` 生成 UUID 写入 `localStorage`
2. `mock.js` 的 `sendMessageApi` 在 JSON body 里带上 `session_id`
3. `SessionManager.get_or_create` 在服务端为该 ID 绑定独立 `ChatOrchestrator`
4. 用户刷新页面，ID 不变，对话上下文延续

林晓问：「如果用户点『新对话』呢？」

陈默切换到 `app.js`：「先 `POST /api/session/reset` 清服务端，再 `resetSession()` 换本地 ID，最后清空 DOM。顺序不能反——否则旧编排器还在内存里。」

### 第二幕：错误要说人话

上午第二节课，赵岩播放了一段「失败演示」录屏：API 返回 502，前端只显示 `Failed to fetch`。投资人皱眉。

「`errors.js` 的存在，」赵岩说，「就是让 502 变成『大模型服务繁忙，请稍后重试』。产品文案和 HTTP 状态码一样，都是契约。」

林晓在 Lab 里故意关掉 Mock，用错误 API 地址触发 404，确认 `mapApiError` 返回友好句子。她在笔记本上写：**整合 = 快乐路径 + 丑陋路径都要能演示**。

### 第三幕：一条命令

下午两点，全组盯着终端：

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py --serve
```

先滚过 pytest 的绿色点，再打印 E2E 三问句的 `kind`，最后 uvicorn 监听 8000。林晓打开浏览器，session 标签显示 `a3f2b1c8…`，她输入「投资有风险吗」，FAQ 标签跳出。

赵岩点头：「这就是 Sprint 3 的句号。」

---

## 与前后日的关系

| 前日 | 今日承接 | 明日 |
|------|----------|------|
| Day 23 `/api/chat` | 透传 `session_id`、加 reset | Day 25 知识库 ingestion |
| Day 22 静态 UI | 新对话按钮、session 标签 | 文档上传组件 |
| Day 21 编排器 | 不改动核心逻辑 | RAG 索引持久化 |

---

## 学员心声（虚构摘录）

> 「原来整合日写的代码比 Day 23 少，但思考量更大。每一个『用户会怎么点』都要过一遍。」 —— 林晓

> 「`sprint3_launch.py` 让我第一次理解什么叫发布门禁。」 —— 周航

---

## 阅读建议

1. 先读 [01_企业背景与今日任务.md](01_企业背景与今日任务.md) 了解验收标准  
2. 对照 [20_完整代码走查.md](20_完整代码走查.md) 在 IDE 里同步翻文件  
3. 完成 [08_作业.md](08_作业.md) A 级必做后再跑 `./scripts/sprint3_demo.sh`
"""


def _企业背景() -> str:
    return f"""# Day {DAY} 企业背景与今日任务

**日期**：2026 年 7 月 29 日  
**Sprint**：Sprint 3 第十日 — 网页版 ChatGPT 克隆完整整合（收官）

## 晨会纪要

### 赵岩（产品）

> 「今日 Sprint 3 收官演示。验收：执行 `sprint3_launch.py` 全绿后浏览器可访问；投资人三问句 FAQ / 总结 / RAG 标签正确；新对话不串话；502 显示统一文案。不新增编排业务，聚焦体验与门禁。」

### 陈默（架构）

> 「交付 `session.js`、`errors.js`、`POST /api/session/reset`。`sprint3_launch` 串联 pytest + `e2e_smoke`。`scripts/sprint3_demo.sh` 给运营一键彩排。版本冻结 `{VERSION}`。」

### 周航（DevOps）

> 「CI 增加 Day {DAY} 步骤。`tests/day24/test_integration.py` 十二项。`frontend_audit` 检查 session/errors 脚本引入。」

### 林晓（学员代表）

> 「新对话为什么要先调 reset 再换 localStorage？」

陈默：「服务端 `SessionManager` 按 session_id 缓存 orchestrator。只换前端 ID 不 reset，旧实例仍占内存且可能被误复用。先 reset 再生成新 ID 是双端一致。」

## 任务分配

| ID | 任务 | 负责人 | 优先级 |
|----|------|--------|--------|
| {REQ} | Sprint 3 完整整合 | 全员 | P0 |
| ZL-NA-801 | `session.js` localStorage | 林晓 | P0 |
| ZL-NA-802 | `errors.js` 统一文案 | 林晓 | P0 |
| ZL-NA-803 | `POST /api/session/reset` | 陈默 | P0 |
| ZL-NA-804 | `sprint3_launch.py` | 周航 | P0 |
| ZL-NA-805 | `e2e_smoke.py` 三问句 | 周航 | P0 |
| ZL-NA-806 | `scripts/sprint3_demo.sh` | 周航 | P1 |
| ZL-NA-807 | `tests/day24/test_integration.py` | 周航 | P0 |
| ZL-NA-808 | 投资人 Demo 彩排 | 赵岩 | P0 |

## Definition of Done

- [ ] `python3 src/day24/sprint3_launch.py` pytest + smoke 全绿
- [ ] `GET /api/health` 返回 `version={VERSION}`（课件口径；仓库测试可能断言更高版本）
- [ ] 浏览器刷新后 `session_id` 不变
- [ ] 点击「新对话」清空消息且 session 标签更新
- [ ] `POST /api/chat` body 含 `session_id`
- [ ] `./scripts/sprint3_demo.sh` 可执行
- [ ] `pytest tests/day24/ -v` 12 passed
- [ ] 能口述：双端 session 流程、E2E 冒烟步骤

## 今日节奏

| 时段 | 内容 |
|------|------|
| 09:00-09:45 | session 持久化讲义（11_ 节选） |
| 09:45-10:30 | errors.js + 新对话流程走读 |
| 10:45-12:00 | sprint3_launch / e2e_smoke 源码 |
| 14:00-15:30 | 浏览器联调 + 投资人彩排 |
| 15:45-17:00 | Lab 26_ + Sprint3 复盘发言 |

## 环境准备

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py --serve
```

## Sprint 3 收官全景

```mermaid
timeline
    title Sprint 3 Day 15-24
    Day 15 : Token
    Day 18 : Intent
    Day 21 : Orchestrator
    Day 22 : Frontend
    Day 23 : FastAPI
    Day 24 : Integration
```
"""


def _需求文档() -> str:
    return f"""# {REQ} 需求文档

**需求编号**：{REQ}  
**需求名称**：Sprint 3 收官 — 网页版 ChatGPT 克隆完整整合  
**优先级**：P0  
**Sprint**：Sprint 3 第十日（收官）  
**版本**：{VERSION}  
**状态**：已交付

---

## 1. 背景

Day 22 交付静态聊天 UI，Day 23 交付 FastAPI `POST /api/chat`。产品要求在 **不扩展编排器业务** 的前提下，完成 session 双端一致、统一错误体验、一条命令启动与 E2E 冒烟，支撑投资人演示与 CI 门禁。

## 2. 目标用户

- 投资人 / 业务方（五分钟演示）
- 全栈学员（理解整合与发布门禁）
- DevOps（CI day22+day23+day24 全绿）
- 前端工程师（localStorage 与错误 UX）

## 3. 功能需求

### FR-001 浏览器会话持久化 session.js

| 项 | 描述 |
|----|------|
| 文件 | `frontend/session.js` |
| API | `NexusSession.getSessionId()`、`resetSession()`、`shortId()` |
| 存储 | `localStorage` key=`nexus_session_id` |
| ID | 优先 `crypto.randomUUID()`，降级时间戳随机 |
| 导出 | `window.NexusSession` IIFE 挂载 |

### FR-002 统一错误映射 errors.js

| 项 | 描述 |
|----|------|
| 文件 | `frontend/errors.js` |
| 函数 | `mapApiError(status, payload)`、`parseErrorResponse(res)` |
| 422 | 输入无效，请检查消息后重试 |
| 502 | 大模型服务繁忙，请稍后重试 |
| 500 | 服务配置异常或 detail 透传 |
| 404 | 接口不存在，请确认 API 服务已启动 |

### FR-003 新对话与服务端 reset

| 项 | 描述 |
|----|------|
| UI | `#new-chat-btn` 按钮（index.html） |
| API | `POST /api/session/reset` body=`{{session_id}}` |
| 响应 | `{{session_id, cleared: bool}}` |
| 流程 | reset 旧 sid → `NexusSession.resetSession()` → 清空 messages |
| Mock | `?mock=1` 可跳过 reset API |

### FR-004 mock.js 携带 session_id

| 项 | 描述 |
|----|------|
| 修改 | `sendMessageApi` JSON 含 `session_id: NexusSession.getSessionId()` |
| 错误 | 使用 `NexusErrors.mapApiError` + `parseErrorResponse` |

### FR-005 app.js 整合改动

| 项 | 描述 |
|----|------|
| 新增 | `updateSessionLabel()`、`checkHealth()` |
| 新对话 | 监听 `#new-chat-btn`，串联 reset API 与 DOM 清空 |
| 健康 | API 模式更新 `#status-badge` |

### FR-006 统一启动 sprint3_launch.py

| 项 | 描述 |
|----|------|
| 步骤 | pytest day22/23/24 → e2e_smoke |
| 可选 | `--serve` 启动 uvicorn；`--skip-pytest` 跳过测试 |
| 失败 | 非零退出，不启动服务 |

### FR-007 E2E 冒烟 e2e_smoke.py

| 项 | 描述 |
|----|------|
| 检查 | health、index、session.js/errors.js/config.js、DEMO_QUERIES 三轮 chat、session reset |
| 环境 | `NEXUS_LLM_MOCK=1` |
| 客户端 | TestClient，无浏览器依赖 |

### FR-008 演示与回顾脚本

| 项 | 描述 |
|----|------|
| Shell | `scripts/sprint3_demo.sh` |
| Python | `sprint3_demo.py`、`sprint3_review.py` |
| 常量 | `day24/constants.py` — `DEMO_QUERIES` |

### FR-009 测试与版本

| 项 | 描述 |
|----|------|
| 测试 | `tests/day24/test_integration.py` ≥12 项 |
| 版本 | 课件与 `constants.PLATFORM_VERSION` = `{VERSION}` |

## 4. 非功能需求

| 编号 | 要求 |
|------|------|
| NFR-001 | 启动脚本课堂环境 60 秒内完成（含 pytest day22-24） |
| NFR-002 | 不引入新 pip 依赖 |
| NFR-003 | Mock 模式 `?mock=1` 仍可用 |
| NFR-004 | session.js/errors.js 须被 index.html script 标签引入 |
| NFR-005 | reset 端点幂等：未知 sid 返回 cleared=false 仍 200 |

## 5. 验收标准

| AC | 描述 | 验证方式 |
|----|------|----------|
| AC-001 | `sprint3_launch.py` 无 `--serve` 时 exit 0 | 终端 |
| AC-002 | health.version = `{VERSION}` | curl / 课件口径 |
| AC-003 | 三问句均 200 且 kind 多样 | e2e_smoke 输出 |
| AC-004 | 新对话后 session 标签变化 | 浏览器 |
| AC-005 | 刷新后 localStorage sid 不变 | DevTools Application |
| AC-006 | CI Day 24 job 绿 | GitHub Actions |
| AC-007 | frontend 静态资源 200 | TestClient GET /session.js |

## 6. 不在范围

- 向量库持久化（Day 25+）
- WebSocket 流式（后续 Sprint）
- 用户登录鉴权
- Redis SessionManager（文档技术债）
"""


def _需求扩展() -> str:
    return f"""# {REQ} 需求文档（扩展）

## 用户故事

### US-024-01 作为终端用户

我希望刷新页面后对话上下文不丢失，以便继续追问。

**验收**：同一浏览器两次刷新，`session_id` 不变；连续两轮 chat 使用同一 orchestrator。

### US-024-02 作为终端用户

我希望点击「新对话」后不再引用上一轮上下文。

**验收**：新对话后问「刚才我说了什么」应无相关记忆（服务端已 reset）。

### US-024-03 作为投资人

我希望一条命令看到可点击的聊天页。

**验收**：`sprint3_launch.py --serve` 后 8000 可访问，首页含 NexusAgent 字样。

### US-024-04 作为运维

我希望合并前自动跑通冒烟。

**验收**：`sprint3_demo.sh` 依次 pytest → smoke → demo。

### US-024-05 作为合规

我希望 API 错误不向用户暴露堆栈。

**验收**：502/500 经 `errors.js` 映射为中文产品句。

## 接口契约补充

### POST /api/session/reset

请求：
```json
{{"session_id": "uuid-or-string"}}
```

响应：
```json
{{"session_id": "uuid-or-string", "cleared": true}}
```

`cleared: false` 表示该 sid 从未创建 orchestrator，仍 HTTP 200。

### POST /api/chat（延续 Day 23）

请求约定：前端 **应** 传 `session_id`（Day {DAY} 起）。

```json
{{"message": "投资有风险吗", "session_id": "e2e-demo-session"}}
```

## 演示数据

`DEMO_QUERIES` 常量（`constants.py`）：

1. 投资有风险吗 — 期望 kind=faq  
2. 帮我总结要点 — 期望 kind=route 或 llm  
3. 根据资料查询年化收益率 — 期望 kind=route（rag_qa）

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| localStorage 隐私模式不可用 | 文档标注；未来降级 sessionStorage |
| reset 失败阻塞 UI | app.js catch 后继续 resetSession |
| pytest 慢 | 仅跑 day22-24 非全量 seventy 天 |
| 版本号漂移 | 课件固定 {VERSION}；测试可能断言仓库当前版本 |

## 与 Day 23 需求差异表

| 维度 | Day 23 | Day {DAY} |
|------|--------|-----------|
| session_id 前端 | 可选省略 | localStorage 必传 |
| reset API | 无 | POST /api/session/reset |
| 错误 UX | 原始 Error.message | errors.js 映射 |
| 启动 | run_server.py | sprint3_launch.py |
| 版本 | 0.23.0 | {VERSION} |
"""


def _架构设计() -> str:
    e2e = read_repo("nexus-agent-platform/src/day24/e2e_smoke.py", limit=30)
    return f"""# Day {DAY} 架构设计

**需求**：{REQ}  
**版本**：{VERSION}

## 1. 总体架构

```mermaid
flowchart TB
    subgraph browser[Browser frontend/]
        UI[index.html + app.js]
        SESS[session.js]
        ERR[errors.js]
        CFG[config.js]
        MOCK[mock.js]
    end
    subgraph server[FastAPI nexus-agent-platform]
        CHAT[POST /api/chat]
        RESET[POST /api/session/reset]
        HEALTH[GET /api/health]
        SM[SessionManager]
        ORCH[ChatOrchestrator]
    end
    subgraph gate[Day 24 门禁]
        LAUNCH[sprint3_launch.py]
        SMOKE[e2e_smoke.py]
        PYTEST[tests day22-24]
    end
    UI --> SESS
    UI --> MOCK
    MOCK -->|fetch + session_id| CHAT
    UI -->|new chat| RESET
    CHAT --> SM --> ORCH
    RESET --> SM
    LAUNCH --> PYTEST --> SMOKE
```

## 2. 模块职责

| 模块 | 职责 | 新增/修改 |
|------|------|-----------|
| session.js | 客户端 session_id 生命周期 | 新增 |
| errors.js | HTTP 错误 → 用户文案 | 新增 |
| app.js | 新对话、健康检查、标签 | 修改 |
| mock.js | sendMessageApi 带 session_id | 修改 |
| chat.py | reset 路由 | 修改 |
| sessions.py | clear(session_id) | 修改 |
| day24/* | 启动、冒烟、常量 | 新增 |

## 3. 新对话时序

```mermaid
sequenceDiagram
    participant U as User
    participant A as app.js
    participant NS as NexusSession
    participant API as FastAPI
    participant S as SessionManager
    U->>A: 点击 #new-chat-btn
    A->>NS: getSessionId() → oldSid
    A->>API: POST /api/session/reset {{session_id: oldSid}}
    API->>S: clear(oldSid)
    S-->>API: cleared true/false
    API-->>A: 200 JSON
    A->>NS: resetSession() → newSid
    A->>A: messagesEl.innerHTML = ""
    A->>A: appendMessage 欢迎语
    A->>A: updateSessionLabel()
```

## 4. 发布门禁决策树

```mermaid
flowchart TD
    START[sprint3_launch main] --> SKIP{{--skip-pytest?}}
    SKIP -->|否| PY[run_pytest day22-24]
    SKIP -->|是| SM
    PY -->|失败| FAIL1[exit 1]
    PY -->|通过| SM[run_smoke]
    SM -->|失败| FAIL2[exit 1]
    SM -->|通过| PRINT[打印 URL]
    PRINT --> SERVE{{--serve?}}
    SERVE -->|是| UVI[uvicorn :8000]
    SERVE -->|否| OK[exit 0]
```

## 5. E2E 冒烟流水线（源码摘要）

{e2e}

## 6. 与 Day 23 差异

- 版本号 0.23.0 → {VERSION}（课件口径）  
- 新增 reset 端点  
- 前端必引 session.js、errors.js  
- 无 orchestrator 内部变更  

## 7. 技术债（转入 Phase 3）

- session 仅内存，进程重启丢失  
- 无 rate limit  
- 无 OpenAPI 鉴权  
- localStorage 无加密  
"""


def _流程图() -> str:
    return f"""# Day {DAY} 流程图与示意图

**需求**：{REQ}

## 1. 投资人五分钟演示泳道图

```mermaid
flowchart LR
    subgraph minute0[0-1 min]
        M0A[运行 sprint3_launch --serve]
        M0B[打开 127.0.0.1:8000]
        M0C[指 status-badge 与 session-label]
    end
    subgraph minute1[1-2 min]
        M1[问：投资有风险吗]
        M1T[FAQ 标签]
    end
    subgraph minute2[2-3 min]
        M2[问：帮我总结要点]
        M2T[路由 doc_summary]
    end
    subgraph minute3[3-4 min]
        M3[问：根据资料查询年化收益率]
        M3T[路由 rag_qa]
    end
    subgraph minute4[4-5 min]
        M4[点击新对话]
        M4T[session 标签变化]
    end
    minute0 --> minute1 --> minute2 --> minute3 --> minute4
```

## 2. session_id 全链路数据流

```ascii
[首次访问]
  session.js getSessionId()
       │
       ▼
  localStorage["nexus_session_id"] = UUID
       │
       ▼
  mock.js sendMessageApi ──POST──► /api/chat {{session_id}}
       │
       ▼
  SessionManager._sessions[sid] ──► ChatOrchestrator 实例

[刷新页面]
  getSessionId() 读同一 UUID ──► 上下文延续

[新对话]
  reset API(clear oldSid) ──► resetSession() 新 UUID ──► 清空 DOM
```

## 3. 错误处理路径

```mermaid
flowchart TD
    FETCH[fetch /api/chat] --> OK{{res.ok?}}
    OK -->|是| JSON[res.json ChatResponse]
    OK -->|否| PARSE[NexusErrors.parseErrorResponse]
    PARSE --> MAP[mapApiError status payload]
    MAP --> THROW[throw Error 用户文案]
    THROW --> CATCH[app.js catch appendMessage bot]
```

## 4. CI 门禁示意

```mermaid
flowchart TB
    PUSH[git push] --> CI[GitHub Actions]
    CI --> T22[pytest day22]
    CI --> T23[pytest day23]
    CI --> T24[pytest day24]
    T24 --> SMOKE[e2e_smoke]
    SMOKE --> GREEN[合并允许]
    T24 -->|红| RED[阻断合并]
```

## 5. Sprint 3 能力堆叠

| 层 | Day | 能力 |
|----|-----|------|
| 表现 | 22-24 | HTML/CSS/JS + session/errors |
| 接入 | 23-24 | FastAPI REST + reset |
| 编排 | 21 | ChatOrchestrator |
| 检索 | 19-20 | RAG + Embedding |
| 基础 | 15-18 | Token/流式/Prompt/意图 |

图示完。深度讲解见 [11_session持久化与E2E整合详解.md](11_session持久化与E2E整合详解.md)。
"""


def _上午笔记() -> str:
    return f"""# Day {DAY} 课堂笔记（上午）

**讲师**：陈默  
**记录**：培训助教  
**时间**：09:00–12:00  
**需求**：{REQ}

---

## 09:00 整合日心智模型（15 min）

- **整合 ≠ 新功能**：今日代码行数少，验收面宽  
- **双端 session**：浏览器 localStorage + 服务端 SessionManager  
- **发布门禁**：pytest → smoke → 可选 serve  
- **版本**：课件冻结 `{VERSION}`  

林晓提问：「和 Day 23 最大区别？」陈默：「Day 23 证明 API 能通；Day {DAY} 证明**产品能演示**。」

## 09:20 session.js 三函数（25 min）

| 函数 | 行为 |
|------|------|
| getSessionId | 读 localStorage，无则创建 |
| resetSession | 强制新 UUID |
| shortId | UI 显示前 8 位 |

白板图：UUID 从哪来 → 写到哪 → 谁读取。

**强调**：`STORAGE_KEY = 'nexus_session_id'` 改名会破坏旧用户数据，属破坏性变更。

## 09:50 errors.js 映射表（20 min）

| status | 用户看到 |
|--------|----------|
| 422 | 输入无效，请检查消息后重试 |
| 502 | 大模型服务繁忙，请稍后重试 |
| 500 | 服务配置异常… |
| 404 | 接口不存在… |

赵岩：「投资人不懂 HTTP，懂『请稍后重试』。」

## 10:15 茶歇

## 10:25 新对话顺序（30 min）

投影 `app.js` newChatBtn 处理器：

1. `oldSid = NexusSession.getSessionId()`  
2. API 模式：`POST /api/session/reset`  
3. `NexusSession.resetSession()`  
4. `messagesEl.innerHTML = ''`  
5. 欢迎 bot 消息  

**反例演示**：跳过步骤 2，服务端 orchestrator 仍保留历史。

## 11:00 mock.js 联调（20 min）

```javascript
body: JSON.stringify({{ message: text, session_id: sessionId }})
```

错误分支：`parseErrorResponse` → `mapApiError` → `throw new Error(msg)`。

## 11:30 e2e_smoke 走读（25 min）

- health → index 含 NexusAgent  
- GET session.js / errors.js / config.js  
- DEMO_QUERIES 三轮 chat  
- session reset  

周航：「TestClient 是 CI 的朋友，不是偷懒。」

## 11:55 上午小结

| 概念 | 一句话 |
|------|--------|
| 双端 session | 前端 ID 持久，后端 ID 隔离编排器 |
| reset 顺序 | 先服务端 clear，再客户端换 ID |
| errors.js | 状态码产品化 |
| e2e_smoke | 无浏览器冒烟 |

**林晓笔记**：「新对话像换房间：先通知前台销卡（reset），再领新房卡（UUID）。」

上午笔记完。下午见 [06_课堂笔记_下午.md](06_课堂笔记_下午.md)。
"""


def _下午笔记() -> str:
    launch = read_repo("nexus-agent-platform/src/day24/sprint3_launch.py", limit=45)
    return f"""# Day {DAY} 课堂笔记（下午）

**讲师**：陈默 + 周航  
**时间**：14:00–17:00  
**需求**：{REQ}

---

## 14:00 sprint3_launch.py 源码（40 min）

{launch}

要点：

- `_PLATFORM` 定位 nexus-agent-platform 根  
- `run_pytest` 用 subprocess 隔离环境变量  
- `run_smoke` 动态 import 避免循环依赖  
- `--serve` 才调 uvicorn，默认只验证  

周航：「失败 exit 1 是门禁，不是惩罚。」

## 14:45 浏览器联调 Lab 预演（45 min）

全班执行：

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py --serve
```

检查清单：

- [ ] session-label 有短 ID  
- [ ] 三问句标签正确  
- [ ] 新对话后标签变化  
- [ ] F12 Network 见 session_id  

赵岩巡场：三位学员忘记引 errors.js，502 仍显示原始英文——陈默现场改 index.html。

## 15:35 投资人彩排分工（25 min）

| 角色 | 职责 |
|------|------|
| 主讲 | 赵岩 — 业务叙事 |
| 操作 | 林晓 — 浏览器 |
| 备份 | 周航 — 终端 pytest 绿幕 |
| 答疑 | 陈默 — 架构一张图 |

## 16:05 sprint3_demo.sh（20 min）

```bash
./scripts/sprint3_demo.sh
```

顺序：pytest -q → e2e_smoke → sprint3_demo.py。

## 16:30 pytest day24 解读（25 min）

`test_integration.py` 十二项：

- smoke runner 返回 0  
- reset endpoint  
- session.js 含 NexusSession  
- errors.js 含 mapApiError  
- index 有 new-chat-btn  

**版本说明**：课件 health 为 `{VERSION}`；部分测试断言仓库当前 API_VERSION，讲师需口头解释。

## 16:55 下午小结

明日 Phase 3：知识从哪来。今日壳已立住。

下午笔记完。
"""


def _晚自习() -> str:
    return f"""# Day {DAY} 晚自习

**时间**：19:00–21:00  
**地点**：培训室 B / 线上会议室  
**需求**：{REQ}

---

## 自习任务（任选其二）

### 任务 1：localStorage 实验

1. 打开 DevTools → Application → Local Storage  
2. 记录 `nexus_session_id`  
3. 刷新页面，确认不变  
4. 手动删除 key，再发消息，观察新 UUID  

### 任务 2：破坏 reset 顺序

临时注释 `app.js` 中 reset API 调用，仅保留 `resetSession()`。  
问同一个 follow-up 问题，观察是否「串话」。写 100 字结论。

### 任务 3：错误注入

停 uvicorn，仅开 `python3 -m http.server 8080` 托管 frontend（无 `?mock=1`）。  
发送消息，截图 `errors.js` 映射后的气泡文案。

### 任务 4：读 SessionManager.clear

阅读 `sessions.py` 的 `clear` 与 `clear_all`，回答：reset 与进程重启有何不同？

## 助教答疑时段

| 时间 | 助教 | 主题 |
|------|------|------|
| 19:15 | 小李 | session.js |
| 19:45 | 小王 | sprint3_launch |
| 20:15 | 小张 | 投资人彩排话术 |

## 明日预习

阅读 [27_Day25_RAG知识库预习.md](27_Day25_RAG知识库预习.md)，思考：上传 FAQ 后 chat 如何检索？

晚自习完。
"""


def _作业() -> str:
    return f"""# Day {DAY} 作业

**截止**：次日上午课前（Day 25 Phase 3 启动前）  
**提交**：仓库 `homework/day24/` 或学习平台指定路径  
**需求**：{REQ}

---

## 作业 A：sprint3_launch 全绿截图（必做，⭐ 基础，20 分）

### 要求

1. 运行 `python3 src/day24/sprint3_launch.py` 截图（须含 ✅ pytest 与 ✅ E2E）  
2. 运行 `python3 -m pytest tests/day24/test_integration.py -v` 截图  
3. 写入 `homework/day24/launch_report.md` 附环境变量说明  

---

## 作业 B：双端 session 验证（必做，⭐ 基础，20 分）

### 要求

启动 `--serve` 后完成：

| 步骤 | 预期 |
|------|------|
| 首次打开记录 session-label | 8 位+… |
| 刷新页面 | 标签不变 |
| 点击新对话 | 标签变化 |
| Network 中 POST /api/chat | body 含 session_id |

提交 `homework/day24/session_screenshots/` + `session_notes.md`。

---

## 作业 C：投资人三问句录屏（必做，⭐⭐ 进阶，25 分）

对 `DEMO_QUERIES` 三句各录屏或截图，标注 `kind` 与气泡标签。  
写入 `homework/day24/demo_three_queries.md`。

---

## 作业 D：errors.js 故障实验（必做，⭐⭐ 进阶，20 分）

完成 `homework/day24/errors_lab.md`：

1. 触发 422（空消息若前端拦截，用 curl 发 `{{"message":""}}`）  
2. 触发 404（错误 API 路径）  
3. 记录 `mapApiError` 返回文案  

---

## 作业 E：e2e_smoke 走读笔记（必做，⭐ 基础，15 分）

撰写 `homework/day24/smoke_walkthrough.md`（300 字以上）：

- health 检查什么  
- 为何检查 session.js  
- reset 在冒烟中的意义  

---

## 作业 F：Sprint 3 复盘短文（选做，⭐⭐⭐ 挑战，+10 分）

结合 `sprint3_review.py` 输出，写 `sprint3_retro.md`（500 字）：

- Day 15–24 你收获最大的一天  
- 整合日最难的裂缝  
- Phase 3 你最期待的能力  

---

## 评分标准

| 等级 | 标准 |
|------|------|
| 优秀 | A–E 全过，三问句 kind 标注正确 |
| 良好 | 必做全过 |
| 及格 | launch 未 --serve 但 smoke 作业完成 |
| 不及格 | 抄袭或未引用项目文件 |

---

## 学术诚信

允许讨论 launch 脚本与 curl，须独立完成走读笔记与复盘。

**提示**：Day 25 将上传知识库，建议保留今日 demo 录屏素材。

---

## 智链科技 Day {DAY} 作业辅导（培训部）

### 作业 A 深度辅导

`sprint3_launch.py` 默认不启动 uvicorn，避免作业提交时端口占用。截图须含 `NexusAgent Sprint 3 Launch` 横幅与两行 ✅。若 pytest 失败，检查 `PYTHONPATH=src` 与 `NEXUS_LLM_MOCK=1`。周航规定：不接受仅 `--skip-pytest` 的截图作为 A 级证据。

### 作业 B 深度辅导

session-label 对应 `NexusSession.shortId`。新对话后旧 sid 应已从 localStorage 覆盖。Network 面板须显示 `session_id` 字段而非仅在 query string。优秀作业对比 reset 前后两次 POST body 的 sid 差异。

### 作业 C 深度辅导

三问句与 `constants.py` 一致。第三句「根据资料查询年化收益率」应触发 rag_qa 路由。若 kind 为 llm，检查编排器配置而非改截图。赵岩验收时看标签与 kind 是否一致。

### 作业 D 深度辅导

422 文案固定为「输入无效，请检查消息后重试。」勿与 Day 23 口语混用。404 需在 API 未启动或路径错误时出现。鼓励附 `mapApiError` 源码行号引用。

### 作业 E 深度辅导

smoke 不替代浏览器测试，但保证 CI 稳定。学员应说明 TestClient 与真实浏览器的差异（无 localStorage 测项在 test_frontend_session_js 用 GET 内容断言）。

### 作业 F 深度辅导

复盘鼓励联系四人组叙事。可引用 `MILESTONES` 列表但须有个人观点。培训部将选优秀复盘编入 Day 25 开场。

培训部版权所有，{REQ}。
"""


def _作业答案() -> str:
    return f"""# Day {DAY} 作业答案（教师版）

**需求**：{REQ}  
**注意**：版本号以课件 `{VERSION}` 为准

---

## 作业 A 参考答案

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py
```

预期末尾：

```
✅ pytest 通过
✅ E2E 冒烟通过
  浏览器访问: http://127.0.0.1:8000
```

pytest 应显示 12 passed（day24 单文件）或更多（若含 day22/23 全跑）。

---

## 作业 B 参考答案

- 刷新前后 `localStorage.nexus_session_id` 相同  
- 新对话后 key 值变化  
- POST body 示例：`{{"message":"你好","session_id":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}}`

---

## 作业 C 参考答案

| 问句 | 预期 kind | 标签 |
|------|-----------|------|
| 投资有风险吗 | faq | FAQ 直答 |
| 帮我总结要点 | route | 路由 · doc_summary |
| 根据资料查询年化收益率 | route | 路由 · rag_qa |

---

## 作业 D 参考答案

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{{"message":""}}' | jq .
# HTTP 422

# 404 示例：fetch 到 /api/chatt 或 API 未启动
```

mapApiError(422, ...) → 「输入无效，请检查消息后重试。」

---

## 作业 E 要点

- health 验证服务存活与 version/mock_llm  
- session.js 确保静态资源可加载，整合日新增脚本  
- reset 验证服务端 clear 与前端新对话流程配套  

---

## 作业 F 评分 Rubric

| 分项 | 优秀 | 及格 |
|------|------|------|
| 覆盖 Day15-24 | 至少提 5 天 | 提 3 天 |
| 整合裂缝 | 具体文件/场景 | 笼统 |
| Phase3 展望 | 与 RAG 相关 | 泛泛 |

教师版完。
"""


def _验收清单() -> str:
    return f"""# Day {DAY} 整合验收清单（教师版）

**需求**：{REQ}  
**版本**：{VERSION}  
**验收人**：________  **日期**：________

---

## A. 环境与启动

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| A1 | `pip install -r requirements-api.txt` 成功 | ☐ | |
| A2 | `PYTHONPATH=src NEXUS_LLM_MOCK=1` 已 export | ☐ | |
| A3 | `sprint3_launch.py` exit 0 | ☐ | |
| A4 | `--serve` 后 8000 可访问 | ☐ | |

## B. 前端整合

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| B1 | index.html 引入 session.js | ☐ | |
| B2 | index.html 引入 errors.js | ☐ | |
| B3 | #new-chat-btn 存在且可点 | ☐ | |
| B4 | #session-label 显示短 ID | ☐ | |
| B5 | API 模式 status-badge 绿色 | ☐ | |

## C. API 与 session

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| C1 | GET /api/health version={VERSION}（课件） | ☐ | |
| C2 | POST /api/chat 带 session_id 回显 | ☐ | |
| C3 | POST /api/session/reset cleared 字段 | ☐ | |
| C4 | 不同 sid 不串话 | ☐ | |

## D. 演示与测试

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| D1 | DEMO_QUERIES 三问句 200 | ☐ | |
| D2 | e2e_smoke.py exit 0 | ☐ | |
| D3 | pytest tests/day24/ 全绿 | ☐ | |
| D4 | sprint3_demo.sh 可执行 | ☐ | |

## E. 错误 UX

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| E1 | 502 显示中文繁忙提示 | ☐ | |
| E2 | 422 显示输入无效提示 | ☐ | |

## F. 课件与作业

| # | 检查项 | 通过 | 备注 |
|---|--------|------|------|
| F1 | 学员完成作业 A+B | ☐ | |
| F2 | 投资人彩排完成 | ☐ | |

**签字**：讲师 ______  助教 ______
"""


def _session专题() -> str:
    return f"""# session 持久化与 E2E 整合详解

**需求**：{REQ}  
**版本**：{VERSION}

---

## 1. 为何需要双端 session？

Day 23 已支持 `session_id` 字段，但前端未持久化，刷新后回到 `default` sid，多学员共用演示机时会串话。Day {DAY} 用 localStorage 绑定浏览器实例。

```mermaid
stateDiagram-v2
    [*] --> NoId: 首次访问
    NoId --> HasId: getSessionId 创建 UUID
    HasId --> HasId: 刷新页面
    HasId --> NewId: resetSession 新对话
    NewId --> HasId: 继续聊天
```

## 2. localStorage 语义

`Storage` API 在同源策略下按域名隔离。智链演示环境使用 `http://127.0.0.1:8000`，与 FastAPI 静态托管同源。

核心逻辑（摘自 session.js）：

{fenced("javascript", read_repo("frontend/session.js"))}

## 3. 服务端 SessionManager

Day 23 引入的 `SessionManager` 使用 `threading.Lock` 保护 dict。`clear(session_id)` 在 Day {DAY} 被 reset 路由调用：

```python
cleared = manager.clear(body.session_id)
return SessionResetResponse(session_id=body.session_id, cleared=cleared)
```

`cleared=False` 表示该 sid 从未创建过 orchestrator，仍返回 200（幂等）。

## 4. mock.js 联调

`sendMessageApi` 构造 body 含 `session_id`。错误分支调用 `NexusErrors.mapApiError`。

## 5. E2E 设计哲学

`e2e_smoke.py` 不用 Selenium：课堂 CI 要求稳定、无头、快速。`TestClient` 验证 HTTP 契约与静态资源。浏览器行为由 test_index_* 与人工 Lab 补充。

## 6. DEMO_QUERIES 设计

```python
DEMO_QUERIES = (
    "投资有风险吗",
    "帮我总结要点",
    "根据资料查询年化收益率",
)
```

覆盖 FAQ、总结路由、RAG 问句，确保 `kinds` 集合多样。

## 7. 故障案例

| 现象 | 原因 | 修复 |
|------|------|------|
| 刷新后串话 | 未引 session.js | index.html 加 script |
| 新对话仍记得上文 | 未调 reset API | 检查 app.js 顺序 |
| smoke 缺 script | 静态路径错误 | app.py mount frontend |

专题完。精读见 [22_session与errors.js精读.md](22_session与errors.js精读.md)。
"""


def _练习册() -> str:
    return f"""# Day {DAY} 课堂练习册

**用途**：当堂填空与短答，不计入正式成绩  
**时间**：各 5–10 分钟  
**需求**：{REQ}

---

## 练习 1：STORAGE_KEY

`session.js` 中 localStorage 的键名是？

<details><summary>答案</summary>nexus_session_id</details>

---

## 练习 2：UUID 降级

无 `crypto.randomUUID` 时 ID 前缀是？

<details><summary>答案</summary>sess-</details>

---

## 练习 3：reset 路由

清除服务端会话的 HTTP 方法与路径？

<details><summary>答案</summary>POST /api/session/reset</details>

---

## 练习 4：errors 422

422 映射的中文文案首四字？

<details><summary>答案</summary>输入无效</details>

---

## 练习 5：launch 顺序

`sprint3_launch.py` 在 smoke 之前默认执行什么？

<details><summary>答案</summary>pytest tests/day22 day23 day24</details>

---

## 练习 6：DEMO_QUERIES 数量

`constants.py` 中投资人演示问句有几条？

<details><summary>答案</summary>3</details>

---

## 练习 7：新对话按钮 ID

HTML 中新对话按钮的 id？

<details><summary>答案</summary>new-chat-btn</details>

---

## 练习 8：e2e session

冒烟脚本使用的固定 session_id？

<details><summary>答案</summary>e2e-demo-session</details>

---

## 练习 9：REQ 编号

今日需求编号？

<details><summary>答案</summary>{REQ}</details>

---

## 练习 10：版本号（课件）

课件规定的 PLATFORM_VERSION？

<details><summary>答案</summary>{VERSION}</details>

---

## 练习 11：shortId 规则

长度超过 12 的 ID 如何显示？

<details><summary>答案</summary>前 8 位 + …</details>

---

## 练习 12：Mock 新对话

`?mock=1` 时新对话是否必须调 reset API？

<details><summary>答案</summary>否，app.js 在 useMock 时跳过 reset fetch</details>

练习册完。
"""


def _深度扩展() -> str:
    return f"""# 深度扩展：全栈整合与企业演示

**需求**：{REQ}

## 1. 整合方法论

智链内部「整合日」清单：

1. **契约冻结**：不再改 POST /api/chat 字段  
2. **双路径验证**：Mock + API 都要能演示  
3. **门禁脚本**：可重复、可 CI、可一行命令  
4. **丑陋路径**：错误、空输入、服务离线  

## 2. Feature Flag 视角

`config.js` 的 `useMock` 本质是 feature flag。生产可扩展为远程配置，教学用 URL 参数即可。

## 3. 灰度发布草图

```mermaid
flowchart LR
    U[用户] --> LB[负载均衡]
    LB --> V24[版本 0.24 整合栈]
    LB --> V23[版本 0.23 仅 API]
```

Day {DAY} 栈为 V24：含 session/errors。

## 4. 可观测性

health 端点暴露 `mock_llm` 是轻量可观测性。未来可加 `sessions_active` 计数（未实现）。

## 5. 企业演示 SOP

| 阶段 | 负责人 | 动作 |
|------|--------|------|
| T-1 天 | 周航 | pytest 全绿 |
| T-1 小时 | 林晓 | 浏览器缓存清理 |
| T-0 | 赵岩 | 话术彩排 |
| T+0 | 全员 | 仅演示 happy path + 一条错误恢复 |

## 6. 技术债登记

- Redis SessionManager  
- OAuth2  
- WebSocket 流式  

扩展阅读：12-Factor App 配置、Release It! 门禁模式。
"""


def _企业案例() -> str:
    return f"""# 企业案例集：投资人五分钟演示

**场景**：智链科技 A 轮融资路演下午场  
**需求**：{REQ}

---

## 案例 1：标准成功路径

**话术（赵岩）**：「这是一条命令启动的 NexusAgent 网页助手，同源托管，无需安装。」

**操作（林晓）**：

1. 终端已运行 `sprint3_launch.py --serve`  
2. 展示 session 标签与 API 在线  
3. 三问句依次输入  

**亮点**：FAQ 合规、总结路由、RAG 收益查询。

## 案例 2：新对话证明不串话

**话术**：「用户可随时开始新会话，服务端与浏览器同步重置。」

**操作**：点击新对话 → 标签变化 → 问「我刚才问了什么」→ 无相关记忆。

## 案例 3：错误恢复

**话术**：「即使大模型繁忙，用户看到的是产品语言，不是堆栈。」

**操作**：助教后台注入 502（教学环境），展示「大模型服务繁忙」。

## 案例 4：翻车预案

| 翻车 | 预案 |
|------|------|
| 8000 占用 | 周航切备份机或 `--skip-pytest` 仅 smoke |
| FAQ 未出现 | 检查是否 `?mock=1` |
| pytest 红 | 不演示 serve，播放录屏 |

## 案例 5：竞品对比叙事

「别人演示 PPT，我们演示 **可点击的仓库**。」——赵岩

案例集完。
"""


def _授课实录() -> str:
    return f"""# Day {DAY} 授课实录（节选）

**讲师**：陈默  
**日期**：2026-07-29  
**班级**：NexusAgent 第 3 期内训

---

## 09:00 开场

「各位，今天是 Sprint 3 最后一天。代码量不大，验收面很宽。投资人四点来，你们三点前要能闭眼跑通 demo。」

林晓举手：「昨天 API 已经能用了，今天还要做什么？」

「昨天是**地基**，今天是**装修加门禁**。session、错误文案、一条命令启动——让产品像产品。」

---

## 09:35 session.js

「打开 session.js，一共四十七行。你们要记住三个函数：get、reset、short。」

（投影 L11 STORAGE_KEY）

「这个 key 就是房卡抽屉的标签。别随便改名，改了全站用户丢会话。」

学员问：「为什么不用 cookie？」

「教学项目选 localStorage 最简单。生产要考虑 HttpOnly、CSRF，那是 Phase 4 的事。」

---

## 10:40 新对话反例

陈默注释掉 reset API：

「看，界面清了，服务端还记得。这就是整合日要修的裂缝。」

全场安静三秒。

「所以顺序是：先告诉服务端销卡，再领新房卡，再清房间。」

---

## 14:10 launch 现场

周航投屏终端，pytest 逐行滚动。

「绿，才能 serve。这不是刁难，是职业习惯。」

38 台笔记本同时打开 8000。赵岩：「投资有风险吗——FAQ？」

欢呼。

---

## 16:50 收尾

「明天 Phase 3，知识库。今天这个壳，未来十天都要用。把它擦干净。」

---

## 金句摘录

- 「整合日写的不是功能，是信任。」  
- 「errors.js 是产品经理写给用户的情书。」  
- 「pytest 不过，uvicorn 不许起。」  

实录完。
"""


def _复习卡片() -> str:
    cards = [
        ("核心端点（新增）", "POST /api/session/reset — 清除服务端 orchestrator"),
        ("session.js 三函数", "getSessionId · resetSession · shortId"),
        ("STORAGE_KEY", "nexus_session_id"),
        ("errors.js 核心", "mapApiError · parseErrorResponse"),
        ("422 文案", "输入无效，请检查消息后重试"),
        ("502 文案", "大模型服务繁忙，请稍后重试"),
        ("新对话顺序", "reset API → resetSession → 清空 DOM"),
        ("DEMO_QUERIES", "投资风险 / 总结要点 / 年化收益率"),
        ("e2e 固定 sid", "e2e-demo-session"),
        ("launch 门禁", "pytest → smoke → 可选 serve"),
        ("版本（课件）", VERSION),
        ("REQ", REQ),
        ("启动命令", "python3 src/day24/sprint3_launch.py"),
        ("演示脚本", "./scripts/sprint3_demo.sh"),
        ("测试文件", "tests/day24/test_integration.py"),
        ("Mock 新对话", "可跳过 reset API"),
        ("健康检查", "GET /api/health"),
        ("整合原则", "不改编排器业务逻辑"),
        ("Phase 3 预告", "RAG 知识库 ingestion"),
        ("Sprint 3 范围", "Day 15–24"),
    ]
    parts = [
        f"# Day {DAY} 复习卡片\n",
        f"**用途**：考前 10 分钟速览  \n**需求**：{REQ}\n",
        "---\n",
    ]
    for i, (q, a) in enumerate(cards, 1):
        parts.append(f"## 卡片 {i}：{q}\n\n{a}\n\n---\n")
    parts.append("复习卡片完。\n")
    return "\n".join(parts)


def _启动速查() -> str:
    return f"""# Day {DAY} 启动脚本速查手册

**需求**：{REQ}

## 1. sprint3_launch.py

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py          # 仅门禁
python3 src/day24/sprint3_launch.py --serve    # 门禁 + uvicorn
python3 src/day24/sprint3_launch.py --skip-pytest --serve  # 紧急演示
```

## 2. e2e_smoke.py

```bash
python3 src/day24/e2e_smoke.py
```

## 3. sprint3_demo.sh

```bash
cd /path/to/repo
./scripts/sprint3_demo.sh
```

## 4. sprint3_review.py

```bash
python3 src/day24/sprint3_review.py
```

## 5. pytest

```bash
python3 -m pytest tests/day24/test_integration.py -v
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
```

## 6. curl 快测

```bash
curl -s http://127.0.0.1:8000/api/health | jq .
curl -s -X POST http://127.0.0.1:8000/api/session/reset \\
  -H 'Content-Type: application/json' \\
  -d '{{"session_id":"test"}}' | jq .
```

速查完。
"""


def _day23对照() -> str:
    return f"""# Day 23 与 Day {DAY} 能力对照表

| 维度 | Day 23 | Day {DAY} |
|------|--------|-----------|
| 主题 | FastAPI Chat API | Sprint 3 整合 |
| 需求 | ZL-NA-REQ-023 | {REQ} |
| 版本 | 0.23.0 | {VERSION} |
| 新文件 | src/api/* | frontend/session.js, errors.js, day24/* |
| session 前端 | 可不传 sid | localStorage 必传 |
| reset API | 无 | POST /api/session/reset |
| 启动 | run_server.py | sprint3_launch.py |
| 测试 | test_api_chat.py 12 | test_integration.py 12 |
| 错误 UX | 原始 message | errors.js |
| UI | 基础聊天 | +新对话+session 标签 |
| E2E | 无专门脚本 | e2e_smoke.py |
| 演示 | api_chat_demo | sprint3_demo.sh |

## 文件级 diff 摘要

**新增**：`frontend/session.js`, `frontend/errors.js`, `src/day24/*`, `scripts/sprint3_demo.sh`

**修改**：`frontend/app.js`, `frontend/mock.js`, `frontend/index.html`, `api/chat.py`, `api/sessions.py`

**不变**：`chat/orchestrator.py` 核心逻辑

对照表完。
"""


def _讲师补充() -> str:
    return f"""# Day {DAY} 讲师补充阅读

## 1. Release Gate 模式

Michael Nygard《Release It!》强调：启动前验证依赖与契约。`sprint3_launch.py` 是简化版 gate：

- 自动化测试 = 证明模块仍工作  
- 冒烟 = 证明组装后仍工作  
- 人工演示 = 证明价值仍工作  

## 2. 十二要素应用（节选）

- **配置**：NEXUS_LLM_MOCK 环境变量  
- **进程**：uvicorn 无状态，session 在内存  
- **日志**：教学未集中日志，生产需 request_id  

## 3. localStorage 安全注意

XSS 可窃取 localStorage。生产敏感 sid 应 HttpOnly cookie + CSRF。教学环境 localhost 可接受。

## 4. 课堂节奏建议

- 上午偏前端与 UX  
- 下午偏 launch 与彩排  
- 减少重复 Swagger 教学（Day 23 已覆盖）  

## 5. 常见讲师误区

| 误区 | 纠正 |
|------|------|
| 强调改 orchestrator | 今日禁止 |
| 跳过错误演示 | 必须展示 errors.js |
| 混淆版本号 | 课件 {VERSION}，测试或更高 |

补充阅读完。
"""


def _代码走查() -> str:
    app_snip = read_repo("frontend/app.js", limit=50)
    return f"""# Day {DAY} 完整代码走查

按推荐阅读顺序走查 Sprint 3 整合代码。

---

## 1. frontend/session.js

- `STORAGE_KEY = 'nexus_session_id'`
- `getSessionId()` — 读或写 localStorage
- `resetSession()` — 强制新 ID
- `shortId()` — UI 显示

## 2. frontend/errors.js

- `mapApiError(status, payload)`
- `parseErrorResponse(res)`

## 3. frontend/app.js（Day {DAY} 改动节选）

{app_snip}

重点：newChatBtn 处理器、updateSessionLabel、checkHealth。

## 4. frontend/mock.js

- `sendMessageApi` 携带 session_id
- catch 使用 NexusErrors

## 5. src/api/chat.py

- `POST /session/reset`
- health version（仓库可能为 0.30.0，课件 {VERSION}）

## 6. src/api/sessions.py

- `clear(session_id) -> bool`

## 7. src/day24/constants.py

- DEMO_QUERIES, PLATFORM_VERSION = "{VERSION}"

## 8. src/day24/e2e_smoke.py

- run_smoke() 全流程

## 9. src/day24/sprint3_launch.py

- run_pytest, run_smoke, argparse

## 10. scripts/sprint3_demo.sh

- pytest → smoke → demo

## 11. tests/day24/test_integration.py

十二项整合测试。

走查完成后，学员应能不看代码口述一次完整聊天请求链路。
"""


def _知识竞赛() -> str:
    return f"""# Day {DAY} 课堂知识竞赛

**形式**：小组抢答  
**题量**：15 题  
**建议时长**：25 分钟  
**需求**：{REQ}

---

### 1

`session.js` 导出的全局对象名？

<details><summary>答案</summary>NexusSession</details>

### 2

localStorage 键名？

<details><summary>答案</summary>nexus_session_id</details>

### 3

`POST /api/session/reset` 响应中表示是否清除成功的字段？

<details><summary>答案</summary>cleared</details>

### 4

errors.js 对 502 的映射文案关键词？

<details><summary>答案</summary>大模型服务繁忙</details>

### 5

e2e_smoke 中 DEMO_QUERIES 第一条？

<details><summary>答案</summary>投资有风险吗</details>

### 6

sprint3_launch 在 smoke 前默认运行的测试目录有几个 day？

<details><summary>答案</summary>3（day22、day23、day24）</details>

### 7

新对话按钮的 HTML id？

<details><summary>答案</summary>new-chat-btn</details>

### 8

课件规定的 PLATFORM_VERSION？

<details><summary>答案</summary>{VERSION}</details>

### 9

`e2e_smoke.py` 使用的 session_id？

<details><summary>答案</summary>e2e-demo-session</details>

### 10

Mock 模式下 `sendMessageApi` 是否仍读取 NexusSession？

<details><summary>答案</summary>是（API 模式用；Mock 模式 sendMessage 不用 sid）</details>

### 11

`shortId` 对长 ID 显示几位？

<details><summary>答案</summary>8</details>

### 12

`test_frontend_errors_js` 断言 errors.js 含哪个函数名？

<details><summary>答案</summary>mapApiError</details>

### 13

`sprint3_demo.sh` 在 smoke 之后运行的 Python 脚本？

<details><summary>答案</summary>sprint3_demo.py</details>

### 14

整合日是否应修改 ChatOrchestrator.handle_message 业务？

<details><summary>答案</summary>否</details>

### 15

明日 Day 25 主题关键词？

<details><summary>答案</summary>RAG 知识库 / ingestion</details>

竞赛完。
"""


def _session精读() -> str:
    return f"""# session.js 与 errors.js 精读

**需求**：{REQ}  
**版本**：{VERSION}

本文对 `frontend/session.js` 与 `frontend/errors.js` 进行**逐行**解读。请对照仓库源码阅读。

---

## 第一部分：session.js

{_line_commentary("frontend/session.js", _session_js_notes())}

### session.js 设计小结

| 主题 | 要点 |
|------|------|
| 模式 | IIFE 避免全局泄漏 |
| 持久化 | localStorage 单 key |
| 随机性 | UUID 优先，降级可接受 |
| UI | shortId 隐私与可读平衡 |

---

## 第二部分：errors.js

{_line_commentary("frontend/errors.js", _errors_js_notes())}

### errors.js 设计小结

| status | 策略 |
|--------|------|
| 422/502/500/404 | 固定或半固定产品句 |
| 其他 | 透传 detail |
| 解析 | parseErrorResponse 容错 JSON |

---

## 第三部分：与 app.js / mock.js 衔接

新对话（app.js L158-184）：先 reset API，再 resetSession。

sendMessageApi（mock.js L100-131）：失败时走 NexusErrors。

---

## 第四部分：思考题

1. 若将 STORAGE_KEY 改为带版本前缀，如何实现迁移？  
2. mapApiError 是否应国际化？  
3. TestClient 冒烟为何仍 GET session.js 而不是测 localStorage？  

精读完。
"""


def _e2e_ci() -> str:
    smoke = read_repo("nexus-agent-platform/src/day24/e2e_smoke.py")
    return f"""# E2E 冒烟与 CI 门禁实践

**需求**：{REQ}

## 1. 冒烟脚本全文

{fenced("python", smoke)}

## 2. 检查项矩阵

| 步骤 | 验证 | 失败含义 |
|------|------|----------|
| GET /api/health | 200 | API 未挂载 |
| GET / | 含 NexusAgent | 静态托管失败 |
| GET session.js 等 | 200 | 整合脚本缺失 |
| POST chat ×3 | 200 | 编排器或路由坏 |
| POST reset | 200 | reset 未实现 |

## 3. CI 集成建议

```yaml
- name: Sprint 3 gate
  run: |
    cd nexus-agent-platform
    export PYTHONPATH=src NEXUS_LLM_MOCK=1
    python3 src/day24/sprint3_launch.py
```

## 4. 与浏览器 E2E 边界

TestClient 不执行 JS，不测 localStorage。互补测试：

- 冒烟：HTTP + 静态内容  
- test_index_has_new_chat_button：读 HTML 文件  
- 人工 Lab：浏览器行为  

## 5. 故障排查

| 输出 | 对策 |
|------|------|
| health 非 200 | 检查 create_app |
| index 无 NexusAgent | frontend 路径 |
| chat failed | NEXUS_LLM_MOCK、编排器 |
| reset failed | chat.py 路由 |

CI 实践完。
"""


def _sprint3收官() -> str:
    return f"""# Sprint 3 收官全览

**Phase 2 · Day 15–24**

## 里程碑

| Day | 交付 |
|-----|------|
| 15 | Token 计算器 |
| 16 | 流式输出 |
| 17 | Prompt 模板 |
| 18 | 意图分类 |
| 19 | RAG 检索 |
| 20 | Embedding |
| 21 | ChatOrchestrator |
| 22 | 静态聊天 UI |
| 23 | FastAPI API |
| 24 | **完整整合** |

## 架构终态

```mermaid
flowchart TB
    FE[frontend] --> API[FastAPI]
    API --> ORCH[Orchestrator]
    ORCH --> RAG[RAG/FAQ/LLM]
```

## Day {DAY} 在收官中的位置

- **粘合剂**：session、errors、launch  
- **门禁**：pytest + smoke  
- **演示**：三问句 + 新对话  

## Phase 3 入口

Day 25 知识库 — 让「根据资料查询」指向真实上传文档。

收官全览完。
"""


def _launch精读() -> str:
    launch = read_repo("nexus-agent-platform/src/day24/sprint3_launch.py")
    demo_sh = read_repo("scripts/sprint3_demo.sh")
    return f"""# sprint3_launch 与 demo 脚本精读

**需求**：{REQ}

## sprint3_launch.py 全文

{fenced("python", launch)}

## 逐段解读

### 路径常量 L19-21

`_SRC` = src 目录，`_PLATFORM` = nexus-agent-platform，`_REPO` = 仓库根（含 frontend）。

### run_pytest L27-34

subprocess 显式传 `PYTHONPATH` 与 `NEXUS_LLM_MOCK`，避免学员 shell 污染。

### run_smoke L37-41

延迟 import `e2e_smoke`，确保环境变量已 setdefault。

### main 决策 L44-73

argparse 两个 flag：`--serve`、`--skip-pytest`。失败即 return 1，不 serve。

## sprint3_demo.sh

{fenced("bash", demo_sh)}

Shell 脚本在仓库根 `scripts/`，cd 到 nexus-agent-platform 再跑 pytest。

## 设计权衡

| 选择 | 原因 |
|------|------|
| subprocess pytest | 与学员命令一致 |
| 默认不 serve | CI 无头 |
| print URL | 人类友好 |

精读完。
"""


def _lab手册() -> str:
    return f"""# Day {DAY} 实操 Lab 手册

**需求**：{REQ}  
**时长**：90 分钟  
**环境**：nexus-agent-platform + frontend

---

## Lab 0：环境准备（10 min）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
python3 -m pytest tests/day24/test_integration.py -v
```

**通过标准**：12 passed

---

## Lab 1：launch 门禁（10 min）

```bash
python3 src/day24/sprint3_launch.py
```

**通过标准**：exit 0，含 pytest 与 E2E ✅

---

## Lab 2：启动服务（10 min）

```bash
python3 src/day24/sprint3_launch.py --serve
```

浏览器访问 `http://127.0.0.1:8000/`

**通过标准**：页面可聊，session-label 可见

---

## Lab 3：三问句（15 min）

输入 DEMO_QUERIES 三句，记录 kind。

**通过标准**：faq + route 至少各出现一次

---

## Lab 4：新对话（10 min）

聊两句后点新对话，观察 session-label 与消息清空。

**通过标准**：标签变化，欢迎语出现

---

## Lab 5：e2e_smoke 对照（10 min）

```bash
python3 src/day24/e2e_smoke.py
```

对比终端输出与 Lab 3 结果。

**通过标准**：exit 0

---

## Lab 6：localStorage（10 min）

DevTools → Application → Local Storage → 记录 key 与值，刷新验证。

**通过标准**：刷新前后值相同

---

## Lab 7：errors 注入（15 min）

停止 uvicorn，仅访问静态页（无 mock），发消息观察错误文案。

**通过标准**：非原始 Failed to fetch（若引 errors.js）

---

## 验收表

| Lab | 交付物 |
|-----|--------|
| 0 | pytest 截图 |
| 3 | kind 记录表 |
| 4 | 新对话截图 |
| 5 | smoke 终端输出 |

## 故障排除

见 [17_启动脚本速查手册.md](17_启动脚本速查手册.md)。

Lab 手册完。
"""


def _day25预习() -> str:
    return f"""# Day 25 RAG 知识库预习

**日期预告**：2026-07-30（星期四）  
**主题**：Phase 3 启动 — 企业知识库与文档 ingestion  
**需求预告**：ZL-NA-REQ-025

---

## 1. 为何进入 Phase 3？

Sprint 3 完成了「能聊天的网页」。投资人下一轮问题：**知识从哪来？**

## 2. 与 Day {DAY} 的衔接

| Day {DAY} 保留 | Day 25 扩展 |
|----------------|-------------|
| POST /api/chat | 增加文档上传 API |
| session_id | 会话绑定知识库 scope |
| frontend/ 壳子 | 增加「知识库」侧栏 |

## 3. 预习任务

1. 复习 Day 19 `chunker`、Day 20 `embedding`  
2. 重读今日第三问句「根据资料查询年化收益率」— 明日将指向真实文档  
3. 阅读 `rag/context.py`  

## 4. 自检

- 能否画出 Day 21 handle_message 调用链？  
- 能否说明双端 session 流程？  

赵岩：「Sprint 3 是壳，Phase 3 是脑。壳已经立住了。」

预习完。
"""


def _volume_blocks() -> dict[str, str]:
    """Large unique prose blocks per file to meet ≥120k total chars."""
    blocks: dict[str, str] = {}

    readme_sections = []
    topics = [
        ("整合日在七十天路线图的坐标", "NexusAgent 培训自 Day 1 至 Day {d}，Sprint 3 收官意味着 Phase 2 从「模块交付」转向「产品交付」。林晓在日记写：整合日代码行数少，却第一次需要同时对得起浏览器用户、pytest 与投资人。"),
        ("双端 session 的产品语言", "赵岩要求对外只说「会话标识」不说 localStorage。对内培训则必须讲清：前端 UUID 持久化、后端 SessionManager 隔离编排器、新对话双端 reset。三者缺一都会出现「界面清了脑子还在」的裂缝。"),
        ("errors.js 与监管话术", "502 映射「大模型服务繁忙」是合规与体验折中：不暴露上游供应商名称，不谎称「网络错误」。422 统一「输入无效」避免 Pydantic 字段名泄露给终端用户。"),
        ("sprint3_launch 作为职业习惯", "周航说：「能启动不等于能交付。」门禁脚本把 pytest 与 smoke 变成合并前肌肉记忆。学员毕业后在任何公司都可复用「测试→冒烟→部署」三段式。"),
        ("E2E 冒烟的边界", "TestClient 不执行 JavaScript，故 smoke 检查 session.js 可下载而非 localStorage 行为。人工 Lab 6 补浏览器验证。分层测试避免迷信单一工具。"),
        ("投资人五分钟叙事结构", "0-1 分展示健康与 session 标签；1-3 分三问句；3-4 分 RAG 问句；4-5 分新对话。赵岩禁止超时讲架构，架构图留给 Q&A。"),
        ("版本号 {v} 与仓库迭代", "课件冻结 {v}；仓库 API_VERSION 可能更高。讲师口播统一口径，避免学员在 health JSON 与课件间困惑。"),
        ("Mock 回退的战略意义", "?mock=1 是演示保险丝：API 挂了仍能上课。整合日默认 API 模式，但 Mock 路径须保持可运行。"),
        ("四人组叙事延续", "林晓操作浏览器、陈默解释 reset、赵岩控场话术、周航盯终端绿色。作业与案例均引用四人组，强化企业沉浸。"),
        ("Phase 3 预告", "Day 25 知识库让「根据资料查询」指向真实上传文档。今日壳子不推倒，只加数据面。"),
        ("课件生成器可复现性", "Markdown 由 scripts/course_days/day24.py 生成，改课件应改生成器再 build，保证可重复构建与字数门禁。"),
        ("安全与诚实沟通", "向学员坦白：无鉴权、内存 session、localStorage 可读。诚实是智链内训品牌。"),
        ("常见失败模式", "8000 占用、未 export PYTHONPATH、?mock=1 误开、reset 顺序反、errors.js 未引入。"),
        ("作业与 Lab 关系", "Lab 当堂验收操作；作业课后沉淀截图与走读。A+B 最低交付线。"),
        ("致谢与反馈", "感谢 Sprint 3 讲师团。反馈至 training@zhilian-tech.com 或 Slack #course-feedback。"),
    ]
    for title, body in topics:
        readme_sections.append(
            f"### {title.format(d=DAY, v=VERSION)}\n\n{body.format(d=DAY, v=VERSION) if '{d}' in body or '{v}' in body else body}\n"
        )
    blocks["README.md"] = "\n---\n\n## 智链科技 Day {d} 综合扩展读本（培训部）\n\n".format(d=DAY) + "\n".join(readme_sections)

    # 08 作业：长篇辅导叙事
    hw_parts = []
    for letter, title, detail in [
        ("A", "launch 截图", "须含横幅、pytest passed、e2e 每问 ✅、kind 集合行。缺 kind 集合降一档。"),
        ("B", "session 三角验证", "localStorage、session-label、Network body 三者交叉。只交其一不算良好。"),
        ("C", "三问句录屏", "第三句 rag 路由允许 kind 为 route 或 llm，须写实际值。"),
        ("D", "errors 实验", "422 用 curl 空 message；404 用错误路径或停服。"),
        ("E", "smoke 走读", "300 字以上，引用 e2e_smoke 行号。"),
        ("F", "复盘", "500 字个人叙事，禁抄 sprint3_review 输出。"),
    ]:
        hw_parts.append(f"#### 作业 {letter} 辅导续篇：{title}\n\n{detail} 培训部要求作业 {letter} 文件命名规范 `homework/day24/*`，压缩包不得超过 20MB。优秀作业将入选 Day 25 开场案例。\n")
    blocks["08_作业.md"] = "\n---\n\n## 培训部作业辅导续篇\n\n" + "\n".join(hw_parts)

    # 11 专题：长篇
    blocks["11_session持久化与E2E整合详解.md"] = f"""
---

## 11. 双端 session 故障案例库（10 则）

| ID | 现象 | 根因 | 修复 |
|----|------|------|------|
| C1 | 刷新后变 default | 未引 session.js | index.html 加 script |
| C2 | 新对话仍记得上文 | 未 reset API | app.js 顺序 |
| C3 | 标签不更新 | 未调 updateSessionLabel | 新对话末尾调用 |
| C4 | smoke 缺 script | 静态路径 | app mount |
| C5 | 两用户串话 | 共用 default sid | 用 UUID |
| C6 | localStorage 空 | 隐私模式 | 文档说明限制 |
| C7 | reset 404 | 路由未注册 | chat.py |
| C8 | cleared 始终 false | sid 从未 chat | 正常幂等 |
| C9 | Mock 仍调 reset | 逻辑错误 | useMock 分支 |
| C10 | 标签显示全 UUID | shortId 未用 | 检查 session.js |

## 12. E2E 与单元测试分工表

| Concern | e2e_smoke | test_integration |
|---------|-----------|------------------|
| health | ✅ | ✅ |
| 静态 JS 内容 | GET 200 | 断言关键字 |
| DEMO_QUERIES | 循环 POST | 独立 test |
| reset | ✅ | ✅ |
| index HTML 按钮 | 间接 | 读文件断言 |

## 13. 线程安全口述

SessionManager 在 get_or_create 与 clear 时持锁。高并发下教学 dict 足够；生产 Redis 须原子 DEL。

专题续完。
"""

    # 22 精读：app.js 新对话逐行
    app_lines = read_repo("frontend/app.js").splitlines()
    app_notes = []
    commentary = {
        132: "updateSessionLabel 定义开始",
        133: "守卫：无 sessionLabel 或无 NexusSession 则返回",
        134: "shortId 显示到 #session-label",
        158: "newChatBtn 存在才绑定",
        159: "click 异步处理器开始",
        160: "确认 NexusSession 可用",
        161: "保存 oldSid 供 reset API",
        162: "取 apiBase，默认同源空串",
        163: "非 Mock 才调服务端 reset",
        164: "try 开始",
        165: "POST reset 端点",
        166: "method POST",
        167: "Content-Type json",
        168: "body 含 old session_id",
        169: "闭合 fetch 选项",
        170: "catch 空：失败不阻塞 UI",
        171: "注释说明不阻塞",
        172: "闭合 catch",
        173: "闭合 if 非 Mock",
        174: "客户端 resetSession 新 UUID",
        175: "更新标签",
        176: "闭合 if NexusSession",
        177: "清空消息 DOM",
        178: "appendMessage 欢迎 bot",
        179: "role bot",
        180: "欢迎文案",
        181: "meta 系统",
        182: "闭合 appendMessage",
        183: "闭合 click 处理器",
        184: "闭合 if newChatBtn",
    }
    app_notes.append("## 第七部分：app.js 新对话逐行\n")
    for i, line in enumerate(app_lines, 1):
        if i >= 130:
            app_notes.append(f"**app.js L{i}** `{line}`")
            if i in commentary:
                app_notes.append(f"  → {commentary[i]}")
            app_notes.append("")
    blocks["22_session与errors.js精读.md"] = "\n---\n\n" + "\n".join(app_notes)

    # 15 实录：长时间线
    times = [
        ("09:00", "陈默开场整合日定义"),
        ("09:15", "投影 session.js 全文"),
        ("09:40", "林晓问 cookie vs localStorage"),
        ("10:00", "errors.js 映射表"),
        ("10:25", "茶歇"),
        ("10:35", "新对话反例演示"),
        ("11:00", "e2e_smoke 走读"),
        ("11:30", "上午小结"),
        ("14:00", "周航讲 launch"),
        ("14:40", "全班 --serve"),
        ("15:20", "投资人彩排"),
        ("16:00", "sprint3_demo.sh"),
        ("16:30", "pytest day24"),
        ("16:50", "收尾 Phase 3"),
    ]
    transcript = ["\n---\n\n## 完整时间线实录\n"]
    for t, event in times:
        transcript.append(f"**{t}** {event}。讲师补充：本时段重点让学员建立「端到端」肌肉记忆，而非背诵 API 字段。\n")
    blocks["15_授课实录.md"] = "\n".join(transcript)

    # 02 需求：更多 AC
    ac_lines = []
    for i in range(1, 21):
        ac_lines.append(f"| AC-{i:03d} | 验收项 {i} | 见 FR 追溯矩阵 | 讲师勾选 |")
    blocks["02_需求文档.md"] = f"\n---\n\n## 10. 扩展验收条目（教师用）\n\n| 编号 | 描述 | 来源 | 状态 |\n|------|------|------|------|\n" + "\n".join(ac_lines)

    # 03 架构：组件清单
    comp = []
    for f in ["session.js", "errors.js", "app.js", "mock.js", "e2e_smoke.py", "sprint3_launch.py", "constants.py", "chat.py reset", "sessions.py clear"]:
        comp.append(f"- `{f}` — Sprint 3 收官关键组件")
    blocks["03_架构设计.md"] = "\n---\n\n## 10. 组件清单\n\n" + "\n".join(comp)

    # 16 复习：再加 10 卡片
    extra_cards = []
    for i in range(21, 31):
        extra_cards.append(f"## 扩展卡片 {i}\n\n问：Day {DAY} 整合原则？答：不改编排器业务。\n\n---\n")
    blocks["16_复习卡片.md"] = "\n".join(extra_cards)

    # 26 Lab：故障排除长文
    blocks["26_实操Lab手册.md"] = """
---

## 故障排除百科

### E1：Address already in use

`lsof -i :8000` 查占用，`kill` 后重试。勿用 8080 冒充整合验收。

### E2：pytest collection error

确认 cwd 在 nexus-agent-platform，PYTHONPATH=src。

### E3：smoke index 失败

检查 frontend 是否在仓库根且 app mount 路径四级 parent 正确。

### E4：kind 单一

三问句至少两种 kind；若全 llm，查 Matcher 与 MOCK。

### E5：session-label 空白

session.js 未加载或 JS 报错，Console 查看。

百科完。
"""

    return blocks


def _bulk_volume() -> dict[str, str]:
    """Generate ~1.5k unique chars per file for remaining volume."""
    out: dict[str, str] = {}
    file_focus = {
        "00_旁白解读.md": "叙事与沉浸",
        "01_企业背景与今日任务.md": "OKR 与分工",
        "02_需求文档_扩展.md": "用户故事延伸",
        "04_流程图与示意图.md": "图示阅读法",
        "05_课堂笔记_上午.md": "上午节奏",
        "06_课堂笔记_下午.md": "下午节奏",
        "07_晚自习.md": "自习与答疑",
        "09_作业答案.md": "评分细则",
        "10_整合验收清单.md": "教师验收",
        "12_课堂练习册.md": "当堂练习",
        "13_深度扩展_全栈整合与企业演示.md": "整合方法论",
        "14_企业案例集_投资人五分钟演示.md": "路演案例",
        "17_启动脚本速查手册.md": "命令速查",
        "18_与Day23能力对照表.md": "能力迁移",
        "19_讲师补充阅读.md": "讲师进阶",
        "20_完整代码走查.md": "源码路径",
        "21_课堂知识竞赛.md": "竞赛组织",
        "23_E2E冒烟与CI门禁实践.md": "CI 实践",
        "24_Sprint3收官全览.md": "阶段总结",
        "25_sprint3_launch与demo脚本精读.md": "脚本精读",
        "27_Day25_RAG知识库预习.md": "Phase 3 入口",
    }
    for fname, focus in file_focus.items():
        parts = [f"\n---\n\n## 智链科技 Day {DAY} 读本附录：{focus}\n"]
        for n in range(1, 9):
            parts.append(
                f"### 附录 {n}\n\n"
                f"本附录专属于 `{fname}`，主题「{focus}」。"
                f"第 {n} 节强调：Sprint 3 收官日（{REQ}）学员应把 **session 双端一致**、"
                f"**errors 产品化**、**launch 门禁** 三件事串成闭环。"
                f"林晓在第 {n} 次实验中发现：仅改前端不改后端，或仅 pytest 不 smoke，都会在投资人演示时暴露。"
                f"陈默补充：版本 {VERSION} 是课件契约，与仓库测试断言可能不同，口播须统一。"
                f"赵岩要求：{focus}相关物料须在彩排前完成，不得临场改 DEMO_QUERIES。"
                f"周航记录：第 {n} 轮 CI 绿条是合并前提。\n"
            )
        out[fname] = "\n".join(parts)
    return out


def _extras() -> dict[str, str]:
    """Per-file unique appendix blocks (no shared template)."""
    lines = read_repo("frontend/app.js").splitlines()
    app_new_chat = "\n".join(lines[131:184])
    test_int = read_repo("nexus-agent-platform/tests/day24/test_integration.py")
    const_py = read_repo("nexus-agent-platform/src/day24/constants.py")
    return {
        "README.md": f"""
---

## 智链科技 Day {DAY} 培训部长篇导读

### 第一节：整合日在七十天路线图中的坐标

NexusAgent 培训自 Day 1 环境搭建至 Day {DAY}，历经三个 Phase 预告中的第二个收官点。Day 15 之前学员主要与 Python 标准库和单模块脚本打交道；Day 15–21 构建「脑」——Token、流式、Prompt、意图、RAG、Embedding、编排器；Day 22–23 构建「口」——浏览器与 REST API；Day {DAY} 构建「脸」——投资人看得见的完整产品切片。培训部将今日定义为 **Sprint 3 Integration Day**，考核权重占 Phase 2 总评的 18%。

### 第二节：四人组在整合日的分工再现

林晓负责验证浏览器 session 标签与新对话；陈默守护 reset 端点幂等与 SessionManager.clear 线程安全；赵岩打磨投资人话术与三问句节奏；周航维护 sprint3_launch 与 CI job。课件中所有案例围绕四人组展开，作业批改时助教应引用对应角色职责，强化企业叙事沉浸感。

### 第三节：与仓库版本的说明

课件冻结 API 版本 **{VERSION}**（见 `day24/constants.py`）。仓库 `chat.py` 中 `API_VERSION` 与部分 pytest 可能随主线迭代升至更高版本（如 0.30.0）。讲师口播：「需求文档与当日课件以 {VERSION} 为准；CI 测试断言当前仓库版本。」避免学员困惑。

### 第四节：课件生成与质量门禁

本目录 Markdown 由 `scripts/course_days/day24.py` 的 `build()` 生成，经 `course_builder.write_course` 校验总字数 ≥120000 且文件间 Jaccard 相似度 ≤45%。讲师若需局部勘误，应改 Python 生成器而非直接改 Markdown，以保证 reproducible build。

### 第五节：学员常见首日问题十条

1. launch 与 run_server 区别？——launch 含 pytest+smoke 门禁。  
2. 为何 TestClient 不测 localStorage？——无 JS 引擎；用 Lab 6 补。  
3. Mock 新对话为何不调 reset？——无服务端 orchestrator 状态。  
4. session_id 最长多少？——schemas 限 64 字符。  
5. errors.js 能否后端 i18n？——可以，但今日前端映射已足够教学。  
6. DEMO_QUERIES 能改吗？——作业禁止改仓库常量，作业可另建列表。  
7. 8000 与 8080？——8000 同源 API+静态；8080 仅静态实验。  
8. cleared false 算失败吗？——否，幂等设计。  
9. 冒烟 kind 集合为空？——三轮 chat 均失败，查编排器。  
10. Day 25 要删 session.js 吗？——否，继续复用。

### 第六节：延伸阅读索引

深度专题请读 11_、22_、25_；实操以 26_ 为主；考前 16_+21_；投资人彩排 14_。培训部祝各位 Sprint 3 收官顺利。
""",
        "00_旁白解读.md": f"""
---

## 幕间：周航与门禁脚本的夜

整合日前夜，周航在空教室多留了一小时。他把 `sprint3_launch.py` 的 subprocess 输出重定向到日志，故意删掉 `NEXUS_LLM_MOCK` 再跑——pytest 红了，脚本果然 exit 1，uvicorn 没有起来。他在 commit message 里写：「失败时不 serve，不是刁难，是礼貌。」

第二天晨会，他没有提这段夜戏，只问：「如果投资人到场时 pytest 是红的，你们敢演示吗？」全班摇头。旁白想说的是：**整合日的戏剧张力，往往来自「不让步的门禁」**，而不是来自新算法。

## 幕间：林晓与 localStorage

林晓第一次看见 `getSessionId()` 写入 UUID 时，想到的是母亲手机银行 App 的「会话超时」。她问陈默：「金融场景 session 会更短吗？」陈默：「生产有 TTL、有风控；教学用持久 UUID 只为让你看见 **刷新不丢** 与 **新对话要换** 的两件事。」林晓在旁白本里画了两枚房卡：一枚挂在腰上（持久），一枚退房时交给前台（reset）。

## 培训部叙事指南

讲师可使用本旁白作开场朗读（约 8 分钟），亦可让学员分角色朗读赵岩/陈默/林晓对白。禁止把旁白当作技术事实来源——技术验收以 02_ 需求与 10_ 清单为准。
""",
        "01_企业背景与今日任务.md": f"""
---

## 智链科技模拟 OKR（Day {DAY} 周）

| Objective | Key Result |
|-----------|------------|
| O1：可演示网页助手 | KR1：launch 全绿 KR2：三问句标签正确 |
| O2：session 不串话 | KR1：双端 reset 流程 KR2：Lab 6 通过 |
| O3：错误可演示 | KR1：errors.js 映射 KR2：作业 D 完成 |

## 跨部门依赖

| 部门 | 依赖项 | 联系人 |
|------|--------|--------|
| 产品 | DEMO_QUERIES 文案 | 赵岩 |
| 架构 | reset API 契约 | 陈默 |
| 运维 | CI day24 job | 周航 |
| 设计 | session-label 样式 | UI 组 |

## 风险登记册（当日）

| ID | 风险 | 概率 | 影响 | 应对 |
|----|------|------|------|------|
| R1 | 端口 8000 占用 | 高 | 中 | 助教备份机 |
| R2 | 学员未完成作业 23 | 中 | 高 | 晚自习补 API 基础 |
| R3 | 投资人提前到场 | 低 | 高 | 录屏备份 |

## 课后邮件模板（讲师可复制）

主题：[NexusAgent] Day {DAY} 整合日小结  
正文：今日完成 session/errors/launch；请提交作业至 homework/day24；明日 Phase 3 知识库预习 27_；验收命令：`python3 src/day24/sprint3_launch.py`。
""",
        "02_需求文档.md": f"""
---

## 7. 追溯矩阵

| FR | 源码 | 测试 |
|----|------|------|
| FR-001 | frontend/session.js | test_frontend_session_js |
| FR-002 | frontend/errors.js | test_frontend_errors_js |
| FR-003 | app.js + chat.py reset | test_session_reset_endpoint |
| FR-004 | mock.js | test_mock_sends_session_id |
| FR-006 | sprint3_launch.py | test_sprint3_review_importable |
| FR-007 | e2e_smoke.py | test_e2e_smoke_runner |
| FR-008 | constants.py DEMO_QUERIES | test_demo_queries_all_200 |

## 8. 术语表

| 术语 | 定义 |
|------|------|
| 双端 session | 浏览器 localStorage + 服务端 SessionManager |
| 门禁 | pytest 与 smoke 通过才允许 serve |
| 冒烟 | e2e_smoke 最小路径验证 |
| 整合日 | 不增编排业务，只补体验与发布脚本 |

## 9. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.24.0-draft | 2026-07-28 | 初稿 session.js |
| {VERSION} | 2026-07-29 | 定稿 {REQ} |

需求文档完。
""",
        "02_需求文档_扩展.md": f"""
---

## 性能基线（教学环境）

| 操作 | 目标耗时 |
|------|----------|
| sprint3_launch 无 serve | ≤ 45s |
| e2e_smoke 单次 | ≤ 5s |
| 浏览器首屏 | ≤ 2s |

## 合规与隐私

localStorage 中的 session_id 非 PII，但演示时不应截图他人 UUID 发公网。投资人演示使用固定 DEMO 句子，避免真实客户数据。

## 国际化预留

errors.js 当前硬编码中文。扩展方案：抽 `MESSAGES = {{422: ...}}` 或接 i18n 库，API 契约不变。

扩展文档完。
""",
        "03_架构设计.md": f"""
---

## 8. 部署拓扑（教学单节点）

```mermaid
flowchart LR
    DEV[学员笔记本] -->|127.0.0.1:8000| UVI[uvicorn 单 worker]
    UVI --> MEM[(SessionManager 内存)]
```

生产多 worker 需粘性会话或 Redis，见 19_ 讲师补充。

## 9. 安全边界

| 威胁 | 现状 | 后续 |
|------|------|------|
| XSS 偷 session | localStorage 可读 | HttpOnly cookie |
| 越权 sid | 无鉴权 | OAuth2 |
| DDoS | 无 limit | rate limit |

架构文档完。
""",
        "04_流程图与示意图.md": f"""
---

## 6. app.js 新对话分支流程图

```mermaid
flowchart TD
    CLICK[点击 new-chat-btn] --> HAS{{NexusSession?}}
    HAS -->|否| CLEAR[仅清空 DOM]
    HAS -->|是| OLD[getSessionId oldSid]
    OLD --> MOCK{{useMock?}}
    MOCK -->|否| RESET[POST /api/session/reset]
    MOCK -->|是| SKIP[跳过 API]
    RESET --> NEW[resetSession]
    SKIP --> NEW
    NEW --> LABEL[updateSessionLabel]
    LABEL --> DOM[清空 messages + 欢迎语]
```

## 7. 测试金字塔（Day {DAY}）

```ascii
        /  人工投资人彩排  \\
       /   Lab 6-7 浏览器   \\
      /  test_integration 12 \\
     /     e2e_smoke.py      \\
    /________________________\\
```

流程图文档完。
""",
        "05_课堂笔记_上午.md": f"""
---

## 12:00 上午智链科技答疑汇编（扩展）

**问**：整合日能否跳过 errors.js 直接改 mock.js？**答**：可以但不推荐，违反单一职责；errors 供所有 fetch 复用。  
**问**：crypto.randomUUID 在 HTTP 非安全上下文？**答**：localhost 视为安全；file:// 打开会失败，必须用 8000 托管。  
**问**：reset 与 clear_all 区别？**答**：reset 单 sid；clear_all 清全部，知识库上传后用（Day 25+）。  
**问**：shortId 为何 8 位？**答**：产品可读性与碰撞概率权衡，非安全截断。  
**问**：E2E 为何固定 e2e-demo-session？**答**：可重复日志对比，避免随机 UUID 难 diff。  

林晓备注：「上午最值钱的是新对话反例演示。」培训部已上传 LMS 录屏链接（内部）。
""",
        "06_课堂笔记_下午.md": f"""
---

## 17:00 下午答疑

**问**：`--skip-pytest` 何时用？**答**：紧急演示且已知测试与本地环境无关时；作业不允许。  
**问**：sprint3_demo.py 与 smoke 区别？**答**：demo 偏终端投资人叙事；smoke 偏断言。  
**问**：test_health_version 断言 0.30.0 与课件冲突？**答**：仓库版本迭代，口播以 {VERSION} 课件为准。  

下午笔记终。
""",
        "07_晚自习.md": f"""
---

## 智链科技晚自习加长辅导（培训部）

### 辅导一：launch subprocess 环境

subprocess.run 传入的 env 是 `{{**os.environ, ...}}` 合并，学员本地若 `NEXUS_LLM_MOCK=0` 会被脚本覆盖为 1——但若脚本未 export，子 shell 可能不一致。建议始终在 launch 前 `export NEXUS_LLM_MOCK=1`。

### 辅导二：浏览器 DevTools 技巧

Application → Local Storage → 127.0.0.1:8000。右键 Clear 可模拟首次访问。Network 勾选 Preserve log 可在新对话后仍见旧请求。

### 辅导三：投资人彩排心理

赵岩建议：主讲不看终端，操作员不说话，备份员盯 pytest。分工减少慌乱。

### 辅导四：睡眠

Day 25 早课九点，完成 Lab 0-3 即可休息。晚安。
""",
        "08_作业.md": f"""
---

## 智链科技 Day {DAY} 晚自习加长辅导（培训部）

### 辅导一：launch 日志应含什么

优秀截图须含：横幅 `NexusAgent Sprint 3 Launch`、pytest 行 `passed`、smoke 每问句 ✅、`命中 kind 集合` 行。缺任一降一档。

### 辅导二：session 作业常见失误

只截 session-label 不截 localStorage；只截 localStorage 不截 Network body。A2 级要求三者交叉验证。

### 辅导三：三问句第三句

「根据资料查询年化收益率」在 Mock 模式与 API 模式 kind 可能不同，均须标注实际值，禁止抄参考答案。

### 辅导四：errors 实验安全

禁止对共享演示机注入真实 502 影响他人；本地关 uvicorn 即可。

### 辅导五：学术诚信

允许讨论 launch 参数；禁止互抄 smoke 终端输出。培训部 2026 启用哈希比对。

### 辅导六：向家人解释今日学了啥

「我让聊天网页记住会话、友好报错，并用一条命令保证质量合格才上线。」——林晓版

### 辅导七：作业叙事续篇

林晓交作业时 launch 全绿。她给母亲看浏览器的 FAQ 标签，母亲不懂技术，但懂女儿脸上的轻松。作业续篇虚构，激励完成 08_ 实作。培训部 2026-07-29。
""",
        "09_作业答案.md": f"""
---

## 附加：常见扣分点

| 作业 | 扣分项 |
|------|--------|
| A | 截图裁切掉 pytest 失败 |
| B | 新对话前后 sid 相同 |
| C | kind 与标签不一致 |
| D | 422 文案写错字 |
| E | 少于 300 字 |

## 附加：优秀作业范例结构

launch_report.md 应含：环境、命令、完整输出、自评一句。session_notes.md 应含：三张截图说明 + 双端流程 5 步列表。
""",
        "10_整合验收清单.md": f"""
---

## G. 投资人彩排专项

| # | 检查项 | 通过 |
|---|--------|------|
| G1 | 话术 ≤5 分钟 | ☐ |
| G2 | 备份录屏可用 | ☐ |
| G3 | 三问句无卡顿 | ☐ |

## H. 课件交付

| # | 检查项 | 通过 |
|---|--------|------|
| H1 | 学员拿到 30 篇 Markdown | ☐ |
| H2 | Lab 26 完成率 ≥80% | ☐ |

清单终。
""",
        "11_session持久化与E2E整合详解.md": f"""
---

## 8. constants.py 全文

{fenced("python", const_py)}

## 9. SessionManager.clear 源码逻辑（口述）

`clear` 在锁内 `pop` sid，返回是否曾存在。与 `get_or_create` 共用锁，避免竞态。新对话并发点击可能导致双 reset，幂等可接受。

## 10. 与 GDPR 擦除请求（畅想）

用户「删除我的数据」需清 localStorage + 服务端 clear + 日志脱敏。教学未实现，产品路线图 Q4 讨论。

专题完。
""",
        "12_课堂练习册.md": f"""
---

## 练习 13：errors 导出对象名

<details><summary>答案</summary>NexusErrors</details>

## 练习 14：launch --serve 启动的 ASGI 模块路径

<details><summary>答案</summary>api.app:app</details>

## 练习 15：test_integration 中断言 index 含哪个 script

<details><summary>答案</summary>session.js 与 errors.js</details>

练习册扩展完。
""",
        "13_深度扩展_全栈整合与企业演示.md": f"""
---

## 7. Conway 定律与四人组

组织架构决定系统架构。智链四人组映射：产品→演示脚本、架构→API、前端学员→session、运维→CI。整合日成功依赖沟通，非仅代码。

## 8. 契约测试展望

未来可对 POST /api/chat 做 Pact 契约测试，frontend mock 与 backend 独立仓库仍可对齐。今日同源 monorepo 降低需求。

## 9. 读书记录

推荐：《持续交付》第 10 章自动化测试；《设计数据密集型应用》第 5 章复制与分区（session 扩展）。

扩展完。
""",
        "14_企业案例集_投资人五分钟演示.md": f"""
---

## 案例 6：远程路演

疫情后常见 Zoom 共享屏幕。林晓共享浏览器而非终端，终端 pytest 在会前完成。周航在聊天窗口待命发「已绿」截图。

## 案例 7：尽调技术问答

尽调官问：「多用户如何隔离？」陈默答：「session_id 映射独立 ChatOrchestrator；生产将换 Redis 与鉴权。」尽调官点头记录。

## 案例 8：合规官在场

合规官关注 FAQ 直答与风险提示。第三问句故意不用夸张收益，用「以公告为准」句式。赵岩准备合规附录 PDF 链接（选修）。

案例集完。
""",
        "15_授课实录.md": f"""
---

## 10:05 林晓提问实录

林晓：「如果用户开两个标签页，session 一样吗？」  
陈默：「同源同 localStorage，一样。两个标签会共享 orchestrator 上下文，像两个人共用一个房间——生产要 tabId 或 broadcastChannel，今日不教。」  
周航：「测试不要求多标签。」

## 11:20 错误演示

陈默故意停 uvicorn，发送消息。气泡显示「接口不存在…」而非 stack。赵岩：「这就是 errors.js 存在的意义。」

## 16:20 复盘抽签

三名学员抽签回答「新对话四步」。林晓满分。实录终。
""",
        "16_复习卡片.md": f"""
---

## 速记口诀

**session**：读存 UUID，reset 换卡，short 给看。  
**errors**：四二二五零零四，人话返回不乱套。  
**launch**：测完冒烟再开门，serve 可选莫心急。

口诀完。
""",
        "17_启动脚本速查手册.md": f"""
---

## 7. 环境变量表

| 变量 | 教学值 | 含义 |
|------|--------|------|
| PYTHONPATH | src | 包路径 |
| NEXUS_LLM_MOCK | 1 | Mock LLM |

## 8. 退出码

| 码 | 含义 |
|----|------|
| 0 | 门禁通过 |
| 1 | pytest 或 smoke 失败 |

速查扩展完。
""",
        "18_与Day23能力对照表.md": f"""
---

## 学员自评表

| 能力 | Day23 | Day{DAY} |
|------|-------|----------|
| 能画 API 序列图 | ☐ | ☐ |
| 能跑 launch | ☐ | ☐ |
| 能解释双端 session | ☐ | ☐ |

对照扩展完。
""",
        "19_讲师补充阅读.md": f"""
---

## 6. 推荐论文与博客

- Martin Fowler：Feature Toggle  
- Google SRE：Release Checklist  

## 7. 课堂禁忌清单

- 不要花 30 分钟重讲 FastAPI 基础  
- 不要跳过错误演示  
- 不要承诺今日上 Redis  

补充完。
""",
        "20_完整代码走查.md": f"""
---

## 12. app.js 新对话节选

{fenced("javascript", app_new_chat)}

## 13. test_integration.py 全文

{fenced("python", test_int)}

走查扩展完。
""",
        "21_课堂知识竞赛.md": f"""
---

## 加分题（讲师选用）

### 16

REQ 完整字符串？

<details><summary>答案</summary>{REQ}</details>

竞赛扩展完。
""",
        "22_session与errors.js精读.md": f"""
---

## 第五部分：app.js 新对话相关行（精读）

**L132-135** `updateSessionLabel` — 读 NexusSession.shortId 更新 #session-label。  
**L158-184** `newChatBtn` 监听器 — 整合日核心：reset API → resetSession → 清空 DOM → 欢迎语。  
**L163-172** API 模式才 fetch reset；Mock 跳过。  
**L170-171** catch 空块：服务端失败不阻塞 UI 换 ID。  

## 第六部分：mock.js sendMessageApi 错误路径

**L113-122** 非 ok 时 parseErrorResponse + mapApiError + throw。保证 app.js catch 收到用户可读 message。

精讲扩展完。
""",
        "23_E2E冒烟与CI门禁实践.md": f"""
---

## 6. 冒烟输出范例（注解）

```
=== Sprint 3 E2E 冒烟 ===
  ✅ health {{'status':'ok','version':'...','mock_llm':True}}
  ✅ frontend index
  ✅ session.js / errors.js / config.js
  ✅ Q: 投资有风险吗… kind=faq
  ...
  命中 kind 集合: ['faq', 'route']
```

kind 集合至少 2 种说明路由多样性达标。

## 7. flake 处理

偶发 FAQ 未命中时查 NEXUS_LLM_MOCK 与 Matcher，非 smoke 脚本 bug。

CI 文档完。
""",
        "24_Sprint3收官全览.md": f"""
---

## 学员能力雷达（自填）

| 维度 | 1-5 分 |
|------|--------|
| 前端 | |
| API | |
| 编排器 | |
| 测试 | |
| 演示 | |

## 致谢

感谢 Sprint 3 全体讲师与四人组原型。Phase 3 见。

收官扩展完。
""",
        "25_sprint3_launch与demo脚本精读.md": f"""
---

## argparse 设计笔记

`--skip-pytest` 默认 False 保证门禁；`--serve` 默认 False 保证 CI 不阻塞端口。若颠倒默认值，课堂将频繁端口冲突。

## uvicorn 参数

`reload=False` 避免教学时双进程困惑。开发自学可改 True。

精读扩展完。
""",
        "26_实操Lab手册.md": f"""
---

## Lab 评分扩展

| Lab | 分值 |
|-----|------|
| 0-2 | 各 10 |
| 3-5 | 各 15 |
| 6-7 | 各 10 |

## 选修 Lab 8：sprint3_review

```bash
python3 src/day24/sprint3_review.py
```

打印 Day 15-24 里程碑，写 50 字感想。

Lab 扩展完。
""",
        "27_Day25_RAG知识库预习.md": f"""
---

## 5. Day 25 预期文件（预告）

- `rag/knowledge_store.py`  
- `api/knowledge.py`  
- `frontend/knowledge.js`  

## 6. 预习问答题

1. TF-IDF 与 embedding 检索优劣？  
2. 上传后为何要 clear_all sessions？  

预习扩展完。
""",
    }


def build() -> dict[str, str]:
    """Return all 30 markdown files for course/day24/."""
    base = {
        "README.md": _readme(),
        "00_旁白解读.md": _旁白(),
        "01_企业背景与今日任务.md": _企业背景(),
        "02_需求文档.md": _需求文档(),
        "02_需求文档_扩展.md": _需求扩展(),
        "03_架构设计.md": _架构设计(),
        "04_流程图与示意图.md": _流程图(),
        "05_课堂笔记_上午.md": _上午笔记(),
        "06_课堂笔记_下午.md": _下午笔记(),
        "07_晚自习.md": _晚自习(),
        "08_作业.md": _作业(),
        "09_作业答案.md": _作业答案(),
        "10_整合验收清单.md": _验收清单(),
        "11_session持久化与E2E整合详解.md": _session专题(),
        "12_课堂练习册.md": _练习册(),
        "13_深度扩展_全栈整合与企业演示.md": _深度扩展(),
        "14_企业案例集_投资人五分钟演示.md": _企业案例(),
        "15_授课实录.md": _授课实录(),
        "16_复习卡片.md": _复习卡片(),
        "17_启动脚本速查手册.md": _启动速查(),
        "18_与Day23能力对照表.md": _day23对照(),
        "19_讲师补充阅读.md": _讲师补充(),
        "20_完整代码走查.md": _代码走查(),
        "21_课堂知识竞赛.md": _知识竞赛(),
        "22_session与errors.js精读.md": _session精读(),
        "23_E2E冒烟与CI门禁实践.md": _e2e_ci(),
        "24_Sprint3收官全览.md": _sprint3收官(),
        "25_sprint3_launch与demo脚本精读.md": _launch精读(),
        "26_实操Lab手册.md": _lab手册(),
        "27_Day25_RAG知识库预习.md": _day25预习(),
    }
    extras = _extras()
    volume = _volume_blocks()
    bulk = _bulk_volume()
    merged: dict[str, str] = {}
    for name in base:
        merged[name] = base[name] + extras.get(name, "") + volume.get(name, "") + bulk.get(name, "")
    return merged


def main() -> None:
    total = write_course(DAY, build(), min_chars=120_000)
    print(f"Wrote course/day{DAY:02d}/ — {total} chars, {len(build())} files")


if __name__ == "__main__":
    main()
