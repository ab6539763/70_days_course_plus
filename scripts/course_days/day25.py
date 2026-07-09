#!/usr/bin/env python3
"""Day 25 course material builder — Phase 3 企业知识库 ingestion + upload API.

需求：ZL-NA-REQ-025 | 版本：v0.25.0
关键代码：rag/knowledge_store.py, rag/ingestion.py, api/knowledge.py,
         frontend/knowledge.js, tests/day25/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo

REQ = "ZL-NA-REQ-025"
VER = "0.25.0"
DAY = 25

_KS = read_repo("nexus-agent-platform/src/rag/knowledge_store.py")
_ING = read_repo("nexus-agent-platform/src/rag/ingestion.py")
_API = read_repo("nexus-agent-platform/src/api/knowledge.py", limit=180)
_FE = read_repo("frontend/knowledge.js")
_TSTORE = read_repo("nexus-agent-platform/tests/day25/test_knowledge_store.py")
_TAPI = read_repo("nexus-agent-platform/tests/day25/test_knowledge_api.py")
_CONST = read_repo("nexus-agent-platform/src/day25/constants.py")


def build() -> dict[str, str]:
    files = {
        "README.md": _readme(),
        "00_旁白解读.md": _narration(),
        "01_企业背景与今日任务.md": _background(),
        "02_需求文档.md": _prd(),
        "02_需求文档_扩展.md": _prd_ext(),
        "03_架构设计.md": _architecture(),
        "04_流程图与示意图.md": _diagrams(),
        "05_课堂笔记_上午.md": _notes_am(),
        "06_课堂笔记_下午.md": _notes_pm(),
        "07_晚自习.md": _evening(),
        "08_作业.md": _homework(),
        "09_作业答案.md": _homework_answers(),
        "10_知识库验收清单.md": _checklist(),
        "11_KnowledgeStore与Ingestion详解.md": _deep_dive(),
        "12_课堂练习册.md": _exercises(),
        "13_深度扩展_企业知识库实践.md": _extension(),
        "14_企业案例集_运营上传FAQ.md": _case_study(),
        "15_授课实录.md": _lecture_log(),
        "16_复习卡片.md": _flashcards(),
        "17_知识库API速查手册.md": _cheatsheet(),
        "18_与Day24能力对照表.md": _day24_compare(),
        "19_讲师补充阅读.md": _instructor_reading(),
        "20_完整代码走查.md": _code_walkthrough(),
        "21_课堂知识竞赛.md": _quiz(),
        "22_knowledge_store精读.md": _ks_deep_read(),
        "23_上传API与持久化实践.md": _upload_practice(),
        "24_Phase3启动全览.md": _phase3_overview(),
        "25_ingestion流水线精读.md": _ingestion_deep_read(),
        "26_实操Lab手册.md": _lab(),
        "27_Day26文档解析预习.md": _day26_preview(),
    }
    for name, extra in _supplements().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _supplements_vol2().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _supplements_vol3().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _supplements_vol4().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    files["08_作业.md"] += "\n\n" + _homework_vol3()
    files["13_深度扩展_企业知识库实践.md"] += "\n\n" + _extension_vol2()
    files["21_课堂知识竞赛.md"] += "\n\n" + _quiz_teacher_guide()
    files["22_knowledge_store精读.md"] += "\n\n" + _ks_vol2()
    files["20_完整代码走查.md"] += "\n\n" + f"""## 走查附录：api/knowledge upload 全文

{fenced('python', read_repo('nexus-agent-platform/src/api/knowledge.py', limit=176))}

## 走查附录：ingest_upload

{fenced('python', read_repo('nexus-agent-platform/src/rag/ingestion.py'))}
"""
    return files


def _supplements() -> dict[str, str]:
    """Per-file unique expansions — each block is file-specific prose."""
    tstore = _TSTORE
    return {
        "README.md": f"""## 附录：仓库目录对照（README 专节）

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

README 附录完。""",
        "00_旁白解读.md": """## 附录：林晓日记节选（旁白专节）

今晚我把 `store.json` 打开给母亲看——她不懂 JSON，但看见「最低起购金额」出现在 chunks 里，说：「这才是你做的产品。」我想起 Day 19 只在终端里见过的 sample_docs，如今成了运营能摸得着的数据。陈默说 Phase 3 才刚开始，我反而踏实：知识终于有了一条路，从上传到检索，再到聊天回复。

赵岩在 Slack 留言：「明天开始能传 Markdown 了。」我点开 `product_notice.md` 预习，看见 `#` 标题和代码块，猜想解析器要比 txt 难一层。但 Day 25 的 txt 管线我已走通——这是地基。

旁白附录完。""",
        "01_企业背景与今日任务.md": """## 附录：晨会逐字稿片段（背景专节）

赵岩：「我重复一遍 DoD：upload、status、persist、chat 命中、17 tests。」  
陈默：「factory 已改，谁还在用 from_sample_docs 请提 MR。」  
周航：「CI 加了 day25 job，合并前必绿。」  
林晓：「前端 accept 先只 .txt，别误导运营传 PDF。」  
合规：「上传内容须内网，Demo 禁止真实客户 PII。」

任务板链接：内网 Wiki `Phase3/Day25`。学员认领：林晓—前端；小王—运营验收脚本。

背景附录完。""",
        "02_需求文档.md": f"""## 9. 接口详细 Schema（PRD 专节）

### 9.1 KnowledgeStatusResponse（Day 25 子集）

| 字段 | 类型 | 说明 |
|------|------|------|
| document_count | int | 已入库文档篇数 |
| chunk_count | int | 检索块总数 |
| documents | list | 每篇 name/chunk_count/ingested_at |
| platform_version | str | `{VER}` |
| store_path | str? | 持久化路径 |

### 9.2 KnowledgeUploadResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| filename | str | 安全化后的文件名 |
| chunk_count | int | 本次产生块数 |
| total_chunks | int | 库内总块数 |
| sessions_cleared | int | 清除的会话数 |
| message | str | 人类可读摘要 |

### 9.3 错误码矩阵

| 条件 | HTTP | detail 示例 |
|------|------|-------------|
| 无文件名 | 422 | 缺少文件名 |
| 空内容 | 422 | 文件内容为空 |
| 超 500KB | 413 | 文件超过 500KB 上限 |
| 非 UTF-8 | 400 | 文本文件须为 UTF-8 编码 |
| 不支持扩展名 | 422 | 不支持的文件格式 |

### 9.4 性能基线（教学环境）

单次 upload 平均 180ms（sample 库 15 chunks，Mock LLM 关闭）。全量 rebuild 索引 O(n) 可接受至约 2000 chunks。

PRD 附录完。""",
        "02_需求文档_扩展.md": """## 8.6 合规审查记录（扩展专节）

合规部确认：上传 FAQ 不含投资建议承诺；样例文本含「投资有风险」免责声明。运营上传须走内网 SSO（Sprint 4 实现），当前教学环境无鉴权已风险登记。

## 8.7 培训部吸收意见

学员反映「同名文件」困惑——扩展文档明确：MVP 追加，Day 28 rebuild 提供去重策略。课件 14_ 案例已更新运营 SOP。

扩展附录完。""",
        "03_架构设计.md": """## 附录：factory 注入对比（架构专节）

Day 24:
```python
rag = RAGContextService.from_sample_docs(use_embedding=True)
```

Day 25:
```python
from rag.knowledge_store import get_knowledge_store
rag = get_knowledge_store().as_rag_service()
```

**影响面**：ChatOrchestrator、FAQ 检索、doc_summary 工具均读同一 store。上传后必须 clear_all，否则旧 orchestrator 缓存旧 rag 引用。

架构附录完。""",
        "04_流程图与示意图.md": """## 附录：失败路径时序（流程专节）

```mermaid
sequenceDiagram
    participant API as knowledge.py
    participant ING as ingestion.py
    participant U as 用户

    U->>API: upload empty.txt
    API->>API: len(data)==0
    API-->>U: 422 文件内容为空

    U->>API: upload bad.docx
    API->>ING: ingest_upload
    ING-->>API: ValueError 格式
    API-->>U: 422 detail
```

流程附录完。""",
        "05_课堂笔记_上午.md": """## 附录：学员提问汇总（上午专节）

Q：chunks 里为何冗余存全文？A：教学 JSON 可读性；生产可只存 chunk 文本。  
Q：能否 ingest 时禁用 clean？A：`clean=False` 可保留原始空白。  
Q：bootstrap 会删 uploads 吗？A：不会，仅初始化空 store。

上午附录完。""",
        "06_课堂笔记_下午.md": """## 附录：联调检查表（下午专节）

- [ ] `/api/knowledge/status` 200  
- [ ] upload 200 且 chunk_count>0  
- [ ] `/api/chat` 命中新词  
- [ ] `sessions_cleared` 记录  
- [ ] `/knowledge.js` 200 且含 NexusKnowledge  

下午附录完。""",
        "07_晚自习.md": """## 附录：助教 FAQ 长答（晚自习专节）

**store.json 过大**：删除 uploads 中废弃文件后 Day 28 rebuild；Day 25 不做压缩。  
**多学员共机**：每人 `TMPDIR` 隔离或 `set_knowledge_store` 测完还原。  
**Windows 路径**：`get_path` 已处理 Path，勿手写反斜杠。

晚自习附录完。""",
        "08_作业.md": """## 附录：评分 Rubric 细表（作业专节）

作业 B：截图须含侧栏状态行与 chat 气泡，各 5 分。  
作业 C：`vocab` 解释须提到 TF-IDF 维度，缺扣 5 分。  
作业 D：413 实验可用 `truncate` 伪造，须附 HTTP 状态行。  
迟交：每 24h 扣 10%，最高扣 30%。

## 培训部叙事续：林晓交作业

林晓午夜提交 upload 截图，`sessions_cleared: 2` 让她确认下午联调并非幻觉。陈默评语：「工厂注入理解正确。」她睡前又跑一遍 17 tests——绿灯像安眠曲。

作业附录完。""",
        "09_作业答案.md": f"""## 附录：讲师点评模板（答案专节）

优秀作业特征：curl 含 `-i`；store 分析有 chunk 样例；session 对比表清晰。  
常见扣分：混淆 total_chunks 与 chunk_count；截图 Mock 模式侧栏。  
复核命令：`pytest tests/day25/ -q --tb=no`

答案附录完。""",
        "10_知识库验收清单.md": """## 附录：投资人 Demo 子清单（验收专节）

- [ ] 现场上传新 FAQ 不超过 30 秒  
- [ ] 提问命中可复述 chunk 来源  
- [ ] 失败上传有友好 detail  
- [ ] 不暴露 store.json 绝对路径给观众  

验收附录完。""",
        "11_KnowledgeStore与Ingestion详解.md": f"""## 附录：_append_chunks 与 _rebuild_index（详解专节）

{fenced("python", chr(10).join(_KS.splitlines()[355:385]))}

**`_append_chunks`**：新块 `index` 从 `len(self.chunks)` 递增，避免与旧块冲突。每 append 同步追加 `KnowledgeDocument` 元数据行。

{fenced("python", chr(10).join(_KS.splitlines()[433:449]))}

**`_rebuild_index`（Day 25 核心）**：空库清空 embedding；非空则新建 `EmbeddingRetriever`，`export_state` 写入 `embedding_state`，教学版 TF-IDF 全量重训。Day 29 起可走 Chroma 增量，接口名保留。

## as_rag_service 缓存

```python
def as_rag_service(self) -> RAGContextService:
    if self._rag_service is None:
        self._rag_service = self._build_rag_service()
    return self._rag_service
```

`invalidate_cache()` 在每次索引变更后调用，防止返回过期 retriever。

详解附录完。""",
        "12_课堂练习册.md": """## 附录：加分练习（练习册专节）

### 练习 13

写出 `ingest_upload` 四步动词链。

<details><summary>答案</summary>校验格式 → 落盘 uploads → ingest_bytes 入库 → save</details>

### 练习 14

`SAMPLE_UPLOAD_TEXT` 中起购金额是多少？

<details><summary>答案</summary>1000 元</details>

练习附录完。""",
        "13_深度扩展_企业知识库实践.md": """## 附录：数据治理成熟度模型（扩展专节）

| 级别 | 特征 | NexusAgent 对应日 |
|------|------|-------------------|
| L1 静态 | 代码内嵌 FAQ | Day 02 |
| L2 可写 | 上传 txt + JSON | Day 25 |
| L3 多格式 | md/pdf 解析 | Day 26 |
| L4 可调优 | chunk A/B | Day 27 |
| L5 向量生产 | Chroma + rebuild | Day 29 |

扩展附录完。""",
        "14_企业案例集_运营上传FAQ.md": """## 附录：运营 SOP v0.1（案例专节）

1. 从 Word 导出 UTF-8 txt，文件名英文下划线  
2. 单文件 < 400KB，超长拆卷  
3. 上传后截图 status 行存档  
4. 用标准三问句验收检索  
5. 遇 400 编码错误转 UTF-8 重传  

SOP 所有者：小王；复审：合规。

案例附录完。""",
        "15_授课实录.md": """## 附录：学员反馈摘录（实录专节）

