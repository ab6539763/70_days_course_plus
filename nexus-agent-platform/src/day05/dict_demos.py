"""Day 5 dict 与 JSON 演示"""

import json
from pathlib import Path


def demo_dict_crud():
    print("=== dict CRUD ===")
    user = {"name": "张三", "age": 25}
    user["role"] = "developer"
    print(user.get("email", "无邮箱"))
    for k, v in user.items():
        print(f"  {k}: {v}")


def demo_nested():
    print("\n=== 嵌套 dict ===")
    response = {
        "choices": [{"message": {"content": "你好"}}]
    }
    content = response["choices"][0]["message"]["content"]
    print("content:", content)


def demo_json_roundtrip():
    print("\n=== JSON 往返 ===")
    data = {"features": ["RAG", "Agent"], "version": 0.5}
    s = json.dumps(data, ensure_ascii=False)
    print("dumps:", s)
    print("loads:", json.loads(s))


def main():
    demo_dict_crud()
    demo_nested()
    demo_json_roundtrip()


if __name__ == "__main__":
    main()
