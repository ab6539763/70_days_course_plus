# Day 25 RAG 知识库预习

**日期预告**：2026-07-30（星期四）  
**主题**：Phase 3 启动 — 企业知识库与文档 ingestion  
**需求预告**：ZL-NA-REQ-025

---

## 1. 为何进入 Phase 3？

Sprint 3 完成了「能聊天的网页」。投资人下一轮问题将是：**知识从哪来？能否上传 PDF？能否换库不换 UI？**

Day 25 起，重点从整合转向 **数据面**：文档解析、分块策略、向量索引持久化。

## 2. 与 Day 24 的衔接

| Day 24 保留 | Day 25 扩展 |
|-------------|-------------|
| `POST /api/chat` | 增加文档上传 API |
| `session_id` | 会话绑定知识库 scope |
| `frontend/` 壳子 | 增加「知识库」侧栏 |

## 3. 预习任务

1. 复习 Day 19 `chunker.py`、Day 20 `embedding.py`  
2. 阅读 `rag/context.py` 如何拼 prompt  
3. 思考：TF-IDF 与真 embedding 的差异  

## 4. 自检

- 能否画出 Day 21 `handle_message` 调用链？  
- 能否说明 FAQ 直答阈值 0.65 的含义？  

---

赵岩：「Sprint 3 是壳，Phase 3 是脑。壳已经立住了。」
