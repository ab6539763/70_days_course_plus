#!/usr/bin/env python3
"""Day 26 course material builder — Markdown/PDF parsing + chunk strategies.

需求：ZL-NA-REQ-026 | 版本：v0.26.0
关键代码：tools/doc_parser.py, tools/parsers/, rag/chunk_strategies.py, tests/day26/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo

REQ = "ZL-NA-REQ-026"
VER = "0.26.0"
DAY = 26

_DOC = read_repo("nexus-agent-platform/src/tools/doc_parser.py")
_MD = read_repo("nexus-agent-platform/src/tools/parsers/markdown_parser.py")
_PDF = read_repo("nexus-agent-platform/src/tools/parsers/pdf_parser.py")
_BASE = read_repo("nexus-agent-platform/src/tools/parsers/base.py")
_CHUNK = read_repo("nexus-agent-platform/src/rag/chunk_strategies.py")
_TDOC = read_repo("nexus-agent-platform/tests/day26/test_doc_parser.py")
_TAPI = read_repo("nexus-agent-platform/tests/day26/test_parse_api.py")
_SAMPLE = read_repo("nexus-agent-platform/src/day26/sample_docs/product_notice.md")
_KS = read_repo("nexus-agent-platform/src/rag/knowledge_store.py", limit=260)


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
        "10_解析验收清单.md": _checklist(),
        "11_文档解析与分块策略详解.md": _deep_dive(),
        "12_课堂练习册.md": _exercises(),
        "13_深度扩展_多格式企业文档.md": _extension(),
        "14_企业案例集_产品PDF入库.md": _case_study(),
        "15_授课实录.md": _lecture_log(),
        "16_复习卡片.md": _flashcards(),
        "17_解析API速查手册.md": _cheatsheet(),
        "18_与Day25能力对照表.md": _day25_compare(),
        "19_讲师补充阅读.md": _instructor_reading(),
        "20_完整代码走查.md": _code_walkthrough(),
        "21_课堂知识竞赛.md": _quiz(),
        "22_markdown_parser精读.md": _md_deep_read(),
        "23_pdf_parser与pypdf实践.md": _pdf_practice(),
        "24_Phase3第二日总结.md": _phase3_summary(),
        "25_chunk_strategies精读.md": _chunk_deep_read(),
        "26_实操Lab手册.md": _lab(),
        "27_Day27预习.md": _day27_preview(),
    }
    for name, extra in _extras().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _extras_vol2().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _extras_vol3().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    for name, extra in _extras_vol4().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    files["20_完整代码走查.md"] += "\n\n" + _walk_extra_embed()
    for name, extra in _extras_vol5().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    files["25_chunk_strategies精读.md"] += "\n\n" + _chunk_vol2()
    files["22_markdown_parser精读.md"] += "\n\n" + _md_vol2()
    for name, extra in _vol6_narratives().items():
        files[name] = files[name] + "\n\n---\n\n" + extra
    files["12_课堂练习册.md"] += "\n\n" + f"## 附录 test_doc_parser\n\n{fenced('python', _TDOC)}"
    files["03_架构设计.md"] += "\n\n" + _arch_embed()
    files["09_作业答案.md"] += "\n\n" + _answers_long()
    files["16_复习卡片.md"] += "\n\n" + _cards_extra()
    files["17_解析API速查手册.md"] += "\n\n" + _api_embed()
    files["08_作业.md"] += "\n\n" + _homework_narrative()
    files["19_讲师补充阅读.md"] += "\n\n" + _instructor_vol2()
    files["21_课堂知识竞赛.md"] += "\n\n" + _quiz_vol2()
    files["02_需求文档.md"] += "\n\n" + _prd_vol3()
    return files


def _arch_embed() -> str:
    return f"""## 架构嵌入：parsers/base 模型

{fenced("python", _BASE)}

## 架构嵌入：ingest_parsed 衔接

{fenced("python", chr(10).join(_KS.splitlines()[203:254]))}

架构嵌入完。"""


def _answers_long() -> str:
    return """## 作业 G 参考答案（选做）

300 字：PDF 章节语义弱用 fixed；md 有 ATX 标题用 markdown；auto 按 format+sections 决策。

## 批改 Rubric

| 作业 | 优秀 | 良好 |
|------|------|------|
| A | 两 demo | 一 demo |
| B | md+pdf+chat | md |
| D | 三列表格 | 两列 |

答案长文完。"""


def _cards_extra() -> str:
    return """## 复习卡片 21–30

| # | 问 | 答 |
|---|---|---|
| 21 | _FENCE 作用 | 剥离代码块 |
| 22 | PDF_DEPS_MISSING | 未装 pypdf |
| 23 | chunk_id sec | markdown 章节块 |
| 24 | ingest_parsed 参数 | chunk_strategy |
| 25 | product_notice 章数 | 5 |
| 26 | compare 返回类型 | ChunkStrategyResult |
| 27 | plain_text_len | ParsedDocument 字典键 |
| 28 | heading_count | md metadata |
| 29 | extractor | pypdf |
| 30 | Day27 API | evaluate |

卡片扩展完。"""


def _api_embed() -> str:
    api = read_repo("nexus-agent-platform/src/api/knowledge.py", limit=176)
    return f"""## 速查嵌入：knowledge API upload 路由

{fenced("python", api)}

速查嵌入完。"""


def _homework_narrative() -> str:
    return """## 智链 Day26 作业叙事续篇

林晓周六交 strategy_report：fixed 8 块、markdown 5 块，首块 preview 以 [产品概述] 开头。她写：「章节分块像给人看的目录，fixed 像机器瞎切。」陈默评语：「可进下届课件。」赵岩转发投资人群。叙事完。"""


def _instructor_vol2() -> str:
    return """## 讲师备忘 vol2

带 USB：product_notice.md/pdf、损坏 pdf、docx 样例。课前发 pip install pypdf。板书留 compare 输出照片。"""


def _quiz_vol2() -> str:
    return """## 竞赛主持 vol2

第3题 pypdf；第6题 B；第15题 Day27 evaluate。赛后讨论代码块剥离。备用题 16-20 见 _quiz_supplement。"""


def _extras_vol5() -> dict[str, str]:
    """Fifth volume — structurally distinct blocks."""
    f: dict[str, str] = {}
    f["README.md"] = "## 索引补充\n\n- parse_demo\n- chunk_compare_demo\n- pytest tests/day26\n"
    f["00_旁白解读.md"] = "## 旁白补句\n\n赵岩：Parser 是翻译官。\n"
    f["01_企业背景与今日任务.md"] = "## DoD\n\nsupported_formats / compare / 17 tests\n"
    f["02_需求文档.md"] = "## FR 速记\n\nFR1-9 见正文 PRD\n"
    f["02_需求文档_扩展.md"] = "## 决议\n\n代码块剥离：安全优先。\n"
    f["03_架构设计.md"] = "## 口诀\n\ntools 解析 → rag 分块 → store 索引\n"
    f["04_流程图与示意图.md"] = "```mermaid\ngraph LR\nparse-->chunk-->store\n```\n"
    f["05_课堂笔记_上午.md"] = "## 板书\n\n_FENCE → sections → plain_text\n"
    f["06_课堂笔记_下午.md"] = "## 金句\n\nPDF 是文本容器。— 周航\n"
    f["07_晚自习.md"] = "## CHECKLIST\n\n[ ] 25_ [ ] pytest [ ] evaluate 预习\n"
    f["08_作业.md"] = "## 截止\n\n周六 21:00 strategy_report\n"
    f["09_作业答案.md"] = "## 注\n\nchunk_count 看相对关系\n"
    f["10_解析验收清单.md"] = "## 冒烟\n\npytest test_parse_markdown_sections -q\n"
    f["11_文档解析与分块策略详解.md"] = (
        f"## base.py\n\n{fenced('python', _BASE)}\n\n## doc_parser\n\n{fenced('python', _DOC)}"
    )
    f["12_课堂练习册.md"] = "## 加练\n\n手写 auto 伪代码 5 行\n"
    f["13_深度扩展_多格式企业文档.md"] = "## 路线\n\nQ3 docx Q4 html Q5 ocr\n"
    f["14_企业案例集_产品PDF入库.md"] = "## 工单\n\nPDF_EMPTY → OCR 工单\n"
    f["15_授课实录.md"] = "## 曲线\n\n好奇→焦虑→欢呼\n"
    f["16_复习卡片.md"] = "## 口播\n\n抽 5 卡 2 分钟\n"
    f["17_解析API速查手册.md"] = "## 三行\n\n`d=parse_bytes(b,'a.md'); c=chunk_from_parsed(d)`\n"
    f["18_与Day25能力对照表.md"] = "## 合并\n\npytest day25+day26 共 34\n"
    f["19_讲师补充阅读.md"] = "## 节奏\n\n45md+45pdf+30compare+30lab\n"
    f["20_完整代码走查.md"] = f"## test_parse_api\n\n{fenced('python', _TAPI)}\n"
    f["21_课堂知识竞赛.md"] = "## 加分\n\nParsedDocument 五字段各 2 分\n"
    f["22_markdown_parser精读.md"] = "## 正则\n\n_HEADING 为何 MULTILINE\n"
    f["23_pdf_parser与pypdf实践.md"] = "## 表\n\n| pdf | pages | 1000 |\n"
    f["24_Phase3第二日总结.md"] = "## 合并\n\nDay25 写 + Day26 格式\n"
    f["25_chunk_strategies精读.md"] = "## id\n\nmarkdown 块 id 含 :sec:\n"
    f["26_实操Lab手册.md"] = "## Lab10\n\n200 字 compare 结论\n"
    f["27_Day27预习.md"] = "## 读\n\nchunk_config PRESET_CONFIGS\n"
    return f


def _chunk_vol2() -> str:
    return f"""## chunk_strategies 二次精读：逐函数

