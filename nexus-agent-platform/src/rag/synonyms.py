"""
金融领域同义词扩展 — 提升 TF-IDF「伪 Embedding」语义召回

Day 25+ 密集向量 API 可移除此层；MVP 用于教学演示同义词检索。

需求：ZL-NA-REQ-020
"""

from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+")

# 词级同义词
TOKEN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "收益": ("收益", "回报率", "盈利", "年化"),
    "回报率": ("收益", "回报率", "投资回报", "年化收益"),
    "年化": ("年化", "年化收益", "收益率", "收益"),
    "投资": ("投资", "理财", "配置", "认购"),
    "风险": ("风险", "风险提示", "风险揭示", "谨慎"),
    "客服": ("客服", "联系电话", "咨询电话", "热线"),
    "电话": ("电话", "客服", "手机", "联系"),
    "合规": ("合规", "审阅", "审查", "违规"),
    "文档": ("文档", "资料", "说明书", "条款"),
    "上传": ("上传", "导入", "添加"),
}

# 短语级同义组（组内互相扩展）
PHRASE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("投资回报率", "年化收益", "年化收益率", "投资回报", "收益率"),
    ("风险提示", "风险揭示", "投资有风险", "入市需谨慎"),
    ("理财产品", "理财产品说明书", "稳健增值"),
    ("内部资料", "禁止外传", "机密"),
)


def tokenize(text: str) -> list[str]:
    """提取 token（小写英文、中文词段）"""
    tokens: list[str] = []
    seen: set[str] = set()
    for part in _TOKEN_PATTERN.findall(text or ""):
        key = part.lower()
        if key not in seen:
            tokens.append(key)
            seen.add(key)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                bg = part[i : i + 2]
                if bg not in seen:
                    tokens.append(bg)
                    seen.add(bg)
    return tokens


def expand_tokens(tokens: list[str], text: str = "") -> list[str]:
    """同义词 + 短语组扩展"""
    expanded: list[str] = []
    seen: set[str] = set()

    def add(t: str) -> None:
        if t and t not in seen:
            expanded.append(t)
            seen.add(t)

    for t in tokens:
        add(t)
        for syn in TOKEN_SYNONYMS.get(t, ()):
            add(syn)

    source = text or " ".join(tokens)
    for group in PHRASE_GROUPS:
        if any(phrase in source for phrase in group):
            for phrase in group:
                add(phrase)
                for sub in tokenize(phrase):
                    add(sub)

    return expanded
