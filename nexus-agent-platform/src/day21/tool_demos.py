"""
工具注册与执行演示

运行：python3 src/day21/tool_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.token_counter import TokenCounter
from prompts import IntentRouter
from rag import RAGContextService
from services import SimilarQuestionMatcher
from tools import ToolExecutor, build_nexus_tools


def main() -> int:
    rag = RAGContextService.from_sample_docs(use_embedding=True)
    faq = SimilarQuestionMatcher()
    router = IntentRouter(query_context_provider=rag.retrieve_context)

    registry = build_nexus_tools(
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        token_counter=TokenCounter(),
    )
    executor = ToolExecutor(registry)

    print("=== 工具注册表演示 ===\n")
    print(executor.list_help())
    print()

    demos = [
        ("faq_lookup", {"query": "投资回报率怎么算"}),
        ("rag_search", {"query": "年化收益率", "top_k": 2}),
        ("intent_classify", {"text": "请审阅宣传语是否合规"}),
        ("estimate_tokens", {"text": "智链科技 NexusAgent 测试"}),
    ]

    for name, args in demos:
        result = executor.execute(name, args)
        print(result.summary())
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
