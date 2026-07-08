"""
跨 Day 模块加载器

培训期间各 day 目录独立存放代码，同名模块（如 constants.py）会冲突。
本模块使用 importlib 按路径加载，模块名加 day 前缀避免 sys.modules 污染。

Day 10 包重构后，将改为正规包导入：
    from nexus.preprocessing import clean_text

作者：NexusAgent 项目组
创建日期：2026-07-08
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

# src/ 根目录
_SRC_ROOT = Path(__file__).resolve().parent.parent


def load_day_module(day: str, module_name: str) -> ModuleType:
    """
    从指定 day 目录加载 Python 模块

    Args:
        day: 目录名，如 "day01"、"day02"
        module_name: 文件名（不含 .py），如 "personal_info_card"

    Returns:
        已加载的模块对象

    Raises:
        FileNotFoundError: 模块文件不存在

    Example:
        >>> card = load_day_module("day01", "personal_info_card")
        >>> card.main()
    """
    module_path = _SRC_ROOT / day / f"{module_name}.py"

    if not module_path.exists():
        raise FileNotFoundError(f"模块不存在: {module_path}")

    # 使用唯一模块名避免与已缓存的同名模块冲突
    unique_name = f"nexus_{day}_{module_name}"
    spec = importlib.util.spec_from_file_location(unique_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_src_root() -> Path:
    """返回 src/ 根目录路径"""
    return _SRC_ROOT
