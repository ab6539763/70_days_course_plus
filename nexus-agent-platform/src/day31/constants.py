"""Day 31 常量"""

DAY = 31
REQ_ID = "ZL-NA-REQ-031"
PLATFORM_VERSION = "0.31.0"

# 混合检索对比问句 — keyword 腿更易命中精确 token
HYBRID_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
