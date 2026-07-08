"""Day 35 常量"""

DAY = 35
REQ_ID = "ZL-NA-REQ-035"
PLATFORM_VERSION = "0.35.0"

EXPANSION_QUERIES = (
    {"query": "理财安全吗", "expect_queries_min": 2, "expect_any": ("风险", "投资")},
    {"query": "年化收益怎么样", "expect_queries_min": 2, "expect_any": ("年化", "收益")},
    {"query": "客服电话多少", "expect_queries_min": 2, "expect_any": ("联系", "客服", "电话")},
)
