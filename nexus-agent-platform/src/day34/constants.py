"""Day 34 常量"""

DAY = 34
REQ_ID = "ZL-NA-REQ-034"
PLATFORM_VERSION = "0.34.0"

CITATION_QUERIES = (
    {"query": "年化收益率是多少", "expect_source_any": ("notice", "raw_")},
    {"query": "那个理财能赚多少", "expect_rewrite_contains": "年化"},
    {"query": "投资有风险吗", "expect_citation_contains": ("风险", "谨慎")},
)
