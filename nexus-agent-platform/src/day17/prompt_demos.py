"""
PromptTemplate 基础演示

运行：python3 src/day17/prompt_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prompts import DEFAULT_ASSISTANT, DOC_SUMMARY, RAG_QA


def main() -> None:
    print("=== Prompt 模板渲染演示 ===\n")

    print("1. default_assistant:")
    print(DEFAULT_ASSISTANT.render(company="智链科技"))

    print("\n2. rag_qa preview:")
    print(
        RAG_QA.preview(
            company="智链科技",
            context="理财产品年化收益率 3.5%-4.2%",
        )[:200]
        + "..."
    )

    print("\n3. doc_summary:")
    print(
        DOC_SUMMARY.render(
            max_points="3",
            document="NexusAgent 是企业级 AI 平台。",
        )
    )


if __name__ == "__main__":
    main()
