"""
ReAct 文本解析 — Thought / Action / Final Answer

需求：ZL-NA-REQ-039
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_ACTION_INPUT_RE = re.compile(
    r"Action Input:\s*(\{.*?\})\s*$",
    re.MULTILINE | re.DOTALL,
)
_FINAL_ANSWER_RE = re.compile(
    r"Final Answer:\s*(.+)$",
    re.MULTILINE | re.DOTALL,
)
_THOUGHT_RE = re.compile(r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|$)", re.DOTALL)
_ACTION_RE = re.compile(r"Action:\s*(\S+)")


@dataclass(frozen=True)
class ReactParseResult:
    thought: str
    action: str | None = None
    action_input: dict | None = None
    final_answer: str | None = None


def parse_react_block(text: str) -> ReactParseResult:
    """解析单步 ReAct 文本块"""
    text = (text or "").strip()
    thought_m = _THOUGHT_RE.search(text)
    thought = thought_m.group(1).strip() if thought_m else ""

    final_m = _FINAL_ANSWER_RE.search(text)
    if final_m:
        return ReactParseResult(
            thought=thought,
            final_answer=final_m.group(1).strip(),
        )

    action_m = _ACTION_RE.search(text)
    if not action_m:
        raise ValueError("缺少 Action 或 Final Answer")

    action = action_m.group(1).strip()
    action_input: dict = {}
    input_m = _ACTION_INPUT_RE.search(text)
    if input_m:
        action_input = json.loads(input_m.group(1))

    return ReactParseResult(thought=thought, action=action, action_input=action_input)
