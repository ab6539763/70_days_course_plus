# Day 23 FastAPI 速查手册

**需求**：ZL-NA-REQ-023  
**用途**：桌面备忘

---

## 安装

```bash
pip install -r requirements-api.txt
```

## 环境变量

```bash
export PYTHONPATH=src
export NEXUS_LLM_MOCK=1
```

## 启动服务

```bash
python3 src/day23/run_server.py
# 或
uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## curl 速查

```bash
# 健康
curl -s http://127.0.0.1:8000/api/health | jq

# 聊天
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"投资有风险吗"}' | jq

# 带会话
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好","session_id":"u1"}' | jq
```

## 演示脚本

```bash
python3 src/day23/api_health_demo.py
python3 src/day23/api_chat_demo.py
```

## 测试

```bash
python3 -m pytest tests/day23/test_api_chat.py -v
```

## Swagger

浏览器打开 `http://127.0.0.1:8000/docs`

## 关键路径

| 文件 | 一行职责 |
|------|----------|
| app.py | 应用工厂 + 静态挂载 |
| chat.py | /api/chat 路由 |
| schemas.py | Pydantic 模型 |
| sessions.py | 会话 → orchestrator |
| factory.py | create_orchestrator |
| response_parser.py | classify_reply |
| config.js | useMock 开关 |

## 常见错误

| 现象 | 检查 |
|------|------|
| ModuleNotFoundError api | PYTHONPATH |
| 连接拒绝 | run_server 是否启动 |
| 仍走 Mock | URL 是否 ?mock=1 |
| 422 | message 是否为空 |

速查手册完。

---

## 智链科技 FastAPI 故障树（文字版）

```
无法访问 8000
├─ run_server 未运行 → 启动
├─ 端口占用 → lsof / 换端口
└─ 防火墙 → 内网放行

API 404
├─ 路径错 → 必须 /api/chat
├─ router 未注册 → 查 app.include_router
└─ mount 覆盖 → 查顺序

422
├─ message 空
└─ JSON 格式错

502
├─ APIError 上游
└─ 非 Mock 且无 Key

仍 Mock
├─ ?mock=1
├─ 8080 静态服
└─ config 未加载顺序错

pytest 失败
├─ PYTHONPATH
├─ 缺 fastapi/httpx
└─ FAQ 环境
```

林晓打印贴显示器。故障树完。

**故障树使用说明**：按自上而下排查，勿跳步。智链科技内训部标准作业程序。遇未列现象，查 11_ 详解或 Slack sprint3-api。

---

## 速查附录：端口与路径

| 项目 | 值 |
|------|-----|
| API 端口 | 8000 |
| 静态回退端口 | 8080 |
| health | /api/health |
| chat | POST /api/chat |
| Swagger | /docs |
| 前端根 | / |
| config | /config.js |

速查附录完。十七号文件终。
