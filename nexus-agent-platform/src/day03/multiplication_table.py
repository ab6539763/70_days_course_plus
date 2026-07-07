"""
九九乘法表

练习嵌套 for 循环与 range、字符串格式化。

使用方式：
    python src/day03/multiplication_table.py

需求文档：ZL-NA-REQ-003（子功能 ZL-NA-014）
"""


def print_multiplication_table(size: int = 9) -> None:
    """
    打印九九乘法表

    外层循环 i：控制行数（1 到 size）
    内层循环 j：控制每行列数（1 到 i）

    Args:
        size: 表格大小，默认 9x9
    """
    print()
    print("=" * 50)
    print(f"  {size} x {size} 乘法表")
    print("=" * 50)
    print()

    for i in range(1, size + 1):
        for j in range(1, i + 1):
            # end="\t" 使同一行用制表符分隔
            print(f"{j}x{i}={i * j}", end="\t")
        print()  # 每行结束换行

    print()


def main() -> None:
    print_multiplication_table(9)


if __name__ == "__main__":
    main()
