#!/usr/bin/env python3
"""Regenerate course/day25 — delegates to scripts/course_days/day25.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from course_builder import write_course  # noqa: E402
from course_days.day25 import build  # noqa: E402

if __name__ == "__main__":
    write_course(25, build(), min_chars=100_000)
