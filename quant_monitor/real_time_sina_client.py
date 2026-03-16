#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经实时数据客户端
最稳定的免费实时行情接口
"""

import requests
import re
import json
import time
from datetime import datetime
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SinaRealTimeClient:
    """新浪财经实时客户端"""
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://finance.sina.com.cn',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 股票代码映射
        self.code_map = {}
        
    def get_stock_code(self, symbol):
        """获取新浪财经股票代码"""
        if symbol.startswith('60') or symbol.startswith('68'):
            return f'sh{symbol}'
        elif symbol.startswith('00') or symbol.startswith('30'):
            return f'sz{symbol}'
        elif symbol.startswith('43') or symbol.startswith('83') or symbol.startswith('87'):
            return f'bj{symbol}'
        else:
            return f'sh{symbol}'  # 默认上海
    
    def parse_sina_data(self, data_str):
        """解析新浪财经数据格式"""
        # 示例: var hq_str_sh000001="平安银行,19.580,19.600,19.540,19.610,19.530,19.540,19.550,...";
        
        # 提取数据部分
        match = re.search(r'="(.*)"', data_str)
        if not match:
            return None
            
        data_str = match.group(1)
        fields = data_str.split(',')
        
        if len(fields) < 30:
            return None
        
        # 解析字段（新浪财经标准格式）
        stock_data = {
            'name': fields[0],                     # 股票名称
            'open': float(fields[1]),              # 开盘价
            'pre_close': float(fields[2]),         # 昨收
            'price': float(fields[3]),             # 当前价格
            'high': float(fields[4]),              # 最高价
            'low': float(fields[5]),               # 最低价
            'bid': float(fields[6]),               # 买一价
            'ask': float(fields[7]),               # 卖一价
            'volume': int(fields[8]),              # 成交量（手）
            'amount': float(fields[9]),            # 成交额（万）
            'bid1_volume': int(fields[10]),        # 买一量
            'bid1_price': float(fields[11]),       # 买一价
            'bid2_volume': int(fields[12]),        # 买二量
            'bid2_price': float(fields[13]),       # 买二价
            'bid3_volume': int(fields[14]),        # 买三量
            'bid3_price': float(fields[15]),       # 买三价
            'bid4_volume': int(fields[16]),        # 买四量
            'bid4_price': float(fields[17]),       # 买四价
            'bid5_volume': int(fields[18]),        # 买五量
            'bid5_price': float(fields[19]),       # 买五价
            'ask1_volume': int(fields[20]),        # 卖一量
            'ask1_price': float(fields[21]),       # 卖一价

            'ask2_volume': int(fields[22]),        # 卖二量
            'ask2_price': float(fields[23]),       # 卖二价
            'ask3_volume': int(fields[24]),        # 卖三量
            'ask3_price': float(fields[25]),       # 卖三价

            'ask4_volume': int(fields[26]),        # 卖四量

            'ask4_price': float(fields[27]),       # 卖四价

            'ask5_volume': int(fields[28]),        # 卖五量

            'ask5_price': float(fields[29]),       # 卖五价

            'date': fields[30] if len(fields) > 30 else '',  # 日期

            'time': fields[31] if len(fields) > 31 else '',  # 时间

        }
        
        # 计算涨跌幅

        if stock_data['pre_close'] > 0:

            stock_data['change'] = stock_data['price'] - stock_data['pre_close']

            stock_data['change_pct'] = stock_data['change'] / stock_data['pre_close'] * 100

        else:

            stock_data['change'] = 0

            stock_data['change_pct'] = 0
        
        return stock_data
    
    def get_realtime_quote(self, symbol):
        """
        获取实时行情
        
        Args:
            symbol: 股票代码，如"000001"
            
        Returns:
            实时行情数据字典
        """
        try:
            # 构建请求
            stock_code = self.get_stock_code(symbol)
            url = f'http://hq.sinajs.cn/list={stock_code}'
            
            # 发送请求
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # 解析数据
                data_str = response.text
                stock_data = self.parse_sina_data(data_str)
                
                if stock_data:
                    return {
                        'symbol': symbol,
                        'name': stock_data['name'],
                        'price': stock_data['price'],
                        'change': stock_data['change'],
                        'change_pct': stock_data['change_pct'],
                        'open': stock_data['open'],
                        'pre_close': stock_data['pre_close'],
                        'high': stock_data['high'],
                        'low': stock_data['low'],
                        'volume': stock_data['volume'] * 100,  # 转换为股数
                        'amount': stock_data['amount'] * 10000,  # 转换为元
                        'bid': stock_data['bid'],
                        'ask': stock_data['ask'],
                        'date': stock_data['date'],
                        'time': stock_data['time'],
                        'timestamp': datetime.now().isoformat(),
                        'source': 'sina_realtime',
                        'success': True
                    }
                else:
                    print(f"❌ 解析 {symbol} 数据失败")
                    return {'symbol': symbol, 'success': False, 'error': '解析失败'}
            else:
                print(f"❌ 获取 {symbol} 数据失败: HTTP {response.status_code}")
                return {'symbol': symbol, 'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据异常: {e}")
            return {'symbol': symbol, 'success': False, 'error': str(e)}
    
    def get_multiple_realtime(self, symbols):
        """获取多只股票实时数据"""
        results = []
        
        for symbol in symbols:
            print(f"📡 获取 {symbol} 实时数据...", end=' ')
            data = self.get_realtime_quote(symbol)
            
            if data.get('success'):
                results.append(data)
                print(f"✅ {data['price']:.2f}元 ({data['change_pct']:+.2f}%)")
            else:
                print(f"❌ 失败")
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': data.get('error', '未知错误'),
                    'timestamp': datetime.now().isoformat()
                })
            
            # 避免请求过快
            time.sleep(0.3)
        
        return results
    
    def test_connection(self):
        """测试连接"""
        print("🔗 测试新浪财经实时接口...")
        
        # 测试几只代表性股票
        test_symbols = ['000001', '600519', '300750', '002475']
        
        print(f"\n📊 测试股票: {', '.join(test_symbols)}")
        print("-" * 60)
        
        results = self.get_multiple_realtime(test_symbols)
        
        success_count = sum(1 for r in results if r.get('success'))
        
        if success_count > 0:
            print(f"\n✅ 连接成功! {success_count}/{len(test_symbols)} 只股票数据获取成功")
            
            # 显示详细数据
            print(f"\n📈 实时行情数据:")
            print(f"{'代码':<8} {'名称':<12} {'价格':<8} {'涨跌':<10} {'成交量':<12} {'时间'}")
            print("-" * 80)
            
            for data in results:
                if data.get('success'):
                    print(f"{data['symbol']:<8} {data['name']:<12} {data['price']:<8.2f} "
                          f"{data['change_pct']:<+10.2f}% {data['volume']:<12,} {data['time']}")
            
            return True
        else:
            print(f"\n❌ 连接失败，所有股票数据获取失败")
            return False

def main():
    """主函数"""
    print("🚀 新浪财经实时数据客户端")
    print("=" * 80)
    
    # 创建客户端
    client = SinaRealTimeClient()
    
    # 测试连接
    if client.test_connection():
        print("\n" + "=" * 80)
        print("🎯 实时数据连接成功!")
        print("=" * 80)
        
        # 测试三号策略相关股票
        print(f"\n📊 三号策略相关股票实时数据:")
        
        strategy_stocks = [
            ('000001', '平安银行'),
            ('600519', '贵州茅台'),
            ('300750', '宁德时代'),
            ('002475', '立讯精密'),
            ('601012', '隆基绿能'),
            ('000333', '美的集团'),
            ('002415', '海康威视'),
            ('300059', '东方财富'),
        ]
        
        symbols = [s[0] for s in strategy_stocks]
        results = client.get_multiple_realtime(symbols)
        
        print(f"\n📈 汇总:")
        print(f"{'代码':<8} {'名称':<12} {'价格':<8} {'涨跌':<10} {'换手率(估算)':<12}")
        print("-" * 80)
        
        for data in results:
            if data.get('success'):
                # 估算换手率（假设流通市值1000亿）
                estimated_turnover = (data['volume'] * data['price']) / 100000000000 * 100
                print(f"{data['symbol']:<8} {data['name']:<12} {data['price']:<8.2f} "
                      f"{data['change_pct']:<+10.2f}% {estimated_turnover:<12.2f}%")
        
        print("\n" + "=" * 80)
        print("💡 下一步:")
        print("-" * 80)
        print("1. ✅ 实时数据连接已建立")
        print("2. 🔧 可以基于实时数据执行三号策略")
        print("3. 📊 需要计算技术指标（MACD、RSI、KDJ、BOLL、DMI）")
        print("4. 🎯 使用实时数据验证策略条件")
        
    else:
        print("\n" + "=" * 80)
        print("⚠️  连接失败，尝试其他方案")
        print("-" * 80)
        print("1. 🔄 尝试腾讯财经接口")
        print("2. 📡 尝试网易财经接口")
        print("3. 🌐 检查网络代理设置")

if __name__ == "__main__":
    main()