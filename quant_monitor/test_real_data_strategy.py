#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真实数据测试一号策略 - 以立讯精密（002475）为例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import talib
import warnings
warnings.filterwarnings('ignore')

def get_real_stock_data(symbol, start_date="2026-01-01", end_date="2026-02-13"):
    """
    获取真实股票数据（历史K线）
    
    Args:
        symbol: 股票代码，如"002475"
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame with historical data
    """
    print(f"📊 获取 {symbol} 真实历史数据 ({start_date} 至 {end_date})")
    
    try:
        # 使用AKShare获取日线数据
        # 注意：实际日期可能需要根据AKShare的接口调整
        stock_code = f"sz{symbol}" if symbol.startswith('00') or symbol.startswith('30') else f"sh{symbol}"
        
        # 尝试不同的AKShare接口
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=start_date.replace("-", ""), 
                                end_date=end_date.replace("-", ""),
                                adjust="qfq")
        
        if df.empty:
            print(f"⚠️  无法获取 {symbol} 的历史数据，使用模拟数据")
            return generate_mock_data(symbol, start_date, end_date)
        
        # 重命名列
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        })
        
        # 确保有换手率列
        if 'turnover' not in df.columns:
            df['turnover'] = df['volume'] / df['volume'].rolling(20).mean() * 0.05  # 模拟换手率
        
        print(f"✅ 获取到 {len(df)} 个交易日数据")
        return df
    
    except Exception as e:
        print(f"❌ 获取真实数据失败: {e}")
        print("使用模拟数据进行分析")
        return generate_mock_data(symbol, start_date, end_date)

def generate_mock_data(symbol, start_date, end_date):
    """生成模拟数据（当真实数据不可用时）"""
    print(f"📈 为 {symbol} 生成模拟数据")
    
    # 生成日期范围
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
    n_days = len(dates)
    
    # 基础价格
    base_price = 30.0 if symbol == "002475" else 10.0  # 立讯精密假设30元
    
    # 生成价格序列
    np.random.seed(hash(symbol) % 10000)
    returns = np.random.randn(n_days) * 0.02
    
    # 添加趋势
    trend = np.random.choice([-0.01, 0, 0.01])
    returns += trend
    
    prices = base_price * (1 + returns.cumsum())
    
    # 生成其他数据
    highs = prices + np.random.rand(n_days) * 1.5
    lows = prices - np.random.rand(n_days) * 1.5
    volumes = np.random.randint(10000000, 50000000, n_days)
    turnovers = np.random.uniform(0.01, 0.08, n_days)  # 1-8%换手率
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,  # 开盘价略低于收盘
        'close': prices,
        'high': highs,
        'low': lows,
        'volume': volumes,
        'turnover': turnovers
    })
    
    return df

def calculate_technical_indicators(df):
    """计算技术指标"""
    print("📈 计算技术指标...")
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    
    # MACD
    macd_dif, macd_dea, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    
    # RSI
    rsi6 = talib.RSI(close, timeperiod=6)
    rsi12 = talib.RSI(close, timeperiod=12)
    
    # OBV
    obv = talib.OBV(close, volume)
    ma_obv = pd.Series(obv).rolling(20).mean().values
    
    # BOLL
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    
    # 简单DMI计算（简化版）
    # 实际DMI计算较复杂，这里用ADX代替趋势强度
    adx = talib.ADX(high, low, close, timeperiod=14)
    plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
    
    # 存储指标
    df['macd_dif'] = macd_dif
    df['macd_dea'] = macd_dea
    df['macd_hist'] = macd_hist
    df['rsi6'] = rsi6
    df['rsi12'] = rsi12
    df['obv'] = obv
    df['ma_obv'] = ma_obv
    df['boll_upper'] = upper
    df['boll_middle'] = middle
    df['boll_lower'] = lower
    df['adx'] = adx
    df['plus_di'] = plus_di
    
    # 计算金叉等信号
    df['macd_golden_cross'] = (df['macd_dif'] > df['macd_dea']) & (df['macd_dif'].shift(1) <= df['macd_dea'].shift(1))
    df['rsi_golden_cross'] = (df['rsi6'] > df['rsi12']) & (df['rsi6'].shift(1) <= df['rsi12'].shift(1))
    df['obv_above_ma'] = df['obv'] > df['ma_obv']
    df['price_above_boll_middle'] = df['close'] > df['boll_middle']
    df['volume_ratio'] = df['volume'] / df['volume'].shift(1)
    
    return df

