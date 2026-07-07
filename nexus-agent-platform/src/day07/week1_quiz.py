"""
第一周周测 — Day 1-6 知识点自测

非正式测验，用于复习巩固。共 10 题，每题 10 分。

运行：python3 src/day07/week1_quiz.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_DAY07 = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("day07_constants_quiz", _DAY07 / "constants.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

QUESTIONS: list[dict] = [
    {
        "q": "Python 中用于表示「无值」的关键字是？",
        "options": ["null", "None", "nil", "void"],
        "answer": 1,
        "explain": "Python 使用 None，注意首字母大写。",
    },
    {
        "q": "下列哪个类型可变（mutable）？",
        "options": ["tuple", "str", "list", "int"],
        "answer": 2,
        "explain": "list 可变；tuple、str、int 不可变。",
    },
    {
        "q": "json.load 从文件读取后得到什么类型？",
        "options": ["str", "dict 或 list 等 Python 对象", "bytes", "JSON 对象"],
        "answer": 1,
        "explain": "json.load 反序列化为 Python 内置类型。",
    },
    {
        "q": "函数默认参数不应使用哪种默认值？",
        "options": ["None", "0", "[]", '""'],
        "answer": 2,
        "explain": "可变对象 [] 只创建一次，会被后续调用共享。",
    },
    {
        "q": "sorted(todos, key=lambda t: t['priority']) 中 lambda 的作用是？",
        "options": ["过滤元素", "指定排序键", "修改原列表", "去重"],
        "answer": 1,
        "explain": "key 函数从每个元素提取排序依据。",
    },
    {
        "q": "下列哪个模块属于 Day 6 建立的 utils？",
        "options": ["todo_storage", "json_utils", "platform_cli", "api_response_parser"],
        "answer": 1,
        "explain": "json_utils 在 src/utils/ 中。",
    },
    {
        "q": "for i in range(3) 循环几次？",
        "options": ["2", "3", "4", "无限"],
        "answer": 1,
        "explain": "range(3) 产生 0,1,2 共 3 次。",
    },
    {
        "q": "字典安全获取键的方式是？",
        "options": ["d[key]", "d.get(key)", "d.pop(key)", "d.keys()"],
        "answer": 1,
        "explain": "get 在键不存在时返回 None 而非抛 KeyError。",
    },
    {
        "q": "PYTHONPATH=src 的作用是？",
        "options": ["升级 pip", "让 Python 能找到 src 下的包", "运行测试", "格式化代码"],
        "answer": 1,
        "explain": "将 src 加入模块搜索路径，才能 import utils。",
    },
    {
        "q": "Sprint 1 收官交付物是？",
        "options": ["RAG 知识库", "通讯录管理系统", "FastAPI 服务", "LoRA 微调"],
        "answer": 1,
        "explain": "Day 7 交付通讯录，完成 CLI 工具链第一阶段。",
    },
]


def run_quiz() -> int:
    print("=" * 44)
    print("  NexusAgent 第一周周测（Day 1-6）")
    print("=" * 44)
    score = 0
    for i, item in enumerate(QUESTIONS, 1):
        print(f"\n第 {i} 题：{item['q']}")
        for j, opt in enumerate(item["options"]):
            print(f"  {j}. {opt}")
        raw = input("你的答案（数字）：").strip()
        if raw.isdigit() and int(raw) == item["answer"]:
            print("  ✅ 正确")
            score += 10
        else:
            correct = item["options"][item["answer"]]
            print(f"  ❌ 正确答案：{item['answer']}. {correct}")
            print(f"     解析：{item['explain']}")
    print("\n" + "=" * 44)
    print(f"  得分：{score} / 100")
    if score >= C.QUIZ_PASS_SCORE:
        print("  🎉 及格！可以开始通讯录项目实操。")
    else:
        print("  📚 建议复习 Day 1-6 课件后再测一次。")
    print("=" * 44)
    return score


if __name__ == "__main__":
    run_quiz()
