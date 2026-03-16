#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版策略执行脚本（不依赖AKShare）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.strategy_manager import StrategyManager
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_pingan_bank():
    """分析平安银行是否符合一号策略"""
    print("🔍 分析平安银行(000001)是否符合一号策略")
    print("=" * 60)
    
    strategy_mgr = StrategyManager()
    
    # 分析平安银行
    result = strategy_mgr.analyze_pingan_bank()
    
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return
    
    # 显示分析结果
    print(f"股票: {result['symbol']} - {result['name']}")
    print(f"策略: {result['strategy']}")
    print(f"分析时间: {result['analysis_time']}")
    print()
    
    # 显示综合评分
    print("📊 综合评分:")
    print(f"  总分: {result['total_score']:.1f}")
    print(f"  基本面: {result['scores']['fundamental']['total']:.1f}")
    print(f"  技术面: {result['scores']['technical']['total']:.1f}")
    print(f"  市场面: {result['scores']['market']['total']:.1f}")
    print()
    
    # 显示详细评分
    print("📈 详细评分:")
    
    # 基本面详细评分
    fund_details = result['scores']['fundamental']['details']
    print("  基本面指标:")
    for indicator, detail in fund_details.items():
        value = detail.get('value', 0)
        score = detail.get('score', 0) * 100
        weight = detail.get('weight', 0) * 100
        print(f"    {indicator:15s} 值:{value:8.3f} 得分:{score:6.1f} 权重:{weight:5.1f}%")
    print()
    
    # 显示关键指标
    print("📋 关键指标检查:")
    indicators = result['indicators']
    
    # 检查各项指标是否符合要求
    rules = strategy_mgr.get_strategy_01_rules()
    fund_rules = rules['fundamental']
    
    checks = [
        ("市盈率(PE)", indicators.get('pe_ratio', 0), fund_rules['pe_ratio']['range'], "5-25"),
        ("市净率(PB)", indicators.get('pb_ratio', 0), fund_rules['pb_ratio']['range'], "0.8-3.0"),
        ("ROE", indicators.get('roe', 0), (fund_rules['roe']['min'], None), "≥10%"),
        ("营收增长", indicators.get('revenue_growth', 0), (fund_rules['revenue_growth']['min'], None), "≥15%"),
        ("利润增长", indicators.get('profit_growth', 0), (fund_rules['profit_growth']['min'], None), "≥10%"),
        ("负债率", indicators.get('debt_ratio', 0), (None, fund_rules['debt_ratio']['max']), "≤60%"),
        ("流动比率", indicators.get('current_ratio', 0), (fund_rules['current_ratio']['min'], None), "≥1.2"),
    ]
    
    for name, value, rule_range, requirement in checks:
        if rule_range[0] is not None and value < rule_range[0]:
            status = "❌ 过低" if name != "负债率" else "❌ 过高"
        elif rule_range[1] is not None and value > rule_range[1]:
            status = "❌ 过高" if name != "负债率" else "❌ 过低"
        else:
            status = "✅ 符合"
        
        if name in ["ROE", "营收增长", "利润增长", "负债率"]:
            display_value = f"{value:.2%}"
        else:
            display_value = f"{value:.3f}"
        
        print(f"  {name:10s} {display_value:10s} 要求:{requirement:10s} {status}")
    print()
    
    # 显示条件检查
    print("✅ 条件检查:")
    must_have = result['must_have_passed']
    print(f"  必须条件: {must_have['passed']}/{must_have['total']} 通过")
    
    excluded = result['excluded']
    if excluded['is_excluded']:
        print(f"  排除原因: {', '.join(excluded['exclusion_reasons'])}")
    else:
        print("  未触发排除条件")
    
    print(f"  满足买入条件: {'是' if result['meets_buy_criteria'] else '否'}")
    print()
    
    # 显示结论
    print("🎯 结论:")
    print(f"  {result['conclusion']}")
    print("=" * 60)
    
    # 保存详细结果
    output_file = f"results/pingan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('results', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"详细结果已保存到: {output_file}")
    
    return result


