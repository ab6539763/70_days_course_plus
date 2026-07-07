"""
RAG Prompt + doc_reader 联演示

运行：NEXUS_LLM_MOCK=1 python3 src/day17/rag_prompt_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from core.paths import get_path
from llm import LLMClient
from llm.env import LLMEnvConfig
from models import ChatMessage, ModelConfig
from prompts import RAG_QA
from tools.doc_reader import read_document


def main() -> int:
    print("=" * 52)
    print("  RAG Prompt + 文档上下文演示")
    print("=" * 52)

    doc = read_document(get_path("sample_docs") / "raw_notice.txt", clean=True)
    context = doc.cleaned or doc.content

    system = RAG_QA.to_system_message(company="智链科技", context=context[:300])
    user = ChatMessage("user", "这份文档的核心信息是什么？")

    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env)
    result = client.complete([system, user])

    print(f"\n  system 长度: {len(system.content)} 字符")
    print(f"  助手: {result.message.content[:120]}...")
    print(f"  {result.usage_summary()}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
