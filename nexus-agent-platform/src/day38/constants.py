"""Day 38 常量"""

DAY = 38
REQ_ID = "ZL-NA-REQ-038"
PLATFORM_VERSION = "0.38.0"

RETRY_CASES = (
    {
        "query": "年化收益怎么样",
        "reply": "今天北京天气晴朗，适合出游。",
        "expect_passed_after_retry": False,
    },
    {
        "query": "客服电话多少",
        "reply": "请拨打客服热线 400-888-1234，工作日 9:00-18:00。",
        "expect_passed_after_retry": True,
    },
)