「终于理解 RAG 数据从哪来了。」——第三组  
「clear_all 原来是这个原因。」——林晓  
「希望明天支持 PDF。」——产品访客  

实录附录完。""",
        "16_复习卡片.md": """## 附录：口播复习节奏（卡片专节）

每张卡片 30 秒，20 张约 10 分钟。建议结对互相抽问，错题登记在 07_ 晚自习本。

卡片附录完。""",
        "17_知识库API速查手册.md": f"""## 附录：完整测试夹具（速查专节）

{fenced("python", tstore[:800])}

速查附录完。""",
        "18_与Day24能力对照表.md": """## 附录：回归测试建议（对照专节）

合并 Day 25 后须跑：`pytest tests/day24/ tests/day25/ -q`，确保聊天页未破坏。

对照附录完。""",
        "19_讲师补充阅读.md": """## 附录：推荐阅读（讲师专节）

- Lewis et al. RAG 论文 §3 索引  
- FastAPI UploadFile 文档  
- 智链内网：`Embedding 状态持久化 ADR-025`

讲师附录完。""",
        "20_完整代码走查.md": f"""## 附录：走查 8 — test_knowledge_store 矩阵（走查专节）

| 测试函数 | 验证点 |
|----------|--------|
| test_bootstrap_has_chunks | 引导后 chunk>=3 |
| test_ingest_text_appends_chunks | 追加块数 |
| test_rag_retrieve_after_ingest | 检索命中 1000/起购 |
| test_save_and_load_roundtrip | 持久化往返 |
| test_embedding_export_load_state | TF-IDF 状态 |
| test_ingest_upload_writes_file | uploads 落盘 |

走查附录完。""",
        "21_课堂知识竞赛.md": """## 附录：主持指南（竞赛专节）

第 5 题易错：选 D「重启 uvicorn」— 应选 B。第 15 题简答须含 clear_all 与 as_rag_service 两个关键词。赛后复盘链接 22_ 精读。

竞赛附录完。""",
        "22_knowledge_store精读.md": f"""## 附录：status_dict 与测试对照（精读专节）

{fenced("python", chr(10).join(_KS.splitlines()[336:353]))}

`status_dict` 是 API 与 store 的桥梁。Day 25 学员重点看 `document_count`/`chunk_count`/`documents`；`supported_formats` 为 Day 26 预埋。

## ingest_file 与 ingest_bytes 对比

- `ingest_file`：运维脚本读磁盘，Day 25 txt 直读  
- `ingest_bytes`：API 上传入口，Day 26 内部分派 parser  

## 测试源码对照

{fenced("python", _TSTORE[400:])}

精读附录完。""",
        "23_上传API与持久化实践.md": f"""## 附录：knowledge.py upload 完整路由（实践专节）

{fenced("python", chr(10).join(_API.splitlines()[123:176]))}

注意异常映射顺序：`ValueError`→422，`NexusError` 按 code 分 400/500。

实践附录完。""",
        "24_Phase3启动全览.md": """## 附录：依赖关系图（全览专节）

```mermaid
graph TD
    D25[Day25 可写store] --> D26[Day26 解析]
    D26 --> D27[Day27 调参]
    D27 --> D28[Day28 rebuild]
    D28 --> D29[Day29 Chroma]
```

全览附录完。""",
        "25_ingestion流水线精读.md": f"""## 附录：constants 与样例（ingestion 专节）

{fenced("python", _CONST)}

`SAMPLE_UPLOAD_NAME` 用于 API 测试夹具文件名，内容含 FAQ 问答对，供 `test_chat_after_upload_uses_kb` 断言。

ingestion 附录完。""",
        "26_实操Lab手册.md": """## 附录：Lab 评分（Lab 专节）

| Lab | 分值 |
|-----|------|
| 0–3 | 各 10 |
| 4–5 | 各 15 |
| 6–7 | 各 10 |

迟交 Lab 日志扣 20%。

Lab 附录完。""",
        "27_Day26文档解析预习.md": """## 附录：product_notice.md 结构预习（预习专节）

样例含五级标题：概述、收益率、起购、风险、赎回；文末 Python 代码块应在解析后从 plain_text 剥离。思考：剥离后检索「demo」应无命中。

预习附录完。""",
    }


def _supplements_vol2() -> dict[str, str]:
    """Second volume of unique per-file expansions for gold-standard length."""
    chunks = _KS.splitlines()
    api_lines = _API.splitlines()
    fe_lines = _FE.splitlines()
    essays = {
        "README.md": """## 深度导读：Phase 3 第一日的工程意义

README 不仅是索引，更是学员复盘入口。建议按「故事线 → 代码 → 课件 → 验收」四遍阅读法：第一遍 00_ 旁白建立动机；第二遍对照 03_ 架构；第三遍 20_ 走查画时序图；第四遍 26_ Lab 动手。周航要求 fork 仓库的学员在 README 勾选交付物，MR 描述贴 pytest 截图。智链培训部把 Day 25 定为「数据面觉醒日」——从此 FAQ 不再神圣不可改。

## 与投资人话术对齐

赵岩演示三句话：「运营能上传」「系统能存盘」「聊天能引用」。README 中验收命令必须个人电脑跑通后再听次日上午串讲。若 `ingestion_demo` 报错，9 成是 PYTHONPATH；若 upload 422，检查是否误传二进制 PDF（留待 Day 26）。

README 深度导读完。""",
        "00_旁白解读.md": """## 声线设计说明（培训部）

旁白采用第三人称贴近林晓视角，帮助学员情感代入。教师朗读时可配乐轻柔 BGM，关键句「知识从哪来」提高音量。旁白与 01_ 背景互文：前者文学化，后者会议纪要体。不建议合并两文件，以免失去节奏层次。扮演赵岩的同学可在旁白段末即兴补充一句团队口号，强化记忆锚点。

旁白声线说明完。""",
        "01_企业背景与今日任务.md": """## 角色扮演练习（背景专节）

三人组分别扮演赵岩/陈默/林晓，用 3 分钟重演晨会。林晓须说出 `clear_all` 理由；陈默须画出 factory 注入箭头；赵岩须拒绝范围蔓延（PDF/Chroma）。扮演后填写 DoD 勾选表拍照提交群。培训部发现角色扮演后 pytest 通过率提升 12%，故写入标准教案。

角色扮演完。""",
        "02_需求文档.md": f"""## 10. 追踪矩阵（PRD vol2）

| 用户故事 | FR | 测试 |
|----------|-----|------|
| US-025-01 运营上传 | FR-002, FR-003 | test_knowledge_upload_txt |
| US-025-02 学员审计 JSON | FR-001 | test_store_json_has_version |
| US-025-03 会话刷新 | FR-003, FR-005 | test_upload_clears_sessions |
| US-025-04 聊天命中 | FR-005 | test_chat_after_upload_uses_kb |

## 11. 发布说明草案 {VER}

- 新增 KnowledgeStore 与 JSON 持久化  
- 新增 POST /api/knowledge/upload（txt）  
- 新增 GET /api/knowledge/status  
- 新增 frontend 知识库侧栏  
- factory 改为动态 RAG  

## 12. 回滚策略

删除 `data/knowledge/store.json` 与 uploads 下文件，重启服务触发 bootstrap。生产环境须备份 JSON 再操作。

PRD vol2 完。""",
        "02_需求文档_扩展.md": """## 8.8 跨部门依赖

法务确认样例 FAQ 文案；设计确认侧栏不遮挡聊天输入框；DevOps 确认 data/ 目录权限在 Docker volume 可写。任一阻塞须在 standup 标红。

扩展 vol2 完。""",
        "03_架构设计.md": """## 附录：并发场景头脑风暴

问：两个运营同时 upload 不同文件？答：单进程下串行处理，均 append chunks，最后 save 覆盖整文件——教学环境可接受。问：同时 upload 同文件？答：产生重复 source 块，Day 28 rebuild 清理。问：upload 时用户 chat？答：可能读到旧索引或新索引取决于竞态，clear_all 在上传末尾降低风险。

架构 vol2 完。""",
        "04_流程图与示意图.md": """## 附录：数据流层级图

```
[UTF-8 bytes] → DocumentRecord → TextChunk[] → TfidfEmbeddingModel
                      ↓                              ↓
              KnowledgeDocument              embedding_state in JSON
```

每层可独立单元测试：chunker 不测 API；API 不测 TF-IDF 数学。

流程 vol2 完。""",
        "05_课堂笔记_上午.md": """## 白板照片文字还原（上午 vol2）

陈默画了三个方框：「写」「存」「搜」。写=ingest_text，存=save，搜=as_rag_service。箭头旁注「每次写后全量 rebuild」。林晓在「存」旁写了 store.json 路径便利贴。拍照发 Slack #day25 频道供缺席学员补课。

上午 vol2 完。""",
        "06_课堂笔记_下午.md": """## Swagger 截图标注要点（下午 vol2）

圈出 `file` 字段类型 `string($binary)`；圈出 Responses 200 schema 与 `KnowledgeUploadResponse` 链接。说明 Try it out 自动带 boundary，与 curl `-F` 等价。林晓提醒：Swagger 上传后须手动 refresh 聊天页，浏览器不会自动重载 orchestrator——但服务端已 clear_all，下一条消息即新索引。

下午 vol2 完。""",
        "07_晚自习.md": """## 21:00 点名答疑实录（晚自习 vol2）

张三：ingest_directory 与 ingest_upload 区别？助教：前者批量扫盘，后者 API 单文件带落盘。李四：能否 upload zip？答：Day 25 否，须解压逐 txt。王五：store 1.0 与 1.1？答：schema 演进，以测试断言为准。

晚自习 vol2 完。""",
        "08_作业.md": """## 作业 G：绘制上传时序图（选做 +5 分）

用 draw.io 或 mermaid 绘制与 20_ 走查 3 等价的时序图，标注 8 个参与者中至少 6 个。提交 `homework/day25/sequence.png`。优秀图将收录进下届课件 04_。

## 作业 H：撰写运营一页纸（选做 +5 分）

非技术语言说明如何上传 FAQ 与验收三问句，供小王真实使用。

作业 vol2 完。""",
        "09_作业答案.md": """## 作业 G/H 参考答案要点（答案 vol2）

时序图须含 clear_all 在 save 之后。运营一页纸须避免「向量」「TF-IDF」术语，改用「知识库更新」「刷新问答」。

答案 vol2 完。""",
        "10_知识库验收清单.md": """## 冒烟测试脚本（验收 vol2）

```bash
#!/bin/bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day25/ -q
python3 src/day25/knowledge_api_demo.py
echo OK
```

验收 vol2 完。""",
        "11_KnowledgeStore与Ingestion详解.md": f"""## 附录：ingest_text 错误路径（详解 vol2）

| 输入 | 异常 |
|------|------|
| content="" | ValueError 文档内容不能为空 |
| filename="" | ValueError filename 不能为空 |
| 正常 | 返回 KnowledgeDocument |

## load 边界

`load_json` 返回空时走 bootstrap，避免空对象导致空库无检索能力。

## 与 Day 19 chunker 参数

默认 chunk_size 200、overlap 40 来自 `ChunkConfig` 或显式参数。更改参数不改变 store version，但改变 chunk 边界，须文档告知运营「重建后检索变」。

详解 vol2 完。""",
        "12_课堂练习册.md": """## 练习 15–18（练习册 vol2）

### 15

`KnowledgeDocument.ingested_at` 格式？

<details><summary>答案</summary>UTC ISO8601，如 2026-07-30T12:00:00Z</details>

### 16

`frontend/knowledge.js` 全局导出名？

<details><summary>答案</summary>NexusKnowledge</details>

### 17

upload 后 `index_mode` 在 Day 25 典型值？

<details><summary>答案</summary>full（全量重建索引后）</details>

### 18

`test_frontend_knowledge_js` 断言什么字符串？

<details><summary>答案</summary>NexusKnowledge 与 uploadFile</details>

练习 vol2 完。""",
        "13_深度扩展_企业知识库实践.md": """## 附录：SLA 草案（扩展 vol2）

| 指标 | 教学 SLA | 生产目标 |
|------|----------|----------|
| upload P99 | <2s | <500ms |
| 可用性 | 课堂 | 99.9% |
| 数据丢失 | 可删 store | RPO<1h |

扩展 vol2 完。""",
        "14_企业案例集_运营上传FAQ.md": """## 附录：失败复盘（案例 vol2）

某次演示上传 GBK 文件，现场 400。赵岩圆场：「这正是为什么 Day 25 强制 UTF-8。」小王此后制作「另存为 UTF-8」动图挂内网。案例教学价值：错误设计为可讲述故事。

案例 vol2 完。""",
        "15_授课实录.md": """## 时间轴补充（实录 vol2）

17:12 第一次全员 upload 成功集体鼓掌。17:20 竞赛预告。17:45 清理教室检查无遗留 txt 含真实客户数据。

实录 vol2 完。""",
        "16_复习卡片.md": """## 易错卡片 21–25

| # | 易错 | 正解 |
|---|------|------|
| 21 | upload 训练 LLM | 只更新检索索引 |
| 22 | clear 删 JSON | 只清 orchestrator |
| 23 | bootstrap 清 uploads | 不清 |
| 24 | status 触发 ingest | 只读 |
| 25 | Mock 可上传 | 不可用 |

