"""
练习 1：基本数据类型

演示 int、float、str、bool 四种基本类型的定义与使用。
对应作业题目一。
"""

# 定义四个不同类型的变量
name = "张三"           # str：字符串，用引号包裹
age = 25                # int：整数，没有小数点
height = 1.75           # float：浮点数，有小数点
is_employed = True      # bool：布尔值，只有 True 和 False

# 打印每个变量的类型
print(type(name))
print(type(age))
print(type(height))
print(type(is_employed))

# 使用 f-string 格式化输出
print(f"我是{name}，今年{age}岁，身高{height}米，在职状态：{is_employed}")
