"""Day 3 单元测试"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
from io import StringIO

import pytest

DAY03_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "day03"
SRC_ROOT = DAY03_DIR.parent


def _load(name: str, filepath: Path):
    spec = importlib.util.spec_from_file_location(f"test_day03_{name}", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_module_loader = _load("module_loader", DAY03_DIR / "module_loader.py")
_guess_number = _load("guess_number", DAY03_DIR / "guess_number.py")
_multiplication = _load("multiplication_table", DAY03_DIR / "multiplication_table.py")
_platform_cli = _load("platform_cli", DAY03_DIR / "platform_cli.py")

load_day_module = _module_loader.load_day_module
get_src_root = _module_loader.get_src_root
play_guess_number = _guess_number.play_guess_number
print_multiplication_table = _multiplication.print_multiplication_table
handle_batch_clean = _platform_cli.handle_batch_clean
handle_output_stats = _platform_cli.handle_output_stats
VALID_MENU_CHOICES = _platform_cli.VALID_MENU_CHOICES


class TestModuleLoader:
    def test_load_day01(self):
        mod = load_day_module("day01", "constants")
        assert hasattr(mod, "COMPANY_NAME")

    def test_load_day02_cleaner(self):
        mod = load_day_module("day02", "text_cleaner")
        assert hasattr(mod, "clean_text")

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_day_module("day99", "not_exist")


class TestGuessNumber:
    @patch("builtins.input", side_effect=["50"])
    @patch("random.randint", return_value=50)
    def test_guess_correct_first_try(self, mock_randint, mock_input, capsys):
        play_guess_number(1, 100, 10)
        captured = capsys.readouterr()
        assert "猜对了" in captured.out

    @patch("builtins.input", side_effect=["abc", "50"])
    @patch("random.randint", return_value=50)
    def test_invalid_input_continue(self, mock_randint, mock_input, capsys):
        play_guess_number(1, 100, 10)
        captured = capsys.readouterr()
        assert "猜对了" in captured.out


class TestMultiplicationTable:
    def test_output_has_81(self, capsys):
        print_multiplication_table(9)
        captured = capsys.readouterr()
        assert "9x9=81" in captured.out


class TestPlatformCli:
    def test_valid_menu_choices(self):
        assert "0" in VALID_MENU_CHOICES
        assert "7" in VALID_MENU_CHOICES

    def test_batch_clean_creates_output(self, capsys):
        output_dir = SRC_ROOT / "day03" / "output"
        # 清理旧文件
        for f in output_dir.glob("cleaned_*.txt"):
            f.unlink()

        handle_batch_clean()
        captured = capsys.readouterr()
        assert "完成" in captured.out

        cleaned_files = list(output_dir.glob("cleaned_*.txt"))
        assert len(cleaned_files) >= 3

    def test_output_stats_after_batch(self, capsys):
        handle_output_stats()
        captured = capsys.readouterr()
        assert "文件数量" in captured.out or "output" in captured.out
