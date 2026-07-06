"""练习 1：运算符"""

a, b = 17, 5

print("=== 算术运算 ===")
print(f"a + b = {a + b}")
print(f"a - b = {a - b}")
print(f"a * b = {a * b}")
print(f"a / b = {a / b}")
print(f"a // b = {a // b}")
print(f"a % b = {a % b}")
print(f"a ** 2 = {a ** 2}")

print(f"\n{a} 是奇数: {a % 2 != 0}")
print(f"年龄在 18-65: {18 <= a <= 65}")

quotient, remainder = a // b, a % b
print(f"\n{a} 除以 {b} 商 {quotient} 余 {remainder}")
