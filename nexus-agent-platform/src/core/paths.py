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
