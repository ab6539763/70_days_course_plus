"""
Sprint 3 周测 — Day 15-20 知识点自测

共 10 题，每题 10 分。覆盖 Token、流式、Prompt、意图、RAG、Embedding。

运行：python3 src/day21/sprint3_quiz.py
CI：python3 src/day21/sprint3_quiz.py --scripted
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_DAY21 = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("day21_constants_quiz", _DAY21 / "constants.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

QUESTIONS: list[dict] = [
    {
        "q": "Token 是大模型计费与上下文窗口的基本计量单位，中文粗略估算约几个字 1 token？",
        "options": ["1 字", "1.5-2 字", "5 字", "10 字"],
        "answer": 1,
        "explain": "中文约 1.5-2 字 / token，具体因分词器而异。",
    },
    {
        "q": "SSE 流式响应中，每条 data 行的典型格式是？",
        "options": ["data: {json}", "event: stream", "chunk: text", "body: raw"],
        "answer": 0,
        "explain": "Server-Sent Events 使用 data: 前缀承载 JSON 块。",
    },
    {
        "q": "PromptTemplate.render 缺少必填变量时会抛出？",
        "options": ["ValueError", "ConfigError", "APIError", "KeyError"],
        "answer": 1,
        "explain": "项目统一用 ConfigError 表示配置/模板变量缺失。",
    },
    {
        "q": "IntentRouter 为 rag_qa 按用户问题检索上下文应使用？",
        "options": ["context_provider", "query_context_provider", "default_registry", "auto_route"],
        "answer": 1,
        "explain": "query_context_provider(query) 支持按查询动态检索。",
    },
    {
        "q": "文档分块 overlap 参数的主要作用是？",
        "options": ["压缩文件", "避免语义在块边界断裂", "加密", "去重"],
        "answer": 1,
        "explain": "重叠窗口减少关键信息被切在两块之间导致检索丢失。",
    },
    {
        "q": "相对 KeywordRetriever，EmbeddingRetriever 的主要优势是？",
        "options": ["更快", "同义表达语义召回", "无需索引", "可解释性更高"],
        "answer": 1,
        "explain": "向量余弦相似度能匹配「投资回报率」与「年化收益」等同义表述。",
    },
    {
        "q": "cosine_similarity 对非零向量取值范围约为？",
        "options": ["0 到 1", "-1 到 1", "0 到 100", "任意实数"],
        "answer": 1,
        "explain": "余弦相似度理论范围 [-1, 1]，文本向量多为非负故常见 [0, 1]。",
    },
    {
        "q": "ChatAssistant 的 /similar 命令调用的是？",
        "options": ["KeywordRetriever", "SimilarQuestionMatcher", "IntentRouter", "StreamingLLMClient"],
        "answer": 1,
        "explain": "/similar 预览 FAQ 相似问题匹配结果。",
    },
    {
        "q": "RAGContextService.from_sample_docs(use_embedding=True) 注入的检索器是？",
        "options": ["KeywordRetriever", "EmbeddingRetriever", "doc_reader", "PromptRegistry"],
        "answer": 1,
        "explain": "use_embedding=True 切换为 EmbeddingRetriever。",
    },
    {
        "q": "Day 21 Sprint 3 周测整合的核心能力是？",
        "options": ["仅多轮对话", "FAQ+RAG+意图+工具编排", "仅向量库", "Docker 部署"],
        "answer": 1,
        "explain": "Day 21 将 Day 15-20 能力通过 ChatOrchestrator 与 ToolRegistry 串联。",
    },
]


def run_quiz_scripted(answers: list[int] | None = None) -> int:
    """非交互评分（供 CI 与单元测试）"""
    if answers is None:
        answers = [q["answer"] for q in QUESTIONS]
    score = 0
    for i, (item, ans) in enumerate(zip(QUESTIONS, answers)):
        if ans == item["answer"]:
            score += 10
    return score


def run_quiz() -> int:
    print("=" * 48)
    print("  NexusAgent Sprint 3 周测（Day 15-20）")
    print("=" * 48)
    score = 0
    for i, item in enumerate(QUESTIONS, 1):
        print(f"\n第 {i} 题：{item['q']}")
        for j, opt in enumerate(item["options"]):
            print(f"  {j}. {opt}")
        raw = input("你的答案（数字）：").strip()
        if raw.isdigit() and int(raw) == item["answer"]:
            print("  ✅ 正确")
            score += 10
        else:
            correct = item["options"][item["answer"]]
            print(f"  ❌ 正确答案：{item['answer']}. {correct}")
            print(f"     解析：{item['explain']}")
    print("\n" + "=" * 48)
    print(f"  得分：{score} / 100")
    if score >= C.QUIZ_PASS_SCORE:
        print("  🎉 及格！Sprint 3 前半程验收通过。")
    else:
        print("  📚 建议复习 Day 15-20 课件后再测。")
    print("=" * 48)
    return score


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--scripted" in argv:
        score = run_quiz_scripted()
        print(f"Sprint3 quiz scripted score: {score}/100")
        return 0 if score >= C.QUIZ_PASS_SCORE else 1
    run_quiz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