def screen_weekly_stocks():
    """执行一周股票筛选"""
    print("🔍 执行一号策略一周股票筛选")
    print("=" * 60)
    
    strategy_mgr = StrategyManager()
    
    # 执行筛选
    print("正在筛选股票...")
    results = strategy_mgr.screen_stocks_weekly()
    
    if 'error' in results:
        print(f"❌ 筛选失败: {results['error']}")
        return
    
    # 生成报告
    report = strategy_mgr.generate_screening_report(results)
    print(report)
    
    # 保存结果
    output_file = f"results/weekly_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"详细结果已保存到: {output_file}")
    
    # 显示推荐股票详情
    top_candidates = results.get('top_candidates', [])
    if top_candidates:
        print("\n📋 推荐股票详情 (前5只):")
        print("=" * 60)
        
        for i, stock in enumerate(top_candidates[:5], 1):
            print(f"\n{i}. {stock['symbol']} - {stock['name']}")
            print(f"   综合评分: {stock['total_score']:.1f}")
            
            # 显示关键指标
            scores = stock['scores']
            print(f"   基本面: {scores['fundamental']['total']:.1f}")
            print(f"   技术面: {scores['technical']['total']:.1f}")
            print(f"   市场面: {scores['market']['total']:.1f}")
            
            # 显示详细评分
            fund_details = scores['fundamental']['details']
            print("   关键指标:")
            for indicator in ['pe_ratio', 'pb_ratio', 'roe', 'revenue_growth']:
                if indicator in fund_details:
                    detail = fund_details[indicator]
                    value = detail['value']
                    
                    if indicator in ['roe', 'revenue_growth']:
                        display_value = f"{value:.2%}"
                    else:
                        display_value = f"{value:.2f}"
                    
                    score = detail['score'] * 100
                    print(f"     {indicator:15s} {display_value:10s} → {score:5.1f}分")
        
        print("\n" + "=" * 60)
    
    return results


def show_strategy_rules():
    """显示策略规则"""
    strategy_mgr = StrategyManager()
    rules = strategy_mgr.get_strategy_01_rules()
    
    print("\n📋 一号策略规则详情")
    print("=" * 60)
    print(f"策略名称: {rules['name']}")
    print(f"策略描述: {rules['description']}")
    print()
    
    print("📊 评分权重:")
    print(f"  基本面: {rules['weights'].get('fundamental', 0.4):.0%}")
    print(f"  技术面: {rules['weights'].get('technical', 0.35):.0%}")
    print(f"  市场面: {rules['weights'].get('market', 0.25):.0%}")
    print()
    
    print("✅ 必须满足的条件:")
    for condition in rules['screening'].get('must_have', []):
        print(f"  • {condition}")
    print()
    
    print("🚫 排除条件:")
    for condition in rules['screening'].get('exclude', []):
        print(f"  • {condition}")
    print()
    
    print("💰 交易规则:")
    trading = rules['trading']
    buy = trading.get('buy', {})
    sell = trading.get('sell', {})
    position = trading.get('position', {})
    
    print("  买入条件:")
    print(f"    • 综合评分 ≥ {buy.get('total_score', 80)}")
    print(f"    • 技术面评分 ≥ {buy.get('technical_score', 70)}")
    print(f"    • 趋势方向: {buy.get('market_timing', 'trend_up')}")
    print()
    
    print("  卖出条件:")
    print(f"    • 综合评分 ≤ {sell.get('total_score', 60)}")
    print(f"    • 止损: {sell.get('stop_loss', 0.08):.0%}")
    print(f"    • 止盈: {sell.get('take_profit', 0.25):.0%}")
    print(f"    • 移动止损: {sell.get('trailing_stop', 0.10):.0%}")
    print()
    
    print("  仓位管理:")
    print(f"    • 单股最大仓位: {position.get('max_position', 0.10):.0%}")
    print(f"    • 初始仓位: {position.get('initial_position', 0.05):.0%}")
    print(f"    • 允许加仓: {'是' if position.get('pyramid', True) else '否'}")
    print(f"    • 最多加仓次数: {position.get('max_additions', 2)}")
    print("=" * 60)


def main():
    """主函数"""
    print("🚀 一号策略执行系统")
    print("=" * 60)
    
    # 创建必要的目录
    os.makedirs('results', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    while True:
        print("\n请选择操作:")
        print("1. 分析平安银行是否符合一号策略")
        print("2. 执行一周股票筛选")
        print("3. 查看策略规则")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            analyze_pingan_bank()
        elif choice == '2':
            screen_weekly_stocks()
        elif choice == '3':
            show_strategy_rules()
        elif choice == '4':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新输入")


if __name__ == "__main__":
    main()