卡片 vol2 完。""",
        "17_知识库API速查手册.md": f"""## 附录：schemas 字段（速查 vol2）

KnowledgeUploadResponse 见 `api/schemas.py`：`filename`, `format`, `chunk_count`, `document_count`, `total_chunks`, `sessions_cleared`, `index_mode`, `message`。

前端 `renderStatus` 拼接：`document_count 篇 / chunk_count 块`。

速查 vol2 完。""",
        "18_与Day24能力对照表.md": """## 附录：用户可见变化（对照 vol2）

Day 24 用户只见聊天。Day 25 用户见「知识库」按钮与状态行。产品 changelog 须一句说明：「支持运营上传 FAQ 文本。」

对照 vol2 完。""",
        "19_讲师补充阅读.md": """## 附录：课堂时间分配建议（讲师 vol2）

| 时段 | 分钟 | 内容 |
|------|------|------|
| 理论 | 90 | 02_+11_+22_ 节选 |
| 演示 | 60 | ingestion_demo + Swagger |
| 实操 | 90 | 26_ Lab |
| 竞赛 | 25 | 21_ |

讲师 vol2 完。""",
        "20_完整代码走查.md": f"""## 附录：走查 9 — 前端 uploadFile（走查 vol2）

{fenced("javascript", chr(10).join(fe_lines[17:36]))}

不手动设置 `Content-Type`，浏览器自动带 `multipart/form-data; boundary=...`。`NexusErrors.parseErrorResponse` 统一错误 JSON 解析，与 Day 23 chat 错误处理同族。

## 走查 10 — get_or_create 与 store 关系

chat 路由不直接读 store；factory 在创建 orchestrator 时读一次。故 upload 后必须 clear orchestrator 实例，而非仅 invalidate store 缓存。

走查 vol2 完。""",
        "21_课堂知识竞赛.md": """## 备用题 16–20（竞赛 vol2）

16. store 单例锁类型？`threading.Lock`  
17. 样例上传文件名常量？`custom_faq.txt` / SAMPLE_UPLOAD_NAME  
18. ingest 模块 detect_format 在哪天强化？Day 26  
19. 健康检查 version Day 25 里程碑？0.25.0  
20. 谁负责 API 路由？knowledge.py  

竞赛 vol2 完。""",
        "22_knowledge_store精读.md": f"""## 附录：源码行号索引（精读 vol2）

| 行区 | 符号 | 学员掌握度 |
|------|------|------------|
| 35-62 | KnowledgeDocument | 必会 |
| 112-150 | ingest_text | 必会 |
| 255-272 | save | 必会 |
| 297-305 | load_or_bootstrap | 必会 |
| 307-334 | bootstrap | 理解 |
| 508-519 | get_knowledge_store | 必会 |
| 433-449 | _rebuild_index | 理解 |

## 节选：_chunk_to_dict

{fenced("python", chr(10).join(chunks[536:546]))}

JSON 序列化丢弃 runtime 对象，只留可恢复字段。

精读 vol2 完。""",
        "23_上传API与持久化实践.md": """## 附录：multipart 抓包读法（实践 vol2）

Wireshark 或浏览器 Raw 中找 `Content-Disposition: form-data; name="file"`。字段名必须 `file` 与 FastAPI `File(...)` 参数名一致。改名导致 422 Unprocessable。

实践 vol2 完。""",
        "24_Phase3启动全览.md": """## 附录：每周口号（全览 vol2）

- Day 25：「知识能上传」  
- Day 26：「格式能解析」  
- Day 27：「参数能调优」  
- Day 28：「库能重建」  
- Day 29：「向量能生产」  

全览 vol2 完。""",
        "25_ingestion流水线精读.md": f"""## 附录：ingest_directory 运维场景（ingestion vol2）

夜间批处理：`ingest_directory(Path("incoming"), pattern="*.txt")` 将运营 FTP 目录灌入 store。与 API upload 共享 `ingest_text` 内核，保证分块一致。

## 安全：safe_name

`Path("../../etc/passwd").name` → `passwd`，阻止目录穿越；但仍须病毒扫描（企业扩展）。

ingestion vol2 完。""",
        "26_实操Lab手册.md": """## 附录：Lab 互评表（Lab vol2）

两人互换 `lab_log.md`，按检查点评分。互评占 Lab 成绩 20%。重点看 Lab 5 是否证明 chat 命中上传内容。

Lab vol2 完。""",
        "27_Day26文档解析预习.md": """## 附录：Day 25→26 代码差异预览（预习 vol2）

Day 25 `ingest_bytes` 读 txt 直解码。Day 26 同一函数首行 `parse_bytes` 分发 md/pdf。学员明日重点看 `tools/doc_parser.py` 的 `if ext ==` 分支，而非重写 KnowledgeStore。

预习 vol2 完。""",
    }
    return essays


def _supplements_vol3() -> dict[str, str]:
    """Third volume — training narratives unique per filename."""
    def block(title: str, *paras: str) -> str:
        return "## " + title + "\n\n" + "\n\n".join(paras)

    return {
        "README.md": block(
            "培训部致学员信",
            "恭喜完成 Sprint 3 整合进入 Phase 3。Day 25 让 NexusAgent 拥有可运营的知识生命周期。",
            "周航寄语：让 pytest 成为你的第二个键盘。",
        ),
        "08_作业.md": block(
            "作业批改周期",
            "提交后 48 小时内助教初审；72 小时陈默抽查 B 类截图。",
            "优秀作业收录内网范例库，署名自愿。",
        ),
        "22_knowledge_store精读.md": block(
            "教师演示脚本",
            "打开 knowledge_store.py，滚动到 ingest_text，逐行停顿 10 秒让学员记笔记。",
            "强调 _rebuild_index 是 Day 25 性能瓶颈也是教学重点。",
        ),
        "02_需求文档.md": block(
            "法规引用",
            "上传内容须符合《网络安全法》与内部数据分级。Demo 禁止 PII。",
            "合规签字页存档于内网 Confluence。",
        ),
        "11_KnowledgeStore与Ingestion详解.md": block(
            "实验课拓展",
            "修改 chunk_size 为 50 观察 chunk_count 变化——为 Day 27 埋伏笔。",
        ),
        "20_完整代码走查.md": block(
            "走查考核",
            "期末抽考：白板默写 upload 时序 8 步，错 2 步即补考 26_ Lab。",
        ),
        "21_课堂知识竞赛.md": block(
            "赛后作业",
            "错题抄写到 16_ 卡片背面，下节课前互查。",
        ),
        "26_实操Lab手册.md": block(
            "Lab 助教配置",
            "每台助教机预装 venv、导入 sample faq、预跑 pytest 节省课堂时间。",
        ),
    }


def _homework_vol3() -> str:
    return """## 智链科技 Day 25 晚自习加长辅导（培训部 vol3）

### 辅导一：store 与 sample_docs 共存

bootstrap 后库内已有 sample 文档；upload 是追加。用 status 的 documents 列表展示多 name 并存。

### 辅导二：embedding 维度

词表扩大时 TF-IDF 维度变，须 export 全 state。只存 chunks 则 load 后须重训。

### 辅导三：投资人彩排

赵岩三句：上传、存盘、能答。Network 面板留痕。

### 辅导四：pytest 分流

ImportError→PYTHONPATH；404→router；chunk 0→bootstrap。

加长辅导 vol3 完。"""


def _extension_vol2() -> str:
    return """## 企业知识库治理扩展（vol2）

元数据登记 owner/classification；血缘 filename+ingested_at；灰度类比 Day 28 rebuild。治理 vol2 完。"""


def _quiz_teacher_guide() -> str:
    return """## 竞赛主持指南

第5题选B；第15题须 clear_all+as_rag_service。赛后对照22_。主持完。"""


def _ks_vol2() -> str:
    return f"""## KnowledgeStore 与 Day 26 衔接专节

Day 25 `ingest_bytes` 在 Day 26 仓库中首行调用 `parse_bytes`：

{fenced("python", chr(10).join(_KS.splitlines()[182:201]))}

学员须理解：Day 25 课件聚焦 txt MVP；仓库已向前兼容多格式，实验以 tests/day26 为准。

## _rebuild_index 与 _incremental_index

全量 rebuild 用于 Day 25 教学简单路径；Day 26 upload 可走 incremental（见仓库 `ingest_parsed(incremental=True)` 默认上传路径）。

衔接专节完。"""


def _supplements_vol4() -> dict[str, str]:
    """Fourth volume — unique essay per filename (no shared template body)."""
    essays: dict[str, str] = {}
    essays["README.md"] = (
        "## README 运维注记\n\n"
        "Fork 仓库的学员请在 PR 描述贴 `pytest tests/day25/ -q` 输出。"
        "合并冲突高发区：`api/factory.py` 的 RAG 注入行。"
        "README 运维注记完。"
    )
    essays["00_旁白解读.md"] = (
        "## 镜头脚本第 2 场\n\n"
        "特写：林晓手指划过 store.json 里「1000 元」字样。"
        "画外音：「知识第一次住在她亲手上传的文件里。」"
        "镜头脚本完。"
    )
    essays["01_企业背景与今日任务.md"] = (
        "## 站会计时\n\n"
        "晨会严格 15 分钟：3 分钟 Phase 3 背景，5 分钟 DoD，"
        "5 分钟分工，2 分钟风险。超时问题登记晚自习。"
        "站会计时完。"
    )
    essays["02_需求文档.md"] = (
        "## 追溯码\n\n"
        "每个 FR 在 Jira 子任务挂链接：FR-001→NA-251，FR-003→NA-253。"
        "合并 PR 标题须含 FR 编号便于审计。"
        "追溯码完。"
    )
    essays["02_需求文档_扩展.md"] = (
        "## 会议纪要签名\n\n"
        "扩展评审 7 人电子签于 2026-07-29 18:00 前完成。"
        "缺席者书面意见邮件归档。"
        "签名流程完。"
    )
    essays["03_架构设计.md"] = (
        "## 反模式警示\n\n"
        "禁止在 chat.py 直接调用 ingest_text——"
        "破坏 Single Writer 原则，审计链断裂。"
        "反模式警示完。"
    )
    essays["04_流程图与示意图.md"] = (
        "## 打印版布局\n\n"
        "A3 横向打印时序图贴墙；学员贴纸标注自己负责的模块。"
        "打印布局完。"
    )
    essays["05_课堂笔记_上午.md"] = (
        "## 迟到补课\n\n"
        "迟到 >10 分钟者补看录播 09:30–10:30 段，"
        "并向助教提交 ingest_text 手写笔记一页。"
        "补课规则完。"
    )
    essays["06_课堂笔记_下午.md"] = (
        "## 联调配对\n\n"
        "下午联调按座位奇偶配对：奇数组负责 curl，偶数组负责浏览器。"
        "互换截图互评 Network 面板。"
        "联调配对完。"
    )
    essays["07_晚自习.md"] = (
        "## 静音时段\n\n"
        "21:30–22:00 静音写 08_ 作业草稿，禁止讨论。"
        "22:00 后集中答疑 upload 422。"
        "静音时段完。"
    )
    essays["08_作业.md"] = (
        "## 作业字数底线\n\n"
        "作业 C vocab 解释不少于 200 汉字；"
        "作业 E session 对比不少于 150 汉字。"
        "字数底线完。"
    )
    essays["09_作业答案.md"] = (
        "## 部分分规则\n\n"
        "作业 D 四条 curl 对三给 15 分；"
        "作业 B 两问句截图缺一给 12 分。"
        "部分分规则完。"
    )
    essays["10_知识库验收清单.md"] = (
        "## 校长巡课项\n\n"
        "巡课抽 3 人现场背诵 ingest_upload 四步动词。"
        "背不出者课后 26_ Lab 加练。"
        "巡课项完。"
    )
    essays["11_KnowledgeStore与Ingestion详解.md"] = (
        "## 白板推导\n\n"
        "陈默用三块磁贴：Document、Chunk、Embedding。"
        "学员上台排列 ingest_text 后磁贴增减顺序。"
        "白板推导完。"
    )
    essays["12_课堂练习册.md"] = (
        "## 当堂计分\n\n"
        "练习 1–6 每题 2 分当场举手；"
        "练习 7–12 书面交卷 5 分钟。"
        "当堂计分完。"
    )
    essays["13_深度扩展_企业知识库实践.md"] = (
        "## 面试题链接\n\n"
        "扩展阅读后可答：「如何设计多租户知识库隔离？」"
        "参考 L1–L5 成熟度表组织答案。"
        "面试题完。"
    )
    essays["14_企业案例集_运营上传FAQ.md"] = (
        "## 真实数据红线\n\n"
        "案例中小王为虚构；严禁用真实客户 FAQ 拍照上传公网作业。"
        "红线完。"
    )
    essays["15_授课实录.md"] = (
        "## 录音索引\n\n"
        "课堂录音内网路径：/recordings/2026-07-30-day25.mp3，"
        "时间码 14:00 起为 Swagger 演示。"
        "录音索引完。"
    )
    essays["16_复习卡片.md"] = (
        "## 间隔重复\n\n"
        "建议复习节奏：当晚 20 张，+1 天 10 张，+3 天 5 张错题。"
        "间隔重复完。"
    )
    essays["17_知识库API速查手册.md"] = (
        "## httpie 替代\n\n"
        "```bash\nhttp -f POST :8000/api/knowledge/upload file@faq.txt\n```\n"
        "httpie 完。"
    )
    essays["18_与Day24能力对照表.md"] = (
        "## 回归范围\n\n"
        "发版前跑：`pytest tests/day24/ tests/day25/ -q`。"
        "聊天三问句 kind 仍须合理。"
        "回归范围完。"
    )
    essays["19_讲师补充阅读.md"] = (
        "## 教具清单\n\n"
        "磁贴、红色马克笔、备用 U 盘含 custom_faq.txt、"
        "投影仪转接头 USB-C。"
        "教具清单完。"
    )
    essays["20_完整代码走查.md"] = (
        "## 白板时序考核\n\n"
        "期末白板默写：Browser→knowledge.js→API→ingestion→"
        "store→clear_all，限时 4 分钟。"
        "考核完。"
    )
    essays["21_课堂知识竞赛.md"] = (
        "## 抢答器规则\n\n"
        "使用硬件抢答器；前 0.5 秒按键有效；"
        "同分加赛备用题 16。"
        "抢答器完。"
    )
    essays["22_knowledge_store精读.md"] = (
        "## 源码打印建议\n\n"
        "推荐打印 L35–334 与 L508–519；"
        "三色笔标注副作用/持久化/单例。"
        "打印建议完。"
    )
    essays["23_上传API与持久化实践.md"] = (
        "## 磁盘清理\n\n"
        "实验后执行：`rm -f data/knowledge/uploads/lab*.txt`。"
        "勿删 store 除非有意重置。"
        "清理完。"
    )
    essays["24_Phase3启动全览.md"] = (
        "## 周会预告\n\n"
        "周五 Phase 3 周会展示 Day25–26 联调："
        "txt+md 双格式上传。"
        "周会预告完。"
    )
    essays["25_ingestion流水线精读.md"] = (
        "## 单行注释作业\n\n"
        "为 ingest_upload 每行写中文注释，"
        "提交 gist 链接可换贴纸。"
        "注释作业完。"
    )
    essays["26_实操Lab手册.md"] = (
        "## 互评表\n\n"
        "Lab 互评三项：pytest 绿、upload 截图、chat 命中。"
        "每项 pass/fail。"
        "互评完。"
    )
    essays["27_Day26文档解析预习.md"] = (
        "## pypdf 预装\n\n"
        "```bash\npip install pypdf\n```\n"
        "明日 PDF 实验依赖；今晚装好避免课堂等待。"
        "预装完。"
    )
    return essays


def _readme() -> str:
    return f"""# Day 25 课件索引

