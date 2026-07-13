"""Day 44 常量"""

REQ_ID = "ZL-NA-REQ-044"
PLATFORM_VERSION = "0.44.0"

MCP_CASES = [
    {"query": "客服电话多少", "expect_tool": "faq_lookup"},
    {"query": "年化收益怎么样", "expect_tool": "rag_search"},
    {"query": "帮我总结一下理财产品", "expect_tool": "intent_classify"},
]
