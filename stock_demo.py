#!/usr/bin/env python3
"""
股票数据获取示例
需要安装：pip install yfinance pandas
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_stock_info(symbol):
    """获取股票基本信息"""
    stock = yf.Ticker(symbol)
    
    print(f"=== {symbol} 股票信息 ===")
    
    # 基本信息
    info = stock.info
    print(f"公司名称: {info.get('longName', 'N/A')}")
    print(f"当前价格: {info.get('currentPrice', 'N/A')}")
    print(f"市值: {info.get('marketCap', 'N/A'):,}")
    print(f"市盈率: {info.get('trailingPE', 'N/A')}")
    print(f"股息率: {info.get('dividendYield', 'N/A')}")
    
    # 历史数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    history = stock.history(start=start_date, end=end_date)
    if not history.empty:
        latest = history.iloc[-1]
        print(f"\n最新数据 ({latest.name.date()}):")
        print(f"  开盘: {latest['Open']:.2f}")
        print(f"  最高: {latest['High']:.2f}")
        print(f"  最低: {latest['Low']:.2f}")
        print(f"  收盘: {latest['Close']:.2f}")
        print(f"  成交量: {latest['Volume']:,}")
    
    return stock

if __name__ == "__main__":
    # 示例：腾讯控股 (0700.HK)
    get_stock_info("0700.HK")
    
    print("\n" + "="*40)
    
    # 示例：苹果公司 (AAPL)
    get_stock_info("AAPL")