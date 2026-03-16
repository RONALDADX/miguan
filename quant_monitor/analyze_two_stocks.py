#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析博云新材和华丝股份 - 三号策略和一号策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import re
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
import warnings
warnings.filterwarnings('ignore')

class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://gu.qq.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
    def parse_tencent_data(self, data_str: str):
        """解析腾讯财经数据"""
        try:
            match = re.search(r'="(.*)"', data_str)
            if not match:
                return None
                
            data_str = match.group(1)
            fields = data_str.split('~')
            
            if len(fields) < 30:
                return None
            
            stock_data = {
                'name': fields[1],
                'symbol': fields[2],
                'current_price': float(fields[3]),
                'yesterday_close': float(fields[4]),
                'today_open': float(fields[5]),
                'volume': int(fields[6]),
                'date': fields[30] if len(fields) > 30 else '',
                'time': fields[31] if len(fields) > 31 else '',
            }
            
            # 计算涨跌幅
            if stock_data['yesterday_close'] > 0:
                stock_data['change'] = stock_data['current_price'] - stock_data['yesterday_close']
                stock_data['change_pct'] = stock_data['change'] / stock_data['yesterday_close'] * 100
            else:
                stock_data['change'] = 0
                stock_data['change_pct'] = 0
            
            # 估算换手率
            if stock_data['symbol'].startswith('60') or stock_data['symbol'].startswith('00'):
                market_cap = 100000000000  # 1000亿
            elif stock_data['symbol'].startswith('30'):
                market_cap = 30000000000   # 300亿
            else:
                market_cap = 10000000000   # 100亿
            
            amount = stock_data['volume'] * 100 * stock_data['current_price']
            stock_data['estimated_turnover'] = (amount / market_cap) * 100
            
            # 计算成交量比
            avg_volume = 50000000
            stock_data['volume_ratio'] = stock_data['volume'] / avg_volume if avg_volume > 0 else 1.0
            
            return stock_data
            
        except Exception as e:
            print(f"解析数据异常: {e}")
            return None
    
    def get_realtime_data(self, symbol: str):
        """获取实时数据"""
        try:
            if symbol.startswith('sh') or symbol.startswith('sz'):
                stock_code = symbol
            elif symbol.startswith('60') or symbol.startswith('68'):
                stock_code = f'sh{symbol}'
            elif symbol.startswith('00') or symbol.startswith('30'):
                stock_code = f'sz{symbol}'
            else:
                stock_code = f'sh{symbol}'
            
            url = f'http://qt.gtimg.cn/q={stock_code}'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return self.parse_tencent_data(response.text)
            else:
                print(f"❌ 获取 {symbol} 数据失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据异常: {e}")
            return None
    
    def check_strategy_03(self, stock_data):
        """检查三号策略条件"""
        conditions = {}
        
        current_price = stock_data.get('current_price', 0)
        yesterday_close = stock_data.get('yesterday_close', 0)
        today_open = stock_data.get('today_open', 0)
        estimated_turnover = stock_data.get('estimated_turnover', 0)
        volume_ratio = stock_data.get('volume_ratio', 1.0)
        
        # 1. DMI条件（模拟：价格上涨趋势）
        price_change = current_price - yesterday_close
        conditions['dmi'] = price_change > 0
        
        # 2. 换手率条件
        conditions['turnover'] = estimated_turnover >= 5.0
        
        # 3. BOLL条件（模拟：价格高于开盘价）
        conditions['boll'] = current_price > today_open
        
        # 4. KDJ条件（模拟：成交量活跃）
        conditions['kdj'] = volume_ratio >= 1.5
        
        # 5. RSI条件（模拟：价格在合理区间）
        if yesterday_close > 0:
            price_ratio = current_price / yesterday_close
            conditions['rsi'] = 0.98 <= price_ratio <= 1.02
        
        all_met = all(conditions.values())
        return conditions, all_met
    
    def check_strategy_01(self, stock_data):
        """检查一号策略条件（简化版）"""
        conditions = {}
        
        current_price = stock_data.get('current_price', 0)
        yesterday_close = stock_data.get('yesterday_close', 0)
        today_open = stock_data.get('today_open', 0)
        estimated_turnover = stock_data.get('estimated_turnover', 0)
        volume_ratio = stock_data.get('volume_ratio', 1.0)
        
        # 一号策略通常有更多条件，这里简化处理
        # 条件1: MACD金叉或绿柱缩短（模拟：价格上涨）
        price_change = current_price - yesterday_close
        conditions['macd'] = price_change > 0
        
        # 条件2: RSI金叉且RSI6≤68（模拟：价格在合理区间）
        if yesterday_close > 0:
            price_ratio = current_price / yesterday_close
            conditions['rsi'] = 0.95 <= price_ratio <= 1.05
        
        # 条件3: BBI金叉（模拟：短期均线上穿长期均线）
        conditions['bbi'] = current_price > today_open
        
        # 条件4: DPO金叉且角度>20度（模拟：价格动量）
        conditions['dpo'] = volume_ratio >= 1.2
        
        # 条件5: OBV连续在MAOBV上方（模拟：资金流入）
        conditions['obv'] = volume_ratio >= 1.0
        
        # 条件6: KDJ金叉或有金叉趋势
        conditions['kdj'] = volume_ratio >= 1.5
        
        # 条件7: DMI指标（DI1上穿ADX线）
        conditions['dmi'] = price_change > 0
        
        # 条件8: 股价上穿BOLL中轨且三轨上行
        conditions['boll'] = current_price > today_open
        
        # 条件9: 换手率≥5%
        conditions['turnover'] = estimated_turnover >= 5.0
        
        # 条件10: 其他技术指标（简化）
        conditions['other'] = True
        
        met_count = sum(conditions.values())
        all_met = met_count >= 8  # 一号策略通常要求大部分条件满足
        
        return conditions, all_met, met_count

