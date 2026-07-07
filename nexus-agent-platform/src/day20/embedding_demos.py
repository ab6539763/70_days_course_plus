"""
余弦相似度与 Embedding 演示

运行：python3 src/day20/embedding_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag import EmbeddingClient, cosine_similarity

PAIRS = [
    ("年化收益", "年化收益率可达 8%"),
    ("投资回报率", "年化收益率可达 8%"),
    ("客服电话", "请联系客服：400-888-9999"),
    ("天气不错", "理财产品说明书"),
]


def main() -> int:
    corpus = [b for _, b in PAIRS]
    client = EmbeddingClient()
    client.fit_corpus(corpus)

    print("=== Embedding 余弦相似度演示 ===\n")
    print(f"  词表维度: {client.model.dimension}\n")

    for query, doc in PAIRS:
        sim = client.similarity(query, doc)
        print(f"  Q: {query}")
        print(f"  D: {doc[:40]}...")
        print(f"  sim={sim:.3f}\n")

    # 展示公式
    va = client.embed("年化收益").values
    vb = client.embed("年化收益率").values
    print(f"  cosine_similarity(年化收益, 年化收益率) = {cosine_similarity(va, vb):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