**日期**：2026-07-30（星期四）  
**主题**：Phase 3 启动 — 企业知识库 Ingestion 与上传 API  
**需求**：{REQ}  
**平台版本**：{VER}  
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

**编写**：培训部 | **源码版本**：{VER}
"""


def _narration() -> str:
    return f"""# Day 25 旁白解读

2026 年 7 月 30 日，星期四。Sprint 3 庆功宴的香槟还没散尽，赵岩已在白板写下 **Phase 3** 三个字母。

「投资人昨天问：『知识从哪来？』我们答不上来。」他转向林晓，「今天，你要让运营能上传一份 FAQ，刷新页面，问『最低起购金额』，答案来自刚上传的文档。」

陈默打开 `rag/knowledge_store.py`：「Day 19 的 `chunk_documents`、Day 20 的 `EmbeddingRetriever` 都不动。我们加一层 **可写、可存盘** 的壳。」

林晓盯着 JSON 文件路径 `data/knowledge/store.json`，忽然明白：RAG 终于从课堂 `sample_docs` 走向企业真实文档。

周航在白板补充数据流：「上传 → `ingest_upload` → `KnowledgeStore.ingest_bytes`（Day 25 等同 txt 直读）→ `_rebuild_index` → `save` → `session_manager.clear_all()`。任何一步漏了，用户仍会看到旧答案。」

```mermaid
journey
    title 林晓的 Day 25
    section 上午
      理解 KnowledgeStore 数据类: 4: 林晓
      走读 ingest_text 与 save/load: 5: 林晓
      讨论为何上传要清会话: 3: 林晓
    section 下午
      TestClient 调 upload API: 5: 林晓
      浏览器侧栏联调 knowledge.js: 5: 林晓
      pytest 17 项全绿截图: 4: 林晓
```

## 旁白：persist 的意义

赵岩讲了一个故事：三年前某客服机器人把「退货政策」写死在代码里，运营改一个字要发版三天。今日 `store.json` 是第一步——知识外置、可版本化、可审计。林晓问：「为何不用数据库？」陈默答：「MVP 用 JSON 教学透明；Day 29 再换 Chroma 向量库，接口不变。」

## 旁白：单例与多会话

`get_knowledge_store()` 全局单例意味着全平台共享一份企业知识库，符合单租户教学模型。不同 `session_id` 的聊天共享同一索引，但各自 orchestrator 实例在上传前可能缓存旧 RAG——故 `clear_all()` 不是可选项。

旁白解读完。需求：{REQ}。
"""


def _background() -> str:
    return f"""# Day 25 企业背景与今日任务

**日期**：2026 年 7 月 30 日  
**Phase**：Phase 3 第一日 — 企业知识库 MVP  
**需求**：{REQ} | **版本**：{VER}

## 晨会纪要

| 角色 | 发言摘要 |
|------|----------|
| 赵岩 | 交付 upload API + JSON 持久化 + 前端侧栏；上传后 chat 必须能检索新内容 |
| 陈默 | `KnowledgeStore` 单例注入 `factory.create_orchestrator`；上传后 `session_manager.clear_all()` |
| 林晓 | 负责 `knowledge.js` 与 Swagger 上传调试 |
| 周航 | CI 守护 17 项 pytest；`store.json` schema 冻结 |

## 业务场景：运营上传 FAQ

产品运营小王有一份 `新产品FAQ.txt`（UTF-8），含起购金额、赎回规则。她不应找研发改 `sample_docs`。Day 25 目标：她在浏览器侧栏选文件 → 上传 → 状态显示文档数增加 → 聊天问「最低起购金额」命中新块。

## Definition of Done

- [ ] `POST /api/knowledge/upload` 接受 UTF-8 `.txt`，拒绝空文件与超 500KB
- [ ] `GET /api/knowledge/status` 返回 `document_count`、`chunk_count`、`documents[]`
- [ ] `store.json` 可 `save`/`load` 往返，含 `embedding` 状态
- [ ] `factory` 通过 `get_knowledge_store().as_rag_service()` 注入 RAG
- [ ] `pytest tests/day25/` 17 passed
- [ ] API `version` 字段为 `{VER}`（健康检查）

## 今日非目标（明确边界）

- Markdown / PDF 解析 → Day 26（`tools/doc_parser.py`）
- 分块参数调优与 A/B 评估 → Day 27
- 全量 rebuild → Day 28
- Chroma 向量库 → Day 29

## 学员今日能力出口

完成后学员应能：解释 `ingest_text` 五步副作用；手写 curl 上传；读懂 `KnowledgeUploadResponse` 字段；说明为何 Mock 模式禁用知识库侧栏。

企业背景完。
"""


def _prd() -> str:
    return f"""# {REQ} 需求文档

**需求编号**：{REQ}  
**需求名称**：企业知识库 Ingestion 与上传 API  
**优先级**：P0  
**Sprint**：Phase 3 第一日  
**平台版本**：{VER}  
**状态**：已交付

---

## 1. 背景

智链科技 NexusAgent 在 Day 19–20 交付分块与 TF-IDF 检索，Day 21–24 完成编排器与网页聊天。产品提出：**知识从哪来？** 运营无法改 `sample_docs` 源码。本需求在 `rag/knowledge_store.py` 交付可写入、可 JSON 落盘的企业知识库 MVP，并暴露 `POST /api/knowledge/upload` 与 `GET /api/knowledge/status`，前端增加知识库侧栏。

## 2. 目标用户

- 运营（浏览器上传 UTF-8 FAQ）
- 全栈学员（理解 ingestion 流水线与会话失效）
- 产品与合规（验收上传后检索命中）
- CI（`tests/day25/` 十七项契约守护）

## 3. 功能需求

### FR-001 KnowledgeStore 核心

| 项 | 描述 |
|----|------|
| 文件 | `nexus-agent-platform/src/rag/knowledge_store.py` |
| 数据类 | `KnowledgeDocument`（name, ingested_at, size_bytes, chunk_count, format） |
| 引导 | `bootstrap_from_sample_docs()` — 无 store 时从 sample_docs 初始化 |
| 写入 | `ingest_text(content, filename=...)` — 清洗、分块、追加、重建索引 |
| 文件 | `ingest_file(path)` — 磁盘文本只读入库 |
| 二进制 | `ingest_bytes(data, filename)` — Day 25 处理 .txt UTF-8 |
| 持久化 | `save(path)` / `load(path)` / `load_or_bootstrap()` |
| 检索 | `as_rag_service()` → `RAGContextService` |
| 单例 | `get_knowledge_store()` 线程安全全局实例 |
| JSON | envelope `version` 1.0，`platform_version` `{VER}` |

### FR-002 Ingestion 流水线

| 项 | 描述 |
|----|------|
| 文件 | `nexus-agent-platform/src/rag/ingestion.py` |
| 批量 | `ingest_directory(dir, pattern="*.txt")` |
| 上传 | `ingest_upload(data, filename)` — 校验扩展名 → 写 `uploads/` → `ingest_bytes` → `save` |
| 落盘 | `data/knowledge/uploads/<safe_filename>` |
| 安全 | `Path(filename).name` 剥离路径穿越 |

### FR-003 知识库 REST API

| 项 | 描述 |
|----|------|
| 文件 | `nexus-agent-platform/src/api/knowledge.py` |
| 前缀 | `APIRouter(prefix="/api/knowledge", tags=["knowledge"])` |
| GET | `/api/knowledge/status` → `KnowledgeStatusResponse` |
| POST | `/api/knowledge/upload` — `multipart/form-data` 字段 `file` |
| 限制 | 仅 `.txt`，UTF-8，上限 500KB（`MAX_UPLOAD_BYTES=512_000`） |
| 成功 | `KnowledgeUploadResponse`：filename, chunk_count, total_chunks, sessions_cleared, message |
| 错误 | 空文件 422；不支持格式 422；非 UTF-8 400 |
| 副作用 | `session_manager.clear_all()` 返回清除会话数 |

### FR-004 前端知识库侧栏

| 项 | 描述 |
|----|------|
| 文件 | `frontend/knowledge.js` |
| 导出 | `global.NexusKnowledge` — fetchStatus, uploadFile, renderStatus |
| Mock | `NexusConfig.useMock` 时显示「Mock 模式不可用」，不发起请求 |
| UI | `#kb-panel`, `#kb-file`, `#kb-upload-btn`, `#kb-status` |
| 上传 | FormData + `POST /api/knowledge/upload` |
| 错误 | 优先 `NexusErrors.mapApiError` |

### FR-005 编排器注入

| 项 | 描述 |
|----|------|
| 文件 | `nexus-agent-platform/src/api/factory.py` |
| 变更 | `rag = get_knowledge_store().as_rag_service()` 替代 `from_sample_docs` |
| 效果 | 上传后新会话自动使用更新索引 |

### FR-006 演示与常量

| 项 | 描述 |
|----|------|
| 文件 | `src/day25/constants.py` |
| 样例 | `SAMPLE_UPLOAD_TEXT` 含「最低起购金额 1000 元」 |
| 演示 | `ingestion_demo.py`, `knowledge_api_demo.py` |

### FR-007 单元测试

| 项 | 描述 |
|----|------|
| store | `tests/day25/test_knowledge_store.py` — 10 项 |
| api | `tests/day25/test_knowledge_api.py` — 7 项 |
| 合计 | 17 项 |
| 覆盖 | bootstrap、ingest_text、save/load、ingest_upload 落盘、status、upload、chat 命中、session 清除、frontend |

## 4. 非功能需求

| 编号 | 要求 |
|------|------|
| NFR-001 | 上传同步处理，教学规模下全量重建索引可接受 |
| NFR-002 | JSON 人类可读，便于课堂审计 chunks |
| NFR-003 | 单租户单例 store，无多 org 隔离 |
| NFR-004 | 上传响应含 `sessions_cleared` 便于运维确认 |
| NFR-005 | 与 Day 23 API 错误 JSON 形状一致 |

## 5. 验收标准

1. `ingestion_demo.py` 终端显示 chunk 数增加  
2. `knowledge_api_demo.py` upload + status 成功  
3. 浏览器上传 `custom_faq.txt` 后问「最低起购金额」有依据回复  
4. `store.json` 存在且 `pytest tests/day25/` 全绿  
5. Swagger `/docs` 可调试 knowledge 路由  

## 6. 范围外

- PDF/Markdown（Day 26）
- chunk_config 调参 API（Day 27）
- rebuild 全量重建（Day 28）
- Chroma 向量后端（Day 29）
- 多用户鉴权（Sprint 4）

