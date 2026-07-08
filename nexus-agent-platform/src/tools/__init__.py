"""NexusAgent 工具层 — 文档读取、工具注册与执行（Day 11+）"""

from tools.doc_reader import (
    DocumentRecord,
    batch_clean_directory,
    iter_text_files,
    read_document,
    read_documents,
    read_text_file,
    write_cleaned_documents,
)
from tools.executor import ToolExecutor
from tools.tool_registry import (
    ToolDefinition,
    ToolRegistry,
    ToolResult,
    build_nexus_tools,
    parse_tool_arguments,
)

__all__ = [
    "DocumentRecord",
    "batch_clean_directory",
    "iter_text_files",
    "read_document",
    "read_documents",
    "read_text_file",
    "write_cleaned_documents",
    "ToolDefinition",
    "ToolRegistry",
    "ToolResult",
    "ToolExecutor",
    "build_nexus_tools",
    "parse_tool_arguments",
]
