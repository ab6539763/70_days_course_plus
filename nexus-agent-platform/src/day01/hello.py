"""
hello.py - NexusAgent 平台第一行代码

用途：
    验证开发环境是否正确配置。
    新成员入职第一天运行此脚本，确认 Python 解释器、
    终端编码、文件路径均正常。

运行方式：
    cd nexus-agent-platform
    python src/day01/hello.py

期望输出：
    Hello, NexusAgent!
    你好，灵犀智能体平台！
    Day 1 - 环境配置成功 ✅
    Python 版本: 3.11.x
    平台版本: 0.1.0

作者：NexusAgent 项目组
创建日期：2026-07-06
"""

import sys
from pathlib import Path

# 将 day01 目录加入模块搜索路径，确保能导入 constants
# 这是 Day 1 的简化做法，Day 10 学包管理后会用正规方式
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from constants import PROJECT_DISPLAY_NAME, VERSION


def check_python_version():
    """
    检查 Python 版本是否满足最低要求 (3.10+)
    
    Returns:
        bool: 版本满足要求返回 True
    """
    major, minor = sys.version_info[:2]
    
    if major < 3 or (major == 3 and minor < 10):
        print(f"❌ Python 版本过低: {major}.{minor}")
        print("   请安装 Python 3.10 或更高版本")
        return False
    
    return True


def main():
    """主程序：环境验证"""
    print("Hello, NexusAgent!")
    print(f"你好，{PROJECT_DISPLAY_NAME}！")
    print()
    
    if check_python_version():
        version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"Day 1 - 环境配置成功 ✅")
        print(f"Python 版本: {version_str}")
        print(f"平台版本: {VERSION}")
        print()
        print("下一步：运行 python src/day01/personal_info_card.py")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
