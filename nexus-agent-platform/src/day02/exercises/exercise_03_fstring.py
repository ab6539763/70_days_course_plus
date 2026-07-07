"""练习 3：f-string 格式化报告"""

source = "test.txt"
raw_len = 2500
clean_len = 2100
replace_count = 7
compression = (raw_len - clean_len) / raw_len

report = f"""
=== 清洗报告（练习版）===
输入来源: {source}
原始字符数: {raw_len:,}
清洗后字符数: {clean_len:,}
压缩率: {compression:.1%}
敏感词替换: {replace_count} 次
"""
print(report)
