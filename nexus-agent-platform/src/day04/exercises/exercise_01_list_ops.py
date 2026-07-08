nums = [3, 1, 4, 1, 5, 9, 2, 6]
nums.append(7)
nums.remove(1)
nums.sort()
print("排序后:", nums)
print("max:", max(nums), "min:", min(nums))
big = [n for n in nums if n > 4]
print(">4:", big)
