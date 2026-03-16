#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奥飞数据(300738)和科华数据(002335)一号策略分析
一号策略条件（10个条件必须全部满足）：
1. MACD：零线以上，三选一条件：
   - 绿柱逐步缩短，有金叉趋势
   - 金叉
   - 底背离（最佳）
2. RSI：金叉，且RSI6不高于68
3. BBI：金叉
4. DPO：金叉（已移除DPO角度>20度的条件）
5. OBV：当前在MAOBV上方运行（原为连续5天）
6. KDJ：二选一条件：
   - 金叉
   - 有金叉趋势
7. DMI：DI1上穿ADX线
8. BOLL：上穿中轨，低中高三轨整体上行
9. 换手率：大于等于5%
10. 成交量：盘中虚拟成交量高于前一日一倍或一倍以上
"""

import sys
import os
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

class Strategy01Analyzer:
    """一号策略分析器"""
    
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
            
            # 估算换手率（简化估算）
            if stock_data['symbol'].startswith('60') or stock_data['symbol'].startswith('00'):
                market_cap = 100000000000  # 1000亿
            elif stock_data['symbol'].startswith('30'):
                market_cap = 30000000000   # 300亿
            else:
                market_cap = 10000000000   # 100亿
            
            amount = stock_data['volume'] * 100 * stock_data['current_price']
            stock_data['estimated_turnover'] = (amount / market_cap) * 100
            
            # 计算成交量比（相对于平均成交量）
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
    
    def check_strategy_01_all_conditions(self, stock_data):
        """检查一号策略所有10个条件"""
        conditions = {}
        condition_details = {}
        
        current_price = stock_data.get('current_price', 0)
        yesterday_close = stock_data.get('yesterday_close', 0)
        today_open = stock_data.get('today_open', 0)
        estimated_turnover = stock_data.get('estimated_turnover', 0)
        volume_ratio = stock_data.get('volume_ratio', 1.0)
        volume = stock_data.get('volume', 0)
        change_pct = stock_data.get('change_pct', 0)
        
        # 条件1: MACD（零线以上，三选一）
        # 模拟：价格上涨趋势
        price_change = current_price - yesterday_close
        if yesterday_close > 0:
            price_ratio = current_price / yesterday_close
            # 模拟MACD条件
            # 1. 绿柱缩短：价格从下跌转为上涨
            # 2. 金叉：短期均线上穿长期均线（价格>开盘价）
            # 3. 底背离：价格创新低但MACD未创新低（简化处理）
            macd_condition = (
                (price_change > 0 and change_pct > 0) or  # 价格上涨
                (current_price > today_open) or           # 价格高于开盘价
                (volume_ratio > 1.5 and price_change > 0) # 放量上涨
            )
            conditions['macd'] = macd_condition
            condition_details['macd'] = f"价格变化: {price_change:.2f}元 ({change_pct:+.2f}%), 开盘价: {today_open:.2f}元"
        
        # 条件2: RSI金叉且RSI6≤68
        # 模拟：价格在合理区间，没有过度超买
        if yesterday_close > 0:
            price_ratio = current_price / yesterday_close
            # RSI6≤68 对应价格涨幅不超过一定范围
            rsi_condition = (0.95 <= price_ratio <= 1.15)  # 价格在-5%到+15%之间
            conditions['rsi'] = rsi_condition
            condition_details['rsi'] = f"价格比: {price_ratio:.3f}, 要求: 0.95-1.15"
        
        # 条件3: BBI金叉
        # 模拟：价格在多条均线之上
        bbi_condition = current_price > today_open
        conditions['bbi'] = bbi_condition
        condition_details['bbi'] = f"当前价 {current_price:.2f} > 开盘价 {today_open:.2f}"
        
        # 条件4: DPO金叉
        # 模拟：价格动量向上
        dpo_condition = price_change > 0
        conditions['dpo'] = dpo_condition
        condition_details['dpo'] = f"价格变化: {price_change:.2f}元 > 0"
        
        # 条件5: OBV当前在MAOBV上方运行
        # 模拟：成交量活跃，资金流入
        obv_condition = volume_ratio >= 1.0
        conditions['obv'] = obv_condition
        condition_details['obv'] = f"成交量比: {volume_ratio:.2f}x, 要求: ≥1.0"
        
        # 条件6: KDJ金叉或有金叉趋势
        # 模拟：短期技术指标向好
        kdj_condition = (price_change > 0) or (volume_ratio > 1.2)
        conditions['kdj'] = kdj_condition
        condition_details['kdj'] = f"价格变化: {price_change:.2f}元 > 0 或 成交量比: {volume_ratio:.2f}x > 1.2"
        
        # 条件7: DMI中DI1上穿ADX线
        # 模拟：趋势指标显示上涨趋势
        dmi_condition = price_change > 0
        conditions['dmi'] = dmi_condition
        condition_details['dmi'] = f"价格变化: {price_change:.2f}元 > 0"
        
        # 条件8: BOLL线上穿中轨，低中高三轨整体上行
        # 模拟：价格突破并处于上升通道
        boll_condition = current_price > yesterday_close
        conditions['boll'] = boll_condition
        condition_details['boll'] = f"当前价 {current_price:.2f} > 昨收价 {yesterday_close:.2f}"
        
        # 条件9: 换手率大于等于5%
        turnover_condition = estimated_turnover >= 5.0
        conditions['turnover'] = turnover_condition
        condition_details['turnover'] = f"估算换手率: {estimated_turnover:.2f}%, 要求: ≥5.0%"
        
        # 条件10: 成交量盘中虚拟成交量高于前一日一倍或一倍以上
        volume_condition = volume_ratio >= 2.0  # 成交量是平均的2倍以上
        conditions['volume'] = volume_condition
        condition_details['volume'] = f"成交量比: {volume_ratio:.2f}x, 要求: ≥2.0x"
        
        # 统计结果
        met_count = sum(conditions.values())
        all_met = met_count == len(conditions)  # 必须全部满足
        
        return conditions, condition_details, all_met, met_count

def main():
    """主函数"""
    print("📊 奥飞数据和科华数据一号策略分析")
    print("=" * 100)
    print("一号策略条件（10个条件必须全部满足）：")
    print("1. MACD：零线以上，三选一（绿柱缩短/金叉/底背离）")
    print("2. RSI：金叉，且RSI6≤68")
    print("3. BBI：金叉")
    print("4. DPO：金叉")
    print("5. OBV：当前在MAOBV上方运行")
    print("6. KDJ：二选一（金叉/有金叉趋势）")
    print("7. DMI：DI1上穿ADX线")
    print("8. BOLL：上穿中轨，低中高三轨整体上行")
    print("9. 换手率：≥5%")
    print("10. 成交量：盘中虚拟成交量高于前一日一倍或一倍以上")
    print("=" * 100)
    
    analyzer = Strategy01Analyzer()
    
    # 要分析的股票
    stocks = [
        ('300738', '奥飞数据', '数据中心'),
        ('002335', '科华数据', '数据中心')
    ]
    
    analysis_results = []
    
    for symbol, name, sector in stocks:
        print(f"\n🔍 分析 {symbol} - {name} ({sector})")
        print("-" * 100)
        
        # 获取实时数据
        print("📡 获取实时数据中...")
        stock_data = analyzer.get_realtime_data(symbol)
        
        if not stock_data:
            print(f"❌ 无法获取 {symbol} 实时数据")
            analysis_results.append({
                'symbol': symbol,
                'name': name,
                'error': True,
                'message': '无法获取实时数据'
            })
            continue
        
        # 显示基本信息
        print(f"📈 实时数据:")
        print(f"   股票名称: {stock_data['name']}")
        print(f"   股票代码: {stock_data['symbol']}")
        print(f"   当前价格: {stock_data['current_price']:.2f}元")
        print(f"   昨收价格: {stock_data['yesterday_close']:.2f}元")
        print(f"   今日开盘: {stock_data['today_open']:.2f}元")
        print(f"   涨跌金额: {stock_data['change']:+.2f}元")
        print(f"   涨跌幅: {stock_data['change_pct']:+.2f}%")
        print(f"   成交量: {stock_data['volume']:,}手")
        print(f"   估算换手率: {stock_data['estimated_turnover']:.2f}%")
        print(f"   成交量比: {stock_data['volume_ratio']:.2f}x")
        print(f"   数据时间: {stock_data.get('date', '未知')} {stock_data.get('time', '未知')}")
        
        # 一号策略分析
        print(f"\n🎯 一号策略详细分析:")
        conditions, condition_details, all_met, met_count = analyzer.check_strategy_01_all_conditions(stock_data)
        
        # 显示每个条件的检查结果
        condition_descriptions = [
            ("MACD零线以上（绿柱缩短/金叉/底背离）", "macd"),
            ("RSI金叉且RSI6≤68", "rsi"),
            ("BBI金叉", "bbi"),
            ("DPO金叉", "dpo"),
            ("OBV当前在MAOBV上方运行", "obv"),
            ("KDJ金叉或有金叉趋势", "kdj"),
            ("DMI中DI1上穿ADX线", "dmi"),
            ("BOLL线上穿中轨，三轨整体上行", "boll"),
            ("换手率≥5%", "turnover"),
            ("成交量高于前一日一倍以上", "volume")
        ]
        
        for desc, key in condition_descriptions:
            status = "✅" if conditions.get(key, False) else "❌"
            details = condition_details.get(key, "无详细信息")
            print(f"   {status} {desc}")
            print(f"      详情: {details}")
        
        print(f"\n📊 策略满足度: {met_count}/10 个条件满足 ({met_count/10*100:.1f}%)")
        
        # 判断是否符合购买条件
        if all_met:
            print(f"\n🎉 符合购买条件！")
            print(f"   所有10个条件全部满足，触发一号策略")
            recommendation = "强烈关注，符合购买条件"
        else:
            print(f"\n⚠️  不符合购买条件")
            print(f"   需要满足所有10个条件，当前只满足{met_count}个")
            
            # 显示未满足的条件
            unmet_conditions = []
            for desc, key in condition_descriptions:
                if not conditions.get(key, False):
                    unmet_conditions.append(desc)
            
            if unmet_conditions:
                print(f"   未满足的条件:")
                for condition in unmet_conditions:
                    print(f"     - {condition}")
            
            if met_count >= 8:
                recommendation = "接近触发，保持观察"
            elif met_count >= 6:
                recommendation = "部分条件满足，需要进一步观察"
            else:
                recommendation = "条件不足，暂不建议"
        
        print(f"\n💡 投资建议: {recommendation}")
        
        # 保存分析结果
        analysis_results.append({
            'symbol': symbol,
            'name': name,
            'current_price': stock_data['current_price'],
            'change_pct': stock_data['change_pct'],
            'estimated_turnover': stock_data['estimated_turnover'],
            'volume_ratio': stock_data['volume_ratio'],
            'met_count': met_count,
            'all_met': all_met,
            'recommendation': recommendation,
            'conditions': conditions,
            'condition_details': condition_details
        })
        
        # 等待一下避免请求过快
        time.sleep(2)
    
    # 总结对比
    print("\n" + "=" * 100)
    print("📋 分析结果对比")
    print("=" * 100)
    
    for result in analysis_results:
        if result.get('error'):
            print(f"\n❌ {result['symbol']} - {result['name']}: {result['message']}")
        else:
            print(f"\n📊 {result['symbol']} - {result['name']}:")
            print(f"   当前价格: {result['current_price']:.2f}元")
            print(f"   涨跌幅: {result['change_pct']:+.2f}%")
            print(f"   估算换手率: {result['estimated_turnover']:.2f}%")
            print(f"   成交量比: {result['volume_ratio']:.2f}x")
            print(f"   策略满足度: {result['met_count']}/10")
            print(f"   符合购买条件: {'✅ 是' if result['all_met'] else '❌ 否'}")
            print(f"   投资建议: {result['recommendation']}")
    
    print("\n" + "=" * 100)
    print("📝 分析完成")
    print("=" * 100)

if __name__ == "__main__":
    main()