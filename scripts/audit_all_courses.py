#!/usr/bin/env python3
"""Audit course/day01-day37 and optionally fix Mermaid blocks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from course_mermaid import sanitize_mermaid_blocks  # noqa: E402

COURSE = ROOT / "course"
GOLD_DAYS = range(24, 38)


def audit(*, fix: bool = False) -> int:
    issues: list[str] = []
    for day in range(1, 38):
        d = COURSE / f"day{day:02d}"
        if not d.is_dir():
            issues.append(f"day{day:02d}: missing directory")
            continue
        mds = sorted(d.glob("*.md"))
        total = sum(f.stat().st_size for f in mds)
        if day in GOLD_DAYS:
            if len(mds) != 30:
                issues.append(f"day{day:02d}: {len(mds)} files (expected 30)")
            if total < 100_000:
                issues.append(f"day{day:02d}: {total:,} chars < 100,000")
        for f in mds:
            text = f.read_text(encoding="utf-8")
            if fix and "```mermaid" in text:
                fixed = sanitize_mermaid_blocks(text)
                if fixed != text:
                    f.write_text(fixed, encoding="utf-8")
            # H1 day mismatch (skip next-day preview files)
            if f.name.startswith("27_") or "预习" in f.name:
                continue
            if f.name.startswith("14_") and day < 14:
                continue  # cross-day case studies
            m = re.match(r"^# Day (\d+)\b", text)
            if m and int(m.group(1)) != day:
                issues.append(f"day{day:02d}/{f.name}: H1 says Day {m.group(1)}")
            for line in text.splitlines():
                if "->>" in line and "?" in line.split(">>", 1)[-1] and '"' not in line:
                    if "mermaid" not in line:
                        issues.append(f"day{day:02d}/{f.name}: unquoted mermaid ?")
                        break
    print(f"Audit complete: {len(issues)} issue(s)")
    for i in issues:
        print(f"  - {i}")
    return 1 if issues else 0


if __name__ == "__main__":
    do_fix = "--fix" in sys.argv
    raise SystemExit(audit(fix=do_fix))
