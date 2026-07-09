"""Day 42 常量"""

REQ_ID = "ZL-NA-REQ-042"
PLATFORM_VERSION = "0.42.0"

APPROVAL_CASES = [
    {"query": "客服电话多少", "expect_tool": "faq_lookup", "needs_approval": False},
    {"query": "年化收益怎么样", "expect_tool": "rag_search", "needs_approval": True},
]
