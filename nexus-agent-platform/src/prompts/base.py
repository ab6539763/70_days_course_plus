"""
Prompt 模板基类 — 变量插值与校验

使用 Python str.format 风格占位符 `{variable}`。
Day 17 标准库实现；Day 18 将扩展少样本与意图分类模板。

需求：ZL-NA-REQ-017
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.exceptions import ConfigError
from models import ChatMessage

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def extract_variables(template: str) -> tuple[str, ...]:
    """从模板字符串提取占位符变量名（去重保序）"""
    seen: set[str] = set()
    result: list[str] = []
    for match in _PLACEHOLDER_RE.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return tuple(result)


@dataclass
class PromptTemplate:
    """
    可复用 Prompt 模板

    Attributes:
        name: 模板唯一标识
        template: 含 {var} 占位符的文本
        description: 用途说明
        required_vars: 必填变量；默认从 template 自动推断
    """

    name: str
    template: str
    description: str = ""
    required_vars: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("模板 name 不能为空")
        if not self.template.strip():
            raise ValueError("模板 template 不能为空")
        if not self.required_vars:
            object.__setattr__(self, "required_vars", extract_variables(self.template))

    def render(self, **variables: str) -> str:
        """
        渲染模板，填充变量。

        Raises:
            ConfigError: 缺少必填变量
        """
        missing = [v for v in self.required_vars if v not in variables]
        if missing:
            raise ConfigError(f"模板 {self.name!r} 缺少变量: {missing}")

        try:
            return self.template.format(**variables)
        except KeyError as exc:
            raise ConfigError(f"模板 {self.name!r} 渲染失败: {exc}") from exc

    def render_safe(self, **variables: str) -> tuple[str | None, str | None]:
        """渲染模板，返回 (结果, 错误消息)"""
        try:
            return self.render(**variables), None
        except ConfigError as exc:
            return None, exc.message

    def to_system_message(self, **variables: str) -> ChatMessage:
        """渲染为 system 角色 ChatMessage"""
        return ChatMessage("system", self.render(**variables))

    def preview(self, **variables: str) -> str:
        """渲染预览（未提供的变量用 <占位> 标记）"""
        filled = {v: variables.get(v, f"<{v}>") for v in self.required_vars}
        return self.template.format(**filled)

    def __repr__(self) -> str:
        return f"PromptTemplate(name={self.name!r}, vars={self.required_vars})"