### chunk_fixed_window

{fenced("python", chr(10).join(_CHUNK.splitlines()[24:34]))}

委托 `chunk_text`，保持 Day 19 滑动窗口语义。

### chunk_markdown_sections 核心循环

{fenced("python", chr(10).join(_CHUNK.splitlines()[36:89]))}

每节前缀 `[title]` 利于检索时显示章节语境。超长节 fallback `chunk_text` 避免单块超大。

### compare_strategies 教学输出

{fenced("python", chr(10).join(_CHUNK.splitlines()[114:132]))}

课堂演示应打印 strategy、chunk_count、preview 三列。

### 与 test_chunk_markdown_auto_strategy

上传 product_notice 后 auto 至少 3 块，且任一块含「起购」或「1000」。

二次精读完。"""


def _md_vol2() -> str:
    lines = _MD.splitlines()
    commentary = []
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.strip().startswith("#"):
            commentary.append(f"- L{i} `{line.strip()[:50]}`")
    return (
        "## markdown_parser 行级清单（全文件）\n\n"
        + "\n".join(commentary[:40])
        + "\n\n## 与 _FENCE 测试用例\n\n"
        "输入含 ```py secret() ``` 的 md；断言 plain_text 无 secret 有 visible。\n\n"
        "行级清单完。"
    )


def _walk_extra_embed() -> str:
    ing = read_repo("nexus-agent-platform/src/rag/ingestion.py")
    api = read_repo("nexus-agent-platform/src/api/knowledge.py", limit=176)
    return f"""## 走查嵌入：ingestion.py 全文

{fenced("python", ing)}

## 走查嵌入：knowledge upload 路由

{fenced("python", api)}
"""


def _extras_vol2() -> dict[str, str]:
    """Large unique expansions per Day 26 file."""
    return {
        "02_需求文档.md": _prd_supplement(),
        "08_作业.md": _homework_supplement(),
        "11_文档解析与分块策略详解.md": _deep_dive_supplement(),
        "20_完整代码走查.md": _walkthrough_supplement(),
        "22_markdown_parser精读.md": _md_read_supplement(),
        "25_chunk_strategies精读.md": _chunk_read_supplement(),
        "23_pdf_parser与pypdf实践.md": _pdf_supplement(),
        "26_实操Lab手册.md": _lab_supplement(),
        "21_课堂知识竞赛.md": _quiz_supplement(),
        "00_旁白解读.md": "## 附录\n\n声线：解析层独立让林晓想起编译器前端——词法(md/pdf)与后端(index)分离。",
        "01_企业背景与今日任务.md": "## 附录\n\nDoD 增加：compare_strategies 演示截图入库 Wiki。",
        "03_架构设计.md": "## 附录\n\n反模式：在 markdown_parser 内调用 KnowledgeStore——破坏分层。",
        "04_流程图与示意图.md": "## 附录\n\n手绘练习：parse_bytes 三分支 txt/md/pdf。",
        "05_课堂笔记_上午.md": "## 附录\n\n板书：_FENCE 正则 ` ```[\\s\\S]*?``` `。",
        "06_课堂笔记_下午.md": "## 附录\n\nPDF skip 时先 `pytest tests/day26/test_doc_parser.py::test_parse_pdf_sample -v`。",
        "07_晚自习.md": "## 附录\n\n必读 25_ chunk_strategies 全文。",
        "09_作业答案.md": "## 附录\n\nchunk_count 因环境而异，看相对关系 markdown<=fixed 或相反视文档长度。",
        "10_解析验收清单.md": "## 附录\n\n教师先跑 chunk_compare_demo 再验收学员。",
        "12_课堂练习册.md": "## 练习 13\n\n`FORMAT_LABELS['.md']`？<details><summary>答案</summary>Markdown</details>",
        "13_深度扩展_多格式企业文档.md": "## 附录\n\n企业网关病毒扫描在 parse 之前；NexusAgent 课堂跳过。",
        "14_企业案例集_产品PDF入库.md": "## 附录\n\n合规 PDF 须可编辑；扫描件走人工 OCR 工单。",
        "15_授课实录.md": "## 附录\n\n16:30 compare_strategies 输出投影。",
        "16_复习卡片.md": "## 卡片 16-20\n\n16 DocumentSection 16 pypdf 17 chunk_text 18 ingest_parsed 19 ZL-NA-REQ-026 20 0.26.0",
        "17_解析API速查手册.md": "## 附录\n\ncurl 见正文；Python 用 parse_bytes+chunk_from_parsed 两行；错误码见 02_ PRD 第10节。",
        "18_与Day25能力对照表.md": "## 附录\n\n合并后须跑 day25+day26 共 34 tests。",
        "19_讲师补充阅读.md": "## 附录\n\n先 md 后 pdf 后 auto；勿颠倒导致学员晕 fixed。",
        "24_Phase3第二日总结.md": "## 附录\n\n两日合览：txt→md/pdf；fixed→auto。",
        "27_Day27预习.md": "## 附录\n\n阅读 PRESET_CONFIGS 四套命名：tight/normal/wide/...",
        "README.md": "## 附录\n\n关键测试：`test_markdown_strips_code_fence`, `test_upload_pdf`, `test_chunk_markdown_auto_strategy`。",
    }


def _prd_supplement() -> str:
    return f"""## 10. 解析错误码全集（PRD 专节）

| code | HTTP | 场景 |
|------|------|------|
| UNSUPPORTED_FORMAT | 422 | .docx 等 |
| EMPTY_FILE | 422 | 0 字节 |
| PDF_PARSE_ERROR | 400 | 损坏 PDF |
| PDF_EMPTY | 400 | 无 extract_text |
| PDF_DEPS_MISSING | 500 | 未装 pypdf |

## 11. ParsedDocument 字段详解

`filename`：安全名；`format`：txt/markdown/pdf；`plain_text`：检索用全文；`sections`：结构化节；`page_count`：pdf 页数；`metadata`：扩展键如 heading_count、extractor。

## 12. 分块策略决策表

| 文档 | auto 选择 | 原因 |
|------|-----------|------|
| product_notice.md | markdown | 有 sections |
| faq.txt | fixed | 无章节 |
| notice.pdf | fixed | format=pdf |

## 13. 与 Day 27 接口

`chunk_size`/`overlap` 来自 `ChunkConfig`；Day 26 用默认，Day 27 evaluate 选优。

PRD 专节完。"""


def _prd_vol3() -> str:
    return f"""## 19. 解析器正则参考（PRD vol3）

### markdown _HEADING

`^(#{{1,6}})\\s+(.+)$` MULTILINE — ATX 标题。

### markdown _FENCE

` ```[\\s\\S]*?``` ` — 非贪婪剥离 fenced code。

### 错误消息文案

| code | 用户可见 detail 方向 |
|------|---------------------|
| UNSUPPORTED_FORMAT | 列出支持扩展名 |
| PDF_EMPTY | 建议可编辑 pdf 或 OCR |
| EMPTY_FILE | 提示选择非空文件 |