def check_strategy_conditions(df, latest_date=None):
    """检查策略条件"""
    if latest_date:
        # 检查指定日期
        row = df[df['date'] == latest_date]
        if len(row) == 0:
            # 取最后一天
            row = df.iloc[-1:]
    else:
        # 检查最后一天
        row = df.iloc[-1:]
    
    if len(row) == 0:
        print("❌ 没有找到指定日期的数据")
        return None
    
    data = row.iloc[0]
    
    print(f"\n🔍 检查日期: {data['date'].strftime('%Y-%m-%d')}")
    print(f"   收盘价: {data['close']:.2f}")
    print(f"   成交量: {data['volume']:,.0f}")
    print(f"   换手率: {data['turnover']:.2%}")
    
    # 检查7个条件
    conditions = {}
    
    # 1. MACD条件（3选1）
    macd_conditions = []
    # a) 绿柱缩短（histogram > -0.1且为负值）
    if data['macd_hist'] > -0.1 and data['macd_hist'] < 0:
        macd_conditions.append("绿柱缩短")
    # b) 金叉
    if data['macd_golden_cross']:
        macd_conditions.append("金叉")
    # c) 底背离（简化判断：价格新低但MACD未新低）
    # 这里简化处理，实际需要更复杂的判断
    
    conditions['macd'] = len(macd_conditions) > 0
    conditions['macd_detail'] = macd_conditions if macd_conditions else ["无"]
    
    # 2. RSI条件：金叉 + RSI6≤68
    conditions['rsi'] = data['rsi_golden_cross'] and data['rsi6'] <= 68
    conditions['rsi_detail'] = {
        'golden_cross': bool(data['rsi_golden_cross']),
        'rsi6_value': data['rsi6']
    }
    
    # 3. OBV条件：在MAOBV上方
    conditions['obv'] = data['obv_above_ma']
    conditions['obv_detail'] = {
        'obv': data['obv'],
        'ma_obv': data['ma_obv']
    }
    
    # 4. DMI条件：DI1上穿ADX（简化：PLUS_DI > ADX）
    conditions['dmi'] = data['plus_di'] > data['adx']
    conditions['dmi_detail'] = {
        'plus_di': data['plus_di'],
        'adx': data['adx']
    }
    
    # 5. BOLL条件：股价上穿中轨
    conditions['boll'] = data['price_above_boll_middle']
    conditions['boll_detail'] = {
        'price': data['close'],
        'boll_middle': data['boll_middle']
    }
    
    # 6. 换手率条件：≥5%
    conditions['turnover'] = data['turnover'] >= 0.05
    conditions['turnover_detail'] = data['turnover']
    
    # 7. 成交量条件：≥前一日1倍
    conditions['volume'] = data['volume_ratio'] >= 2.0
    conditions['volume_detail'] = data['volume_ratio']
    
    # 统计
    conditions_met = sum([1 for k, v in conditions.items() if k in ['macd', 'rsi', 'obv', 'dmi', 'boll', 'turnover', 'volume'] and v])
    
    return conditions, conditions_met

