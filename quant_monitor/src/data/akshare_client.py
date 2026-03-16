#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare数据客户端
支持A股、港股、期货等市场的实时数据获取
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import yaml
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AKShareClient:
    """AKShare数据客户端"""
    
    def __init__(self, config_path: str = "config/market_config.yaml"):
        """
        初始化AKShare客户端
        
        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.markets = self.config.get('markets', {})
        self.data_cache = {}
        
    def get_a_stock_realtime(self, symbol: str) -> Optional[Dict]:
        """
        获取A股实时行情
        
        Args:
            symbol: 股票代码，如"000001"
            
        Returns:
            实时行情数据字典
        """
        try:
            # 使用AKShare获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 筛选指定股票
            stock_data = df[df['代码'] == symbol]
            
            if not stock_data.empty:
                data = stock_data.iloc[0].to_dict()
                return {
                    'symbol': symbol,
                    'name': data.get('名称', ''),
                    'price': float(data.get('最新价', 0)),
                    'change': float(data.get('涨跌幅', 0)),
                    'change_pct': float(data.get('涨跌额', 0)),
                    'volume': int(data.get('成交量', 0)),
                    'amount': float(data.get('成交额', 0)),
                    'high': float(data.get('最高', 0)),
                    'low': float(data.get('最低', 0)),
                    'open': float(data.get('今开', 0)),
                    'pre_close': float(data.get('昨收', 0)),
                    'bid': float(data.get('买一', 0)),
                    'ask': float(data.get('卖一', 0)),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"未找到股票 {symbol} 的实时数据")
                return None
                
        except Exception as e:
            logger.error(f"获取A股实时数据失败: {e}")
            return None
    
    def get_hk_stock_realtime(self, symbol: str) -> Optional[Dict]:
        """
        获取港股实时行情
        
        Args:
            symbol: 股票代码，如"00700"
            
        Returns:
            实时行情数据字典
        """
        try:
            df = ak.stock_hk_spot_em()
            
            stock_data = df[df['代码'] == symbol]
            
            if not stock_data.empty:
                data = stock_data.iloc[0].to_dict()
                return {
                    'symbol': symbol,
                    'name': data.get('名称', ''),
                    'price': float(data.get('最新价', 0)),
                    'change': float(data.get('涨跌额', 0)),
                    'change_pct': float(data.get('涨跌幅', 0)),
                    'volume': int(data.get('成交量', 0)),
                    'amount': float(data.get('成交额', 0)),
                    'high': float(data.get('最高', 0)),
                    'low': float(data.get('最低', 0)),
                    'open': float(data.get('今开', 0)),
                    'pre_close': float(data.get('昨收', 0)),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"未找到港股 {symbol} 的实时数据")
                return None
                
        except Exception as e:
            logger.error(f"获取港股实时数据失败: {e}")
            return None
    
    def get_futures_realtime(self, symbol: str) -> Optional[Dict]:
        """
        获取期货实时行情
        
        Args:
            symbol: 期货代码，如"IF00"
            
        Returns:
            实时行情数据字典
        """
        try:
            # 根据期货代码选择不同的数据源
            if symbol.startswith('IF') or symbol.startswith('IC') or symbol.startswith('IH'):
                # 股指期货
                df = ak.futures_zh_realtime(symbol=symbol)
            else:
                # 商品期货
                df = ak.futures_zh_spot(symbol=symbol)
            
            if not df.empty:
                data = df.iloc[0].to_dict()
                return {
                    'symbol': symbol,
                    'name': data.get('名称', ''),
                    'price': float(data.get('最新价', 0)),
                    'change': float(data.get('涨跌幅', 0)),
                    'volume': int(data.get('成交量', 0)),
                    'open_interest': int(data.get('持仓量', 0)),
                    'bid': float(data.get('买一价', 0)),
                    'ask': float(data.get('卖一价', 0)),
                    'high': float(data.get('最高价', 0)),
                    'low': float(data.get('最低价', 0)),
                    'open': float(data.get('今开盘', 0)),
                    'pre_close': float(data.get('昨收盘', 0)),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"未找到期货 {symbol} 的实时数据")
                return None
                
        except Exception as e:
            logger.error(f"获取期货实时数据失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, market: str = 'a_stock', 
                           period: str = 'daily', start_date: str = None, 
                           end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            symbol: 标的代码
            market: 市场类型
            period: 周期，如'daily', 'weekly', 'monthly'
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            历史数据DataFrame
        """
        try:
            if market == 'a_stock':
                # A股历史数据
                if period == 'daily':
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                          start_date=start_date, end_date=end_date)
                elif period == 'weekly':
                    df = ak.stock_zh_a_hist(symbol=symbol, period="weekly",
                                          start_date=start_date, end_date=end_date)
                elif period == 'monthly':
                    df = ak.stock_zh_a_hist(symbol=symbol, period="monthly",
                                          start_date=start_date, end_date=end_date)
                    
            elif market == 'hk_stock':
                # 港股历史数据
                df = ak.stock_hk_hist(symbol=symbol, period=period,
                                    start_date=start_date, end_date=end_date)
                    
            elif market == 'futures':
                # 期货历史数据
                df = ak.futures_main_sina(symbol=symbol, start_date=start_date,
                                        end_date=end_date)
            
            if df is not None and not df.empty:
                # 标准化列名
                df.columns = [col.strip() for col in df.columns]
                return df
            else:
                logger.warning(f"未找到 {symbol} 的历史数据")
                return None
                
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return None
    
    def get_market_overview(self) -> Dict:
        """
        获取市场概览
        
        Returns:
            市场概览数据
        """
        try:
            overview = {}
            
            # 获取上证指数
            sh_index = ak.stock_zh_index_spot()
            sh_data = sh_index[sh_index['代码'] == '000001'].iloc[0].to_dict()
            overview['shanghai'] = {
                'index': float(sh_data.get('最新价', 0)),
                'change': float(sh_data.get('涨跌幅', 0)),
                'volume': int(sh_data.get('成交量', 0))
            }
            
            # 获取深证成指
            sz_index = ak.stock_sz_a_spot()
            sz_data = sz_index[sz_index['代码'] == '399001'].iloc[0].to_dict()
            overview['shenzhen'] = {
                'index': float(sz_data.get('最新价', 0)),
                'change': float(sz_data.get('涨跌幅', 0)),
                'volume': int(sz_data.get('成交量', 0))
            }
            
            # 获取创业板指
            cy_index = ak.stock_cy_a_spot()
            cy_data = cy_index[cy_index['代码'] == '399006'].iloc[0].to_dict()
            overview['chinext'] = {
                'index': float(cy_data.get('最新价', 0)),
                'change': float(cy_data.get('涨跌幅', 0)),
                'volume': int(cy_data.get('成交量', 0))
            }
            
            # 获取市场情绪指标
            overview['timestamp'] = datetime.now().isoformat()
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {}
    
    def update_all_markets(self) -> Dict:
        """
        更新所有市场数据
        
        Returns:
            所有市场数据字典
        """
        all_data = {}
        
        for market_name, market_config in self.markets.items():
            if market_config.get('enabled', False):
                market_data = {}
                symbols = market_config.get('symbols', [])
                
                for symbol in symbols:
                    if market_name == 'a_stock':
                        data = self.get_a_stock_realtime(symbol)
                    elif market_name == 'hk_stock':
                        data = self.get_hk_stock_realtime(symbol)
                    elif market_name == 'futures':
                        data = self.get_futures_realtime(symbol)
                    else:
                        continue
                    
                    if data:
                        market_data[symbol] = data
                
                if market_data:
                    all_data[market_name] = market_data
        
        # 缓存数据
        self.data_cache = all_data
        return all_data
    
    def save_to_json(self, filepath: str = "data/latest_market_data.json"):
        """
        保存数据到JSON文件
        
        Args:
            filepath: 文件路径
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 {filepath}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")


if __name__ == "__main__":
    # 测试代码
    client = AKShareClient()
    
    # 测试A股数据
    a_stock_data = client.get_a_stock_realtime("000001")
    print("A股测试数据:", a_stock_data)
    
    # 测试港股数据
    hk_stock_data = client.get_hk_stock_realtime("00700")
    print("港股测试数据:", hk_stock_data)
    
    # 测试期货数据
    futures_data = client.get_futures_realtime("IF00")
    print("期货测试数据:", futures_data)
    
    # 测试市场概览
    overview = client.get_market_overview()
    print("市场概览:", overview)
    
    # 保存数据
    client.save_to_json()