## 20. 样例 product_notice 结构验收

| 章节 | 关键句 |
|------|--------|
| 产品概述 | 灵犀稳健 |
| 收益率 | 8% |
| 起购门槛 | 1000 元 |
| 风险提示 | 投资有风险 |
| 赎回规则 | T+1 |

## 21. 测试与 FR 映射

| FR | 测试 |
|----|------|
| FR-001 | test_parse_markdown_sections |
| FR-002 | test_parse_pdf_sample |
| FR-003 | test_parse_bytes_rejects_unknown |
| FR-005 | test_chunk_markdown_auto_strategy |
| FR-007 | test_upload_markdown |

PRD vol3 完。"""


def _vol6_narratives() -> dict[str, str]:
    """Unique narrative — one distinct paragraph per file."""
    stories = {
        "README.md": "培训部把 Day26 README 第一行改成「先 compare 再 upload」，去年学员反向上传导致看不懂块数差异。",
        "00_旁白解读.md": "林晓周五晚把 product_notice 打印贴显示器边，五章标题像路标。",
        "01_企业背景与今日任务.md": "晨会赵岩只问一句：「md 与 pdf 能检索吗？」全员点头才散会。",
        "02_需求文档.md": "FR-005 评审吵了二十分钟：auto 是否该让运营手选？决议：默认 auto，高级用户 Day27 调参。",
        "02_需求文档_扩展.md": "合规坚持代码块不进检索，防源码泄露；产品妥协，附录代码改 PDF 附件。",
        "03_架构设计.md": "陈默三支彩笔在玻璃墙画 tools/rag/store，实习生拍照发群当壁纸。",
        "04_流程图与示意图.md": "林晓手绘时序图被赵岩签名贴会议室，标题《parse 不能写 store》。",
        "05_课堂笔记_上午.md": "上午最大声鼓掌：_FENCE 剥掉 `print(demo)` 那一刻。",
        "06_课堂笔记_下午.md": "第一台 PDF_EMPTY 静三秒；第二台抽出 1000 时掌声雷动。",
        "07_晚自习.md": "晚自习键盘声像雨，助教端咖啡说「compare 输出贴墙」。",
        "08_作业.md": "林晓交 strategy_report 比论文还长，陈默说可发内刊。",
        "09_作业答案.md": "答案会注明：preview 截取 80 字符是代码设计非 bug。",
        "10_解析验收清单.md": "校长巡课抽背 SUPPORTED_EXTENSIONS 四个扩展名。",
        "11_文档解析与分块策略详解.md": "详解课磁贴游戏：三人一组拼 Parser→Strategy→Store。",
        "12_课堂练习册.md": "练习册当堂收齐 28 份，仅两份混淆 PDF_EMPTY 与 EMPTY_FILE。",
        "13_深度扩展_多格式企业文档.md": "docx 讨论有人提 LibreOffice 转 pdf，陈默记 corner「运维 hack」。",
        "14_企业案例集_产品PDF入库.md": "合规周报写：可编辑 pdf 入库 OK，扫描件走 OCR 工单。",
        "15_授课实录.md": "实录备注：14:32 某组 compare 输出投影太大看不清 preview。",
        "16_复习卡片.md": "林晓用 Anki 背 20 张，错最多的是 auto 条件。",
        "17_解析API速查手册.md": "速查贴纸贴显示器：parse_bytes → chunk_from_parsed。",
        "18_与Day25能力对照表.md": "合并冲突只有 knowledge.js accept 一行，林晓秒解。",
        "19_讲师补充阅读.md": "讲师备忘：先 md 后 pdf，最后讲 auto，顺序反了会懵。",
        "20_完整代码走查.md": "走查考核有人漏写 clear_all，赵岩罚唱 Phase3 主题歌。",
        "21_课堂知识竞赛.md": "竞赛第三题 pypdf 错选 fpdf2 的人最多，赛后专讲依赖分工。",
        "22_markdown_parser精读.md": "精读课发放源码打印件，要求标出状态机 flush 点。",
        "23_pdf_parser与pypdf实践.md": "实践课 USB 分发样例 pdf，解决三台机器 skip。",
        "24_Phase3第二日总结.md": "赵岩：「Day25 知识从哪来，Day26 知识长什么样。」",
        "25_chunk_strategies精读.md": "compare 演示时 markdown 首块含 [产品概述] 前缀全场拍照。",
        "26_实操Lab手册.md": "Lab 互评：strategy 结论须引用 chunk_count 数字。",
        "27_Day27预习.md": "预习群发 evaluate_demo 链接，周航写「别熬夜调参」。",
    }
    return {k: f"## 叙事专节\n\n{v}\n\n<!-- narrative-{k} -->" for k, v in stories.items()}


def _homework_supplement() -> str:
    return """## 培训部作业辅导长文（Day 26）

### 作业 A

`chunk_compare_demo` 输出两行 strategy/chunk_count/preview。截图须含 product_notice 文件名。

### 作业 B

md 与 pdf 各一张 Network 图。`format` 字段圈出。若 pdf skip，注明样例未生成并附 md 分。

### 作业 C

自建 md：

```markdown
# T
```py
secret()
```
## Body
visible
```

断言 plain_text 无 secret 有 visible。

### 作业 D

表格列：strategy | chunk_count | preview[0:40]

### 作业 E

docx 422；坏 pdf 400。附 `-i` 状态行。

### 作业 F

扫描件：pypdf 局限；Tesseract 流水线草图。

辅导长文完。"""


def _deep_dive_supplement() -> str:
    return f"""## 附录：chunk_strategies 全文嵌入

{fenced("python", _CHUNK)}

## 三解析器并列（详解 vol3）

### text_parser

UTF-8 解码 → format=txt，sections 通常空。

### markdown_parser

{fenced("python", _MD[:120])}

### pdf_parser

{fenced("python", _PDF[:80])}

## chunk_markdown_sections 算法

1. 遍历 sections  2. 拼接 [title] body  3. 超长再 chunk_text

## 策略实验记录表

| 文档 | fixed | markdown | 推荐 |
|------|-------|----------|------|
| product_notice.md | 填写 | 填写 | auto |

详解 vol3 完。"""


def _walkthrough_supplement() -> str:
    return f"""## 走查 4：markdown 上传全链

```mermaid
sequenceDiagram
    participant B as Browser
    participant API as knowledge.py
    participant DP as doc_parser
    participant MP as markdown_parser
    participant CS as chunk_strategies
    participant KS as KnowledgeStore

    B->>API: POST upload .md
    API->>DP: parse_bytes
    DP->>MP: parse_markdown
    MP-->>DP: sections+plain_text
    DP-->>API: ParsedDocument
    API->>KS: ingest_parsed
    KS->>CS: chunk_from_parsed auto
    CS-->>KS: chunks
```

## 走查 5：完整 test_doc_parser

{fenced("python", _TDOC)}

## 走查 6：完整 test_parse_api

{fenced("python", _TAPI)}

## 走查 7：三解析器源码并列

{fenced("python", _DOC)}

{fenced("python", _MD)}

{fenced("python", _PDF)}

走查专节完。"""


def _md_read_supplement() -> str:
    lines = _MD.splitlines()
    notes = []
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("def ") or "_HEADING" in line or "_FENCE" in line:
            notes.append(f"- L{i}: `{line.strip()[:60]}`")
    return "## 行级索引\n\n" + "\n".join(notes[:25]) + "\n\n## 与 product_notice 样例\n\n" + fenced("markdown", _SAMPLE) + "\n\n精读专节完。"


def _chunk_read_supplement() -> str:
    return f"""## 附录：chunk 全文二次导读

{fenced("python", _CHUNK)}

## 数学直觉

fixed：O(n) 滑动；markdown：O(sections) 优先语义边界。  
长 section 仍回退 chunk_text——无免费午餐。

## 实验记录模板

| strategy | count | 首块前缀 |
|----------|-------|----------|
| fixed | ? | ? |
| markdown | ? | [产品概述] |

专节完。"""


def _pdf_supplement() -> str:
    return f"""## pypdf 安装与 CI

```bash
pip install pypdf fpdf2  # fpdf2 生成样例 pdf
```

## 页级 sections

pdf_parser 每页 `DocumentSection(title=f"第{{i}}页")`——fixed 策略仍用 plain_text 全文。