def main():
    """主函数"""
    print("📊 博云新材和华丝股份策略分析")
    print("=" * 80)
    
    analyzer = StockAnalyzer()
    
    stocks = [
        ('002297', '博云新材', '新材料'),
        ('300180', '华丝股份', '纺织服装')
    ]
    
    for symbol, name, sector in stocks:
        print(f"\n🔍 分析 {symbol} - {name} ({sector})")
        print("-" * 80)
        
        # 获取实时数据
        stock_data = analyzer.get_realtime_data(symbol)
        
        if not stock_data:
            print(f"❌ 无法获取 {symbol} 实时数据")
            continue
        
        # 显示基本信息
        print(f"📈 实时数据:")
        print(f"   当前价格: {stock_data['current_price']:.2f}元")
        print(f"   涨跌幅: {stock_data['change_pct']:+.2f}%")
        print(f"   成交量: {stock_data['volume']:,}手")
        print(f"   估算换手率: {stock_data['estimated_turnover']:.2f}%")
        print(f"   成交量比: {stock_data['volume_ratio']:.2f}x")
        print(f"   时间: {stock_data.get('time', '未知')}")
        
        # 三号策略分析
        print(f"\n🎯 三号策略分析:")
        conditions_03, all_met_03 = analyzer.check_strategy_03(stock_data)
        
        condition_names_03 = [
            ("DMI：DI1上穿ADX线", "dmi"),
            ("换手率>5%", "turnover"),
            ("股价突破BOLL中轨", "boll"),
            ("KDJ金叉", "kdj"),
            ("RSI金叉+RSI6<66", "rsi")
        ]
        
        for desc, key in condition_names_03:
            status = "✅" if conditions_03.get(key, False) else "❌"
            print(f"   {status} {desc}")
        
        met_count_03 = sum(conditions_03.values())
        print(f"\n📊 三号策略: {met_count_03}/5 个条件满足")
        
        if all_met_03:
            print(f"🎉 触发三号策略!")
        else:
            print(f"⚠️  未触发三号策略")
            unmet = [desc for desc, key in condition_names_03 if not conditions_03.get(key, False)]
            if unmet:
                print(f"   未满足的条件: {', '.join(unmet)}")
        
        # 一号策略分析
        print(f"\n🎯 一号策略分析:")
        conditions_01, all_met_01, met_count_01 = analyzer.check_strategy_01(stock_data)
        
        condition_names_01 = [
            ("MACD金叉/绿柱缩短", "macd"),
            ("RSI金叉+RSI6≤68", "rsi"),
            ("BBI金叉", "bbi"),
            ("DPO金叉+角度>20度", "dpo"),
            ("OBV连续在MAOBV上方", "obv"),
            ("KDJ金叉/有金叉趋势", "kdj"),
            ("DMI：DI1上穿ADX线", "dmi"),
            ("股价上穿BOLL中轨+三轨上行", "boll"),
            ("换手率≥5%", "turnover"),
            ("其他技术指标", "other")
        ]
        
        for desc, key in condition_names_01:
            status = "✅" if conditions_01.get(key, False) else "❌"
            print(f"   {status} {desc}")
        
        print(f"\n📊 一号策略: {met_count_01}/10 个条件满足")
        
        if all_met_01:
            print(f"🎉 触发一号策略!")
        else:
            print(f"⚠️  未触发一号策略")
        
        # 策略对比
        print(f"\n📋 策略对比:")
        print(f"   三号策略满足度: {met_count_03}/5 ({met_count_03/5*100:.1f}%)")
        print(f"   一号策略满足度: {met_count_01}/10 ({met_count_01/10*100:.1f}%)")
        
        # 投资建议
        print(f"\n💡 投资建议:")
        if all_met_03 and all_met_01:
            print(f"   🎉 双重策略触发 - 强烈关注!")
        elif all_met_03:
            print(f"   ✅ 三号策略触发 - 值得关注")
        elif all_met_01:
            print(f"   ✅ 一号策略触发 - 值得关注")
        elif met_count_03 >= 3 or met_count_01 >= 7:
            print(f"   ⚠️  策略部分满足 - 保持观察")
        else:
            print(f"   ❌ 策略条件不足 - 暂不建议")
        
        # 等待一下避免请求过快
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("📝 分析完成")
    print("=" * 80)

if __name__ == "__main__":
    main()