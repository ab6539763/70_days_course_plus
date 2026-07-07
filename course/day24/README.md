# Day 24 课件索引

**日期**：2026-07-29（星期三）  
**主题**：Sprint 3 收官 — 网页版 ChatGPT 克隆整合  
**需求**：ZL-NA-REQ-024  
**版本**：0.24.0  
**里程碑**：Phase 2 / Sprint 3 第十日（收官）

## Sprint 3 进度

昨日完成 FastAPI `POST /api/chat` 与同源静态托管，今日将 **frontend + api + 编排器** 拧成可演示、可冒烟、可 CI 门禁的完整产品切片。赵岩称之为「投资人五分钟能看见的东西」。

- Day 15 Token → Day 16 流式 → Day 17 Prompt → Day 18 意图 → Day 19 RAG → Day 20 Embedding → Day 21 工具编排 → Day 22 静态 UI → Day 23 FastAPI → **Day 24 完整整合**
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
- [x] Day 24 全套课件（30 篇）

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

1. **整合优先**：Day 24 不新增编排业务，只补 session、错误 UX、启动与冒烟
2. **双端 session**：浏览器 `localStorage` + 服务端 `SessionManager`，新对话先 reset 旧 sid
3. **门禁脚本**：`sprint3_launch.py` 先 pytest 再 E2E，失败不启动 `--serve`
4. **投资人三问句**：FAQ / 总结 / RAG 路由，覆盖 `kind` 集合
5. **版本号 0.24.0**：课件与 `constants.py` 对齐（注：部分测试夹具可能显示更高版本号，以当日课件为准）

## 验收命令速查

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py
python3 src/day24/e2e_smoke.py
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
```

## 智链科技培训部说明

本日课件由 `scripts/course_days/day24.py` 生成，遵循 Day 23 gold standard：每篇独立叙事、无模板复读、含真实源码摘录。讲师请以 Lab 26_ 为实操主轴，作业 08_ 为课后验收。

---

## 智链科技 Day 24 培训部长篇导读

### 第一节：整合日在七十天路线图中的坐标

NexusAgent 培训自 Day 1 环境搭建至 Day 24，历经三个 Phase 预告中的第二个收官点。Day 15 之前学员主要与 Python 标准库和单模块脚本打交道；Day 15–21 构建「脑」——Token、流式、Prompt、意图、RAG、Embedding、编排器；Day 22–23 构建「口」——浏览器与 REST API；Day 24 构建「脸」——投资人看得见的完整产品切片。培训部将今日定义为 **Sprint 3 Integration Day**，考核权重占 Phase 2 总评的 18%。

### 第二节：四人组在整合日的分工再现

林晓负责验证浏览器 session 标签与新对话；陈默守护 reset 端点幂等与 SessionManager.clear 线程安全；赵岩打磨投资人话术与三问句节奏；周航维护 sprint3_launch 与 CI job。课件中所有案例围绕四人组展开，作业批改时助教应引用对应角色职责，强化企业叙事沉浸感。

### 第三节：与仓库版本的说明

课件冻结 API 版本 **0.24.0**（见 `day24/constants.py`）。仓库 `chat.py` 中 `API_VERSION` 与部分 pytest 可能随主线迭代升至更高版本（如 0.30.0）。讲师口播：「需求文档与当日课件以 0.24.0 为准；CI 测试断言当前仓库版本。」避免学员困惑。

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

---

## 智链科技 Day 24 综合扩展读本（培训部）

### 整合日在七十天路线图的坐标

NexusAgent 培训自 Day 1 至 Day 24，Sprint 3 收官意味着 Phase 2 从「模块交付」转向「产品交付」。林晓在日记写：整合日代码行数少，却第一次需要同时对得起浏览器用户、pytest 与投资人。

### 双端 session 的产品语言

赵岩要求对外只说「会话标识」不说 localStorage。对内培训则必须讲清：前端 UUID 持久化、后端 SessionManager 隔离编排器、新对话双端 reset。三者缺一都会出现「界面清了脑子还在」的裂缝。

### errors.js 与监管话术

502 映射「大模型服务繁忙」是合规与体验折中：不暴露上游供应商名称，不谎称「网络错误」。422 统一「输入无效」避免 Pydantic 字段名泄露给终端用户。

### sprint3_launch 作为职业习惯

周航说：「能启动不等于能交付。」门禁脚本把 pytest 与 smoke 变成合并前肌肉记忆。学员毕业后在任何公司都可复用「测试→冒烟→部署」三段式。

### E2E 冒烟的边界

TestClient 不执行 JavaScript，故 smoke 检查 session.js 可下载而非 localStorage 行为。人工 Lab 6 补浏览器验证。分层测试避免迷信单一工具。

### 投资人五分钟叙事结构

0-1 分展示健康与 session 标签；1-3 分三问句；3-4 分 RAG 问句；4-5 分新对话。赵岩禁止超时讲架构，架构图留给 Q&A。

### 版本号 0.24.0 与仓库迭代

课件冻结 0.24.0；仓库 API_VERSION 可能更高。讲师口播统一口径，避免学员在 health JSON 与课件间困惑。

### Mock 回退的战略意义

?mock=1 是演示保险丝：API 挂了仍能上课。整合日默认 API 模式，但 Mock 路径须保持可运行。

### 四人组叙事延续

林晓操作浏览器、陈默解释 reset、赵岩控场话术、周航盯终端绿色。作业与案例均引用四人组，强化企业沉浸。

### Phase 3 预告

Day 25 知识库让「根据资料查询」指向真实上传文档。今日壳子不推倒，只加数据面。

### 课件生成器可复现性

Markdown 由 scripts/course_days/day24.py 生成，改课件应改生成器再 build，保证可重复构建与字数门禁。

### 安全与诚实沟通

向学员坦白：无鉴权、内存 session、localStorage 可读。诚实是智链内训品牌。

### 常见失败模式

8000 占用、未 export PYTHONPATH、?mock=1 误开、reset 顺序反、errors.js 未引入。

### 作业与 Lab 关系

Lab 当堂验收操作；作业课后沉淀截图与走读。A+B 最低交付线。

### 致谢与反馈

感谢 Sprint 3 讲师团。反馈至 training@zhilian-tech.com 或 Slack #course-feedback。
