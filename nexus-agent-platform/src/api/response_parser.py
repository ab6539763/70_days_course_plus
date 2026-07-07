"""
解析 handle_message 返回字符串 → kind / meta

与 frontend/app.js parseReply 语义对齐。

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

import re

_ROUTE_RE = re.compile(r"^\[路由:\s*([^\]]+)\]\s*(.*)$", re.DOTALL)


def classify_reply(reply: str) -> tuple[str, str]:
    """
    根据 reply 前缀推断 kind 与 meta。

    Returns:
        (kind, meta) — kind 为 faq | route | system | llm
    """
    text = (reply or "").strip()
    if not text:
        return "system", "空回复"
    if text.startswith("[FAQ"):
        return "faq", "FAQ 直答"
    if text.startswith("[FAQ 直答"):
        return "faq", "FAQ 直答"
    match = _ROUTE_RE.match(text)
    if match:
        template = match.group(1).strip()
        return "route", f"路由 · {template}"
    if text.startswith("请输入"):
        return "system", "系统提示"
    if text.startswith("配置错误") or text.startswith("API 调用失败"):
        return "error", "错误"
    return "llm", "LLM 回复"
