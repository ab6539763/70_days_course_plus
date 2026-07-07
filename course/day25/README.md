# Day 25 课件索引

**日期**：2026-07-30（星期四）  
**主题**：Phase 3 启动 — 企业知识库 Ingestion 与上传 API  
**需求**：ZL-NA-REQ-025  
**平台版本**：0.25.0  
**里程碑**：Phase 3 第一日

## 今日故事线

Sprint 3 网页版 ChatGPT 克隆交付后，投资人追问：「知识从哪来？」赵岩拍板 Phase 3：今日要让运营上传一份 UTF-8 `.txt` FAQ，刷新页面后聊天能检索到新内容。陈默在 `rag/knowledge_store.py` 加可写、可落盘壳层；林晓联调 `POST /api/knowledge/upload` 与 `frontend/knowledge.js` 侧栏。

## 配套代码

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1

python3 src/day25/ingestion_demo.py
python3 src/day25/knowledge_api_demo.py
python3 -m pytest tests/day25/ -v

# 启动服务后浏览器「知识库」上传 .txt
python3 src/day24/sprint3_launch.py --serve --skip-pytest
```

## 今日交付物

- [x] `rag/knowledge_store.py` — JSON 持久化、TF-IDF 索引重建、`get_knowledge_store()` 单例
- [x] `rag/ingestion.py` — `ingest_upload` 落盘至 `data/knowledge/uploads/`
- [x] `api/knowledge.py` — `GET /status`、`POST /upload`（Day 25 仅 .txt）
- [x] `frontend/knowledge.js` — 知识库侧栏上传与状态
- [x] `src/day25/*` 演示脚本
- [x] `tests/day25/` — 17 项（store 10 + api 7）
- [x] Day 25 全套课件（30 篇）

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | 旁白解读 | Phase 3 叙事 |
| 02 | 需求文档 | 完整 PRD |
| 11 | KnowledgeStore 详解 | 深度专题 |
| 20 | 完整代码走查 | 时序图 + 调用链 |
| 22 | knowledge_store 精读 | 源码逐段注释 |
| 25 | ingestion 流水线精读 | ingest_upload 走读 |
| 26 | 实操 Lab | 六步实验 |
| 27 | Day26 预习 | Markdown/PDF 预告 |

## 验收命令

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 -m pytest tests/day25/ -q
# 期望：17 passed
```

**编写**：培训部 | **源码版本**：0.25.0


---

## 附录：仓库目录对照（README 专节）

| 路径 | Day 25 职责 |
|------|-------------|
| `src/rag/knowledge_store.py` | 可写知识库 + JSON 持久化 |
| `src/rag/ingestion.py` | ingest_upload 流水线 |
| `src/api/knowledge.py` | status/upload 路由 |
| `frontend/knowledge.js` | 侧栏 UI |
| `tests/day25/test_knowledge_store.py` | 存储 10 测 |
| `tests/day25/test_knowledge_api.py` | API 7 测 |
| `src/day25/constants.py` | 样例上传文本 |

林晓备注：先 `pytest tests/day25/` 再启动 `--serve`，避免脏 store 干扰演示。

## 故障排查速查

端口占用：`lsof -i :8000`。store 权限：确保 `data/knowledge/` 可写。侧栏不显示：检查 `index.html` 是否引入 `knowledge.js`。

README 附录完。

---

## 深度导读：Phase 3 第一日的工程意义

README 不仅是索引，更是学员复盘入口。建议按「故事线 → 代码 → 课件 → 验收」四遍阅读法：第一遍 00_ 旁白建立动机；第二遍对照 03_ 架构；第三遍 20_ 走查画时序图；第四遍 26_ Lab 动手。周航要求 fork 仓库的学员在 README 勾选交付物，MR 描述贴 pytest 截图。智链培训部把 Day 25 定为「数据面觉醒日」——从此 FAQ 不再神圣不可改。

## 与投资人话术对齐

赵岩演示三句话：「运营能上传」「系统能存盘」「聊天能引用」。README 中验收命令必须个人电脑跑通后再听次日上午串讲。若 `ingestion_demo` 报错，9 成是 PYTHONPATH；若 upload 422，检查是否误传二进制 PDF（留待 Day 26）。

README 深度导读完。

---

## 培训部致学员信

恭喜完成 Sprint 3 整合进入 Phase 3。Day 25 让 NexusAgent 拥有可运营的知识生命周期。

周航寄语：让 pytest 成为你的第二个键盘。

---

## README 运维注记

Fork 仓库的学员请在 PR 描述贴 `pytest tests/day25/ -q` 输出。合并冲突高发区：`api/factory.py` 的 RAG 注入行。README 运维注记完。
