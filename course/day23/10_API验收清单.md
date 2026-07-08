# Day 23 API 验收清单（教师版）

**需求**：ZL-NA-REQ-023  
**用途**：授课验收、Code Review、演示前检查

---

## A. API 包结构（6/6）

- [ ] `src/api/app.py` 存在且含 `create_app`  
- [ ] `src/api/chat.py` 存在且含 `router`  
- [ ] `src/api/schemas.py` 含 ChatRequest/ChatResponse  
- [ ] `src/api/sessions.py` 含 SessionManager  
- [ ] `src/api/factory.py` 含 create_orchestrator  
- [ ] `src/api/response_parser.py` 含 classify_reply  

## B. 路由与契约（5/5）

- [ ] `GET /api/health` 返回 200  
- [ ] `POST /api/chat` 接受 JSON `{message}`  
- [ ] 响应含 `reply`, `meta`, `kind`, `session_id`  
- [ ] 空 message 返回 422  
- [ ] API_VERSION = `0.23.0`  

## C. 编排器集成（4/4）

- [ ] chat 调用 `handle_message`  
- [ ] 使用 `classify_reply` 填充 kind/meta  
- [ ] SessionManager 依赖注入  
- [ ] factory 默认 NEXUS_LLM_MOCK  

## D. 静态与前端（4/4）

- [ ] `GET /` 返回含 NexusAgent 的 HTML  
- [ ] `GET /config.js` 含 NexusConfig  
- [ ] frontend 由 app.mount 托管  
- [ ] mock.js sendMessageApi 指向 `/api/chat`  

## E. 演示脚本（3/3）

- [ ] `api_health_demo.py` 退出码 0  
- [ ] `api_chat_demo.py` 打印三条问句  
- [ ] `run_server.py` 可启动 8000  

## F. 依赖与文档（2/2）

- [ ] `requirements-api.txt` 含 fastapi、uvicorn  
- [ ] app.py 模块 docstring 含启动命令  

## G. 自动化（2/2）

- [ ] `pytest tests/day23/test_api_chat.py` 12 passed  
- [ ] CI 环境变量 PYTHONPATH=src  

## H. 演示场景（林晓验收，3/3）

- [ ] 「投资有风险吗」→ kind=faq  
- [ ] Network 可见 POST /api/chat  
- [ ] `/docs` 可调试  

---

## 扣分项

| 项 | 扣分 |
|----|------|
| 未装 requirements-api | -10 |
| 用 8080 静态服冒充 API 演示 | -15 |
| classify_reply 与测试不一致 | -10 |
| 生产环境误用 CORS `*` | 警告 |

---

**验收签字**：讲师 ______  日期 ______

验收清单完。

---

## I. 智链科技验收演说模板（赵岩用）

「各位评委，Day 23 我们交付 FastAPI Chat API。现在演示：第一，健康检查显示 mock_llm 为 true，表示教学 Mock 环境；第二，浏览器输入合规问句，Network 显示 POST /api/chat 返回 kind faq；第三，pytest 十二项连续通过。以上三步对应 ZL-NA-REQ-023 的 FR-001 至 FR-007。」

## J. 常见验收失败与话术

| 失败现象 | 对业务解释 |
|----------|------------|
| 8000 拒绝连接 | 服务未启动，非功能缺陷 |
| kind 错误 | 契约回归，开发修复中 |
| 仍 Mock | URL 或 config 问题，非后端 |

## K. 签字后归档

验收签字扫描件存入 `docs/acceptance/day23/`，与 FR 文档同 hash 存证。周航负责 git tag `sprint3-day23`。

验收扩展完。
