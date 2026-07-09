"""Day 32 常量"""

DAY = 32
REQ_ID = "ZL-NA-REQ-032"
PLATFORM_VERSION = "0.32.0"

# rerank 对比问句 — 精排应提升精确命中 chunk 的排名
RERANK_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
