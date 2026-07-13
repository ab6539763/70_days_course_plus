"""Day 36 常量"""

DAY = 36
REQ_ID = "ZL-NA-REQ-036"
PLATFORM_VERSION = "0.36.0"

ROUTE_QUERIES = (
    {"query": "客服电话多少", "expect_intent": "faq_fast", "expect_expand": False},
    {"query": "年化收益怎么样", "expect_intent": "rag_standard", "expect_expand": False},
    {"query": "理财安全吗", "expect_intent": "rag_wide", "expect_expand": True},
)
