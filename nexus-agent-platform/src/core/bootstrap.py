"""
运行时引导 — PYTHONPATH 与包初始化

需求：ZL-NA-REQ-010
"""

from __future__ import annotations

import sys
from pathlib import Path

from core.paths import SRC_ROOT


def setup_python_path(extra: Path | None = None) -> Path:
    """
    将 src/ 加入 sys.path（若尚未加入）

    Returns:
        SRC_ROOT 路径
    """
    roots = [str(SRC_ROOT)]
    if extra:
        roots.insert(0, str(extra))
    for root in roots:
        if root not in sys.path:
            sys.path.insert(0, root)
    return SRC_ROOT


def ensure_importable(*module_names: str) -> None:
    """
    验证模块可导入，否则抛 ImportPathError

    Args:
        module_names: 如 "models", "utils", "core"
    """
    from core.exceptions import ImportPathError

    setup_python_path()
    missing = []
    for name in module_names:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        raise ImportPathError(
            f"无法导入模块 {missing}。请从 nexus-agent-platform 运行并设置 PYTHONPATH=src"
        )
