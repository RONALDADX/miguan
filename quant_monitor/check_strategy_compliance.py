#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查哪些股票符合简化版一号策略（7个条件）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
import yaml
import json

class StrategyComplianceChecker:
    """策略符合性检查器"""
    
    def __init__(self):
        """初始化"""
        # 加载策略配置
        with open("config/strategy_01_technical.yaml", 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 获取股票池
        self.stocks = self.get_a_stock_universe()
        
    def get_a_stock_universe(self):
        """获取A股股票池"""
        a_stocks = [
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
            ('000333', '美的集团'),
            ('002415', '海康威视'),
            ('300750', '宁德时代'),
            ('300059', '东方财富'),
            ('002475', '立讯精密'),
            ('002594', '比亚迪'),
            ('601012', '隆基绿能'),
            ('600887', '伊利股份'),
            ('000568', '泸州老窖'),
            ('600276', '恒瑞医药'),
            ('600436', '片仔癀'),
            ('600309', '万华化学'),
            ('603288', '海天味业'),
            ('601888', '中国中免'),
            ('000725', '京东方A'),
            ('002049', '紫光国微'),
            ('300124', '汇川技术'),
            ('603986', '兆易创新'),
            ('688981', '中芯国际'),
            ('603259', '药明康德'),
            ('300122', '智飞生物'),
            ('300142', '沃森生物'),
            ('300015', '爱尔眼科'),
            ('300347', '泰格医药'),
            ('600585', '海螺水泥'),
            ('601899', '紫金矿业'),
            ('600028', '中国石化'),
            ('601857', '中国石油'),
            ('600111', '北方稀土'),
            ('002241', '歌尔股份'),
            ('002456', '欧菲光'),
            ('002714', '牧原股份'),
            ('300498', '温氏股份'),
            ('300413', '芒果超媒'),
            ('600030', '中信证券'),
            ('601166', '兴业银行'),
            ('600900', '长江电力'),
            ('601668', '中国建筑'),
            ('601800', '中国交建')
        ]
        return a_stocks
    
    def generate_simulated_data(self, symbol, days=5):
        """生成模拟数据"""
        np.random.seed(hash(symbol) % 10000)
        
        periods = days
        base_price = np.random.uniform(5, 100)
        
        # 生成随机走势
        returns = np.random.randn(periods) * 0.02
        
        # 增加趋势性
        trend = np.random.choice([-0.03, -0.01, 0.01, 0.03])
        returns += trend
        
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 2
        lows = prices - np.random.rand(periods) * 2
        
        # 生成成交量
        volumes = np.random.randint(1000000, 10000000, periods)
        
        # 生成换手率（1-10%）
        turnover_rates = np.random.uniform(0.01, 0.10, periods)
        
        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes,
            'turnover': turnover_rates
        })
        
        return data
    
    def calculate_indicators(self, data):
        """计算技术指标（简化版）"""
        # 模拟指标计算结果
        indicators = {
            'macd': {
                'dif': np.random.uniform(-1, 1),
                'dea': np.random.uniform(-1, 1),
                'histogram': np.random.uniform(-0.5, 0.5),
                'golden_cross': np.random.choice([True, False], p=[0.3, 0.7]),
                'bottom_divergence': np.random.choice([True, False], p=[0.1, 0.9])
            },
            'rsi': {
                'rsi6': np.random.uniform(20, 80),
                'rsi12': np.random.uniform(20, 80),
                'rsi24': np.random.uniform(20, 80),
                'golden_cross': np.random.choice([True, False], p=[0.4, 0.6])
            },
            'obv': {
                'above_ma': np.random.choice([True, False], p=[0.5, 0.5])
            },
            'dmi': {
                'di1_cross_adx': np.random.choice([True, False], p=[0.3, 0.7])
            },
            'boll': {
                'break_middle': np.random.choice([True, False], p=[0.4, 0.6])
            }
        }
        
        return indicators
    
    def check_conditions(self, indicators, turnover_rate, volume_ratio):
        """检查7个条件"""
        conditions = {
            'macd_condition': False,
            'rsi_condition': False,
            'obv_condition': False,
            'dmi_condition': False,
            'boll_condition': False,
            'turnover_condition': False,
            'volume_condition': False
        }
        
        # 1. MACD条件（3选1）
        macd = indicators['macd']
        if (macd['histogram'] > -0.1 and macd['histogram'] < 0):  # 绿柱缩短
            conditions['macd_condition'] = True
        elif macd['golden_cross']:  # 金叉
            conditions['macd_condition'] = True
        elif macd['bottom_divergence']:  # 底背离
            conditions['macd_condition'] = True
        
        # 2. RSI条件
        rsi = indicators['rsi']
        if rsi['golden_cross'] and rsi['rsi6'] <= 68:
            conditions['rsi_condition'] = True
        
        # 3. OBV条件
        if indicators['obv']['above_ma']:
            conditions['obv_condition'] = True
        
        # 4. DMI条件
        if indicators['dmi']['di1_cross_adx']:
            conditions['dmi_condition'] = True
        
        # 5. BOLL条件
        if indicators['boll']['break_middle']:
            conditions['boll_condition'] = True
        
        # 6. 换手率条件（≥5%）
        if turnover_rate >= 0.05:
            conditions['turnover_condition'] = True
        
        # 7. 成交量条件（≥前一日1倍）
        if volume_ratio >= 2.0:
            conditions['volume_condition'] = True
        
        # 检查是否所有条件都满足
        all_met = all(conditions.values())
        
        return conditions, all_met
    
    def run_compliance_check(self):
        """运行符合性检查"""
        print("🔍 检查股票符合简化版一号策略（7个条件）")
        print("=" * 80)
        print("策略条件：")
        print("1. MACD绿柱缩短/金叉/底背离（3选1）")
        print("2. RSI金叉 + RSI6≤68")
        print("3. OBV在MAOBV上方")
        print("4. DMI：DI1上穿ADX线")
        print("5. 股价上穿BOLL中轨")
        print("6. 换手率≥5%")
        print("7. 成交量≥前一日1倍")
        print("=" * 80)
        
        compliant_stocks = []
        condition_stats = {f'condition_{i+1}': 0 for i in range(7)}
        
        for symbol, name in self.stocks:
            # 生成模拟数据
            data = self.generate_simulated_data(symbol)
            
            # 计算指标
            indicators = self.calculate_indicators(data)
            
            # 获取最新数据
            latest_turnover = data['turnover'].iloc[-1]
            latest_volume = data['volume'].iloc[-1]
            prev_volume = data['volume'].iloc[-2] if len(data) > 1 else latest_volume * 0.5
            volume_ratio = latest_volume / prev_volume if prev_volume > 0 else 1.0
            
            # 检查条件
            conditions, all_met = self.check_conditions(indicators, latest_turnover, volume_ratio)
            
            # 统计每个条件的通过情况
            for i, (cond_name, met) in enumerate(conditions.items()):
                if met:
                    condition_stats[f'condition_{i+1}'] += 1
            
            if all_met:
                compliant_stocks.append({
                    'symbol': symbol,
                    'name': name,
                    'conditions': conditions,
                    'indicators': {
                        'macd_golden_cross': indicators['macd']['golden_cross'],
                        'rsi6': indicators['rsi']['rsi6'],
                        'turnover_rate': latest_turnover,
                        'volume_ratio': volume_ratio
                    }
                })
        
        # 输出结果
        print(f"\n📊 筛选统计:")
        print(f"  股票总数: {len(self.stocks)}")
        print(f"  符合策略: {len(compliant_stocks)}")
        print(f"  符合率: {len(compliant_stocks)/len(self.stocks)*100:.2f}%")
        
        print(f"\n📈 各条件通过率:")
        for i in range(7):
            pass_rate = condition_stats[f'condition_{i+1}'] / len(self.stocks) * 100
            print(f"  条件{i+1}: {condition_stats[f'condition_{i+1}']}/{len(self.stocks)} ({pass_rate:.1f}%)")
        
        if compliant_stocks:
            print(f"\n✅ 符合策略的股票 ({len(compliant_stocks)}只):")
            print("-" * 80)
            for stock in compliant_stocks:
                print(f"  {stock['symbol']} - {stock['name']}")
                print(f"    指标: MACD金叉={stock['indicators']['macd_golden_cross']}, "
                      f"RSI6={stock['indicators']['rsi6']:.1f}, "
                      f"换手率={stock['indicators']['turnover_rate']:.2%}, "
                      f"成交量比={stock['indicators']['volume_ratio']:.2f}")
        else:
            print(f"\n⚠️  没有股票完全符合7个条件")
            
            # 显示最接近的股票（满足条件最多的）
            print(f"\n🔍 最接近的股票（满足条件最多的）:")
            print("-" * 80)
            
            # 重新计算每只股票满足的条件数量
            stock_conditions_count = []
            for symbol, name in self.stocks:
                data = self.generate_simulated_data(symbol)
                indicators = self.calculate_indicators(data)
                latest_turnover = data['turnover'].iloc[-1]
                latest_volume = data['volume'].iloc[-1]
                prev_volume = data['volume'].iloc[-2] if len(data) > 1 else latest_volume * 0.5
                volume_ratio = latest_volume / prev_volume if prev_volume > 0 else 1.0
                
                conditions, _ = self.check_conditions(indicators, latest_turnover, volume_ratio)
                met_count = sum(conditions.values())
                
                stock_conditions_count.append({
                    'symbol': symbol,
                    'name': name,
                    'met_count': met_count,
                    'conditions': conditions
                })
            
            # 按满足条件数量排序
            stock_conditions_count.sort(key=lambda x: x['met_count'], reverse=True)
            
            # 显示前10只
            for i, stock in enumerate(stock_conditions_count[:10]):
                print(f"  {i+1:2d}. {stock['symbol']} - {stock['name']}: "
                      f"{stock['met_count']}/7 个条件")
                
                # 显示具体满足的条件
                met_conditions = [f"条件{j+1}" for j, met in enumerate(stock['conditions'].values()) if met]
                if met_conditions:
                    print(f"      满足: {', '.join(met_conditions)}")
        
        return compliant_stocks

def main():
    """主函数"""
    checker = StrategyComplianceChecker()
    compliant_stocks = checker.run_compliance_check()
    
    print("\n" + "=" * 80)
    print("💡 分析建议:")
    print("-" * 80)
    
    if compliant_stocks:
        print("1. ✅ 策略可以触发股票，说明简化有效")
        print("2. 🧪 建议使用真实数据进行验证")
        print("3. 📈 监控实际交易表现")
    else:
        print("1. ⚠️  策略仍然过于严格，需要进一步简化")
        print("2. 🔧 建议调整：")
        print("   a) 降低换手率要求（5% → 3%）")
        print("   b) 简化MACD条件（3选1 → 金叉即可）")
        print("   c) 考虑移除OBV或DMI条件")
        print("3. 🎯 目标是让策略能触发3-8只股票（在49只样本中）")

if __name__ == "__main__":
    main()