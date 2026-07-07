"""
意图分类规则演示

运行：python3 src/day18/intent_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prompts import RuleBasedIntentClassifier

SAMPLES = [
    "请根据产品说明书回答收益率是多少？",
    "帮我总结以下会议纪要要点",
    "请审阅这段宣传语是否合规",
    "理财产品年化收益怎么样？",
    "你好，今天天气不错",
]


def main() -> None:
    clf = RuleBasedIntentClassifier()
    print("=== 意图分类演示 ===\n")
    for text in SAMPLES:
        match = clf.classify(text)
        print(f"  输入: {text}")
        print(f"  {match.summary()}\n")


if __name__ == "__main__":
    main()
