"""
Day 3 常量

平台 CLI Shell 版本号、菜单配置、路径常量。
"""

PLATFORM_CLI_VERSION = "0.3.0"
PLATFORM_NAME = "NexusAgent 平台工具箱"

# 合法菜单选项
VALID_MENU_CHOICES = frozenset({"0", "1", "2", "3", "4", "5", "6", "7"})

# 猜数字游戏配置
GUESS_MIN = 1
GUESS_MAX = 100
GUESS_MAX_ATTEMPTS = 10

# 相对路径（基于 src/ 目录）
SAMPLE_DOCS_REL = "day02/sample_docs"
OUTPUT_DIR_REL = "day03/output"
