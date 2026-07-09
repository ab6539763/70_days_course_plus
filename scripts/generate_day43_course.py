#!/usr/bin/env python3
"""Regenerate course/day43 — delegates to scripts/course_days/day43.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from course_days.day43 import build  # noqa: E402
from course_builder import write_course  # noqa: E402

if __name__ == "__main__":
    write_course(43, build(), min_chars=100_000)