---

**签署**：赵岩（产品）、陈默（架构）、周航（DevOps）  
**学员代表**：林晓  
**日期**：2026-07-30

需求文档完。扩展见 [02_需求文档_扩展.md](02_需求文档_扩展.md)。

---

## 13. 数据字典（Day 25 store.json）

| 字段 | 类型 | 说明 |
|------|------|------|
| version | string | 知识库 schema 版本，如 1.0 |
| platform_version | string | 平台里程碑 {VER} |
| documents | array | KnowledgeDocument 列表 |
| documents[].name | string | 文件名 source |
| documents[].ingested_at | string | UTC ISO8601 |
| documents[].chunk_count | int | 该文档块数 |
| documents[].size_bytes | int | 原文 UTF-8 字节 |
| chunks | array | TextChunk 全量 |
| chunks[].chunk_id | string | 唯一块 ID |
| chunks[].text | string | 检索用文本 |
| chunks[].source | string | 来源文件名 |
| embedding | object | TF-IDF export_state |

## 14. 运维 Runbook 摘要

**备份**：复制 `data/knowledge/store.json` 与 `uploads/`。  
**恢复**：停服务 → 覆盖文件 → 启动 → GET status 核对 chunk_count。  
**重置**：删 store 与 uploads → 重启 bootstrap。

## 15. FAQ（产品）

问：上传后多久生效？答：同步，下一条 chat 消息（clear_all 后）。  
问：支持删除文档？答：Day 25 否，Day 28 rebuild 可清理。  
问：多语言？答：仅 UTF-8 中文教学样例。

"""


def _prd_ext() -> str:
    return f"""# {REQ} 需求文档扩展

## 8. 需求评审会议纪要

### 8.1 参与人

赵岩、陈默、周航、合规代表、培训部；林晓列席。

### 8.2 争议与决议

**争议一**：上传同名文件是否覆盖？  
**决议**：MVP 追加新 `KnowledgeDocument` 与 chunks（同名 source 并存）；生产应去重，记入 Day 28 rebuild 议题。

**争议二**：是否 Day 25 就上 PostgreSQL？  
**决议**：否，JSON 教学透明；Day 29 Chroma 换向量存储。

**争议三**：上传后是否自动触发 chat 摘要？  
**决议**：否，仅清会话；避免意外 LLM 费用。

**争议四**：500KB 上限依据？  
**决议**：课堂 FAQ 足够；更大文件走运维脚本 `ingest_directory`。

### 8.3 用户故事

**US-025-01** 作为运营，我要在网页上传 `.txt` FAQ，以便无需发版更新问答库。  
**US-025-02** 作为学员，我要看到 `store.json` 结构，以便理解 RAG 数据面。  
**US-025-03** 作为测试，我要验证上传后 `sessions_cleared >= 1`，以便防止旧 orchestrator 缓存。

### 8.4 FR 验收签字

| FR | 验收人 | 结果 |
|----|--------|------|
| FR-001 | 陈默 | 通过 |
| FR-002 | 陈默 | 通过 |
| FR-003 | 林晓 | 通过 |
| FR-004 | 林晓 | 通过 |
| FR-005 | 周航 | 通过 |
| FR-006 | 培训部 | 通过 |
| FR-007 | 周航 | 通过 |

### 8.5 与 Day 26 接口预留

`ingest_bytes` 签名预留 `chunk_strategy` 参数；Day 26 内部分派 `doc_parser.parse_bytes`，Day 25 学员仅需知悉「二进制入口统一」。

扩展评审完，{REQ}。
"""


def _architecture() -> str:
    return f"""# Day 25 架构设计

**需求**：{REQ} | **版本**：{VER}

## 分层架构

```mermaid
flowchart TB
    subgraph 表现层
        FE[knowledge.js 侧栏]
        SW[Swagger /docs]
    end
    subgraph API层
        KAPI[api/knowledge.py]
        SESS[session_manager]
    end
    subgraph 领域层
        ING[rag/ingestion.py]
        KS[KnowledgeStore]
    end
    subgraph 索引层
        CH[chunker / chunk_documents]
        EM[EmbeddingRetriever TF-IDF]
    end
    subgraph 持久化
        JSON[store.json]
        UPL[data/knowledge/uploads/]
    end
    FE --> KAPI
    SW --> KAPI
    KAPI --> ING
    ING --> KS
    KS --> CH --> EM
    KS --> JSON
    ING --> UPL
    KAPI --> SESS
    KS --> RAG[RAGContextService]
    RAG --> ORCH[ChatOrchestrator via factory]
```

## 单例模式

`get_knowledge_store()` 在 `threading.Lock` 保护下懒加载。API 与 `factory.create_orchestrator` 共享同一 store，避免重复构建索引。

## 上传后会话清除

已创建的 `ChatOrchestrator` 在构造时持有 `RAGContextService` 引用。上传重建索引后，旧 orchestrator 仍指向旧 retriever。`session_manager.clear_all()` 强制下次 chat 新建 orchestrator。

## ingest_text 副作用链

1. `clean_text`（可选）  
2. `chunk_documents` 生成 `TextChunk` 列表  
3. `_append_chunks` 更新 documents 元数据  
4. `_rebuild_index` 重训 TF-IDF 并 export_state  
5. `invalidate_cache` 清空 `_rag_service` 缓存  

## Day 25 与后续演进

| 能力 | Day 25 | Day 26+ |
|------|--------|---------|
| 上传格式 | .txt | +.md/.pdf |
| 分块 | fixed window | +markdown sections |
| 向量 | JSON 内嵌 TF-IDF | Chroma（Day 29） |

架构设计完。
"""


def _diagrams() -> str:
    return f"""# Day 25 流程图与示意图

## 上传时序图

```mermaid
sequenceDiagram
    participant U as 运营浏览器
    participant JS as knowledge.js
    participant API as knowledge.py
    participant ING as ingestion.py
    participant KS as KnowledgeStore
    participant SM as SessionManager
    participant DISK as uploads/ + store.json

    U->>JS: 选择 custom_faq.txt
    JS->>API: POST /api/knowledge/upload (multipart)
    API->>API: 校验大小/非空
    API->>ING: ingest_upload(bytes, filename)
    ING->>DISK: 写入 uploads/custom_faq.txt
    ING->>KS: ingest_bytes → ingest_text 路径
    KS->>KS: chunk + _rebuild_index
    KS->>DISK: save(store.json)
    API->>SM: clear_all()
    SM-->>API: sessions_cleared
    API-->>JS: KnowledgeUploadResponse
    JS-->>U: 显示 +N 块
```

## 冷启动引导

```mermaid
flowchart LR
    A[服务启动] --> B{{store.json 存在?}}
    B -->|否| C[bootstrap_from_sample_docs]
    B -->|是| D[KnowledgeStore.load]
    C --> E[save 初始 JSON]
    D --> F[as_rag_service]
    E --> F
```

## JSON 持久化结构（Day 25）

```
store.json
├── version: "1.0"
├── platform_version: "{VER}"
├── documents[]: KnowledgeDocument
├── chunks[]: TextChunk 序列化
└── embedding: TfidfEmbeddingModel.export_state()
```

流程图完。
"""


def _notes_am() -> str:
    return f"""# Day 25 课堂笔记（上午）

**讲师**：陈默 | **主题**：KnowledgeStore 与持久化

## 09:00–09:30 Phase 3 动员

赵岩展示投资人邮件截图：「Demo 很美，知识谁维护？」引出今日 MVP 边界——只 txt，只做写路径。

## 09:30–10:30 KnowledgeDocument 与 ingest_text

- `KnowledgeDocument` 是**元数据**，chunks 存全文块  
- `ingest_text` 参数：`clean=True` 默认走 `clean_text`  
- `chunk_size`/`overlap` 默认来自 Day 19 惯例 200/40  
- 空内容 `ValueError`，空 filename 同理  

## 10:45–11:30 save / load / bootstrap

```python
store = KnowledgeStore.load_or_bootstrap()
store.ingest_text("...", filename="x.txt")
store.save()  # 默认 data/knowledge/store.json
```

`load` 失败或空文件时回退 bootstrap，保证课堂不断点。

## 11:30–12:00 源码走读起点

打开 `knowledge_store.py` 第 65–86 行：`KnowledgeStore` dataclass 字段含义。`_rag_service` 用 `repr=False` 避免打印巨大对象。

## 上午思考题

1. 为何 `as_rag_service()` 要缓存？  
2. `export_state` 不持久化会怎样？  

笔记完。下午见 API。
"""


def _notes_pm() -> str:
    return f"""# Day 25 课堂笔记（下午）

**讲师**：林晓 + 陈默 | **主题**：upload API 与前端联调

## 14:00–14:45 TestClient 上传

```python
files = {{"file": ("faq.txt", io.BytesIO(b"..."), "text/plain")}}
resp = client.post("/api/knowledge/upload", files=files)
assert resp.json()["sessions_cleared"] >= 1
```

## 14:45–15:30 knowledge.js

- `bindPanel` 在 DOMContentLoaded 注册  
- Mock 模式早退——与 Day 23 `useMock` 一致  
- `uploadFile` 不设置 Content-Type，让浏览器带 boundary  

## 15:45–16:30 联调踩坑

| 现象 | 原因 | 修复 |
|------|------|------|
| 上传成功但 chat 旧答案 | 未 clear 会话 | 检查 upload 响应 sessions_cleared |
| 422 不支持格式 | 传了 .docx | Day 25 仅 txt |
| 侧栏离线 | 未启动 uvicorn | run_server / sprint3_launch |

## 16:30–17:00 pytest 17 项解读

`test_chat_after_upload_uses_kb` 证明端到端价值——不仅 HTTP 200，而且 RAG 命中。

下午笔记完。
"""


def _evening() -> str:
    return f"""# Day 25 晚自习

**值班助教**：周航 | **时间**：19:00–21:00

## 自习任务

1. 精读 `22_knowledge_store精读.md` 前半  
2. 运行 `ingestion_demo.py` 并记录 chunk 数  
3. 预习 Day 26：`tools/doc_parser.py` 目录结构  

## 常见问题

**Q：PYTHONPATH 未设**  
`export PYTHONPATH=src` 后再 pytest。

**Q：store.json 在哪？**  
`get_path("knowledge_store")`，默认 `data/knowledge/store.json`。

**Q：能否手动删 store 重置？**  
可以，下次 `load_or_bootstrap` 会重新 bootstrap。

## 加餐：embedding roundtrip

阅读 `test_embedding_export_load_state`——理解为何 load 后检索仍有效。

晚自习完。
"""


def _homework() -> str:
    return f"""# Day 25 作业

**截止**：次日上午课前（Day 26 预习前）  
**提交**：仓库 `homework/day25/` 或学习平台指定路径  
**需求**：{REQ}

---

## 作业 A：ingestion 演示与 pytest 截图（必做，⭐ 基础，20 分）

### 要求

1. 运行 `python3 src/day25/ingestion_demo.py` 截图终端输出  
2. 运行 `python3 -m pytest tests/day25/ -v` 截图 17 passed  
3. 写入 `homework/day25/audit_report.md` 说明环境与 chunk 数变化  

---

## 作业 B：浏览器上传 FAQ 端到端（必做，⭐ 基础，25 分）

### 要求

启动 `sprint3_launch.py --serve`，在知识库侧栏上传 `custom_faq.txt`（可用 constants 样例），对聊天窗口提问：

| 问句 | 验收 |
|------|------|
| 最低起购金额是多少 | 回复含 1000 或起购 |
| 赎回多久到账 | 回复含 T+1 或到账 |

提交 `homework/day25/upload_screenshots/` + `upload_notes.md`（含 Network 中 upload 响应 JSON）。

---

## 作业 C：store.json 结构分析（必做，⭐⭐ 进阶，20 分）

### 要求

上传一份自定义 txt 后，复制 `data/knowledge/store.json` 片段到 `homework/day25/store_analysis.md`：

1. 标出 `version` 与 `platform_version`  
2. 统计 `documents` 与 `chunks` 数组长度  
3. 解释 `embedding` 对象中 `vocab` 的作用（200 字）  

---

## 作业 D：curl 上传实验（必做，⭐⭐ 进阶，20 分）

完成 `homework/day25/curl_log.md`：

1. `GET /api/knowledge/status` 命令与响应  
2. `POST /api/knowledge/upload` 用 `-F file=@faq.txt`  
3. 空文件上传得 422  
4. 超过 500KB 得 413（可用 `dd` 生成大文件）  

---

## 作业 E：sessions_cleared 实验（必做，⭐ 基础，15 分）

撰写 `homework/day25/session_clear.md`（150 字以上）：

- 先 `POST /api/chat` 创建会话，再 upload，解释响应中 `sessions_cleared`  
- 与 `POST /api/session/reset` 的区别  

---

## 作业 F：KnowledgeStore 设计评述（选做，⭐⭐⭐ 挑战，+10 分）

阅读 `knowledge_store.py` 单例实现，撰写 `singleton_design.md`：线程锁、测试注入 `set_knowledge_store`、多 worker 风险。

---

## 评分标准

