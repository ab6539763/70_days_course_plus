"""
NexusAgent 统一异常体系

分层异常便于上层捕获与日志分类。Day 23 FastAPI 将映射为 HTTP 状态码。

需求：ZL-NA-REQ-010

作者：NexusAgent 项目组
创建日期：2026-07-15
"""

from __future__ import annotations


class NexusError(Exception):
    """NexusAgent 平台所有业务异常的基类"""

    def __init__(self, message: str, *, code: str = "NEXUS_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigError(NexusError):
    """配置缺失或非法"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFIG_ERROR")


class ModelError(NexusError):
    """领域模型相关错误"""

    def __init__(self, message: str, *, code: str = "MODEL_ERROR") -> None:
        super().__init__(message, code=code)


class ModelValidationError(ModelError, ValueError):
    """
    模型校验失败

    继承 ValueError 以兼容 Day 9 代码与 except ValueError 捕获。
    """

    def __init__(self, message: str, *, model_type: str = "BaseModel") -> None:
        self.model_type = model_type
        super().__init__(f"[{model_type}] {message}", code="MODEL_VALIDATION")


class StorageError(NexusError):
    """文件/数据库读写错误"""

    def __init__(self, message: str, *, path: str | None = None) -> None:
        self.path = path
        detail = f"{message} (path={path})" if path else message
        super().__init__(detail, code="STORAGE_ERROR")


class JsonParseError(StorageError):
    """JSON 解析或格式错误"""

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message, path=path)
        self.code = "JSON_PARSE_ERROR"


class ImportPathError(NexusError):
    """模块导入或 PYTHONPATH 配置错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="IMPORT_PATH_ERROR")
