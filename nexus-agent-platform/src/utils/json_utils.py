"""
JSON 读写工具

从 Day 5 todo_storage 抽取的通用 JSON 文件操作。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any = None) -> Any:
    """
    安全加载 JSON 文件

    Args:
        path: 文件路径
        default: 文件不存在或解析失败时的返回值

    Returns:
        解析后的 Python 对象，或 default
    """
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """
    将数据写入 JSON 文件

    Args:
        path: 目标路径
        data: 可序列化对象
        indent: 缩进空格数
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def ensure_dict_keys(data: dict, defaults: dict) -> dict:
    """
    确保 dict 包含指定键，缺失则用 defaults 补全

    Args:
        data: 待补全字典
        defaults: 默认键值

    Returns:
        补全后的同一 dict（原地修改并返回）
    """
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    return data
