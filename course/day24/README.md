# Day 24 课件索引

**日期**：2026-07-29（星期三）  
**主题**：Sprint 3 收官 — 网页版 ChatGPT 克隆完整整合  
**需求**：ZL-NA-REQ-024  
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

# 单元测试（12 项 day24 + day22/23）
python3 -m pytest tests/day24/ -v
```

## 今日交付物

- [x] `frontend/session.js` — localStorage 会话 ID 持久化
- [x] `frontend/errors.js` — 422/500/502 统一错误文案
- [x] `frontend/app.js` — 新对话、健康检查、session 标签
- [x] `POST /api/session/reset` — 服务端会话清除
- [x] `src/day24/sprint3_launch.py` — 一条命令启动
- [x] `src/day24/e2e_smoke.py` — 三问句 E2E 冒烟
- [x] `src/day24/sprint3_demo.py` — 终端投资人 Demo
- [x] `src/day24/sprint3_review.py` — Day 15–24 里程碑回顾
- [x] `scripts/sprint3_demo.sh` — Shell 演示入口
- [x] `tests/day24/test_integration.py`（12 tests）
- [x] Day 24 全套课件（29 篇 + 本 README）

## 上下文链

```
Day 23 POST /api/chat → Day 24 session_id 全链路透传
Day 23 SessionManager → Day 24 reset + localStorage 双端一致
Day 22 mock.js → Day 24 仍可作为 ?mock=1 回退
```

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
5. **版本号 0.24.0**：health、PACKAGE_STRUCTURE、CI 对齐

## Day 25 预告

Phase 3 启动：企业知识库、向量库持久化、文档 ingestion 流水线。Sprint 3 的网页聊天壳子将挂载更重的 RAG 后端。

## 验收命令速查

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day24/sprint3_launch.py
python3 src/day24/e2e_smoke.py
python3 -m pytest tests/day22/ tests/day23/ tests/day24/ -q
```