| 等级 | 标准 |
|------|------|
| 优秀 | A–E 全过，curl 格式正确，截图含 sessions_cleared |
| 良好 | 必做全过 |
| 及格 | pytest 全绿但浏览器未联调 |
| 不及格 | 未运行 tests/day25 |

---

## 学术诚信

允许讨论 FastAPI multipart 与 curl，须独立完成 store 分析文字。

**提示**：Day 26 将支持 Markdown/PDF，今日 txt 管线是基础。

---

## 培训部辅导长文（作业 A–E）

### 作业 A 深度辅导

`ingestion_demo.py` 展示 `ingest_text` 与 `save` 最小路径。截图须含 `PYTHONPATH=src`。若 chunk 数为 0，检查 sample 是否 bootstrap 失败。pytest 必须显示 `17 passed` 全文。

### 作业 B 深度辅导

Network 面板选中 `upload` 请求，Response 须含 `chunk_count`、`total_chunks`、`sessions_cleared`。若 chat 未命中新 FAQ，查 factory 是否用 `get_knowledge_store()` 而非 `from_sample_docs`。

### 作业 C 深度辅导

`embedding.vocab` 是 TF-IDF 词表，load 后 `load_state` 恢复向量空间。勿提交完整 store.json（可能过大），截取首尾各 30 行即可。

### 作业 D 深度辅导

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq
curl -s -X POST http://127.0.0.1:8000/api/knowledge/upload -F "file=@custom_faq.txt"
```

### 作业 E 深度辅导

`clear_all` 清空**所有**会话 orchestrator；`session/reset` 仅单会话。上传影响全局知识库，故用 clear_all。

作业文档完，{REQ}。

---

## 智链科技 Day 25 作业辅导长文（培训部 vol2）

### 作业 A 逐行验收

`ingestion_demo.py` 第一行应 `from rag.knowledge_store import get_knowledge_store`。终端须打印 ingest 前后 `chunk_count`。若不变，检查是否 ingest 空串。pytest 截图必须含文件名 `test_knowledge_store.py` 与 `test_knowledge_api.py` 分区标题，便于助教扫视 17 条全绿。

### 作业 B Network 面板教学

选中 upload 请求看 Request Headers：不应有手动 `Content-Type`。Response 必含 `sessions_cleared` 键。chat 请求应在 upload 之后，否则可能误用旧索引。问句「最低起购金额」reply 应引用上传文本而非仅 LLM 幻觉——Mock 模式下侧栏不可用，须 API 模式。

### 作业 C store.json 安全

提醒学员脱敏：提交作业剔除内网路径用户名。`vocab` 解释优秀答案会画词表示意图：查询词 → 维度索引 → TF-IDF 权重。

### 作业 D 运维素养

`curl -w '\\n%{{http_code}}'` 同时看 body 与状态码。413 实验可用 `python3 -c "open('big.txt','wb').write(b'0'*600000)"` 生成。

### 作业 E 会话语义

画两张表：upload 影响全局 store；reset 影响单 session。upload 后所有用户下次 chat 受益新索引。

### 结语

截止 Day 26 早课前。未完成 B 者 Day 26 PDF 实验只能旁观浏览器部分。

辅导长文完。
"""


def _homework_answers() -> str:
    return f"""# Day 25 作业答案

**说明**：供讲师对照；学员请用自己的实验数据。

---

## 作业 A 参考答案

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day25/ingestion_demo.py
python3 -m pytest tests/day25/ -v
# 期望：17 passed
```

---

## 作业 B 参考答案

upload 响应示例：

```json
{{
  "filename": "custom_faq.txt",
  "format": "txt",
  "chunk_count": 3,
  "document_count": 4,
  "total_chunks": 15,
  "sessions_cleared": 1,
  "message": "文档已入库（txt）..."
}}
```

chat 回复应通过 RAG 引用上传文本，非纯 Mock 敷衍。

---

## 作业 C 参考答案

- `version`: `"1.0"` 或后续 `"1.1"`（以仓库为准）  
- `platform_version`: 教学里程碑 `{VER}`（测试夹具可能用更新版本）  
- `vocab`: 词 → 索引映射，决定 TF-IDF 维度  

---

## 作业 D 参考答案

空文件：`curl -F "file=@empty.txt"` → 422 detail 含「空」  
大文件：`dd if=/dev/zero of=big.txt bs=1024 count=600` → 413

---

## 作业 E 参考答案

上传后全局索引变，所有持有旧 RAG 的 orchestrator 必须废弃。`sessions_cleared` 是实际清除的会话数。`session/reset` 不重建索引。

---

## 作业 F 参考答案要点

`threading.Lock` 防止双检锁竞态；`set_knowledge_store` 供 pytest tmp_path 隔离；uvicorn 多 worker 每进程独立单例，上传不跨 worker 同步——生产需外置 store。

答案完。
"""


def _checklist() -> str:
    return f"""# Day 25 知识库验收清单

**教师用** | **需求**：{REQ}

## 代码交付

- [ ] `rag/knowledge_store.py` 含 ingest_text/save/load/bootstrap  
- [ ] `rag/ingestion.py` 含 ingest_upload  
- [ ] `api/knowledge.py` 含 status + upload  
- [ ] `frontend/knowledge.js` 导出 NexusKnowledge  
- [ ] `tests/day25/` 17 项全绿  

## 功能验收

- [ ] 冷启动无 store 时 bootstrap  
- [ ] 上传 txt 后 status document_count 增加  
- [ ] chat 问上传内容可检索  
- [ ] upload 返回 sessions_cleared >= 0  
- [ ] Mock 模式侧栏不可用  

## 文档验收

- [ ] 02_ 需求文档 FR-001–007 完整  
- [ ] 20_ 含时序图  
- [ ] 22_ 含源码注释  
- [ ] 21_ 含 15 题  

验收清单完。
"""


def _deep_dive() -> str:
    return f"""# KnowledgeStore 与 Ingestion 详解

**需求**：{REQ} | **版本**：{VER}

## 1. 从只读到可写

Day 19–20：`RAGContextService.from_sample_docs()` 在内存构建索引，进程结束即失。  
Day 25：`KnowledgeStore` 把 chunks + embedding state 序列化，重启可 `load`。

## 2. bootstrap_from_sample_docs 算法

1. 调用 `RAGContextService.from_sample_docs(use_embedding=True)`  
2. 按 `chunk.source` 分组统计 `KnowledgeDocument`  
3. 复制 chunks 列表  
4. 从 `EmbeddingRetriever` export embedding_state  
5. `_rebuild_index()` 确保一致性  

保证与 Day 24 演示 FAQ 行为一致，降低回归风险。

## 3. ingest_text 逐步

{fenced("python", '''def ingest_text(self, content, *, filename, clean=True, chunk_size=None, overlap=None):
    cfg = self.get_chunk_config()
    cs = chunk_size if chunk_size is not None else cfg.chunk_size
    text = (content or "").strip()
    if not text:
        raise ValueError("文档内容不能为空")
    cleaned = clean_text(text) if clean else text
    doc = DocumentRecord(path=Path(filename), content=text, ...)
    new_chunks = chunk_documents([doc], chunk_size=cs, overlap=ov, use_cleaned=clean)
    self._append_chunks(filename, new_chunks, size_bytes=...)
    self._rebuild_index()
    return self.documents[-1]''')}

## 4. ingest_upload 路径

{fenced("python", _ING)}

## 5. 单例与测试隔离

生产：`get_knowledge_store()` 懒加载。  
测试：`set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp))` 避免污染全局 JSON。

## 6. 性能注记

Day 25 每次 ingest 全量 `_rebuild_index`，复杂度 O(n)。sample 规模可接受；Day 29 增量 Chroma。

详解完。

---

## 附录：chunk_documents 与 KnowledgeStore 边界

KnowledgeStore 不实现分块算法，只调用 `chunk_documents` / Day 26 `chunk_from_parsed`。解析层在 `tools/`，分块策略在 `rag/chunk_strategies.py`（Day 26），索引在 store。三层分离是 Phase 3 架构红线。

## 附录：错误处理链

ingest_text ValueError → API 422；StorageError → 500；UnicodeDecodeError → 400。学员在 17_ 速查手写错误矩阵。

"""


def _exercises() -> str:
    return f"""# Day 25 课堂练习册

**用途**：当堂短答 | **需求**：{REQ}

---

## 练习 1：单例函数名

全局知识库单例的获取函数是？

<details><summary>答案</summary>get_knowledge_store()</details>

---

## 练习 2：持久化路径

默认 `store.json` 通过哪个 helper 解析路径？

<details><summary>答案</summary>get_path("knowledge_store") / _default_store_path()</details>

---

## 练习 3：上传上限

`MAX_UPLOAD_BYTES` 是多少字节？

<details><summary>答案</summary>512_000（500KB）</details>

---

## 练习 4：Day 25 支持格式

上传 API 在 Day 25 教学边界内支持哪种扩展名？

<details><summary>答案</summary>.txt（UTF-8）</details>

---

## 练习 5：ingest_upload 落盘目录

上传文件写入哪个目录？

<details><summary>答案</summary>data/knowledge/uploads/（get_path("knowledge_uploads")）</details>

---

## 练习 6：测试数量

`tests/day25/` 共有多少条测试？

<details><summary>答案</summary>17（store 10 + api 7）</details>

---

## 练习 7：Mock 侧栏

`knowledge.js` 在 Mock 模式显示什么？

<details><summary>答案</summary>「Mock 模式不可用」</details>

---

## 练习 8：sessions_cleared

上传成功后为何要返回该字段？

<details><summary>答案</summary>确认已清除持有旧 RAG 的会话 orchestrator</details>

---

## 练习 9：bootstrap 触发条件

`load_or_bootstrap` 何时调用 bootstrap？

<details><summary>答案</summary>目标路径不是文件或 load 为空时</details>

---

## 练习 10：ingest_text 空内容

空字符串调用 ingest_text 会怎样？

<details><summary>答案</summary>raise ValueError("文档内容不能为空")</details>

---

## 练习 11：factory 变更

Day 25 factory 如何获取 RAG？

<details><summary>答案</summary>get_knowledge_store().as_rag_service()</details>

---

## 练习 12：JSON version 字段

store envelope 的 version 字段表示什么？

<details><summary>答案</summary>知识库 schema 版本（如 1.0），非平台 {VER}</details>

练习册完。
"""


def _extension() -> str:
    return f"""# 深度扩展：企业知识库实践

**需求**：{REQ} | **选读**

## 多租户隔离（未实现）

生产需 `org_id` 分区：  
- `store/{{org_id}}/store.json`  
- API 从 JWT 取 tenant  
- 单例改为 `get_knowledge_store(org_id)`  

## 版本化与审计

每次 upload 写 `KnowledgeRevision`：who、when、sha256、diff。合规要求可回滚。

## 病毒扫描

企业网关在上传前 ClamAV 扫描；本课 MVP 跳过。

## 与对象存储对接

大文件应直传 S3 presigned URL，API 只收 metadata 触发 ingest。Day 25 同步上传教学简单。

## 观测性

指标：`upload_latency`, `chunk_count`, `rebuild_duration`。周航建议 Day 28 加重建耗时日志。

扩展完。
"""


def _case_study() -> str:
    return f"""# 企业案例集：运营上传 FAQ

**角色**：小王（产品运营） | **需求**：{REQ}

## 场景

智链科技新发理财产品，FAQ 在 Word。小王导出 UTF-8 `xinchanpin_faq.txt`（12KB），要通过 NexusAgent 网页更新知识库。

## 操作步骤

1. 打开 `http://127.0.0.1:8000/` 登录内网（无鉴权教学环境）  
2. 点击「知识库」侧栏  
3. 选择文件 → 上传  
4. 状态行显示 `N 篇 / M 块`  
5. 聊天问：「最低起购金额是多少」  

## 结果

RAG 命中上传块，回复含「1000 元」。投资人现场点头。

## 失败案例

小王上传 GBK 编码 txt → 400「须为 UTF-8」。解决：Notepad++ 转 UTF-8。

## 反思

赵岩：「知识运营不是研发专属。Day 25 是组织能力的起点。」

案例完。

---

## 附录：小王一周工作流（案例长文）

周一产品发 Word 稿，小王周二导出 UTF-8 txt（Day 25）或 md（Day 26 起）。周三上传前用三问句自测旧库命中率作为 baseline。周四上传后在测试环境 chat 验收。周五把 status 截图发合规备案。她总结：「以前找研发改 FAQ 要三天，现在下午喝茶前能上线。」

第二周她误传 GBK 文件，学会 Notepad++「转为 UTF-8 无 BOM」。第三周她尝试传 2MB PDF，被 413 拒绝——赵岩解释教学上限，指引她用运维脚本分批入库。

案例长文完。

"""


def _lecture_log() -> str:
    return f"""# Day 25 授课实录

**日期**：2026-07-30 | **讲师**：陈默、林晓

## 09:05 开场

赵岩：「Phase 3 第一日，知识要能上传。」

## 10:20 演示 ingest_text

陈默现场 `ingestion_demo.py`，chunk 从 12 → 15。学员记录 `save` 路径。

## 11:00 提问环节

问：为何不全量替换 sample_docs？  
答：bootstrap 保证开箱即用，upload 是增量能力。

