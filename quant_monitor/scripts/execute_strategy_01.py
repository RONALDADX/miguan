#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行一号策略筛选A股股票
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.strategy_manager import StrategyManager
import json
from datetime import datetime
import pandas as pd

def execute_strategy_01():
    """执行一号策略筛选"""
    print("🚀 开始执行一号策略 - A股股票筛选")
    print("=" * 70)
    
    # 初始化策略管理器
    strategy_mgr = StrategyManager()
    
    # 获取策略规则
    rules = strategy_mgr.get_strategy_01_rules()
    print(f"📋 策略名称: {rules['name']}")
    print(f"📝 策略描述: {rules['description']}")
    print()
    
    # 定义A股股票池（模拟数据）
    a_stock_universe = [
        # 大盘蓝筹
        ('000001', '平安银行'),
        ('000002', '万科A'),
        ('000858', '五粮液'),
        ('600519', '贵州茅台'),
        ('601318', '中国平安'),
        ('600036', '招商银行'),
        ('601988', '中国银行'),
        ('601328', '交通银行'),
        ('601288', '农业银行'),
        ('601398', '工商银行'),
        
        # 成长股
        ('000333', '美的集团'),
        ('002415', '海康威视'),
        ('300750', '宁德时代'),
        ('300059', '东方财富'),
        ('002475', '立讯精密'),
        ('002594', '比亚迪'),
        ('600276', '恒瑞医药'),
        ('600887', '伊利股份'),
        ('000568', '泸州老窖'),
        ('600436', '片仔癀'),
        
        # 中小盘
        ('002241', '歌尔股份'),
        ('002456', '欧菲光'),
        ('002714', '牧原股份'),
        ('300124', '汇川技术'),
        ('300122', '智飞生物'),
        ('300142', '沃森生物'),
        ('300015', '爱尔眼科'),
        ('300347', '泰格医药'),
        ('300413', '芒果超媒'),
        ('300498', '温氏股份'),
        
        # 其他
        ('000725', '京东方A'),
        ('002049', '紫光国微'),
        ('600309', '万华化学'),
        ('600585', '海螺水泥'),
        ('601888', '中国中免'),
        ('601012', '隆基绿能'),
        ('603259', '药明康德'),
        ('603288', '海天味业'),
        ('603986', '兆易创新'),
        ('688981', '中芯国际')
    ]
    
    symbols = [item[0] for item in a_stock_universe]
    symbol_names = {item[0]: item[1] for item in a_stock_universe}
    
    print(f"📊 筛选范围: {len(symbols)} 只A股股票")
    print("=" * 70)
    print()
    
    # 筛选结果存储
    results = {
        'screening_time': datetime.now().isoformat(),
        'strategy': rules['name'],
        'total_screened': len(symbols),
        'passed_stocks': [],
        'failed_stocks': [],
        'excluded_stocks': [],
        'top_candidates': []
    }
    
    print("🔍 开始逐只分析股票...")
    print("-" * 70)
    
    # 逐只分析股票
    for i, symbol in enumerate(symbols, 1):
        name = symbol_names.get(symbol, f"股票{symbol}")
        
        # 显示进度
        if i % 5 == 0 or i == len(symbols):
            print(f"进度: {i}/{len(symbols)} ({i/len(symbols)*100:.1f}%)")
        
        # 获取股票数据（模拟）
        stock_data = strategy_mgr._get_mock_stock_data(symbol)
        stock_data['name'] = name
        
        # 分析股票
        analysis = strategy_mgr.analyze_stock(stock_data, rules)
        
        # 分类结果
        if analysis.get('excluded', {}).get('is_excluded', False):
            results['excluded_stocks'].append({
                'symbol': symbol,
                'name': name,
                'reason': analysis['excluded']['exclusion_reasons']
            })
        elif analysis.get('meets_buy_criteria', False):
            results['passed_stocks'].append({
                'symbol': symbol,
                'name': name,
                'total_score': analysis['total_score'],
                'scores': analysis['scores'],
                'conclusion': analysis['conclusion']
            })
        else:
            results['failed_stocks'].append({
                'symbol': symbol,
                'name': name,
                'total_score': analysis['total_score'],
                'reason': analysis['conclusion']
            })
    
    print()
    print("✅ 筛选完成!")
    print("=" * 70)
    
    # 按评分排序
    results['passed_stocks'].sort(key=lambda x: x['total_score'], reverse=True)
    
    # 选取前20名作为推荐
    results['top_candidates'] = results['passed_stocks'][:20]
    
    # 生成报告
    generate_report(results, symbol_names)
    
    # 保存结果
    save_results(results)
    
    return results

