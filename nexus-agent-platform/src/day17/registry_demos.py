"""
Prompt 注册表与文件加载演示

运行：python3 src/day17/registry_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prompts import PromptRegistry, default_registry


def main() -> None:
    print("=== PromptRegistry 演示 ===\n")
    print(f"  已注册模板 ({len(default_registry.list_names())}):")
    for name in default_registry.list_names():
        tmpl = default_registry.get(name)
        print(f"    - {name}: {tmpl.description or tmpl.required_vars}")

    cs = default_registry.get("customer_service")
    print(f"\n  customer_service 渲染:")
    print(
        cs.render(company="智链科技", channel="CLI", max_chars="200")
    )


if __name__ == "__main__":
    main()
