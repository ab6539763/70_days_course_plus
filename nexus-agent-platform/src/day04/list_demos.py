"""
Day 4 课堂示例：list / tuple / set 操作演示

运行：python src/day04/list_demos.py
"""

from __future__ import annotations


def demo_list_crud():
    """列表增删改查演示"""
    print("=== list CRUD ===")
    todos = []
    todos.append("任务A")
    todos.extend(["任务B", "任务C"])
    print("添加后:", todos)
    todos[1] = "任务B-改"
    print("修改后:", todos)
    removed = todos.pop(0)
    print(f"pop 移除 {removed}:", todos)


def demo_slice():
    """切片演示"""
    print("\n=== 切片 ===")
    messages = [f"msg{i}" for i in range(10)]
    print("最近3条:", messages[-3:])
    print("反转:", messages[::-1])


def demo_comprehension():
    """列表推导式"""
    print("\n=== 列表推导式 ===")
    squares = [x**2 for x in range(6)]
    evens = [x for x in range(10) if x % 2 == 0]
    print("平方:", squares)
    print("偶数:", evens)


def demo_tuple():
    """元组与解包"""
    print("\n=== tuple ===")
    point = (10, 20)
    x, y = point
    print(f"point={point}, x={x}, y={y}")

    def min_max_avg(nums):
        return min(nums), max(nums), sum(nums) / len(nums)

    lo, hi, avg = min_max_avg([1, 5, 3, 9, 2])
    print(f"min={lo}, max={hi}, avg={avg:.1f}")


def demo_set():
    """集合去重"""
    print("\n=== set ===")
    tags = ["AI", "RAG", "AI", "Agent", "RAG"]
    unique = list(set(tags))
    print("去重:", unique)


def main():
    demo_list_crud()
    demo_slice()
    demo_comprehension()
    demo_tuple()
    demo_set()


if __name__ == "__main__":
    main()
