"""
前端静态页结构审计

运行：python3 src/day22/frontend_audit.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SRC.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day22.constants import FRONTEND_DIR_NAME, REQUIRED_ELEMENT_IDS, REQUIRED_FILES

_FRONTEND = _REPO_ROOT / FRONTEND_DIR_NAME


def audit_frontend(root: Path | None = None) -> list[str]:
    """返回错误列表，空列表表示通过"""
    frontend = root or _FRONTEND
    errors: list[str] = []

    if not frontend.is_dir():
        return [f"目录不存在: {frontend}"]

    for name in REQUIRED_FILES:
        path = frontend / name
        if not path.is_file():
            errors.append(f"缺少文件: {name}")

    html_path = frontend / "index.html"
    if html_path.is_file():
        html = html_path.read_text(encoding="utf-8")
        for eid in REQUIRED_ELEMENT_IDS:
            if f'id="{eid}"' not in html and f"id='{eid}'" not in html:
                errors.append(f"index.html 缺少元素 id={eid}")
        if "mock.js" not in html or "app.js" not in html:
            errors.append("index.html 须引入 mock.js 与 app.js")

    mock_path = frontend / "mock.js"
    if mock_path.is_file():
        mock = mock_path.read_text(encoding="utf-8")
        if "sendMessage" not in mock:
            errors.append("mock.js 缺少 sendMessage 函数")
        if "FAQ 直答" not in mock:
            errors.append("mock.js 须包含 FAQ 直答 Mock 规则")

    app_path = frontend / "app.js"
    if app_path.is_file():
        app = app_path.read_text(encoding="utf-8")
        if "appendMessage" not in app:
            errors.append("app.js 缺少 appendMessage 函数")

    css_path = frontend / "style.css"
    if css_path.is_file():
        css = css_path.read_text(encoding="utf-8")
        if ".msg--user" not in css or ".msg--bot" not in css:
            errors.append("style.css 须包含用户/助手气泡样式")

    return errors


def main() -> int:
    print("=" * 50)
    print("  Day 22 frontend 结构审计")
    print("=" * 50)
    print(f"  目录: {_FRONTEND}\n")

    errors = audit_frontend()
    if errors:
        for err in errors:
            print(f"  ❌ {err}")
        print(f"\n  审计失败：{len(errors)} 项")
        return 1

    print("  ✅ 全部检查通过")
    print(f"  文件数: {len(REQUIRED_FILES)}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
