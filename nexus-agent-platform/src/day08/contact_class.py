"""
向后兼容 — Day 8 contact_class 已迁移至 models.contact

请在新代码中使用：from models.contact import Contact
"""

from __future__ import annotations

from models.contact import Contact

__all__ = ["Contact"]
