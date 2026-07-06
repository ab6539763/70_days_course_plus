"""
Day 6 作业练习 01 — 函数基础

完成 calc_bmi 与 bmi_category。
"""

from __future__ import annotations


def calc_bmi(weight: float, height: float) -> float:
    """BMI = weight / height^2"""
    raise NotImplementedError


def bmi_category(bmi: float) -> str:
    """根据 BMI 返回分级字符串"""
    raise NotImplementedError


def main() -> None:
    print("BMI(70kg, 1.75m) =", calc_bmi(70, 1.75))
    print("category =", bmi_category(calc_bmi(70, 1.75)))


if __name__ == "__main__":
    main()
