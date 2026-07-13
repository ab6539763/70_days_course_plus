#!/usr/bin/env python3
"""Patch course_days/day31-37.py: fix titles, diagrams, and header day numbers."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "course_days"


def patch_file04(day: int) -> None:
    path = SCRIPTS / f"day{day}.py"
    text = path.read_text(encoding="utf-8")
    marker = f"def _file04() -> str:\n"
    if marker not in text:
        return
    replacement = f'''def _file04() -> str:
    from course_diagrams import file04

    return file04({day})
'''
    text = re.sub(
        r"def _file04\(\) -> str:.*?(?=\n\ndef _file05)",
        replacement,
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text, encoding="utf-8")
    print(f"  patched _file04 day{day}")


def fix_day_headers(day: int, wrong_day: int) -> None:
    """Fix off-by-one headers like Day 36 titles inside day35.py."""
    path = SCRIPTS / f"day{day}.py"
    text = path.read_text(encoding="utf-8")
    preview_next = day + 1

    def repl_header(m: re.Match[str]) -> str:
        found = int(m.group(1))
        if found == wrong_day:
            return f"# Day {day}"
        return m.group(0)

    # Only fix wrong_day headers outside preview function
    parts = text.split(f"def _file27()")
    main = parts[0]
    tail = f"def _file27(){parts[1]}" if len(parts) > 1 else ""
    main = re.sub(rf"# Day {wrong_day}\b", f"# Day {day}", main)
    text = main + tail
    path.write_text(text, encoding="utf-8")
    print(f"  fixed headers day{day}: Day {wrong_day} -> Day {day}")


def fix_acceptance_title(day: int, title: str) -> None:
    path = SCRIPTS / f"day{day}.py"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'def _file10\(\) -> str:\n    return f"""# Day \d+ \w+验收清单',
        f'def _file10() -> str:\n    return f"""# Day {day} {title}验收清单',
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    for day in range(31, 38):
        patch_file04(day)
    fix_day_headers(35, 36)
    fix_day_headers(36, 37)
    fix_acceptance_title(35, "Expansion")
    fix_acceptance_title(36, "Route")
    fix_acceptance_title(37, "Validation")
    print("Done patching course day scripts.")


if __name__ == "__main__":
    main()
