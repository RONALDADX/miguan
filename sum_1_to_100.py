#!/usr/bin/env python3
"""
计算1到100的和
"""

def main():
    # 方法1: 使用循环
    total = 0
    for i in range(1, 101):
        total += i
    
    print(f"1到100的和是: {total}")
    
    # 方法2: 使用数学公式 n*(n+1)/2
    n = 100
    formula_result = n * (n + 1) // 2
    print(f"使用公式计算的结果: {formula_result}")
    
    # 验证两种方法结果一致
    if total == formula_result:
        print("✓ 两种方法计算结果一致")
    else:
        print("✗ 计算结果不一致")

if __name__ == "__main__":
    main()