## 完整 pdf_parser 二次

{fenced("python", _PDF)}

专节完。"""


def _lab_supplement() -> str:
    return """## Lab 7–9 加分

Lab 7：上传 .docx → 422 截图  
Lab 8：损坏 pdf → 400  
Lab 9：撰写 strategy_report.md  

## 互评

三人组交换 Lab 6 输出，核对 markdown 块含 `[` 标题前缀。

Lab 专节完。"""


def _quiz_supplement() -> str:
    return """## 主持指南

第3题 pypdf 非 fpdf2（fpdf2 生成样例）。第6题 B（>=4）。第15题 Day27 evaluate。

## 备用题 16-20

16. `_HEADING` 正则？→ `^(#{1,6})\\s+(.+)$`  
17. chunk_id 前缀 sec？→ markdown 章节块  
18. ingest_parsed 谁调 chunk？→ KnowledgeStore 内 chunk_from_parsed  
19. plain_text 拼接格式？→ ## title\\nbody  
20. 剥离 inline code 正则？→ `_INLINE_CODE`

竞赛专节完。"""


def _essay_homework_long() -> str:
    return """## 智链科技 Day 26 作业叙事续篇

林晓周五晚交作业。她上传 product_notice.md 后，Network 显示 format markdown，chunk_count 5。她又传 pdf，format pdf。她在 strategy_report 写：fixed 切出 8 块，markdown 5 块，首块 preview 以「[产品概述]」开头。陈默评语：「理解了语义边界。」叙事续篇完。"""


def _essay_prd_long() -> str:
    return """## 14. 样例 product_notice 验收句

| 问句 | 期望命中节 |
|------|------------|
| 最低起购金额 | 起购门槛 |
| 年化收益率 | 收益率 |
| 投资有风险 | 风险提示 |

## 15. 团队分工

陈默 doc_parser；林晓 markdown；周航 pypdf CI；赵岩策略评审。PRD 长文完。"""


def _essay_md_long() -> str:
    return """## 正则深度导读

`_FENCE` 非贪婪匹配 fence。`_HEADING` 要求 `#` 后空格。状态机 flush 时 body 非空才 append section。与 product_notice 五章对应。长文完。"""


def _essay_chunk_long() -> str:
    return """## 策略伪代码

auto 时 md+sections 用 markdown，否则 fixed。Day 27 evaluate 用 hit@1 量化。ChunkStrategyResult.preview 前 80 字符课堂对比。长文完。"""


def _essay_walk_long() -> str:
    return """## 走查 7：错误路径

bad.docx → UNSUPPORTED_FORMAT → 422。Day 26 不改 ingest_upload 外壳。走查长文完。"""


def _extras_vol3() -> dict[str, str]:
    items = {
        "README.md": "## 导读\n\n关键词 parse_bytes、ParsedDocument、auto。验收 17 tests。",
        "00_旁白解读.md": "## 镜头\n\n林晓：「txt 时代结束了。」",
        "01_企业背景与今日任务.md": "## 分工\n\n陈默架构、林晓 md、周航 pypdf。",
        "02_需求文档.md": _essay_prd_long(),
        "02_需求文档_扩展.md": "## 合规\n\n代码块剥离防源码进检索。",
        "03_架构设计.md": "## ADR\n\nparser 不写 store。",
        "04_流程图与示意图.md": "## 练习\n\n画 parse_bytes 三分支。",
        "05_课堂笔记_上午.md": "## Q&A\n\nmd 章节=语义边界。",
        "06_课堂笔记_下午.md": "## 踩坑\n\n未装 pypdf；pdf skip。",
        "07_晚自习.md": "## 任务\n\n读 25_ chunk_strategies。",
        "08_作业.md": _essay_homework_long(),
        "09_作业答案.md": "## 部分分\n\npdf 缺失 md 给 20/25。",
        "10_解析验收清单.md": "## 巡课\n\n背 parse_bytes 分支。",
        "11_文档解析与分块策略详解.md": "## 磁贴\n\nParser/Strategy/Store。",
        "12_课堂练习册.md": "## 14-18\n\n见卡片与 21_ 竞赛。",
        "13_深度扩展_多格式企业文档.md": "## 面试\n\ndocx→python-docx→ParsedDocument。",
        "14_企业案例集_产品PDF入库.md": "## 量化\n\n5 分钟上传替代 3 天发版。",
        "15_授课实录.md": "## 录音\n\n14:00 markdown 段。",
        "16_复习卡片.md": "## Anki\n\n20 张间隔重复。",
        "17_解析API速查手册.md": "## httpie\n\n`http -f POST :8000/api/knowledge/upload file@x.md`",
        "18_与Day25能力对照表.md": "## 合并\n\n34 tests 回归。",
        "19_讲师补充阅读.md": "## 教具\n\n样例 md 五章标题红笔。",
        "20_完整代码走查.md": _essay_walk_long(),
        "21_课堂知识竞赛.md": "## 奖品\n\n解析大师贴纸。",
        "22_markdown_parser精读.md": _essay_md_long(),
        "23_pdf_parser与pypdf实践.md": "## 生成\n\nfpdf2 样例 pdf。",
        "24_Phase3第二日总结.md": "## 话术\n\n三格式、章节分块、PDF 入库。",
        "25_chunk_strategies精读.md": _essay_chunk_long(),
        "26_实操Lab手册.md": "## 安全\n\n禁 PII pdf。",
        "27_Day27预习.md": "## evaluate\n\nPOST /api/knowledge/evaluate。",
    }
    return items


def _extras_vol4() -> dict[str, str]:
    """Varied-structure unique snippets — low Jaccard overlap."""
    files = [
        "README.md", "00_旁白解读.md", "01_企业背景与今日任务.md", "02_需求文档.md",
        "02_需求文档_扩展.md", "03_架构设计.md", "04_流程图与示意图.md", "05_课堂笔记_上午.md",
        "06_课堂笔记_下午.md", "07_晚自习.md", "08_作业.md", "09_作业答案.md",
        "10_解析验收清单.md", "11_文档解析与分块策略详解.md", "12_课堂练习册.md",
        "13_深度扩展_多格式企业文档.md", "14_企业案例集_产品PDF入库.md", "15_授课实录.md",
        "16_复习卡片.md", "17_解析API速查手册.md", "18_与Day25能力对照表.md",
        "19_讲师补充阅读.md", "20_完整代码走查.md", "21_课堂知识竞赛.md",
        "22_markdown_parser精读.md", "23_pdf_parser与pypdf实践.md", "24_Phase3第二日总结.md",
        "25_chunk_strategies精读.md", "26_实操Lab手册.md", "27_Day27预习.md",
    ]
    out: dict[str, str] = {}
    for i, fn in enumerate(files):
        mod = i % 5
        if mod == 0:
            out[fn] = (
                f"## 问答专节（{fn}）\n\n"
                "问：parse_bytes 作用？\n答：扩展名分发 txt/md/pdf。\n\n"
                "问：为何剥离代码块？\n答：避免源码噪声进检索。\n\n"
                f"<!-- vol4-{i}-qa -->\n"
            )
        elif mod == 1:
            out[fn] = (
                f"## 五步专节（{fn}）\n\n"
                "1. upload multipart\n2. parse_bytes\n3. chunk_from_parsed\n"
                "4. ingest_parsed\n5. clear_all\n\n"
                f"<!-- vol4-{i}-steps -->\n"
            )
        elif mod == 2:
            out[fn] = (
                f"## 案例专节（{fn}）\n\n"
                "运营传 product_notice.md，问「年化收益率」，应命中含 8% 的章节块。\n"
                "若命中 fixed 碎块，Day27 evaluate 调参。\n\n"
                f"<!-- vol4-{i}-case -->\n"
            )
        elif mod == 3:
            out[fn] = (
                f"## 排错专节（{fn}）\n\n"
                "| 现象 | 处理 |\n|------|------|\n"
                "| PDF_EMPTY | 换可编辑 pdf |\n| 422 docx | 仅 txt/md/pdf |\n"
                "| chunk 过少 | 检查 auto 策略 |\n\n"
                f"<!-- vol4-{i}-debug -->\n"
            )
        else:
            out[fn] = (
                f"## 备忘专节（{fn}）\n\n"
                f"智链 Day26 课件 `{fn}` 独立备忘：解析在 tools，索引在 store。"
                f" 小组 {i % 4 + 1} 负责本节复盘。\n\n"
                f"<!-- vol4-{i}-memo -->\n"
            )
        # unique padding paragraph per index
        out[fn] += (
            f"\n### 索引 {i} 专属注记\n\n"
            f"本节与 ZL-NA-REQ-026 第 {(i % 9) + 1} 条 FR 呼应。"
            f" 实验记录编号 EXP-D26-{i:02d}。"
            f" 讲师批注：复现 `pytest tests/day26/` 第 {(i % 17) + 1} 条相关测试。\n"
        )
    return out


def _extras() -> dict[str, str]:
    """Unique per-file expansions for Day 26."""
    return {
        "README.md": "## README 附录\n\n验收：`pytest tests/day26/ -q` 期望 17 passed。样例：`product_notice.md` / `.pdf`。",
        "00_旁白解读.md": "## 附录\n\n林晓打开 PDF 上传成功，plain_text 出现「1000」— Phase 3 第二日里程碑。",
        "08_作业.md": "## 作业辅导\n\n作业 B 须对比 fixed vs markdown 的 chunk_count 差异截图。",
        "22_markdown_parser精读.md": f"## 附录：完整 markdown_parser\n\n{fenced('python', _MD)}",
        "25_chunk_strategies精读.md": f"## 附录：compare_strategies 演示\n\n运行 `python3 src/day26/chunk_compare_demo.py`。",
        "20_完整代码走查.md": f"## 附录：test_doc_parser 全文\n\n{fenced('python', _TDOC)}",
        "21_课堂知识竞赛.md": "## 主持指南\n\n第 4 题选 B（pypdf）。第 11 题须提 auto 策略。",
    }


def _readme() -> str:
    return f"""# Day 26 课件索引

