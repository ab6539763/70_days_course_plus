"""Day 45 Phase 4 周测测试。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DAY45 = SRC / "day45"


def _load_quiz():
    spec = importlib.util.spec_from_file_location("phase4_quiz_test", DAY45 / "phase4_quiz.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase4_quiz_has_10_questions():
    quiz = _load_quiz()
    assert len(quiz.QUESTIONS) == 10


def test_phase4_quiz_scripted_full_score():
    quiz = _load_quiz()
    assert quiz.run_quiz_scripted() == 100


def test_phase4_quiz_scripted_fail():
    quiz = _load_quiz()
    wrong = [3] * len(quiz.QUESTIONS)
    score = quiz.run_quiz_scripted(wrong)
    assert score < quiz.QUIZ_PASS_SCORE


def test_phase4_quiz_main_scripted_exit_code():
    quiz = _load_quiz()
    assert quiz.main(["--scripted"]) == 0
