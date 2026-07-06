"""
练习 2：摄氏-华氏温度转换器

公式：华氏温度 = 摄氏温度 × 9/5 + 32
对应作业题目二。
"""

celsius = float(input("请输入摄氏温度："))
fahrenheit = celsius * 9 / 5 + 32
print(f"摄氏 {celsius:.1f}°C = 华氏 {fahrenheit:.1f}°F")
