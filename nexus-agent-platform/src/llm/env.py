"""
LLM 环境变量加载

从 os.environ 与可选 .env 文件读取 API Key、Base URL。
Day 12 使用标准库，不引入 python-dotenv。

需求：ZL-NA-REQ-012
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from core.exceptions import ConfigError
from core.paths import PROJECT_ROOT

ENV_API_KEY = "DEEPSEEK_API_KEY"
ENV_BASE_URL = "DEEPSEEK_BASE_URL"
ENV_MOCK = "NEXUS_LLM_MOCK"

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"


@dataclass
class LLMEnvConfig:
    """LLM 连接配置（来自环境变量）"""

    api_key: str
    base_url: str
    mock: bool = False

    @property
    def chat_completions_url(self) -> str:
        base = self.base_url.rstrip("/")
        return f"{base}/chat/completions"


def parse_env_file(path: Path) -> dict[str, str]:
    """
    简易 .env 解析器（KEY=VALUE，忽略 # 注释与空行）

    不覆盖已存在于 os.environ 的键。
    """
    result: dict[str, str] = {}
    if not path.exists():
        return result

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def load_llm_env(*, env_file: Path | None = None) -> LLMEnvConfig:
    """
    加载 LLM 环境配置。

    优先级：os.environ > .env 文件

    Raises:
        ConfigError: 非 mock 模式且缺少 API Key
    """
    env_path = env_file or PROJECT_ROOT / ".env"
    file_vars = parse_env_file(env_path)

    def _get(key: str, default: str = "") -> str:
        return os.environ.get(key, file_vars.get(key, default))

    mock_raw = _get(ENV_MOCK, "0").lower()
    mock = mock_raw in ("1", "true", "yes", "on")

    api_key = _get(ENV_API_KEY, "")
    base_url = _get(ENV_BASE_URL, DEFAULT_BASE_URL) or DEFAULT_BASE_URL

    if not mock and not api_key:
        raise ConfigError(
            f"缺少 {ENV_API_KEY}。请复制 .env.example 为 .env 并填入 API Key，"
            f"或设置 {ENV_MOCK}=1 使用离线 Mock 模式。"
        )

    return LLMEnvConfig(api_key=api_key, base_url=base_url, mock=mock)
