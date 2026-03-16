#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试东方财富数据接口
使用更稳定的公开接口
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime

def test_eastmoney_simple():
    """测试简单接口"""
    print("🔗 测试东方财富简单接口")
    print("=" * 60)
    
    # 方法1: 使用东方财富的公开数据接口
    test_cases = [
        {
            'name': '实时行情接口',
            'url': 'http://qt.gtimg.cn/q=sh000001,sz399001',
            'method': 'GET'
        },
        {
            'name': '新浪财经接口（备用）',
            'url': 'http://hq.sinajs.cn/list=sh000001,sz399001',
            'method': 'GET'
        },
        {
            'name': '腾讯财经接口（备用）',
            'url': 'http://qt.gtimg.cn/q=sh000001',
            'method': 'GET'
        }
    ]
    
    for test in test_cases:
        print(f"\n📡 测试: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://finance.sina.com.cn',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(test['url'], headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ HTTP状态: {response.status_code}")
                print(f"   响应长度: {len(response.text)} 字节")
                
                # 显示部分内容
                content = response.text[:200]
                print(f"   内容预览: {content}")
                
                # 尝试解析
                if 'v_sh000001' in response.text or 'var hq_str_sh000001' in response.text:
                    print(f"   🎯 成功获取股票数据!")
                    
                    # 解析数据
                    lines = response.text.strip().split(';')
                    for line in lines:
                        if line and ('sh000001' in line or 'sz399001' in line):
                            print(f"   原始数据: {line[:100]}...")
                            
                            # 尝试提取数据
                            if '="' in line:
                                data_part = line.split('="')[1].rstrip('"')
                                fields = data_part.split(',')
                                
                                if len(fields) > 5:
                                    print(f"   解析字段数: {len(fields)}")
                                    print(f"   样例数据: {fields[:5]}")
                                    return True
                else:
                    print(f"   ⚠️  响应格式不符")
            else:
                print(f"   ❌ HTTP状态: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    return False

def test_stock_specific():
    """测试特定股票数据"""
    print("\n" + "=" * 60)
    print("📊 测试特定股票数据获取")
    print("=" * 60)
    
    # 测试几只代表性股票
    test_stocks = [
        ('000001', '平安银行'),
        ('600519', '贵州茅台'),
        ('300750', '宁德时代'),
        ('002475', '立讯精密')
    ]
    
    for symbol, name in test_stocks:
        print(f"\n🔍 测试 {symbol} - {name}")
        
        # 构建请求代码
        if symbol.startswith('60') or symbol.startswith('68'):
            market = 'sh'
        elif symbol.startswith('00') or symbol.startswith('30'):
            market = 'sz'
        else:
            market = 'sh'
        
        stock_code = f'{market}{symbol}'
        
        # 尝试多个接口
        interfaces = [
            f'http://hq.sinajs.cn/list={stock_code}',
            f'http://qt.gtimg.cn/q={stock_code}',
            f'http://api.money.126.net/data/feed/{stock_code}'
        ]
        
        for i, url in enumerate(interfaces, 1):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and len(response.text) > 10:
                    print(f"   接口{i}: ✅ 成功 (长度: {len(response.text)})")
                    
                    # 简单解析
                    content = response.text
                    if '当前价' in content or '最新价' in content or ',' in content:
                        # 提取数字
                        import re
                        numbers = re.findall(r'\d+\.?\d*', content)
                        if numbers:
                            print(f"   发现数字: {numbers[:3]}...")
                else:
                    print(f"   接口{i}: ❌ 失败 (状态: {response.status_code})")
                    
            except Exception as e:
                print(f"   接口{i}: ❌ 异常 ({e})")
        
        # 避免请求过快
        time.sleep(1)

def test_historical_data():
    """测试历史数据"""
    print("\n" + "=" * 60)
    print("📈 测试历史数据获取")
    print("=" * 60)
    
    # 尝试获取历史数据
    try:
        # 使用简单的公开数据源
        url = 'http://quotes.money.163.com/service/chddata.html'
        params = {
            'code': '0000001',  # 上证指数
            'start': '20260101',
            'end': '20260213',
            'fields': 'TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER'
        }
        
        print(f"   请求: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            lines = content.strip().split('\n')
            
            if len(lines) > 1:
                print(f"   ✅ 获取成功!")
                print(f"   数据行数: {len(lines)}")
                print(f"   表头: {lines[0]}")
                print(f"   最新数据: {lines[1] if len(lines) > 1 else '无'}")
                return True
            else:
                print(f"   ⚠️  数据为空")
        else:
            print(f"   ❌ HTTP状态: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    return False

def main():
    """主函数"""
    print("🚀 东方财富数据连接测试")
    print("=" * 60)
    
    # 测试简单接口
    simple_success = test_eastmoney_simple()
    
    # 测试特定股票
    test_stock_specific()
    
    # 测试历史数据
    hist_success = test_historical_data()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    if simple_success or hist_success:
        print("✅ 部分接口可用")
        print("\n💡 可用方案:")
        print("   1. 使用新浪财经/腾讯财经接口获取实时数据")
        print("   2. 使用网易财经接口获取历史数据")
        print("   3. 组合多个数据源确保稳定性")
    else:
        print("❌ 所有接口测试失败")
        print("\n⚠️  可能原因:")
        print("   1. 网络限制: 无法访问外部金融数据接口")
        print("   2. 接口变更: 公开API可能已更新")
        print("   3. 访问限制: 可能需要代理或特殊配置")
        
        print("\n🔧 建议方案:")
        print("   1. 使用离线数据: 如果有历史数据文件")
        print("   2. 使用模拟数据增强: 基于统计特征")
        print("   3. 申请专业数据API: 如聚宽、米筐等")
        print("   4. 使用券商API: 如有交易账户")
    
    print("\n" + "=" * 60)
    print("🎯 下一步建议:")
    print("-" * 60)
    print("基于当前环境，最可行的方案:")
    print("1. 📊 使用模拟数据增强: 基于市场统计特征")
    print("2. 📁 加载本地历史数据: 如果有CSV文件")
    print("3. 🔄 等待网络恢复后安装AKShare")
    print("4. 🧪 先优化策略逻辑，再获取真实数据验证")

if __name__ == "__main__":
    main()