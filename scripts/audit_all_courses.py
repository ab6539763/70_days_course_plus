#!/usr/bin/env python3
"""Audit course/day01-day41 and optionally fix Mermaid blocks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from course_mermaid import sanitize_mermaid_blocks  # noqa: E402

COURSE = ROOT / "course"
GOLD_DAYS = range(24, 42)
PLATFORM = ROOT / "nexus-agent-platform"

# Narrative stale markers (skip next-day preview files 27_*)
STALE_MARKERS: dict[int, list[str]] = {
    35: [
        "## 一、citation_builder.py 全文",
        "@router.get(\"/route-config\"",
        "22_citation_builder精读.md",
    ],
    36: [
        "## 一、citation_builder.py 全文",
        "22_citation_builder精读.md",
        "ZL-NA-REQ-035",
    ],
    37: [
        "## 一、citation_builder.py 全文",
        "22_citation_builder精读.md",
        "@router.get(\"/route-config\"",
    ],
    39: [
        "## 一、citation_builder.py 全文",
        "22_validation_retry精读.md",
        "validation-retry-preview",
    ],
    40: [
        "## 一、citation_builder.py 全文",
        "22_react_agent精读.md",
        "react-preview",
    ],
    41: [
        "## 一、citation_builder.py 全文",
        "22_agent_executor精读.md",
        "executor-preview",
    ],
}


def audit(*, fix: bool = False) -> int:
    issues: list[str] = []
    for day in range(1, 42):
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
        code_readme = d / "code" / "README.md"
        if not code_readme.is_file():
            issues.append(f"day{day:02d}: missing code/README.md pointer")
        for f in mds:
            text = f.read_text(encoding="utf-8")
            if fix and "```mermaid" in text:
                fixed = sanitize_mermaid_blocks(text)
                if fixed != text:
                    f.write_text(fixed, encoding="utf-8")
            if "<!-- missing:" in text:
                issues.append(f"day{day:02d}/{f.name}: embedded missing repo path")
            if day in STALE_MARKERS and not f.name.startswith("27_"):
                for marker in STALE_MARKERS[day]:
                    if marker in text:
                        issues.append(f"day{day:02d}/{f.name}: stale marker {marker!r}")
                        break
            # H1 day mismatch (skip next-day preview files)
            if f.name.startswith("27_") or "预习" in f.name:
                continue
            if f.name.startswith("14_") and day < 14:
                continue
            if f.name.startswith("18_") and "对照" in f.name:
                m = re.match(r"^# Day (\d+)\b", text)
                if m and int(m.group(1)) != day:
                    issues.append(f"day{day:02d}/{f.name}: H1 says Day {m.group(1)}")
                continue
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


def ensure_code_pointers() -> None:
    """Create course/dayXX/code/README.md pointing at platform day modules."""
    for day in range(1, 42):
        d = COURSE / f"day{day:02d}"
        if not d.is_dir():
            continue
        code_dir = d / "code"
        code_dir.mkdir(exist_ok=True)
        readme = code_dir / "README.md"
        day_mod = PLATFORM / "src" / f"day{day:02d}"
        tests = PLATFORM / "tests" / f"day{day:02d}"
        lines = [
            f"# Day {day:02d} 配套代码",
            "",
            "当日可运行代码位于仓库 `nexus-agent-platform/`：",
            "",
            "```bash",
            "cd nexus-agent-platform",
        ]
        if day_mod.is_dir():
            lines.append(f"ls src/day{day:02d}/")
        if tests.is_dir():
            lines.append(f"pytest tests/day{day:02d}/ -q")
        lines.extend(["```", ""])
        readme.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    do_fix = "--fix" in sys.argv
    if "--ensure-code" in sys.argv or do_fix:
        ensure_code_pointers()
    raise SystemExit(audit(fix=do_fix))
