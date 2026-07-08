#!/usr/bin/env python3
"""Regenerate course/day24–day32 from gold-standard modules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from course_builder import write_course  # noqa: E402

DAYS = range(24, 34)


def _load(day: int):
    path = ROOT / "scripts" / "course_days" / f"day{day}.py"
    spec = importlib.util.spec_from_file_location(f"course_day_{day}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    totals: dict[int, int] = {}
    for day in DAYS:
        mod = _load(day)
        files = mod.build()
        if len(files) != 30:
            raise SystemExit(f"day{day}: expected 30 files, got {len(files)}")
        totals[day] = write_course(day, files, min_chars=100_000)
    print("\n=== Regeneration complete ===")
    for day, n in totals.items():
        print(f"  day{day:02d}: {n:,} chars")
    grand = sum(totals.values())
    print(f"  total: {grand:,} chars across {len(DAYS)} days")


if __name__ == "__main__":
    main()
