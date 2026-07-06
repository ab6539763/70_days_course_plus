"""
开发者入职信息采集工具

NexusAgent 平台的成员注册 CLI 原型。
采集开发者基本信息，生成格式化的入职信息卡片。

本模块是 ZL-NA-REQ-001 需求的 Day 1 实现。
后续演进路线：
    Day 5  → 增加 JSON 文件持久化
    Day 8  → 重构为 Member 类
    Day 12 → 增加 API 提交到远程服务
    Day 23 → 封装为 FastAPI POST /api/v1/members

需求文档：course/day01/02_需求文档.md (ZL-NA-REQ-001)
架构文档：course/day01/03_架构设计.md (ZL-NA-ARCH-001)

使用方式：
    cd nexus-agent-platform
    python src/day01/personal_info_card.py

作者：NexusAgent 项目组
创建日期：2026-07-06
版本：0.1.0
"""

import sys
from datetime import date
from pathlib import Path

# 确保能导入同目录下的 constants 模块
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from constants import (
    COMPANY_NAME,
    PROJECT_DISPLAY_NAME,
    VERSION,
    EMPLOYEE_ID_PREFIX,
    EMPLOYEE_ID_SEQ,
)


def show_welcome():
    """
    显示欢迎横幅
    
    在程序启动时向用户展示欢迎信息，
    说明当前程序的用途和所属项目。
    """
    # 使用字符串乘法生成分隔线
    # "=" * 50 等价于 50 个等号组成的字符串
    separator = "=" * 50
    
    print()
    print(separator)
    print(f"  欢迎加入 {COMPANY_NAME}")
    print(f"  {PROJECT_DISPLAY_NAME} 项目组")
    print(f"  开发者入职信息采集 v{VERSION}")
    print(separator)
    print()


def collect_info():
    """
    采集开发者基本信息
    
    通过命令行交互方式，依次提示用户输入
    姓名、年龄、职位、邮箱四项基本信息。
    
    Returns:
        dict: 包含以下键的字典
            - name (str): 姓名
            - age (int): 年龄
            - role (str): 职位
            - email (str): 电子邮箱
    
    Note:
        input() 返回的永远是字符串类型。
        年龄字段需要用 int() 转换为整数。
        Day 6 会添加 try/except 处理非法输入。
    """
    print("请按提示输入您的基本信息：")
    print()
    
    # input() 获取用户输入，返回 str 类型
    name = input("  姓名：")
    
    # int(input()) 是常见的「获取整数输入」模式
    # 如果用户输入非数字，会抛出 ValueError
    age = int(input("  年龄："))
    
    role = input("  职位：")
    email = input("  邮箱：")
    
    print()
    
    # 使用字典组织采集到的数据
    # 字典是 Python 最常用的数据结构之一，Day 5 会深入学习
    return {
        "name": name,
        "age": age,
        "role": role,
        "email": email,
    }


def generate_employee_id():
    """
    生成员工工号
    
    工号格式：ZL-YYYYMMDD-XXX
        - ZL: 智链科技前缀（Zhilian）
        - YYYYMMDD: 入职日期
        - XXX: 3 位序号（Day 1 固定 001）
    
    Returns:
        str: 格式如 ZL-20260706-001 的工号字符串
    
    Example:
        >>> # 假设今天是 2026-07-06
        >>> generate_employee_id()
        'ZL-20260706-001'
    """
    # date.today() 获取当前日期
    today = date.today()
    
    # strftime 格式化日期为字符串
    # %Y = 四位年份, %m = 两位月份, %d = 两位日期
    date_str = today.strftime("%Y%m%d")
    
    # f-string 拼接工号
    return f"{EMPLOYEE_ID_PREFIX}-{date_str}-{EMPLOYEE_ID_SEQ}"


def display_card(info, employee_id):
    """
    显示格式化的入职信息卡片
    
    将采集到的成员信息以 ASCII 字符画边框的卡片形式
    输出到控制台。这种格式化输出在企业 CLI 工具中很常见。
    
    Args:
        info (dict): collect_info() 返回的成员信息字典
        employee_id (str): generate_employee_id() 返回的工号
    
    Note:
        中文字符在终端中占 2 个显示宽度，但 Python 的
        字符串长度按字符数计算。因此中文对齐可能不完美。
        Day 2 会学习更精确的字符串对齐方法。
    """
    # 入职日期，格式化为 YYYY-MM-DD
    today_str = date.today().strftime("%Y-%m-%d")
    
    # 构建 ASCII 卡片
    # 使用 Unicode 制表符绘制边框（在大多数现代终端中显示良好）
    card = f"""
╔══════════════════════════════════════════╗
║     智链科技 · NexusAgent 项目组          ║
║         开发者入职信息卡 v{VERSION}          ║
╠══════════════════════════════════════════╣
║  姓名：{info['name']}
║  年龄：{info['age']}
║  职位：{info['role']}
║  邮箱：{info['email']}
╠══════════════════════════════════════════╣
║  工号：{employee_id}
║  入职日期：{today_str}
╚══════════════════════════════════════════╝
"""
    print(card)


def main():
    """
    程序主入口
    
    串联所有功能模块，完成完整的入职信息采集流程：
    1. 显示欢迎信息
    2. 采集用户输入
    3. 生成工号
    4. 展示信息卡片
    5. 显示完成提示
    """
    # 步骤 1：欢迎
    show_welcome()
    
    # 步骤 2：采集信息
    info = collect_info()
    
    # 步骤 3：生成工号
    employee_id = generate_employee_id()
    
    # 步骤 4：展示卡片
    display_card(info, employee_id)
    
    # 步骤 5：完成提示
    print("🎉 入职信息采集完成！欢迎加入 NexusAgent 项目组！")
    print("   你的工号已生成，请妥善保管。")
    print()


# Python 标准入口
# 只有直接运行此文件时才执行 main()
# 被其他模块 import 时不会自动执行
if __name__ == "__main__":
    main()
