# NexusAgent 包结构说明

**版本**：v0.25.0（Day 25 知识库）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-025

## 仓库根目录（Day 22+）

```
frontend/           # 静态聊天页（HTML/CSS/JS，Day 22–25）
  index.html
  config.js         # Day 23 API/Mock 切换
  session.js        # Day 24 localStorage 会话 ID
  errors.js         # Day 24 统一 API 错误文案
  knowledge.js      # Day 25 知识库上传侧栏
  ...
scripts/
  sprint3_demo.sh   # Day 24 投资人演示冒烟脚本
```

## 生产层目录（长期演进）

```
src/
├── api/            # FastAPI HTTP 层（Day 23–25）
│   ├── app.py      # 应用入口、CORS、静态托管
│   ├── chat.py     # POST /api/chat、POST /api/session/reset
│   ├── knowledge.py # POST /api/knowledge/upload、GET /status
│   ├── schemas.py  # Pydantic 模型
│   └── sessions.py # 会话管理
├── rag/            # RAG 检索（Day 19+）
│   ├── chunker.py
│   ├── embedding.py
│   ├── context.py
│   ├── knowledge_store.py  # Day 25 JSON 持久化知识库
│   └── ingestion.py        # Day 25 上传与批量入库
├── data/knowledge/ # Day 25 持久化数据
│   ├── store.json
│   └── uploads/
├── day23/          # Day 23 API 演示
├── day24/          # Day 24 Sprint 3 整合
└── day25/          # Day 25 知识库演示与 Phase 3 回顾
```

## Day 25 启动

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day25/knowledge_api_demo.py
# 或 uvicorn api.app:app --port 8000 后使用前端「知识库」上传
```

## 异常映射

| 异常 | HTTP | 前端 errors.js |
|------|------|----------------|
| Pydantic 校验失败 | 422 | 输入无效，请检查消息后重试 |
| 上传非 .txt | 422 | 仅支持 .txt |
| 文件过大 | 413 | 请求失败 |
| APIError | 502 | 大模型服务繁忙 |
