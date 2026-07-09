"""Day 27 常量"""

DAY = 27
REQ_ID = "ZL-NA-REQ-027"
PLATFORM_VERSION = "0.27.0"

# 检索质量评估问句 — hit@1 检查 top 块是否含 expect_any 关键词
EVAL_QUERIES = (
    {
        "query": "最低起购金额是多少",
        "expect_any": ["1000", "起购"],
        "label": "起购门槛",
    },
    {
        "query": "年化收益率多少",
        "expect_any": ["8%", "收益", "年化"],
        "label": "收益率",
    },
    {
        "query": "投资有什么风险",
        "expect_any": ["风险", "谨慎"],
        "label": "风险提示",
    },
    {
        "query": "赎回多久到账",
        "expect_any": ["T+1", "到账", "赎回"],
        "label": "赎回规则",
    },
)