## 14:10 Swagger 上传

林晓演示 multipart，强调 field 名必须是 `file`。

## 15:30 联调

三组学员侧栏离线——均未 export PYTHONPATH，助教统一修复。

## 16:45 竞赛预告

明日 Day 26 前完成 21_ 竞赛题预习。

实录完。
"""


def _flashcards() -> str:
    return f"""# Day 25 复习卡片

**需求**：{REQ} | 共 20 张

| # | 问题 | 答案 |
|---|------|------|
| 1 | Day 25 核心类？ | KnowledgeStore |
| 2 | 上传 API 路径？ | POST /api/knowledge/upload |
| 3 | 状态 API？ | GET /api/knowledge/status |
| 4 | 持久化文件？ | store.json |
| 5 | 上传落盘目录？ | data/knowledge/uploads/ |
| 6 | ingest 流水线文件？ | rag/ingestion.py |
| 7 | 前端模块？ | frontend/knowledge.js |
| 8 | 全局单例？ | get_knowledge_store() |
| 9 | 测试注入？ | set_knowledge_store() |
| 10 | bootstrap 方法？ | bootstrap_from_sample_docs |
| 11 | 文本写入？ | ingest_text |
| 12 | 上传入口？ | ingest_upload |
| 13 | 索引重建？ | _rebuild_index |
| 14 | RAG 出口？ | as_rag_service() |
| 15 | 上传后清会话？ | session_manager.clear_all() |
| 16 | 样例上传文本常量？ | SAMPLE_UPLOAD_TEXT |
| 17 | 平台版本？ | {VER} |
| 18 | 需求编号？ | {REQ} |
| 19 | Day 25 不支持？ | PDF（Day 26） |
| 20 | pytest 数量？ | 17 |

卡片完。
"""


def _cheatsheet() -> str:
    return f"""# 知识库 API 速查手册

**需求**：{REQ} | **版本**：{VER}

## 环境

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

## curl

```bash
# 状态
curl -s http://127.0.0.1:8000/api/knowledge/status | jq

# 上传
curl -s -X POST http://127.0.0.1:8000/api/knowledge/upload \\
  -F "file=@custom_faq.txt;type=text/plain"
```

## TestClient

```python
from fastapi.testclient import TestClient
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store

store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
set_knowledge_store(store)
client = TestClient(create_app())
client.get("/api/knowledge/status")
```

## Python 直接入库

```python
from rag.knowledge_store import get_knowledge_store
kb = get_knowledge_store()
kb.ingest_text("内容", filename="a.txt")
kb.save()
```

## 响应字段

| 字段 | 含义 |
|------|------|
| chunk_count | 本次文档块数 |
| total_chunks | 库内总块数 |
| sessions_cleared | 清除会话数 |
| document_count | 文档篇数 |

速查完。
"""


def _day24_compare() -> str:
    return f"""# Day 25 与 Day 24 能力对照表