def analyze_luxshare(symbol="002475", date="2026-02-13"):
    """分析立讯精密"""
    print("=" * 80)
    print(f"📊 立讯精密 ({symbol}) 策略符合性分析")
    print(f"   分析日期: {date}")
    print("=" * 80)
    
    # 获取数据
    df = get_real_stock_data(symbol, start_date="2025-12-01", end_date=date)
    
    if df.empty:
        print("❌ 无法获取数据")
        return
    
    # 计算技术指标
    df = calculate_technical_indicators(df)
    
    # 检查策略条件
    conditions, conditions_met = check_strategy_conditions(df, pd.Timestamp(date))
    
    if conditions is None:
        return
    
    print(f"\n🎯 策略条件检查结果:")
    print("-" * 80)
    
    condition_names = {
        'macd': "1. MACD绿柱缩短/金叉/底背离",
        'rsi': "2. RSI金叉 + RSI6≤68",
        'obv': "3. OBV在MAOBV上方",
        'dmi': "4. DMI：DI1上穿ADX",
        'boll': "5. 股价上穿BOLL中轨",
        'turnover': "6. 换手率≥5%",
        'volume': "7. 成交量≥前一日1倍"
    }
    
    for key, name in condition_names.items():
        met = conditions[key]
        status = "✅" if met else "❌"
        
        detail = conditions.get(f'{key}_detail', '')
        if key == 'macd':
            detail_str = f" ({', '.join(detail)})" if detail else ""
        elif key == 'rsi':
            detail_str = f" (金叉: {detail['golden_cross']}, RSI6: {detail['rsi6_value']:.1f})"
        elif key == 'obv':
            detail_str = f" (OBV: {detail['obv']:.0f}, MA: {detail['ma_obv']:.0f})"
        elif key == 'dmi':
            detail_str = f" (+DI: {detail['plus_di']:.1f}, ADX: {detail['adx']:.1f})"
        elif key == 'boll':
            detail_str = f" (价格: {detail['price']:.2f}, 中轨: {detail['boll_middle']:.2f})"
        elif key == 'turnover':
            detail_str = f" ({detail:.2%})"
        elif key == 'volume':
            detail_str = f" (比率: {detail:.2f}x)"
        else:
            detail_str = ""
        
        print(f"{status} {name}{detail_str}")
    
    print("-" * 80)
    print(f"📊 总计: {conditions_met}/7 个条件满足")
    
    if conditions_met == 7:
        print("🎉 完全符合策略条件！")
    elif conditions_met >= 5:
        print("👍 接近符合策略条件")
    else:
        print("⚠️  与策略条件差距较大")
    
    # 显示历史表现
    print(f"\n📈 近期指标趋势:")
    print("-" * 80)
    
    # 取最近5个交易日
    recent = df.tail(5).copy()
    
    for i, (idx, row) in enumerate(recent.iterrows()):
        date_str = row['date'].strftime('%m-%d')
        print(f"{date_str}: 收盘{row['close']:.2f} | "
              f"RSI6:{row['rsi6']:.1f} | "
              f"换手:{row['turnover']:.2%} | "
              f"量比:{row['volume_ratio']:.2f} | "
              f"BOLL:{'上' if row['price_above_boll_middle'] else '下'}")
    
    return conditions, conditions_met

def main():
    """主函数"""
    # 分析立讯精密
    conditions, met_count = analyze_luxshare("002475", "2026-02-13")
    
    print("\n" + "=" * 80)
    print("💡 策略优化建议:")
    print("-" * 80)
    
    if met_count < 4:
        print("1. ⚠️  策略条件过于严格，与实际市场脱节")
        print("2. 🔍 根据立讯精密实际表现，需要调整:")
        
        if conditions:
            # 分析具体不满足的条件
            problematic = []
            for key in ['macd', 'rsi', 'obv', 'dmi', 'boll', 'turnover', 'volume']:
                if not conditions[key]:
                    problematic.append(key)
            
            print(f"   不满足的条件: {len(problematic)}个")
            for i, key in enumerate(problematic, 1):
                condition_names = {
                    'macd': "MACD条件",
                    'rsi': "RSI条件", 
                    'obv': "OBV条件",
                    'dmi': "DMI条件",
                    'boll': "BOLL条件",
                    'turnover': "换手率条件",
                    'volume': "成交量条件"
                }
                print(f"   {i}. {condition_names[key]}")
        
        print("\n3. 🎯 建议优化方向:")
        print("   a) 使用真实历史数据回测，调整条件参数")
        print("   b) 考虑市场实际情况，如成交量倍率、换手率阈值")
        print("   c) 简化条件组合，避免过多指标共振要求")
        print("   d) 创建基于概率的评分系统，而非硬性条件")
    
    print("\n📝 总结:")
    print("   模拟测试 vs 真实数据 = 理论 vs 实践")
    print("   策略需要基于真实市场表现进行迭代优化")

if __name__ == "__main__":
    main()