"""
Day 4 常量
"""

APP_NAME = "NexusAgent 待办管理器"
APP_VERSION = "0.4.0"

# 优先级
PRIORITY_HIGH = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW = 3

PRIORITY_LABELS = {
    PRIORITY_HIGH: "高",
    PRIORITY_MEDIUM: "中",
    PRIORITY_LOW: "低",
}

VALID_PRIORITIES = frozenset({1, 2, 3})

# 待办 list 索引（Day 5 改为 dict 键名）
IDX_ID = 0
IDX_TITLE = 1
IDX_DESC = 2
IDX_PRIORITY = 3
IDX_DONE = 4