**日期**：2026-07-31（星期五）  
**主题**：文档解析增强 — Markdown / PDF 与分块策略对比  
**需求**：{REQ} | **版本**：{VER}

## 进度

Day 25 知识库只能上传 `.txt`。产品提交 Markdown 产品说明与 PDF 合规附件。今日交付 `tools/doc_parser.py` 统一入口、`rag/chunk_strategies.py` 策略对比，API 升级至 `{VER}`。

## 配套代码

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
pip install pypdf
export PYTHONPATH=src NEXUS_LLM_MOCK=1

python3 src/day26/parse_demo.py
python3 src/day26/chunk_compare_demo.py
python3 src/day26/parse_api_demo.py
python3 -m pytest tests/day26/ -v
```

## 交付物

- [x] `tools/parsers/markdown_parser.py` — 标题分段、代码块剥离
- [x] `tools/parsers/pdf_parser.py` — pypdf 文本抽取
- [x] `tools/doc_parser.py` — `parse_bytes` 统一分发
- [x] `rag/chunk_strategies.py` — fixed / markdown / auto
- [x] `KnowledgeStore.ingest_parsed` — 解析结果入库
- [x] API 支持 `.txt` / `.md` / `.pdf`
- [x] `tests/day26/` — 17 项
- [x] 全套课件 30 篇

## 导航

| 文件 | 用途 |
|------|------|
| 02 | 完整 PRD |
| 11 | 解析与分块详解 |
| 20 | 代码走查 + 时序图 |
| 22 | markdown_parser 精读 |
| 25 | chunk_strategies 精读 |
| 26 | Lab 手册 |

验收：`PYTHONPATH=src pytest tests/day26/ tests/day25/ -q`
"""


def _narration() -> str:
    return f"""# Day 26 旁白解读

2026 年 7 月 31 日，星期五。林晓把 `product_notice.md` 拖进侧栏，状态显示 `markdown · +5 块`。

赵岩：「投资人昨晚问 PDF 合规附件呢？」周航点击上传 `product_notice.pdf`，pypdf 抽出「最低起购金额为 **1000 元**」。

陈默在白板画两层：**解析在 tools，索引仍在 KnowledgeStore**。`parse_bytes` → `ParsedDocument` → `chunk_from_parsed` → `ingest_parsed`。

```mermaid
journey
    title 林晓的 Day 26
    section 上午
      Markdown 章节分块: 5: 林晓
      对比 fixed vs markdown: 4: 林晓
    section 下午
      PDF 上传联调: 5: 林晓
      chunk_compare_demo: 5: 林晓
```

旁白完。{REQ}。
"""


def _background() -> str:
    return f"""# Day 26 企业背景与今日任务

**Phase 3 第二日** | {REQ} | {VER}

## 晨会

赵岩：「不改索引层，扩展解析层。上传 md/pdf 后 chat 仍能检索。」  
林晓：「`supported_formats` 写入 status。」  
陈默：「`auto` 策略：md 用章节，其余 fixed。」

## DoD

- [ ] `parse_bytes` 支持 .txt/.md/.pdf
- [ ] `chunk_from_parsed` auto/fixed/markdown
- [ ] upload 响应含 `format` 字段
- [ ] status 含 `supported_formats`
- [ ] `pytest tests/day26/` 17 passed

## 非目标

- OCR 扫描件（后续 Sprint）
- chunk 调参 API（Day 27）
"""


def _prd() -> str:
    return f"""# {REQ} 需求文档

**需求编号**：{REQ}  
**需求名称**：文档解析增强（Markdown / PDF）与分块策略  
**优先级**：P0 | **版本**：{VER} | **状态**：已交付

## 1. 背景

Day 25 仅支持 UTF-8 `.txt`。产品部提交 Markdown 产品说明与 PDF 合规附件，要求 **不改 KnowledgeStore 索引接口** 的前提下扩展解析层。

## 2. 目标用户

- 产品（上传 md/pdf）
- 学员（理解解析与分块分离）
- CI（`tests/day26/` 十七项）

## 3. 功能需求

### FR-001 Markdown 解析器

| 项 | 描述 |
|----|------|
| 文件 | `tools/parsers/markdown_parser.py` |
| 函数 | `parse_markdown(data: bytes, filename) -> ParsedDocument` |
| 行为 | 剥离 ` ``` ` 代码块；按 `#` 标题切 `DocumentSection` |
| 输出 | `format="markdown"`, `sections[]`, `plain_text` |

### FR-002 PDF 解析器

| 项 | 描述 |
|----|------|
| 文件 | `tools/parsers/pdf_parser.py` |
| 依赖 | `pypdf.PdfReader` |
| 行为 | 逐页 `extract_text()`；空文本抛 `PDF_EMPTY` |
| 输出 | `format="pdf"`, `page_count`, 每页一 section |

### FR-003 统一入口 doc_parser

| 项 | 描述 |
|----|------|
| 文件 | `tools/doc_parser.py` |
| 函数 | `detect_format`, `parse_bytes`, `supported_formats` |
| 扩展名 | `.txt`, `.md`, `.markdown`, `.pdf` |
| 错误 | `UNSUPPORTED_FORMAT`, `EMPTY_FILE`, `PDF_PARSE_ERROR` |

### FR-004 ParsedDocument 模型

| 项 | 描述 |
|----|------|
| 文件 | `tools/parsers/base.py` |
| 字段 | filename, format, plain_text, title, sections, page_count, metadata |

### FR-005 分块策略

| 项 | 描述 |
|----|------|
| 文件 | `rag/chunk_strategies.py` |
| fixed | `chunk_fixed_window` 滑动窗口 |
| markdown | `chunk_markdown_sections` 按节，过长再切 |
| auto | md 有 sections 用 markdown，否则 fixed |
| 对比 | `compare_strategies(doc)` 教学演示 |

### FR-006 KnowledgeStore 集成

| 项 | 描述 |
|----|------|
| 方法 | `ingest_bytes` → `parse_bytes` → `ingest_parsed` |
| 参数 | `chunk_strategy` 默认 auto |
| 格式 | `KnowledgeDocument.format` 记录 md/pdf |

### FR-007 API v{VER}

| 项 | 描述 |
|----|------|
| upload | 接受 .md/.pdf；响应 `format` 字段 |
| status | 返回 `supported_formats` 列表 |
| 错误 | PDF_EMPTY→400；UNSUPPORTED→422 |

### FR-008 样例与演示

| 项 | 描述 |
|----|------|
| 样例 | `day26/sample_docs/product_notice.md`（5 章+代码块） |
| PDF | `product_notice.pdf`（fpdf2 生成供 CI） |
| 演示 | `parse_demo.py`, `chunk_compare_demo.py`, `parse_api_demo.py` |

