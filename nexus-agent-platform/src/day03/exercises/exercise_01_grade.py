"""练习：成绩等级判断"""

while True:
    s = input("请输入成绩（0-100）：").strip()
    if not s.isdigit():
        print("请输入数字")
        continue
    score = int(s)
    if not 0 <= score <= 100:
        print("成绩范围 0-100")
        continue
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    print(f"成绩 {score}，等级 {grade}")
    break
