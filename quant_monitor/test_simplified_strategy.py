#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化版一号策略（八个条件）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import json
from datetime import datetime
import numpy as np

def load_strategy_config():
    """加载简化版策略配置"""
    with open("config/strategy_01_technical.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def analyze_strategy_conditions(config):
    """分析策略条件"""
    strategy = config['strategy_01_technical']
    conditions = strategy['trigger_conditions']
    
    print("📋 简化版一号策略条件分析")
    print("=" * 70)
    print(f"策略名称: {strategy['name']}")
    print(f"策略描述: {strategy['description']}")
    print()
    
    print("🎯 当前条件列表（八个条件必须全部满足）:")
    print("-" * 70)
    
    condition_count = 0
    enabled_conditions = []
    
    for key, condition in conditions.items():
        if condition.get('enabled', False):
            condition_count += 1
            enabled_conditions.append(key)
            
            # 获取条件名称
            if 'conditions' in condition and len(condition['conditions']) > 0:
                cond_names = [c['name'] for c in condition['conditions']]
                logic = condition.get('logic', 'all')
                
                if len(cond_names) == 1:
                    print(f"{condition_count}. {key.upper()}: {cond_names[0]}")
                else:
                    logic_text = "任一" if logic == "any" else "全部"
                    print(f"{condition_count}. {key.upper()}: {logic_text}条件满足")
                    for i, name in enumerate(cond_names, 1):
                        print(f"   {i}) {name}")
            else:
                print(f"{condition_count}. {key.upper()}: 条件已禁用或为空")
    
    print(f"\n📊 总计: {condition_count} 个条件")
    print("-" * 70)
    
    return condition_count, enabled_conditions

def simulate_stock_screening(condition_count):
    """模拟股票筛选（简化版）"""
    print("\n🔍 模拟股票筛选测试")
    print("=" * 70)
    
    # 模拟49只A股股票
    total_stocks = 49
    print(f"筛选范围: {total_stocks} 只A股股票")
    
    # 模拟每个条件通过的概率
    # 假设原始10个条件时通过率为0%
    # 移除2个条件后，假设每个条件通过率从10%提高到15%
    
    original_conditions = 10
    simplified_conditions = condition_count
    
    # 计算每个条件的通过概率
    # 假设原来每个条件通过率约为65%（因为10个条件同时满足概率极低）
    # 0.65^10 ≈ 0.0135 (1.35%)，但实际上测试是0%，说明每个条件通过率更低
    
    # 重新估算：假设原来每个条件通过率约50%
    # 0.5^10 = 0.00098 (0.098%)，接近0%
    
    # 简化后：移除2个最难条件，剩余条件通过率提高到60%
    single_condition_pass_rate = 0.60
    
    # 计算通过所有条件的概率
    all_conditions_pass_rate = single_condition_pass_rate ** simplified_conditions
    
    # 预期触发股票数量
    expected_triggered = int(total_stocks * all_conditions_pass_rate)
    
    print(f"条件数量: {simplified_conditions} 个")
    print(f"单个条件通过率估计: {single_condition_pass_rate:.1%}")
    print(f"所有条件同时满足概率: {all_conditions_pass_rate:.4%}")
    print(f"预期触发股票数量: {expected_triggered} 只")
    
    if expected_triggered == 0:
        print("⚠️  警告：可能仍然过于严格，需要进一步简化")
        print("建议进一步简化：")
        print("1. 将MACD组从'3选1'改为'金叉'即可")
        print("2. 将KDJ组从'2选1'改为'金叉'即可")
        print("3. 降低换手率要求（5% → 3%）")
        print("4. 移除OBV条件（与成交量重叠）")
    else:
        print(f"✅ 简化有效！预期可触发 {expected_triggered} 只股票")
    
    return expected_triggered

def main():
    """主函数"""
    print("🧪 测试简化版一号策略（移除KDJ后）")
    print("=" * 70)
    
    # 加载配置
    config = load_strategy_config()
    
    # 分析条件
    condition_count, enabled_conditions = analyze_strategy_conditions(config)
    
    print(f"\n✅ 已移除的条件: BBI, DPO, BOLL三轨上行, KDJ")
    print(f"✅ 启用的条件: {', '.join(enabled_conditions)}")
    
    # 模拟筛选
    expected_triggered = simulate_stock_screening(condition_count)
    
    print("\n" + "=" * 70)
    print("🎯 下一步建议:")
    print("-" * 70)
    
    if expected_triggered <= 1:
        print("1. 🔧 进一步简化策略：")
        print("   a) 简化MACD：从'3选1'改为'金叉'即可")
        print("   b) 降低换手率：5% → 3%")
        print("   c) 考虑移除OBV条件（与成交量重叠）")
        print("   d) 考虑移除DMI条件")
        print()
        print("2. 🧪 创建更简化的测试版本")
        print("3. 📊 使用真实数据测试")
    else:
        print("1. ✅ 当前简化版策略可能有效")
        print("2. 🧪 使用真实数据验证")
        print("3. 📈 监控实际触发率")
    
    print("\n💡 提示：策略的严格程度需要平衡信号质量与触发频率")
    print("   过于严格 → 无信号")
    print("   过于宽松 → 信号过多，质量下降")

if __name__ == "__main__":
    main()