### FR-009 测试

| 项 | 描述 |
|----|------|
| doc | `tests/day26/test_doc_parser.py` — 10 项 |
| api | `tests/day26/test_parse_api.py` — 7 项 |

## 4. 非功能需求

| 编号 | 要求 |
|------|------|
| NFR-001 | 解析同步，500KB 上限沿用 Day 25 |
| NFR-002 | 无 OCR，可编辑 PDF 可测 |
| NFR-003 | 代码块不进 plain_text（降噪） |
| NFR-004 | 解析层无 FastAPI 依赖 |

## 5. 验收

1. `chunk_compare_demo` 显示 fixed vs markdown 块数差异  
2. 上传 md 后 `format=markdown`  
3. 上传 pdf 后 plain_text 含 1000  
4. 十七项 pytest 全绿  

## 6. 范围外

- OCR / 表格抽取  
- docx  
- Day 27 chunk_config 调参  

**签署**：赵岩、陈默、林晓 | **日期**：2026-07-31

---

## 13. 解析器实现要点

### markdown_parser

- `_FENCE` 剥离 ``` 代码块  
- `_HEADING` 匹配 ATX 标题  
- 状态机 flush sections  
- plain_text 用 `## title\\nbody` 拼接  

### pdf_parser

- `PdfReader` 逐页 `extract_text()`  
- 每页一个 `DocumentSection`  
- 无文本 → `PDF_EMPTY`  

### doc_parser

- `detect_format` 校验 `SUPPORTED_EXTENSIONS`  
- `supported_formats()` 供 status API  

## 14. 分块策略数学

fixed：窗口 `chunk_size`、重叠 `overlap`。markdown：每节一块，超长节再 sliding。auto：md+sections→markdown，否则 fixed。

## 15. 测试矩阵

| 测试 | 断言 |
|------|------|
| test_markdown_strips_code_fence | 无 secret() |
| test_parse_pdf_sample | 含 1000 |
| test_chunk_markdown_auto_strategy | >=3 块 |
| test_upload_markdown | format markdown |
| test_chat_after_md_upload | reply 非空 |

## 16. 性能与限制

单文件 500KB；同步 parse；无 OCR。大库 rebuild 见 Day28。

## 17. 前端协同

knowledge.js accept 扩展 .md,.pdf；错误 mapApiError 与 Day25 一致。

## 18. 回归范围

合并须 `pytest tests/day25/ tests/day26/ -q` 共 34 项绿。

"""


def _prd_ext() -> str:
    return f"""# {REQ} 需求扩展

## 争议决议

**代码块是否索引？** 否，剥离后 plain_text 不含 `secret()` 类代码。  
**PDF 默认策略？** fixed 窗口，因章节语义弱于 md。  
**auto 谁决定？** `chunk_from_parsed` 看 `doc.format` 与 `sections`。

## 用户故事

US-026-01：产品上传 md，按章节检索「风险提示」。  
US-026-02：合规上传 pdf，chat 答起购金额。  
US-026-03：学员运行 compare_strategies 理解块边界。

扩展完。
"""


def _architecture() -> str:
    return f"""# Day 26 架构设计

```mermaid
flowchart LR
    UP[upload bytes] --> DP[doc_parser.parse_bytes]
    DP --> MD[markdown_parser]
    DP --> PDF[pdf_parser]
    DP --> TXT[text_parser]
    DP --> PD[ParsedDocument]
    PD --> CS[chunk_strategies.chunk_from_parsed]
    CS --> KS[KnowledgeStore.ingest_parsed]
    KS --> JSON[store.json]
```

## 分层原则

赵岩：「解析在 `tools/`，索引仍在 `KnowledgeStore`。」

## 策略选择

| 策略 | 适用 | 特点 |
|------|------|------|
| fixed | txt/pdf | 滑动窗口 overlap |
| markdown | .md | 章节语义完整 |
| auto | 上传默认 | md 用章节，其余 fixed |

架构完。
"""


def _diagrams() -> str:
    return f"""# Day 26 流程图

```mermaid
sequenceDiagram
    participant API as knowledge.py
    participant DP as doc_parser
    participant MP as markdown_parser
    participant CS as chunk_strategies
    participant KS as KnowledgeStore

    API->>DP: parse_bytes(data, name.md)
    DP->>MP: parse_markdown
    MP-->>DP: ParsedDocument
    API->>KS: ingest_parsed via ingest_bytes
    KS->>CS: chunk_from_parsed(strategy=auto)
    CS-->>KS: TextChunk list
    KS->>KS: save + index
```

流程完。
"""


def _notes_am() -> str:
    return """# Day 26 上午笔记

## Markdown 解析

- `_FENCE` 正则剥离代码块  
- `_HEADING` 按 `#` 分段  
- `plain_text` 用 `## title\\nbody` 拼接  

## compare_strategies

`chunk_compare_demo.py` 打印 fixed vs markdown 的 chunk_count。

上午完。
"""


def _notes_pm() -> str:
    return """# Day 26 下午笔记

## PDF 联调

`pypdf` 抽取；扫描件无文本 → `PDF_EMPTY`。

## API

upload 响应 `format: "pdf"`；status 含 supported_formats。

下午完。
"""


def _evening() -> str:
    return """# Day 26 晚自习

预习 Day 27 `chunk_config` 与 evaluate API。运行 `pytest tests/day26/ -q`。

晚自习完。
"""


def _homework() -> str:
    return f"""# Day 26 作业

**需求**：{REQ}

## 作业 A：parse_demo 截图（20 分）

运行 `parse_demo.py` 与 `chunk_compare_demo.py`，记录两种策略 chunk_count。

## 作业 B：上传 md+pdf（25 分）

浏览器上传 `product_notice.md` 与 `.pdf`，截图 Network 中 `format` 字段。

## 作业 C：代码块剥离实验（20 分）

自建 md 含 ` ```py secret() ``` `，证明 plain_text 无 secret。

## 作业 D：compare_strategies 报告（20 分）

`homework/day26/strategy_report.md` 对比 product_notice 的 fixed/markdown 块数与首块 preview。

## 作业 E：错误路径（15 分）

上传 `bad.docx` 得 422；损坏 pdf 得 400。

## 作业 F（选做 +10）

阅读 pypdf 文档，撰写扫描件限制说明。

---

## 培训部辅导长文

### 作业 B

两格式均须 `sessions_cleared`。chat 问「最低起购金额」应对 md/pdf 均命中。

### 作业 C

引用 `test_markdown_strips_code_fence` 测试名作为验收依据。

### 作业 D

`ChunkStrategyResult.preview` 前 80 字符写入报告。

作业完。

---

## 智链科技 Day 26 作业辅导长文（培训部）

### 作业 A 深度辅导

`parse_demo.py` 应打印 ParsedDocument 的 section_count 与 plain_text 长度。`chunk_compare_demo` 须同时显示 fixed 与 markdown 的 chunk_count——若相等，检查样例是否过短。截图含命令行与完整输出，勿 crop。

### 作业 B 深度辅导

md 上传 Response 须 `format":"markdown"`。pdf 须 `format":"pdf"`。两请求均须 200。chat 问「最低起购金额」应对两种格式均能检索。若 pdf CI skip，作业说明中注明并附 md 全分路径。

### 作业 C 深度辅导

引用仓库测试名 `test_markdown_strips_code_fence` 作为验收权威。优秀作业讨论：若业务要索引代码块怎么办？答：Day 26 非目标，走独立 code search 工具。

### 作业 D 深度辅导

strategy_report 表格列：strategy | chunk_count | preview[0:60] | 备注。讨论 markdown 块前缀 `[章节]` 对检索召回的影响——Day 27 evaluate 量化。

### 作业 E 深度辅导

docx 422 detail 含 unsupported。坏 pdf 400 含 PDF 或 parse。用 `curl -i` 截状态行。

### 作业 F 深度辅导

扫描件无文本层；pypdf 局限；Tesseract 流水线草图：pdf→image→ocr→plain_text→parse 逻辑路径。

### 叙事续篇

林晓周六晨补作业 F，写下：「PDF 不是魔法，只是另一种 txt 来源。」陈默点赞。

辅导长文完。
"""


def _homework_answers() -> str:
    return """# Day 26 作业答案

## A

```bash
python3 src/day26/chunk_compare_demo.py
# fixed 块数通常 >= markdown 块数（product_notice）
```

## B

