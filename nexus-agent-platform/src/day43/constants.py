"""Day 43 常量"""

REQ_ID = "ZL-NA-REQ-043"
PLATFORM_VERSION = "0.43.0"

SUPERVISOR_CASES = [
    {"query": "客服电话多少", "expect_agent": "faq_worker", "expect_tool": "faq_lookup"},
    {"query": "年化收益怎么样", "expect_agent": "rag_worker", "expect_tool": "rag_search"},
    {"query": "帮我总结一下理财产品", "expect_agent": "intent_worker", "expect_tool": "intent_classify"},
]
