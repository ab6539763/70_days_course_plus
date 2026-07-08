#!/usr/bin/env python3
"""Shared helpers for high-quality course material generation."""

from __future__ import annotations

import re
from pathlib import Path

from course_mermaid import sanitize_mermaid_blocks
from course_fixes import apply_fixes, post_fix_content


def write_course(day: int, files: dict[str, str], *, min_chars: int = 100_000) -> int:
    """Write course/dayXX/ files and validate quality."""
    files = apply_fixes(day, files)
    out = Path(__file__).resolve().parents[1] / "course" / f"day{day:02d}"
    out.mkdir(parents=True, exist_ok=True)
    # Remove stale markdown from prior generations (e.g. renamed filenames)
    keep = set(files.keys())
    for old in out.glob("*.md"):
        if old.name not in keep:
            old.unlink()
    total = 0
    for name, content in sorted(files.items()):
        text = sanitize_mermaid_blocks(post_fix_content(day, name, content.strip())) + "\n"
        (out / name).write_text(text, encoding="utf-8")
        total += len(text)
    _check_duplication(files, day)
    if total < min_chars:
        raise SystemExit(f"day{day:02d}: only {total} chars, need >= {min_chars}")
    print(f"day{day:02d}: {total} chars in {len(files)} files")
    return total


def _check_duplication(files: dict[str, str], day: int) -> None:
    """Fail if unrelated files share too much identical content."""
    skip = {"README.md", "02_需求文档.md", "02_需求文档_扩展.md"}
    exempt_pairs = {
        31: {frozenset({"06_课堂笔记_下午.md", "20_完整代码走查.md"})},
    }
    bodies = {k: v for k, v in files.items() if k not in skip}
    keys = list(bodies.keys())
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if frozenset({a, b}) in exempt_pairs.get(day, set()):
                continue
            if _similarity(bodies[a], bodies[b]) > 0.45:
                raise SystemExit(
                    f"day{day:02d}: {a} and {b} are >45% similar — fix template duplication"
                )


def _similarity(a: str, b: str) -> float:
    """Jaccard similarity on non-trivial lines."""
    la = {ln.strip() for ln in a.splitlines() if len(ln.strip()) > 40}
    lb = {ln.strip() for ln in b.splitlines() if len(ln.strip()) > 40}
    if not la or not lb:
        return 0.0
    return len(la & lb) / len(la | lb)


def read_repo(path: str, *, limit: int | None = None) -> str:
    """Read source file relative to repo root for embedding in course."""
    p = Path(__file__).resolve().parents[1] / path
    if not p.is_file():
        return f"<!-- missing: {path} -->"
    lines = p.read_text(encoding="utf-8").splitlines()
    if limit:
        lines = lines[:limit]
    return "\n".join(lines)


def fenced(lang: str, code: str) -> str:
    return f"```{lang}\n{code.strip()}\n```\n"
