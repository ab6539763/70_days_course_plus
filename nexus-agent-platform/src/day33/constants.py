"""Day 33 常量"""

DAY = 33
REQ_ID = "ZL-NA-REQ-033"
PLATFORM_VERSION = "0.33.0"

# 口语问句 → 规则改写后应含的关键词
REWRITE_QUERIES = (
    {"query": "那个理财能赚多少", "expect_rewrite_contains": "年化"},
    {"query": "客服电话多少", "expect_rewrite_contains": "联系"},
    {"query": "有风险吗", "expect_rewrite_contains": "风险"},
)
