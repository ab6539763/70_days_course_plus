"""Day 37 常量"""

DAY = 37
REQ_ID = "ZL-NA-REQ-037"
PLATFORM_VERSION = "0.37.0"

VALIDATION_CASES = (
    {
        "query": "客服电话多少",
        "reply": "客服热线是 400-888-1234，工作日 9:00-18:00 可拨打。",
        "expect_passed": True,
    },
    {
        "query": "年化收益怎么样",
        "reply": "今天北京天气晴朗，适合出游。",
        "expect_passed": False,
    },
    {
        "query": "理财安全吗",
        "reply": "理财产品不承诺保本，投资需谨慎，详见产品说明书风险提示。",
        "expect_passed": True,
    },
)