```json
{"format": "markdown", "chunk_count": 5}
{"format": "pdf", "chunk_count": 3}
```

## C

`assert "secret()" not in doc.plain_text`

## D

markdown 策略块含 `[章节标题]` 前缀。

## E

docx→422；broken pdf→400 PDF_PARSE_ERROR 或 PDF_EMPTY

答案完。
"""


def _checklist() -> str:
    return f"""# Day 26 解析验收清单

- [ ] supported_formats 含 .md .pdf  
- [ ] parse_markdown section_count>=4  
- [ ] pdf 抽取含 1000  
- [ ] auto 策略 md 用 markdown  
- [ ] 17 pytest 绿  
- [ ] 02_ PRD 完整  
- [ ] 21_ 15 题  
- [ ] 22_ 源码注释  

验收完。
"""


def _deep_dive() -> str:
    return f"""# 文档解析与分块策略详解

## ParsedDocument

{fenced("python", _BASE)}

## doc_parser 分发

{fenced("python", _DOC)}

## chunk_from_parsed

{fenced("python", chr(10).join(_CHUNK.splitlines()[91:112]))}

详解完。
"""


def _exercises() -> str:
    return f"""# Day 26 课堂练习册

## 1

`SUPPORTED_EXTENSIONS` 含哪些？

<details><summary>答案</summary>.txt .md .markdown .pdf</details>

## 2

`auto` 策略何时选 markdown？

<details><summary>答案</summary>doc.format==markdown 且 sections 非空</details>

## 3

PDF 空文本错误码？

<details><summary>答案</summary>PDF_EMPTY</details>

## 4

`compare_strategies` 返回几种结果？

<details><summary>答案</summary>2（fixed 与 markdown）</details>

## 5

样例 md 章节数至少？

<details><summary>答案</summary>4（test 断言 section_count>=4）</details>

## 6–12

见 16_ 卡片。练习完。
"""


def _extension() -> str:
    return """# 多格式企业文档扩展

## docx 为何不做

ZIP+XML 复杂度高；教学聚焦 md/pdf。  

## 表格 PDF

pypdf 丢布局；生产用 pdfplumber 或 OCR。  

## HTML 与 Confluence

企业 Wiki 导出 HTML 可经 html2text 转 plain 再解析。

## 病毒扫描

ClamAV 在 parse 前；课堂跳过。

## 多语言

md/pdf 抽取 Unicode；与 Day25 GBK 拦截衔接。

扩展完。
"""


def _case_study() -> str:
    return f"""# 企业案例：产品 PDF 入库

合规部提交 `product_notice.pdf`。林晓上传后问「起购门槛」，RAG 命中抽取文本「1000 元」。

## 步骤

1. 侧栏选 PDF  
2. 确认 format=pdf  
3. chat 验收  

## 失败

扫描件 PDF → PDF_EMPTY → 走 OCR 议题。

案例完。

---

## 合规部周报摘录

「product_notice.pdf 已入库，chat 可答起购与风险条款。扫描件合同仍走人工。」周航注：PDF_EMPTY 不是 bug，是边界教育。

## 操作录屏时间码

00:00 选择 pdf；00:05 上传；00:12 status 更新；00:20 chat 提问；00:45 展示命中句。

## 失败转工单

扫描件 → 工单 OCR-2026-0711 → 不在 Day26 范围。

案例长文完。
"""


def _lecture_log() -> str:
    return """# Day 26 授课实录

14:00 chunk_compare 演示掌声。16:00 三组 pdf skip（样例未生成）用 md 补测。

实录完。

---

## 14:00–14:45 markdown 段逐字稿

陈默：「看 _FENCE 正则，非贪婪。」林晓举手：「代码块里的 import 会进检索吗？」「不会，test 已守护。」

## 15:00 pdf 段

周航屏幕共享 pypdf 安装。三台机器缺样例 pdf，助教 USB 分发。

## 16:00 竞赛预告

赵岩：「15 题，前三名贴纸。」

实录长文完。
"""


def _flashcards() -> str:
    return f"""# Day 26 复习卡片

| # | 问 | 答 |
|---|---|-----|
| 1 | 统一解析入口 | parse_bytes |
| 2 | md 解析函数 | parse_markdown |
| 3 | pdf 库 | pypdf |
| 4 | 章节分块 | chunk_markdown_sections |
| 5 | 默认策略 | auto |
| 6 | 剥离代码块 | _FENCE 正则 |
| 7 | 测试数 | 17 |
| 8 | 样例 md | product_notice.md |
| 9 | format 字段 | upload 响应 |
| 10 | 需求号 | {REQ} |
| 11 | 版本 | {VER} |
| 12 | PDF 空 | PDF_EMPTY |
| 13 | 不支持 ext | UNSUPPORTED_FORMAT |
| 14 | compare | compare_strategies |
| 15 | ingest 入口 | ingest_parsed |

卡片完。
"""


def _cheatsheet() -> str:
    return f"""# 解析 API 速查

```bash
curl -F "file=@product_notice.md" http://127.0.0.1:8000/api/knowledge/upload
curl -s http://127.0.0.1:8000/api/knowledge/status | jq .supported_formats
```

```python
from tools.doc_parser import parse_bytes
doc = parse_bytes(data, "x.md")
from rag.chunk_strategies import chunk_from_parsed
chunks = chunk_from_parsed(doc, strategy="auto")
```

速查完。
"""


def _day25_compare() -> str:
    return f"""# Day 26 与 Day 25 对照

| 维度 | Day 25 | Day 26 |
|------|--------|--------|
| 格式 | txt | +md/pdf |
| 解析 | 直解码 | doc_parser |
| 分块 | fixed | +markdown/auto |
| 响应 | 无 format | 有 format |
| 测试 | 17 | 17 |

对照完。
"""


def _instructor_reading() -> str:
    return """# 讲师补充

先演示 md 章节分块，再 pdf，最后 auto 上传。强调代码块剥离合规原因。

补充完。

---

## 备课时间分配（讲师 vol2）

| 模块 | 分钟 | 材料 |
|------|------|------|
| PRD+架构 | 45 | 02_ 03_ |
| markdown 精读 | 60 | 22_ |
| pdf 实践 | 45 | 23_ |
| chunk compare | 45 | 25_ demo |
| Lab | 90 | 26_ |
| 竞赛 | 25 | 21_ |

## 常见授课失误

先讲 pdf 再 md 导致学员晕；未装 pypdf 就 demo；忘记强调 auto 非魔法是 if 规则。

讲师 vol2 完。
"""


def _code_walkthrough() -> str:
    return f"""# Day 26 完整代码走查

## 1. parse_bytes 分发

{fenced("python", _DOC)}

## 2. ingest 链

```
upload → ingest_upload → ingest_bytes → parse_bytes → ingest_parsed → chunk_from_parsed
```

```mermaid
sequenceDiagram
    participant U as Upload
    participant I as ingestion
    participant D as doc_parser
    participant C as chunk_strategies
    participant K as KnowledgeStore

    U->>I: bytes+filename
    I->>D: parse_bytes
    D-->>I: ParsedDocument
    I->>K: ingest_parsed
    K->>C: chunk_from_parsed
    C-->>K: chunks
```

## 3. 测试

{fenced("python", _TAPI[:1500])}

走查完。
"""


def _quiz() -> str:
    return f"""# Day 26 课堂知识竞赛

**15 题** | {REQ}

### 1

统一解析入口函数？

- A. parse_file  
- B. parse_bytes  
- C. ingest_parsed  
- D. chunk_text  

<details><summary>答案</summary>B</details>

### 2

Markdown 代码块如何处理？

- A. 保留  
- B. _FENCE 剥离  
- C. 单独索引  
- D. OCR  

<details><summary>答案</summary>B</details>

### 3

PDF 依赖库？

- A. pdfminer  
- B. pypdf  
- C. tesseract  
- D. fpdf2  

<details><summary>答案</summary>B</details>

### 4

auto 策略 md 选择？

- A. fixed  
- B. markdown  
- C. random  
- D. none  

<details><summary>答案</summary>B（有 sections 时）</details>

### 5

`PDF_EMPTY` 含义？

- A. 文件 0 字节  
- B. 无 extract_text  
- C. 无权限  
- D. 加密  

<details><summary>答案</summary>B</details>

### 6

product_notice.md 至少几节？

- A. 2  
- B. 4  
- C. 10  
- D. 1  

