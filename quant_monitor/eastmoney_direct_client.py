#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接连接东方财富API获取实时数据
不使用AKShare，直接调用东方财富公开接口
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EastMoneyDirectClient:
    """东方财富直接客户端"""
    
    # 东方财富公开API接口
    EASTMONEY_API = {
        # 实时行情
        'realtime': 'http://push2.eastmoney.com/api/qt/stock/get',
        
        # 分时数据
        'minute': 'http://push2his.eastmoney.com/api/qt/stock/trends2/get',
        
        # 日K线
        'daily': 'http://push2his.eastmoney.com/api/qt/stock/kline/get',
        
        # 实时资金流向
        'capital_flow': 'http://push2.eastmoney.com/api/qt/stock/fflow/kline/get',
        
        # 板块行情
        'sector': 'http://push2.eastmoney.com/api/qt/clist/get',
    }
    
    # A股市场代码映射
    MARKET_CODES = {
        'sh': '1',  # 上海
        'sz': '0',  # 深圳
        'bj': '2',  # 北京
    }
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://quote.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def get_stock_code_with_market(self, symbol):
        """获取带市场前缀的股票代码"""
        if symbol.startswith('60') or symbol.startswith('68'):
            return f'sh{symbol}'
        elif symbol.startswith('00') or symbol.startswith('30'):
            return f'sz{symbol}'
        elif symbol.startswith('43') or symbol.startswith('83') or symbol.startswith('87'):
            return f'bj{symbol}'
        else:
            # 默认上海
            return f'sh{symbol}'
    
    def get_realtime_quote(self, symbol):
        """
        获取实时行情
        
        Args:
            symbol: 股票代码，如"000001"
            
        Returns:
            实时行情数据字典
        """
        try:
            # 构建请求参数
            stock_code = self.get_stock_code_with_market(symbol)
            market_code = self.MARKET_CODES[stock_code[:2]]
            secid = f'{market_code}.{symbol}'
            
            params = {
                'invt': 2,
                'fltt': 2,
                'fields': 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,f268,f250,f251,f252,f253,f254,f255,f256,f257,f258,f266,f269,f270,f271,f273,f274,f275,f127,f199,f128,f198,f118,f193,f196,f194,f195,f197,f130,f132,f69,f182,f39,f40,f95,f96,f124,f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f23,f24,f25,f26,f28,f33,f22,f11,f30,f31,f32,f34,f35,f36,f37,f38,f113,f114,f115,f46,f129,f205,f206,f207,f208,f209,f210,f211,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f277,f278,f279,f288,f152,f153,f154,f285,f286,f287,f292,f293,f294,f295,f263,f279,f288',
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'cb': 'jQuery18309517428310514094_1623913471540',
                '_': str(int(time.time() * 1000)),
            }
            
            # 发送请求
            response = self.session.get(
                self.EASTMONEY_API['realtime'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                # 解析响应（去除JSONP包装）
                text = response.text
                start = text.find('(')
                end = text.rfind(')')
                
                if start != -1 and end != -1:
                    json_str = text[start+1:end]
                    data = json.loads(json_str)
                    
                    if data.get('rc') == 0 and data.get('data'):
                        stock_data = data['data']
                        
                        return {
                            'symbol': symbol,
                            'name': stock_data.get('f58', ''),
                            'price': stock_data.get('f43', 0) / 100,  # 转换为元
                            'change': stock_data.get('f170', 0) / 100,
                            'change_pct': stock_data.get('f171', 0) / 100,
                            'volume': stock_data.get('f47', 0),
                            'amount': stock_data.get('f48', 0),
                            'high': stock_data.get('f44', 0) / 100,
                            'low': stock_data.get('f45', 0) / 100,
                            'open': stock_data.get('f46', 0) / 100,
                            'pre_close': stock_data.get('f60', 0) / 100,
                            'bid': stock_data.get('f9', 0) / 100,
                            'ask': stock_data.get('f10', 0) / 100,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'eastmoney_direct'
                        }
            
            print(f"❌ 获取 {symbol} 实时数据失败: HTTP {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            print(f"❌ 获取 {symbol} 实时数据超时")
            return None
        except Exception as e:
            print(f"❌ 获取 {symbol} 实时数据异常: {e}")
            return None
    
    def get_historical_data(self, symbol, start_date, end_date, period='daily'):
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期，格式'YYYY-MM-DD'
            period: 周期，'daily'/'weekly'/'monthly'
            
        Returns:
            DataFrame with historical data
        """
        try:
            # 构建请求参数
            stock_code = self.get_stock_code_with_market(symbol)
            market_code = self.MARKET_CODES[stock_code[:2]]
            secid = f'{market_code}.{symbol}'
            
            # 日期转换
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            
            # 周期映射
            klt_map = {
                'daily': 101,
                'weekly': 102,
                'monthly': 103,
            }
            klt = klt_map.get(period, 101)
            
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': klt,
                'fqt': 1,  # 前复权
                'beg': start_date_str,
                'end': end_date_str,
                'lmt': 10000,
                '_': str(int(time.time() * 1000)),
            }
            
            # 发送请求
            response = self.session.get(
                self.EASTMONEY_API['daily'],
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                # 解析响应
                data = response.json()
                
                if data.get('rc') == 0 and data.get('data'):
                    stock_data = data['data']
                    
                    if 'klines' in stock_data and stock_data['klines']:
                        # 解析K线数据
                        klines = stock_data['klines']
                        records = []
                        
                        for kline in klines:
                            parts = kline.split(',')
                            if len(parts) >= 11:
                                record = {
                                    'date': parts[0],
                                    'open': float(parts[1]),
                                    'close': float(parts[2]),
                                    'high': float(parts[3]),
                                    'low': float(parts[4]),
                                    'volume': float(parts[5]),
                                    'amount': float(parts[6]),
                                    'amplitude': float(parts[7]),
                                    'pct_change': float(parts[8]),
                                    'change': float(parts[9]),
                                    'turnover': float(parts[10]) if len(parts) > 10 else 0,
                                }
                                records.append(record)
                        
                        df = pd.DataFrame(records)
                        
                        # 转换日期格式
                        df['date'] = pd.to_datetime(df['date'])
                        
                        print(f"✅ 获取 {symbol} 历史数据成功: {len(df)} 条记录")
                        return df
            
            print(f"❌ 获取 {symbol} 历史数据失败: HTTP {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ 获取 {symbol} 历史数据异常: {e}")
            return None
    
    def test_connection(self):
        """测试连接"""
        print("🔗 测试东方财富API连接...")
        
        # 测试实时行情
        test_symbol = '000001'  # 平安银行
        print(f"📊 测试实时行情: {test_symbol}")
        
        realtime_data = self.get_realtime_quote(test_symbol)
        
        if realtime_data:
            print(f"✅ 实时行情连接成功!")
            print(f"   股票: {realtime_data['name']} ({realtime_data['symbol']})")
            print(f"   价格: {realtime_data['price']:.2f}元")
            print(f"   涨跌: {realtime_data['change']:+.2f} ({realtime_data['change_pct']:+.2f}%)")
            print(f"   成交量: {realtime_data['volume']:,}")
            print(f"   成交额: {realtime_data['amount']:,.2f}")
            
            # 测试历史数据
            print(f"\n📈 测试历史数据: {test_symbol}")
            hist_data = self.get_historical_data(
                test_symbol,
                start_date='2026-01-01',
                end_date='2026-02-13',
                period='daily'
            )
            
            if hist_data is not None and not hist_data.empty:
                print(f"✅ 历史数据连接成功!")
                print(f"   数据范围: {hist_data['date'].min().strftime('%Y-%m-%d')} 至 {hist_data['date'].max().strftime('%Y-%m-%d')}")
                print(f"   记录数: {len(hist_data)}")
                
                # 显示最近5天数据
                print(f"\n📅 最近5个交易日:")
                recent = hist_data.tail(5)
                for _, row in recent.iterrows():
                    print(f"   {row['date'].strftime('%m-%d')}: {row['close']:.2f}元 "
                          f"(涨跌: {row['change']:+.2f}, 换手: {row['turnover']:.2%})")
                
                return True
            else:
                print(f"⚠️  历史数据获取失败，但实时行情可用")
                return True
        else:
            print(f"❌ 连接测试失败")
            return False
    
    def get_multiple_stocks_realtime(self, symbols):
        """获取多只股票的实时数据"""
        results = []
        
        for symbol in symbols:
            print(f"📡 获取 {symbol} 实时数据...")
            data = self.get_realtime_quote(symbol)
            
            if data:
                results.append(data)
                print(f"   ✅ 成功: {data['price']:.2f}元 ({data['change_pct']:+.2f}%)")
            else:
                print(f"   ❌ 失败")
                results.append({
                    'symbol': symbol,
                    'error': '获取失败',
                    'timestamp': datetime.now().isoformat()
                })
            
            # 避免请求过快
            time.sleep(0.5)
        
        return results

def main():
    """主函数"""
    print("🚀 直接连接东方财富API测试")
    print("=" * 80)
    
    # 创建客户端
    client = EastMoneyDirectClient()
    
    # 测试连接
    if client.test_connection():
        print("\n" + "=" * 80)
        print("🎯 连接成功! 可以获取实时和历史数据")
        print("=" * 80)
        
        # 示例：获取立讯精密实时数据
        print(f"\n📊 示例: 获取立讯精密(002475)实时数据")
        luxshare_data = client.get_realtime_quote('002475')
        
        if luxshare_data:
            print(f"   股票: {luxshare_data['name']}")
            print(f"   代码: {luxshare_data['symbol']}")
            print(f"   价格: {luxshare_data['price']:.2f}元")
            print(f"   涨跌: {luxshare_data['change']:+.2f} ({luxshare_data['change_pct']:+.2f}%)")
            print(f"   成交量: {luxshare_data['volume']:,}")
            print(f"   成交额: {luxshare_data['amount']:,.2f}")
            print(f"   时间: {luxshare_data['timestamp']}")
        
        # 示例：获取多只股票数据
        print(f"\n📈 示例: 获取多只股票实时数据")
        test_symbols = ['000001', '600519', '300750', '002475']
        multiple_data = client.get_multiple_stocks_realtime(test_symbols)
        
        print(f"\n📊 汇总结果:")
        print(f"{'代码':<8} {'名称':<12} {'价格':<8} {'涨跌':<10} {'成交量':<12}")
        print("-" * 80)
        
        for data in multiple_data:
            if 'error' not in data:
                print(f"{data['symbol']:<8} {data['name']:<12} {data['price']:<8.2f} "
                      f"{data['change_pct']:<+10.2f}% {data['volume']:<12,}")
        
        print("\n" + "=" * 80)
        print("💡 下一步:")
        print("-" * 80)
        print("1. ✅ 实时数据: 可以获取最新价格、成交量等")
        print("2. 📈 历史数据: 可以获取日K线数据")
        print("3. 🎯 策略回测: 可以使用真实数据进行验证")
        print("4. 🔄 实时监控: 可以建立实时策略监控系统")
        
    else:
        print("\n" + "=" * 80)
        print("⚠️  连接失败，可能原因:")
        print("-" * 80)
        print("1. 网络问题: 无法访问东方财富API")
        print("2. API变更: 东方财富接口可能已更新")
        print("3. 限制访问: 可能需要其他认证方式")
        print("\n🔧 备用方案:")
        print("   1. 使用其他数据源（新浪财经、腾讯财经）")
        print("   2. 使用离线数据文件")
        print("   3. 使用模拟数据增强")

if __name__ == "__main__":
    main()