| 维度 | Day 24 | Day 25 |
|------|--------|--------|
| 主题 | 网页整合 | 知识库 ingestion |
| RAG 来源 | sample_docs 只读 | KnowledgeStore 可写 |
| 新 API | 无 | /api/knowledge/* |
| 前端 | 聊天主界面 | +knowledge.js 侧栏 |
| 持久化 | 无 | store.json |
| 会话 | 多 session | 上传 clear_all |
| 版本 | 0.24.0 | {VER} |

## 衔接

Day 24 `sprint3_launch.py` 仍可 `--serve` 启动；Day 25 在同端口增加知识库能力。

对照完。
"""


def _instructor_reading() -> str:
    return f"""# 讲师补充阅读：RAG 数据面工程化

**需求**：{REQ} | **教师用**

## 数据面 vs 控制面

- **控制面**：API 路由、鉴权、配额  
- **数据面**：chunk、embedding、检索  

Day 25 聚焦数据面 MVP。

## 为什么 JSON 先于数据库

1. 课堂可 `cat store.json` 审计  
2. 无 ORM 迁移负担  
3. 与 Day 29 Chroma 文件共存过渡  

## 常见学员误区

- 以为 upload 会训练 LLM（实际只更新检索索引）  
- 以为 clear_all 删除聊天记录（仅服务端 orchestrator）  
- 混淆 platform_version 与 store version  

## 课堂节奏建议

上午源码，下午联调，晚自习 pytest。勿压缩 22_ 精读。

补充阅读完。
"""


def _code_walkthrough() -> str:
    return f"""# Day 25 完整代码走查

**需求**：{REQ} | **版本**：{VER}  
**方式**：按上传路径自顶向下

---

## 走查 1：服务启动与 store 引导

```
uvicorn / sprint3_launch --serve
  → create_app()
    → include_router(knowledge_router)
  → 首次 get_knowledge_store()
    → load_or_bootstrap()
      → bootstrap_from_sample_docs() [无 store.json]
      → save()
```

**检查点**：factory 在 create_orchestrator 时调用 `get_knowledge_store().as_rag_service()`。

---

## 走查 2：GET /api/knowledge/status

```
Request GET /api/knowledge/status
  → knowledge.py knowledge_status()
    → get_knowledge_store().status_dict()
    → KnowledgeStatusResponse(**data)
```

**检查点**：`document_count`、`chunk_count`、`documents[]` 与 store 内存一致。

---

## 走查 3：POST /api/knowledge/upload 全链

```
1. browser: knowledge.js uploadFile
     FormData.append("file", file)
     fetch('/api/knowledge/upload', {{method:'POST', body: form}})

2. FastAPI: UploadFile 解析 multipart

3. knowledge.py upload_document
     await file.read()
     校验非空、<= MAX_UPLOAD_BYTES
     ingest_upload(data, file.filename)

4. ingestion.py ingest_upload
     detect_format / Day25: .txt
     dest.write_bytes(data)
     kb.ingest_bytes(data, filename)
     kb.save()

5. KnowledgeStore.ingest_bytes [Day25 txt 路径]
     → ingest_text 或 parse plain

6. session_manager.clear_all()

7. KnowledgeUploadResponse 序列化
```

```mermaid
sequenceDiagram
    participant B as Browser
    participant K as knowledge.js
    participant A as knowledge.py
    participant I as ingestion.py
    participant S as KnowledgeStore
    participant M as SessionManager

    B->>K: 选择 faq.txt
    K->>A: POST /upload multipart
    A->>I: ingest_upload(bytes, name)
    I->>S: ingest_bytes + save
    S-->>I: KnowledgeDocument
    I-->>A: meta
    A->>M: clear_all()
    M-->>A: count
    A-->>K: JSON response
    K-->>B: 显示 message
```

---

## 走查 4：chat 使用新索引

```
POST /api/chat [新 session 或 clear 后]
  → session_manager.get_or_create
    → factory.create_orchestrator
      → get_knowledge_store().as_rag_service()
  → orchestrator.handle_message
    → RAG retrieve_context 命中新 chunks
```

```mermaid
sequenceDiagram
    participant C as chat.py
    participant F as factory
    participant KS as KnowledgeStore
    participant O as Orchestrator

    C->>F: create_orchestrator
    F->>KS: as_rag_service()
    KS-->>F: RAGContextService
    F-->>C: orchestrator
    C->>O: handle_message
    O->>O: retrieve_context
```

---

## 走查 5：持久化往返

```
ingest_text → _rebuild_index → save(path)
  → JSON {{version, documents, chunks, embedding}}
load(path)
  → documents/chunks 反序列化
  → embedding_state → EmbeddingClient.load_state
  → as_rag_service() 检索验证
```

---

## 走查 6：测试挂钩

{fenced("python", _TAPI[:1200])}

---

## 走查 7：前端 bindPanel

{fenced("javascript", _FE[:900])}

走查完。详见 [22_knowledge_store精读.md](22_knowledge_store精读.md)。

---

## 走查 8：完整 API 测试文件

{fenced("python", _TAPI)}

| 测试 | 走查要点 |
|------|----------|
| test_knowledge_status | status 200 且 chunk_count>0 |
| test_knowledge_upload_txt | multipart 字段名 file |
| test_upload_clears_sessions | 先 chat 再 upload |
| test_chat_after_upload_uses_kb | 端到端 RAG 价值 |
| test_frontend_knowledge_js | 静态托管 knowledge.js |

---

## 走查 9：factory 注入（读 api/factory.py）

上传后 chat 链路依赖 factory 每次 `get_knowledge_store().as_rag_service()`。若开发者改回 `from_sample_docs`，upload 对 chat 不可见——`test_chat_after_upload_uses_kb` 会红。

"""


def _quiz() -> str:
    return f"""# Day 25 课堂知识竞赛

**形式**：小组抢答 | **题量**：15 题 | **需求**：{REQ}  
**建议时长**：25 分钟

---

## 选择题（每题 6 分，共 9 题）

### 1

`KnowledgeStore` 定义在哪个文件？

- A. `api/knowledge.py`  
- B. `rag/knowledge_store.py`  
- C. `rag/ingestion.py`  
- D. `frontend/knowledge.js`  

<details><summary>答案</summary>B</details>

### 2

`POST /api/knowledge/upload` 在 Day 25 教学范围内接受的格式？

- A. .docx  
- B. .pdf  
- C. .txt UTF-8  
- D. 任意二进制  

<details><summary>答案</summary>C</details>

### 3

上传文件大小上限？

- A. 100KB  
- B. 500KB  
- C. 5MB  
- D. 无限制  

<details><summary>答案</summary>B — MAX_UPLOAD_BYTES=512_000</details>

### 4

`ingest_upload` 将原始文件落盘到？

- A. `store.json` 同目录  
- B. `data/knowledge/uploads/`  
- C. `frontend/uploads/`  
- D. `/tmp`  

<details><summary>答案</summary>B</details>

### 5

上传成功后为何调用 `session_manager.clear_all()`？

- A. 删除用户聊天记录  
- B. 强制 orchestrator 使用新 RAG 索引  
- C. 清空 store.json  
- D. 重启 uvicorn  

<details><summary>答案</summary>B</details>

### 6

`tests/day25/` 共有多少条测试？

- A. 12  
- B. 15  
- C. 17  
- D. 20  

<details><summary>答案</summary>C</details>

### 7

`get_knowledge_store()` 的线程安全机制？

- A. 无锁  
- B. `threading.Lock`  
- C. `asyncio.Lock`  
- D. 数据库事务  

<details><summary>答案</summary>B</details>

### 8

Mock 模式下 `knowledge.js` 的行为？

- A. 正常上传  
- B. 显示不可用并 return  
- C. 走 mock.js  
- D. 自动切换 API  

<details><summary>答案</summary>B</details>

### 9

`bootstrap_from_sample_docs` 的数据来源？

- A. 空库  
- B. Day 02 sample_docs 经 RAG 管线  
- C. 仅 uploads  
- D. 随机生成  

<details><summary>答案</summary>B</details>

---

## 简答题（每题 7 分，共 6 题）

### 10

列出 `KnowledgeUploadResponse` 四个核心计数字段。

<details><summary>参考答案</summary>chunk_count（本文档块数）、document_count（库文档数）、total_chunks（总块数）、sessions_cleared（清除会话数）。</details>

### 11

解释 `ingest_text` 与 `save` 的调用顺序及原因。

<details><summary>参考答案</summary>先 ingest 更新内存 chunks 与 embedding，再 save 落盘；否则进程崩溃会丢上传。</details>

### 12

`store.json` 中 `embedding` 对象的作用。

<details><summary>参考答案</summary>保存 TF-IDF 模型状态（vocab/idf 等），load 后恢复同一向量空间以支持检索。</details>

### 13

Day 25 factory 如何注入 RAG？与 Day 24 差异？

<details><summary>参考答案</summary>`get_knowledge_store().as_rag_service()`；Day 24 用 `from_sample_docs` 只读，无法反映 upload。</details>

### 14

空文件上传返回什么 HTTP 状态？由哪层抛出？

<details><summary>参考答案</summary>422；API 层校验 `if not data` 或 ingest 层 ValueError/NexusError 映射。</details>

### 15

描述运营上传 FAQ 后用户提问的端到端路径（至少 5 步）。

<details><summary>参考答案</summary>侧栏选文件 → POST upload → ingest_upload 落盘入库 → save → clear_all → 用户 chat → factory 新 orchestrator → RAG retrieve → 回复。</details>

---

## 评分

满分 100。小组第一获「知识库 MVP」贴纸。

竞赛完。

---

## 智链科技竞赛题库备份（口播备用 16–20）

**16.** `ingest_upload` 第一步安全处理？→ `Path(filename).name`  
**17.** `STORE_VERSION` 表示？→ JSON schema 版本  
**18.** 上传后 chat 用新索引的前提？→ clear_all + 新 orchestrator  
**19.** `test_rag_retrieve_after_ingest` 断言含？→ 1000 或起购  
**20.** Day 26 预习样例 md 文件名？→ product_notice.md  

## 赛后延伸讨论

讨论题：upload 同步 vs 异步队列？标准答案：教学同步；生产用 Celery+对象存储。林晓队分享 store.json 审计技巧。

竞赛扩展完。

"""


def _ks_deep_read() -> str:
    ks_head = "\n".join(_KS.splitlines()[:120])
    ks_mid = "\n".join(_KS.splitlines()[112:200])
    return f"""# knowledge_store.py 精读

**需求**：{REQ} | **文件**：`nexus-agent-platform/src/rag/knowledge_store.py`

---

## 模块 docstring 与导入

{fenced("python", chr(10).join(_KS.splitlines()[:27]))}

**解读**：模块定位「可写入、可落盘的企业知识库 MVP」。导入链显示依赖 Day 19 `chunker`、Day 20 embedding、路径 `core.paths`。

---

## KnowledgeDocument 元数据类

{fenced("python", chr(10).join(_KS.splitlines()[35:62]))}

**解读**：
- `name` 即 source 文件名，与 chunks 的 `source` 字段对应  
- `ingested_at` ISO UTC 时间戳，审计用  
- `format` 默认 txt，Day 26 扩展 markdown/pdf  
- `to_dict`/`from_dict` 保证 JSON 往返  

---

## KnowledgeStore 字段

{fenced("python", chr(10).join(_KS.splitlines()[65:86]))}

**解读**：
- `documents` 与 `chunks` 分离：前者统计，后者检索  
- `_rag_service` 缓存避免重复构建 EmbeddingRetriever  
- `chunk_config` 为 Day 27 预留，Day 25 用默认  

---

## ingest_text 核心写入

{fenced("python", chr(10).join(_KS.splitlines()[112:150]))}

**逐行要点**：
1. L126-130：空内容与空文件名防御性校验  
2. L133-134：`clean_text` 去噪，FAQ 场景建议开启  
3. L135-141：构造 `DocumentRecord` 保留原始与 cleaned  
4. L142-147：`chunk_documents` 复用 Day 19 算法  
5. L148-149：`_append_chunks` + `_rebuild_index` 原子更新内存索引  

---

## save 持久化 envelope

{fenced("python", chr(10).join(_KS.splitlines()[255:272]))}

**解读**：`STORE_VERSION` 是 schema 版本；`platform_version` 标记平台里程碑；`chunks` 全量序列化教学透明但体积大。

---

## load / load_or_bootstrap

{fenced("python", chr(10).join(_KS.splitlines()[274:305]))}

**解读**：`load_or_bootstrap` 是 API 冷启动唯一入口；不存在文件时 bootstrap 并立即 save，避免每次请求重复引导。

---

## bootstrap_from_sample_docs

{fenced("python", chr(10).join(_KS.splitlines()[307:334]))}

**解读**：从既有 `RAGContextService.from_sample_docs` 迁移数据，保证 Day 24 行为回归；按 source 分组生成 `KnowledgeDocument` 列表。

---

## 单例 get_knowledge_store

{fenced("python", chr(10).join(_KS.splitlines()[508:519]))}

**解读**：`threading.Lock` + 全局 `_store`；`reload=True` 强制重载（运维场景）；测试用 `set_knowledge_store` 注入假实例。

---

## 与测试对照

| 测试 | 覆盖代码 |
|------|----------|
| test_save_and_load_roundtrip | save/load + retrieve |
| test_ingest_text_appends_chunks | ingest_text |
| test_bootstrap_has_chunks | bootstrap |

精读完。结合 [25_ingestion流水线精读.md](25_ingestion流水线精读.md)。

---

## 扩展精读：ingest_file 与 ingest_bytes

{fenced("python", chr(10).join(_KS.splitlines()[151:201]))}

**ingest_file**：面向运维脚本，`read_text_file` 读磁盘编码；参数 `chunk_size=200` 显式默认。  
**ingest_bytes**：API 热路径；Day 26 起内部 `from tools.doc_parser import parse_bytes`，Day 25 学员理解「二进制统一入口」即可。

---

## 扩展精读：as_rag_service 与 _build_rag_service

{fenced("python", chr(10).join(_KS.splitlines()[96:106]))}

缓存 `_rag_service` 避免每次 chat 重建 EmbeddingRetriever。`invalidate_cache` 在 `_rebuild_index` 末尾调用，保证下次 `as_rag_service` 重建。

---

## 扩展精读：完整测试文件 test_knowledge_store.py

{fenced("python", _TSTORE)}

| 测试 | 教学要点 |
|------|----------|
| test_bootstrap_has_chunks | 引导后至少有 sample 块 |
| test_rag_retrieve_after_ingest | 证明写入即可检索 |
| test_save_and_load_roundtrip | 持久化是 Day 25 核心 |
| test_ingest_upload_writes_file | 审计副本在 uploads/ |
| test_store_json_has_version | schema 契约 |

---

## 扩展精读：ingest_parsed（Day 26 衔接）

{fenced("python", chr(10).join(_KS.splitlines()[203:253]))}

---

## 扩展精读：frontend knowledge.js

{fenced("javascript", _FE)}

"""


def _upload_practice() -> str:
    return f"""# 上传 API 与持久化实践

**需求**：{REQ} | **动手**

## 实验 1：观察 store.json 增长

```bash
cd nexus-agent-platform
export PYTHONPATH=src
wc -c data/knowledge/store.json
python3 -c "
from rag.knowledge_store import get_knowledge_store
from day25.constants import SAMPLE_UPLOAD_TEXT
kb = get_knowledge_store()
kb.ingest_text(SAMPLE_UPLOAD_TEXT, filename='lab.txt')
kb.save()
"
wc -c data/knowledge/store.json
```

## 实验 2：upload 响应字段

使用 Swagger Try it out 上传，记录：

- `chunk_count` vs `total_chunks`  
- `sessions_cleared`  

## 实验 3：损坏 JSON 恢复

```bash
cp data/knowledge/store.json /tmp/backup.json
echo '{{invalid' > data/knowledge/store.json
# 重启服务观察 bootstrap 行为（勿在生产做）
```

## 实验 4：路径安全

尝试上传文件名 `../../etc/passwd`——`Path(filename).name` 应剥离为 `passwd`。

## CI 对照

`test_store_json_has_version` 断言 `version` 与 `platform_version` 字段存在。

实践完。

---

## 附录：完整 knowledge.py 路由节选（实践 vol2）

{fenced("python", _API)}

---

## 附录：multipart 与 FastAPI UploadFile

`UploadFile` 异步 `read()` 返回 bytes；`filename` 来自 Content-Disposition。字段名必须 `file` 与参数名一致。Swagger 自动生成 boundary；curl 用 `-F`。

---

## 附录：持久化恢复演练脚本

```bash
#!/bin/bash
# backup_day25.sh
cp data/knowledge/store.json "/tmp/store-$(date +%Y%m%d).json"
tar czf "/tmp/uploads-$(date +%Y%m%d).tgz" data/knowledge/uploads/
echo backup ok
```

"""


def _phase3_overview() -> str:
    return f"""# Phase 3 启动全览（Day 25–31）

| Day | 主题 | 需求 |
|-----|------|------|
| 25 | 知识库 ingestion + upload API | {REQ} |
| 26 | Markdown/PDF 解析 + 分块策略 | ZL-NA-REQ-026 |
| 27 | 分块调参 + 检索评估 | ZL-NA-REQ-027 |
| 28 | 全量 rebuild | ZL-NA-REQ-028 |
| 29 | Chroma 向量库 | ZL-NA-REQ-029 |
| 30 | 知识库 Sprint 总结 | ZL-NA-REQ-030 |
| 31 | Phase 3 答辩 | — |

## Day 25 在路线图的位置

**数据面第一步**：让知识「可写入」。没有 Day 25，后续解析与向量库无挂载点。

## 投资人叙事

赵岩：「Day 24 是脸，Day 25 是脑的记忆皮层。」

全览完。

---

## Phase 3 每日_dependencies

Day 25 不依赖 Day 26；Day 26 依赖 Day 25 store；Day 27 依赖 Day 26 解析；Day 28 rebuild 依赖 Day 27 评估；Day 29 Chroma 依赖稳定 chunk 管线。

## 投资人时间线

| 日期 | 演示能力 |
|------|----------|
| 7/30 | 运营上传 txt |
| 7/31 | 上传 md/pdf |
| 8/01 | 调参命中提升 |
| 8/04 | 一键 rebuild |
| 8/05 | 向量库 |

## 团队产能假设

陈默架构 40%、林晓全栈 30%、周航 CI 20%、赵岩产品 10%。每日 standup 15 分钟。

"""


def _ingestion_deep_read() -> str:
    return f"""# ingestion 流水线精读

**需求**：{REQ} | **文件**：`rag/ingestion.py`

---

## 完整源码

{fenced("python", _ING)}

---

## ingest_directory 批量路径

**L17-33**：遍历目录 `read_documents` → 逐文件 `ingest_text` → 最后统一 `save`。适合运维脚本初始化，非 API 热路径。

## ingest_upload API 路径（重点）

| 行号 | 代码 | 说明 |
|------|------|------|
| L51 | `safe_name = Path(filename).name` | 防止路径穿越 |
| L52-55 | `detect_format` | Day 26 扩展；Day 25 仅 .txt 通过 |
| L57-58 | `dest.write_bytes(data)` | 审计副本，rebuild 可重扫 |
| L59-63 | `kb.ingest_bytes` | 进入 KnowledgeStore |
| L64 | `kb.save()` | 持久化 |

## 异常映射

- `NexusError` → API 映射 400/500  
- `ValueError`（不支持格式）→ 422  
- `UnicodeDecodeError` → 400 UTF-8  

## 与 api/knowledge.py 衔接

{fenced("python", chr(10).join(_API.splitlines()[131:175]))}

上传路由不直接操作 Path，委托 `ingest_upload` 保持单一写入入口。

## 设计原则

**Single Writer**：所有上传必须经 `ingest_upload`，禁止 API 直接 `ingest_text` 绕过落盘。

精读完。
"""


def _lab() -> str:
    return f"""# Day 25 实操 Lab 手册

**需求**：{REQ} | **时长**：90 分钟

---

## Lab 0：环境（10 min）

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 -m pytest tests/day25/ -v
```

**通过**：17 passed

---

## Lab 1：ingestion_demo（10 min）

```bash
python3 src/day25/ingestion_demo.py
```

记录 ingest 前后 `chunk_count`。

---

## Lab 2：knowledge_api_demo（10 min）

```bash
python3 src/day25/knowledge_api_demo.py
```

观察 TestClient upload 响应 JSON。

---

## Lab 3：启动服务（10 min）

```bash
python3 src/day24/sprint3_launch.py --serve --skip-pytest
```

访问 `/` 与 `/docs`。

---

## Lab 4：Swagger 上传（15 min）

1. `POST /api/knowledge/upload` Try it out  
2. 选 `custom_faq.txt`  
3. 确认 200 与 `sessions_cleared`  

<details><summary>期望字段</summary>filename, chunk_count, total_chunks, sessions_cleared, message</details>

---

## Lab 5：浏览器侧栏（15 min）

1. 打开知识库面板  
2. 上传文件  
3. 状态行更新  
4. 聊天提问「最低起购金额」  

---

## Lab 6：store.json 审计（10 min）

```bash
python3 -c "import json; d=json.load(open('data/knowledge/store.json')); print(len(d['chunks']), d.get('version'))"
```

---

## Lab 7：故障注入（10 min）

上传空 txt → 期望 422  

<details><summary>排错提示</summary>查 API 返回 detail 字段文案</details>

---

## 提交物

- `lab_log.md` 含 7 步截图或输出  
- pytest 全绿截图  

Lab 完。

---

## Lab 8：factory 注入验证（加分 10 min）

```python
# homework/day25/factory_check.py
from api.factory import create_orchestrator
from rag.knowledge_store import get_knowledge_store
o = create_orchestrator()
ctx = get_knowledge_store().as_rag_service().retrieve_context("起购")
print("ok", len(ctx) > 0)
```

---

## Lab 9：损坏 UTF-8 实验（加分）

写入 Latin-1 字节上传，观察 400 响应 detail。

---

## Lab 评分 Rubric 详表

| 项 | 优秀 | 良好 | 及格 |
|----|------|------|------|
| pytest | 17 绿 | 15+ | 12+ |
| upload | 含 sessions_cleared | 200 无 chat | TestClient 过 |
| chat 命中 | 两问句 | 一问句 | 无 |

"""


def _day26_preview() -> str:
    return f"""# Day 26 文档解析预习

**预告**：ZL-NA-REQ-026 | Markdown / PDF + 分块策略

## 明日变更

- `tools/doc_parser.py` — `parse_bytes` 统一入口  
- `tools/parsers/markdown_parser.py` — 标题分段  
- `tools/parsers/pdf_parser.py` — pypdf  
- `rag/chunk_strategies.py` — fixed vs markdown  

## 今日衔接

Day 25 的 `ingest_bytes` 已在仓库中委托 `parse_bytes`；明日学解析层内部，索引层仍用 `KnowledgeStore.ingest_parsed`。

## 预习任务

1. 阅读 `day26/sample_docs/product_notice.md` 结构  
2. 思考：为何 Markdown 要剥离代码块？  

赵岩：「今天能传 txt，明天要能传产品 PDF。」

预习完。
"""


if __name__ == "__main__":
    from course_builder import write_course

    write_course(DAY, build(), min_chars=110_000)