def generate_report(results, symbol_names):
    """生成筛选报告"""
    
    # 筛选统计
    print("📊 筛选统计:")
    print("-" * 70)
    print(f"  筛选总数: {results['total_screened']:,}")
    print(f"  ✅ 通过数量: {len(results['passed_stocks']):,}")
    print(f"  ❌ 未通过数: {len(results['failed_stocks']):,}")
    print(f"  🚫 排除数量: {len(results['excluded_stocks']):,}")
    print(f"  通过率: {len(results['passed_stocks'])/results['total_screened']*100:.1f}%")
    print()
    
    # 排除原因统计
    excluded = results['excluded_stocks']
    if excluded:
        print("🚫 排除原因统计:")
        print("-" * 40)
        exclusion_counts = {}
        for stock in excluded:
            for reason in stock.get('reason', []):
                exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
        
        for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason}: {count}只")
        print()
    
    # 推荐股票列表
    top_candidates = results['top_candidates']
    if top_candidates:
        print("🏆 推荐股票清单 (Top 20):")
        print("=" * 70)
        print(f"{'排名':<4} {'代码':<8} {'名称':<12} {'综合评分':<8} {'基本面':<8} {'技术面':<8} {'市场面':<8} {'状态':<10}")
        print("-" * 70)
        
        for i, stock in enumerate(top_candidates, 1):
            symbol = stock['symbol']
            name = stock['name'][:10]  # 限制名称长度
            total_score = stock['total_score']
            scores = stock['scores']
            
            fund_score = scores['fundamental']['total']
            tech_score = scores['technical']['total']
            market_score = scores['market']['total']
            
            # 根据评分确定状态
            if total_score >= 85:
                status = "强烈推荐"
            elif total_score >= 75:
                status = "推荐"
            else:
                status = "观察"
            
            print(f"{i:<4} {symbol:<8} {name:<12} {total_score:<8.1f} {fund_score:<8.1f} {tech_score:<8.1f} {market_score:<8.1f} {status:<10}")
        
        print("=" * 70)
        print()
        
        # 显示前5只股票的详细分析
        print("📋 前5只股票详细分析:")
        print("=" * 70)
        
        for i, stock in enumerate(top_candidates[:5], 1):
            print(f"\n{i}. {stock['symbol']} - {stock['name']}")
            print(f"   综合评分: {stock['total_score']:.1f} ({stock['conclusion'].split(':')[0]})")
            
            # 显示关键指标
            fund_details = stock['scores']['fundamental']['details']
            print("   关键指标:")
            
            key_indicators = [
                ('pe_ratio', '市盈率'),
                ('pb_ratio', '市净率'),
                ('roe', 'ROE'),
                ('revenue_growth', '营收增长'),
                ('profit_growth', '利润增长'),
                ('debt_ratio', '负债率'),
                ('current_ratio', '流动比率')
            ]
            
            for eng_name, chi_name in key_indicators:
                if eng_name in fund_details:
                    detail = fund_details[eng_name]
                    value = detail['value']
                    score = detail['score'] * 100
                    
                    if eng_name in ['roe', 'revenue_growth', 'profit_growth', 'debt_ratio']:
                        display_value = f"{value:.2%}"
                    else:
                        display_value = f"{value:.2f}"
                    
                    print(f"     {chi_name:8s}: {display_value:10s} → {score:5.1f}分")
        
        print("\n" + "=" * 70)
    
    else:
        print("⚠️ 没有股票符合买入条件")
        print()
        
        # 显示评分最高的几只股票
        all_stocks = results['passed_stocks'] + results['failed_stocks']
        all_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        if all_stocks[:5]:
            print("📈 评分最高的5只股票:")
            print("-" * 40)
            for i, stock in enumerate(all_stocks[:5], 1):
                print(f"{i}. {stock['symbol']} - {stock['name']}: {stock['total_score']:.1f}分")
                print(f"   原因: {stock.get('reason', 'N/A')}")
            print()

def save_results(results):
    """保存筛选结果"""
    os.makedirs('results', exist_ok=True)
    
    # 保存JSON格式的详细结果
    json_file = f"results/strategy_01_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 保存CSV格式的推荐股票列表
    top_candidates = results['top_candidates']
    if top_candidates:
        csv_data = []
        for stock in top_candidates:
            csv_data.append({
                '排名': top_candidates.index(stock) + 1,
                '股票代码': stock['symbol'],
                '股票名称': stock['name'],
                '综合评分': stock['total_score'],
                '基本面评分': stock['scores']['fundamental']['total'],
                '技术面评分': stock['scores']['technical']['total'],
                '市场面评分': stock['scores']['market']['total'],
                '状态': '强烈推荐' if stock['total_score'] >= 85 else '推荐' if stock['total_score'] >= 75 else '观察'
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = f"results/strategy_01_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        print(f"💾 详细结果已保存到: {json_file}")
        print(f"📊 推荐列表已保存到: {csv_file}")
    else:
        print(f"💾 详细结果已保存到: {json_file}")

def main():
    """主函数"""
    try:
        results = execute_strategy_01()
        
        # 显示最终总结
        print("\n🎯 策略执行总结:")
        print("=" * 70)
        print(f"筛选时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"筛选股票总数: {results['total_screened']}")
        print(f"符合买入条件的股票: {len(results['passed_stocks'])}")
        
        if results['passed_stocks']:
            avg_score = sum(s['total_score'] for s in results['passed_stocks']) / len(results['passed_stocks'])
            max_score = max(s['total_score'] for s in results['passed_stocks'])
            min_score = min(s['total_score'] for s in results['passed_stocks'])
            
            print(f"平均综合评分: {avg_score:.1f}")
            print(f"最高评分: {max_score:.1f}")
            print(f"最低评分: {min_score:.1f}")
            print(f"推荐关注: {', '.join([s['symbol'] for s in results['top_candidates'][:5]])}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 策略执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()