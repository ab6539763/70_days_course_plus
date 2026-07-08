"""
Prompt 模板注册表 — 按名称查找与加载文件模板

需求：ZL-NA-REQ-017
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import ConfigError, StorageError
from core.paths import get_path
from prompts.base import PromptTemplate, extract_variables
from prompts.library import BUILTIN_TEMPLATES


class PromptRegistry:
    """模板注册中心，支持内置 + 文件扩展"""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = dict(BUILTIN_TEMPLATES)

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise ConfigError(
                f"未知模板: {name!r}，可用: {sorted(self._templates)}"
            )
        return self._templates[name]

    def list_names(self) -> list[str]:
        return sorted(self._templates)

    def load_from_file(self, path: Path, *, name: str | None = None) -> PromptTemplate:
        """从 .txt / .md 文件加载模板（首行可为 # 描述注释）"""
        if not path.exists():
            raise StorageError(f"模板文件不存在: {path}", path=str(path))
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        description = ""
        body_lines = lines
        if lines and lines[0].startswith("# "):
            description = lines[0][2:].strip()
            body_lines = lines[1:]
        template_body = "\n".join(body_lines).strip()
        tmpl_name = name or path.stem
        tmpl = PromptTemplate(
            name=tmpl_name,
            template=template_body,
            description=description,
            required_vars=extract_variables(template_body),
        )
        self.register(tmpl)
        return tmpl

    def load_directory(self, directory: Path | None = None) -> int:
        """加载目录下所有 .txt 模板，返回加载数量"""
        directory = directory or get_path("prompts_dir")
        if not directory.exists():
            return 0
        count = 0
        for path in sorted(directory.glob("*.txt")):
            self.load_from_file(path)
            count += 1
        return count


# 全局默认注册表
default_registry = PromptRegistry()
default_registry.load_directory()
