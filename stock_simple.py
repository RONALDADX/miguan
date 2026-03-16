#!/usr/bin/env python3
"""
简单的股票数据获取示例
使用requests直接调用API
"""

import requests
import json
from datetime import datetime

def get_stock_price(symbol):
    """获取股票价格（使用Alpha Vantage API）"""
    # 注意：免费API有频率限制，建议申请自己的API key
    api_key = "demo"  # 免费演示key，限制较多
    url = f"https://www.alphavantage.co/query"
    
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            print(f"=== {symbol} 实时报价 ===")
            print(f"价格: ${quote.get('05. price', 'N/A')}")
            print(f"涨跌: ${quote.get('09. change', 'N/A')}")
            print(f"涨跌幅: {quote.get('10. change percent', 'N/A')}")
            print(f"最高: ${quote.get('03. high', 'N/A')}")
            print(f"最低: ${quote.get('04. low', 'N/A')}")
            print(f"成交量: {quote.get('06. volume', 'N/A'):,}")
        else:
            print(f"无法获取 {symbol} 数据")
            print(f"响应: {data.get('Note', 'API限制或错误')}")
            
    except Exception as e:
        print(f"获取数据失败: {e}")

def get_crypto_price(coin="BTC"):
    """获取加密货币价格"""
    url = f"https://api.coingecko.com/api/v3/simple/price"
    
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "bitcoin" in data:
            btc = data["bitcoin"]
            print(f"\n=== 比特币价格 ===")
            print(f"价格: ${btc['usd']:,.2f}")
            print(f"24小时涨跌: {btc['usd_24h_change']:.2f}%")
    except Exception as e:
        print(f"获取加密货币数据失败: {e}")

if __name__ == "__main__":
    print("股票数据示例")
    print("=" * 40)
    
    # 获取美股示例
    get_stock_price("AAPL")  # 苹果
    print()
    get_stock_price("MSFT")  # 微软
    
    print("\n" + "=" * 40)
    
    # 获取加密货币
    get_crypto_price()
    
    print(f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")