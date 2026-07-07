"""
平台路径常量 — 集中管理数据文件与源码根路径

避免各 dayXX 模块硬编码相对路径。

需求：ZL-NA-REQ-010
"""

from __future__ import annotations

from pathlib import Path

# src/ 目录（本文件位于 src/core/paths.py）
SRC_ROOT = Path(__file__).resolve().parent.parent

# 项目根 nexus-agent-platform/
PROJECT_ROOT = SRC_ROOT.parent

# 数据目录
DATA_ROOT = SRC_ROOT / "data"

# 各模块数据文件（逐步从 dayXX/data 迁移）
PATHS = {
    "todos": SRC_ROOT / "day05" / "data" / "todos.json",
    "contacts": SRC_ROOT / "day07" / "data" / "contacts.json",
    "messages": SRC_ROOT / "day08" / "data" / "messages.json",
    "sample_docs": SRC_ROOT / "day02" / "sample_docs",
    "doc_output": SRC_ROOT / "day11" / "output",
    "knowledge_store": DATA_ROOT / "knowledge" / "store.json",
    "knowledge_chroma": DATA_ROOT / "knowledge" / "chroma",
    "knowledge_uploads": DATA_ROOT / "knowledge" / "uploads",
    "chat_completion_sample": SRC_ROOT / "day05" / "sample_data" / "chat_completion.json",
    "chat_session": SRC_ROOT / "day14" / "data" / "chat_session.json",
    "stream_mock_sse": SRC_ROOT / "llm" / "sample_data" / "stream_mock.sse",
    "prompts_dir": SRC_ROOT / "prompts" / "templates",
}

# 未来生产包占位
LLM_PKG = SRC_ROOT / "llm"
CHAT_PKG = SRC_ROOT / "chat"
TOOLS_PKG = SRC_ROOT / "tools"
SERVICES_PKG = SRC_ROOT / "services"


def get_path(key: str) -> Path:
    """
    按 key 获取路径

    Raises:
        ConfigError: key 不存在
    """
    from core.exceptions import ConfigError

    if key not in PATHS:
        raise ConfigError(f"未知路径键: {key!r}，可用: {list(PATHS)}")
    return PATHS[key]
