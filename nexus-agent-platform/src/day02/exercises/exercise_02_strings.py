"""练习 2：字符串切片与方法"""

s = "  NexusAgent-RAG-v0.1.0  "
original_len = len(s)

s = s.strip()
s = s.upper()
s = s.replace("-", "_")

# 用切片取 RAG：先定位位置
idx = s.find("RAG")
rag = s[idx : idx + 3]

parts = s.split("_")

print(f"处理后字符串: {s}")
print(f"RAG 片段: {rag}")
print(f"分割结果: {parts}")
print(f"原始长度 {original_len}，处理后长度 {len(s)}")
