"""Day 1 测试用例"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

# 添加 src/day01 到路径
DAY01_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "day01"
sys.path.insert(0, str(DAY01_DIR))

from personal_info_card import generate_employee_id  # noqa: E402
from constants import EMPLOYEE_ID_PREFIX, EMPLOYEE_ID_SEQ  # noqa: E402


class TestGenerateEmployeeId:
    """工号生成测试"""

    def test_format(self):
        """工号应符合 ZL-YYYYMMDD-XXX 格式"""
        employee_id = generate_employee_id()
        parts = employee_id.split("-")
        
        assert len(parts) == 3
        assert parts[0] == EMPLOYEE_ID_PREFIX
        assert len(parts[1]) == 8  # YYYYMMDD
        assert parts[1].isdigit()
        assert parts[2] == EMPLOYEE_ID_SEQ

    def test_date_is_today(self):
        """工号中的日期应为今天"""
        employee_id = generate_employee_id()
        today_str = date.today().strftime("%Y%m%d")
        assert today_str in employee_id


class TestConstants:
    """常量定义测试"""

    def test_company_name_not_empty(self):
        from constants import COMPANY_NAME
        assert len(COMPANY_NAME) > 0

    def test_version_format(self):
        from constants import VERSION
        parts = VERSION.split(".")
        assert len(parts) == 3
