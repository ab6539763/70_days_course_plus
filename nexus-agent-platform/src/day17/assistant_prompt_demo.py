"""
ChatAssistant + Prompt 模板演示

运行：NEXUS_LLM_MOCK=1 python3 src/day17/assistant_prompt_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from chat import ChatAssistant
from prompts import DEFAULT_ASSISTANT


def main() -> int:
    print("=== ChatAssistant + PromptTemplate ===\n")
    assistant = ChatAssistant(
        prompt_template=DEFAULT_ASSISTANT,
        template_variables={"company": "智链科技"},
        track_tokens=False,
    )

    outputs = assistant.run_scripted([
        "/template list",
        "你好，请自我介绍。",
        "/exit",
    ])
    for line in outputs:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