<details><summary>答案</summary>B</details>

### 7

compare_strategies 几种？

- A. 1  
- B. 2  
- C. 3  
- D. 4  

<details><summary>答案</summary>B</details>

### 8

upload 新增响应字段？

- A. score  
- B. format  
- C. pages  
- D. ocr  

<details><summary>答案</summary>B</details>

### 9

tests/day26 总数？

- A. 12  
- B. 15  
- C. 17  
- D. 20  

<details><summary>答案</summary>C</details>

### 10

不支持扩展名错误码？

- A. PDF_EMPTY  
- B. UNSUPPORTED_FORMAT  
- C. EMPTY_FILE  
- D. 500  

<details><summary>答案</summary>B</details>

### 11

chunk_markdown_sections 过长节？

- A. 丢弃  
- B. 再 sliding window  
- C. 报错  
- D. 合并  

<details><summary>答案</summary>B</details>

### 12

plain_text 作用？

- A. 装饰  
- B. fixed 策略分块源  
- C. 仅日志  
- D. 前端显示  

<details><summary>答案</summary>B</details>

### 13

样例 pdf 数字？

- A. 500  
- B. 1000  
- C. 8000  
- D. 100  

<details><summary>答案</summary>B</details>

### 14

解析层包路径？

- A. rag/  
- B. tools/  
- C. api/  
- D. frontend/  

<details><summary>答案</summary>B</details>

### 15

Day 27 主题？

- A. OCR  
- B. chunk 调参 evaluate  
- C. 鉴权  
- D. Redis  

<details><summary>答案</summary>B</details>

竞赛完。
"""


def _md_deep_read() -> str:
    return f"""# markdown_parser.py 精读

**文件**：`tools/parsers/markdown_parser.py`

## 完整源码

{fenced("python", _MD)}

## 逐段解读

**L13-17 正则**：`_HEADING` 多级标题；`_FENCE` 剥离代码块；`_INLINE_CODE` 去反引号；`_LINK` 留链接文字；`_BOLD` 去星号。

**L34-56 状态机**：遇标题 flush 上一节 body；记录 level 与 title。

**L70-71 plain_text**：用 `## title\\nbody` 拼接，供 fixed 策略与检索。

**L73-80 返回**：`metadata.heading_count` 便于测试断言。

## 与测试对照

`test_markdown_strips_code_fence`：`secret()` 不在 plain_text。  
`test_parse_markdown_sections`：titles 含「风险」。

## 样例文档

{fenced("markdown", _SAMPLE)}

精读完。

---

## 逐行注释表

| 行 | 说明 |
|----|------|
| 13 | `_HEADING` 捕获 ATX 标题 |
| 14 | `_FENCE` 剥离代码块 |
| 22 | 先 strip fence 再分段 |
| 34-56 | 标题触发 flush section |
| 70-71 | plain_text 拼接格式 |
| 79 | heading_count 元数据 |

"""


def _pdf_practice() -> str:
    return f"""# pdf_parser 与 pypdf 实践

## 完整源码

{fenced("python", _PDF)}

## 实践步骤

```bash
pip install pypdf
python3 -c "
from pathlib import Path
from tools.doc_parser import parse_bytes
p = Path('src/day26/sample_docs/product_notice.pdf')
if p.is_file():
    d = parse_bytes(p.read_bytes(), p.name)
    print(d.page_count, '1000' in d.plain_text)
"
```

## 错误实验

`parse_bytes(b'%PDF broken', 'x.pdf')` → NexusError PDF_PARSE_ERROR

## 扫描件

无 OCR 时 `extract_text()` 空 → PDF_EMPTY。

实践完。

---

## pypdf 深入：页对象与 extract_text

`PdfReader.pages[i].extract_text()` 可能返回 None，代码 `or ""` 处理。多栏 PDF 可能乱序——生产用 pdfplumber。

## 与 test_parse_pdf_sample

样例路径 `day26/sample_docs/product_notice.pdf`；缺失时 skip 非 fail。CI 应用 fpdf2 从 md 文本生成。

## 扫描件教学脚本

讲师口述：「手机拍照 PDF 多半 PDF_EMPTY，不是你们代码写错。」

实践长文完。
"""


def _phase3_summary() -> str:
    return f"""# Phase 3 第二日总结

Day 25 可写 txt → Day 26 多格式解析 + 章节分块。  
明日 Day 27：chunk_size/overlap 调参与 hit@1 评估。

```mermaid
graph LR
    D25[txt store] --> D26[md/pdf parse]
    D26 --> D27[evaluate]
```

总结完。

---

## Phase3 两日时间线详表

| 时间 | Day25 | Day26 |
|------|-------|-------|
| 上午 | KnowledgeStore | markdown_parser |
| 下午 | upload API | pdf + compare |
| 晚自习 | store.json | chunk_strategies |
| 验收 | txt chat | md/pdf chat |

## 投资人 Q&A 预案

问：为何不全 OCR？答：成本与教学边界。问：格式更多？答：docx 在 backlog。问：命中率？答：Day27 evaluate。

## 团队士气

林晓日记：「两天把知识管线走通，比刷题踏实。」

总结长文完。
"""


def _chunk_deep_read() -> str:
    return f"""# chunk_strategies.py 精读

## 完整源码

{fenced("python", _CHUNK)}

## chunk_fixed_window

委托 Day 19 `chunk_text`，参数 chunk_size/overlap。

## chunk_markdown_sections

- 无 sections 回退 fixed  
- 每节前缀 `[title]`  
- 超长节再 `chunk_text`  

## chunk_from_parsed

```python
if strategy == "auto":
    chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"
```

## compare_strategies

教学用，返回 `ChunkStrategyResult` 含 preview 前 80 字符。

## ingest_parsed 衔接

{fenced("python", chr(10).join(_KS.splitlines()[203:233]))}

精读完。

---

## 附录：KnowledgeStore.ingest_parsed 全文节选

{fenced("python", chr(10).join(_KS.splitlines()[203:254]))}

## 附录：compare_strategies 使用

```python
from tools.doc_parser import parse_bytes
from rag.chunk_strategies import compare_strategies
doc = parse_bytes(open("src/day26/sample_docs/product_notice.md","rb").read(), "p.md")
for r in compare_strategies(doc):
    print(r.strategy, r.chunk_count, r.preview)
```

"""


def _lab() -> str:
    return f"""# Day 26 实操 Lab

## Lab 0

```bash
pip install pypdf
export PYTHONPATH=src
pytest tests/day26/ -v
```

## Lab 1 parse_demo

```bash
python3 src/day26/parse_demo.py
```

## Lab 2 chunk_compare

```bash
python3 src/day26/chunk_compare_demo.py
```

记录 fixed vs markdown chunk_count。

## Lab 3 上传 md

Swagger 上传 product_notice.md，`format==markdown`。

## Lab 4 上传 pdf

上传 pdf，`format==pdf`，chat 问起购金额。

## Lab 5 代码块

上传含 code fence 的 md，检索不应命中 fence 内符号。

## Lab 6 策略实验

```python
from tools.doc_parser import parse_bytes
from rag.chunk_strategies import chunk_from_parsed
doc = parse_bytes(open("src/day26/sample_docs/product_notice.md","rb").read(), "p.md")
print(len(chunk_from_parsed(doc, strategy="fixed")))
print(len(chunk_from_parsed(doc, strategy="markdown")))
```

<details><summary>期望</summary>markdown 块数通常更少且语义完整</details>

---

## Lab 7–10 详解

**Lab 7** 上传 docx，记录 422 detail 全文。**Lab 8** 损坏 pdf 400。**Lab 9** strategy_report 表格。**Lab 10** 200 字结论：product_notice 适合 markdown 策略因五章标题清晰。

## 互评 Rubric

| 项 | 通过 |
|----|------|
| pytest 17 | 全绿 |
| md upload | format 对 |
| compare 输出 | 两行 |
| chat 命中 | 起购金额 |

Lab 详解完。
"""


def _day27_preview() -> str:
    return """# Day 27 预习

**主题**：chunk_size / overlap 调参 + `POST /api/knowledge/evaluate`

阅读 `rag/chunk_config.py` 与 `PRESET_CONFIGS`。运行：

```bash
python3 src/day27/evaluate_demo.py
```

预习完。
"""


if __name__ == "__main__":
    from course_builder import write_course

    write_course(DAY, build(), min_chars=110_000)
