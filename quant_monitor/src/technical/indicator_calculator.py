#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算引擎
计算MACD、RSI、KDJ、BOLL、DMI、DPO、BBI、OBV等指标
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicatorCalculator:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        pass
    
    # ==================== MACD指标 ====================
    def calculate_macd(self, close_prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Dict:
        """
        计算MACD指标
        
        Args:
            close_prices: 收盘价序列
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            MACD指标字典
        """
        try:
            if len(close_prices) < slow_period:
                return {}
            
            # 计算EMA
            ema_fast = close_prices.ewm(span=fast_period, adjust=False).mean()
            ema_slow = close_prices.ewm(span=slow_period, adjust=False).mean()
            
            # 计算DIF
            dif = ema_fast - ema_slow
            
            # 计算DEA
            dea = dif.ewm(span=signal_period, adjust=False).mean()
            
            # 计算MACD柱状图
            macd_bar = (dif - dea) * 2
            
            # 获取最新值
            latest_dif = dif.iloc[-1]
            latest_dea = dea.iloc[-1]
            latest_macd_bar = macd_bar.iloc[-1]
            
            # 判断位置
            above_zero = latest_dif > 0
            
            # 判断金叉死叉
            golden_cross = False
            if len(dif) >= 2 and len(dea) >= 2:
                prev_dif = dif.iloc[-2]
                prev_dea = dea.iloc[-2]
                golden_cross = (prev_dif <= prev_dea) and (latest_dif > latest_dea)
            
            # 判断绿柱缩短
            green_bar_shrinking = False
            if len(macd_bar) >= 3 and latest_macd_bar < 0:
                prev_bar = macd_bar.iloc[-2]
                prev2_bar = macd_bar.iloc[-3]
                green_bar_shrinking = (prev_bar < prev2_bar) and (latest_macd_bar > prev_bar)
            
            # 判断底背离（简化版）
            bottom_divergence = False
            if len(close_prices) >= 20:
                # 检查价格低点但MACD高点
                price_low = close_prices.iloc[-10:].min()
                macd_high = dif.iloc[-10:].max()
                # 简化判断
                if price_low == close_prices.iloc[-1] and dif.iloc[-1] > dif.iloc[-10]:
                    bottom_divergence = True
            
            return {
                'dif': latest_dif,
                'dea': latest_dea,
                'macd_bar': latest_macd_bar,
                'above_zero': above_zero,
                'golden_cross': golden_cross,
                'green_bar_shrinking': green_bar_shrinking,
                'bottom_divergence': bottom_divergence,
                'trend_golden': green_bar_shrinking and not golden_cross  # 有金叉趋势
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return {}
    
    # ==================== RSI指标 ====================
    def calculate_rsi(self, close_prices: pd.Series, period: int = 6) -> Dict:
        """
        计算RSI指标
        
        Args:
            close_prices: 收盘价序列
            period: RSI周期（默认6）
            
        Returns:
            RSI指标字典
        """
        try:
            if len(close_prices) < period + 1:
                return {}
            
            # 计算价格变化
            delta = close_prices.diff()
            
            # 计算上涨和下跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # 计算RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 获取最新值
            latest_rsi = rsi.iloc[-1]
            
            # 判断金叉（简化：RSI上穿50）
            golden_cross = False
            if len(rsi) >= 2:
                prev_rsi = rsi.iloc[-2]
                golden_cross = prev_rsi <= 50 and latest_rsi > 50
            
            return {
                'rsi': latest_rsi,
                'rsi6': latest_rsi if period == 6 else None,
                'golden_cross': golden_cross,
                'below_68': latest_rsi <= 68
            }
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return {}
    
    # ==================== KDJ指标 ====================
    def calculate_kdj(self, high_prices: pd.Series, low_prices: pd.Series, 
                     close_prices: pd.Series, period: int = 9) -> Dict:
        """
        计算KDJ指标
        
        Args:
            high_prices: 最高价序列
            low_prices: 最低价序列
            close_prices: 收盘价序列
            period: KDJ周期
            
        Returns:
            KDJ指标字典
        """
        try:
            if len(close_prices) < period:
                return {}
            
            # 计算RSV
            lowest_low = low_prices.rolling(window=period).min()
            highest_high = high_prices.rolling(window=period).max()
            rsv = 100 * ((close_prices - lowest_low) / (highest_high - lowest_low))
            
            # 计算K、D、J值
            k = rsv.ewm(com=2).mean()  # 默认平滑因子3
            d = k.ewm(com=2).mean()
            j = 3 * k - 2 * d
            
            # 获取最新值
            latest_k = k.iloc[-1]
            latest_d = d.iloc[-1]
            latest_j = j.iloc[-1]
            
            # 判断金叉
            golden_cross = False
            if len(k) >= 2 and len(d) >= 2:
                prev_k = k.iloc[-2]
                prev_d = d.iloc[-2]
                golden_cross = (prev_k <= prev_d) and (latest_k > latest_d)
            
            # 判断金叉趋势（K线向上接近D线）
            trend_golden = False
            if len(k) >= 3 and len(d) >= 3:
                prev_k = k.iloc[-2]
                prev_d = d.iloc[-2]
                prev2_k = k.iloc[-3]
                prev2_d = d.iloc[-3]
                
                # K线向上，D线相对平稳或向下
                k_up = (latest_k > prev_k) and (prev_k > prev2_k)
                d_down = latest_d < prev_d
                approaching = abs(latest_k - latest_d) < abs(prev_k - prev_d)
                
                trend_golden = k_up and approaching and not golden_cross
            
            return {
                'k': latest_k,
                'd': latest_d,
                'j': latest_j,
                'golden_cross': golden_cross,
                'trend_golden': trend_golden
            }
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {e}")
            return {}
    
    # ==================== BOLL指标 ====================
    def calculate_boll(self, close_prices: pd.Series, period: int = 20, 
                      std_dev: int = 2) -> Dict:
        """
        计算BOLL指标
        
        Args:
            close_prices: 收盘价序列
            period: 布林带周期
            std_dev: 标准差倍数
            
        Returns:
            BOLL指标字典
        """
        try:
            if len(close_prices) < period:
                return {}
            
            # 计算中轨
            middle = close_prices.rolling(window=period).mean()
            
            # 计算标准差
            std = close_prices.rolling(window=period).std()
            
            # 计算上下轨
            upper = middle + std_dev * std
            lower = middle - std_dev * std
            
            # 获取最新值
            latest_close = close_prices.iloc[-1]
            latest_middle = middle.iloc[-1]
            latest_upper = upper.iloc[-1]
            latest_lower = lower.iloc[-1]
            
            # 判断上穿中轨
            cross_middle = False
            if len(close_prices) >= 2 and len(middle) >= 2:
                prev_close = close_prices.iloc[-2]
                prev_middle = middle.iloc[-2]
                cross_middle = (prev_close <= prev_middle) and (latest_close > latest_middle)
            
            # 判断三轨上行
            trend_up = False
            if len(middle) >= 3 and len(upper) >= 3 and len(lower) >= 3:
                middle_up = middle.iloc[-1] > middle.iloc[-2] > middle.iloc[-3]
                upper_up = upper.iloc[-1] > upper.iloc[-2] > upper.iloc[-3]
                lower_up = lower.iloc[-1] > lower.iloc[-2] > lower.iloc[-3]
                trend_up = middle_up and upper_up and lower_up
            
            return {
                'upper': latest_upper,
                'middle': latest_middle,
                'lower': latest_lower,
                'close': latest_close,
                'cross_middle': cross_middle,
                'trend_up': trend_up
            }
            
        except Exception as e:
            logger.error(f"计算BOLL失败: {e}")
            return {}
    
    # ==================== DMI指标 ====================
    def calculate_dmi(self, high_prices: pd.Series, low_prices: pd.Series, 
                     close_prices: pd.Series, period: int = 14) -> Dict:
        """
        计算DMI指标
        
        Args:
            high_prices: 最高价序列
            low_prices: 最低价序列
            close_prices: 收盘价序列
            period: DMI周期
            
        Returns:
            DMI指标字典
        """
        try:
            if len(close_prices) < period + 1:
                return {}
            
            # 计算TR
            tr1 = high_prices - low_prices
            tr2 = abs(high_prices - close_prices.shift(1))
            tr3 = abs(low_prices - close_prices.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 计算+DM和-DM
            up_move = high_prices - high_prices.shift(1)
            down_move = low_prices.shift(1) - low_prices
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            # 平滑处理
            atr = tr.rolling(window=period).mean()
            plus_di = 100 * pd.Series(plus_dm, index=high_prices.index).rolling(window=period).mean() / atr
            minus_di = 100 * pd.Series(minus_dm, index=high_prices.index).rolling(window=period).mean() / atr
            
            # 计算ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            # 获取最新值
            latest_plus_di = plus_di.iloc[-1]
            latest_minus_di = minus_di.iloc[-1]
            latest_adx = adx.iloc[-1]
            
            # 判断DI1上穿ADX
            di1_cross_adx = False
            if len(plus_di) >= 2 and len(adx) >= 2:
                prev_plus_di = plus_di.iloc[-2]
                prev_adx = adx.iloc[-2]
                di1_cross_adx = (prev_plus_di <= prev_adx) and (latest_plus_di > latest_adx)
            
            return {
                'plus_di': latest_plus_di,  # DI1
                'minus_di': latest_minus_di,  # DI2
                'adx': latest_adx,
                'di1_cross_adx': di1_cross_adx
            }
            
        except Exception as e:
            logger.error(f"计算DMI失败: {e}")
            return {}
    
    # ==================== DPO指标 ====================
    def calculate_dpo(self, close_prices: pd.Series, period: int = 20) -> Dict:
        """
        计算DPO指标
        
        Args:
            close_prices: 收盘价序列
            period: DPO周期
            
        Returns:
            DPO指标字典
        """
        try:
            if len(close_prices) < period * 2:
                return {}
            
            # 计算移动平均
            ma = close_prices.rolling(window=period).mean()
            
            # 计算DPO
            dpo = close_prices.shift(period // 2) - ma
            
            # 计算MADPO
            madpo = dpo.rolling(window=period).mean()
            
            # 获取最新值
            latest_dpo = dpo.iloc[-1]
            latest_madpo = madpo.iloc[-1]
            
            # 判断金叉
            golden_cross = False
            if len(dpo) >= 2 and len(madpo) >= 2:
                prev_dpo = dpo.iloc[-2]
                prev_madpo = madpo.iloc[-2]
                golden_cross = (prev_dpo <= prev_madpo) and (latest_dpo > latest_madpo)
            
            # 计算角度（简化版）
            angle = 0
            if len(dpo) >= 3:
                angle = np.degrees(np.arctan2(dpo.iloc[-1] - dpo.iloc[-3], 2))
            
            return {
                'dpo': latest_dpo,
                'madpo': latest_madpo,
                'golden_cross': golden_cross,
                'angle': abs(angle),
                'angle_gt_20': abs(angle) > 20
            }
            
        except Exception as e:
            logger.error(f"计算DPO失败: {e}")
            return {}
    
    # ==================== BBI指标 ====================
    def calculate_bbi(self, close_prices: pd.Series) -> Dict:
        """
        计算BBI指标
        
        Args:
            close_prices: 收盘价序列
            
        Returns:
            BBI指标字典
        """
        try:
            if len(close_prices) < 50:
                return {}
            
            # 计算不同周期的移动平均
            ma3 = close_prices.rolling(window=3).mean()
            ma6 = close_prices.rolling(window=6).mean()
            ma12 = close_prices.rolling(window=12).mean()
            ma24 = close_prices.rolling(window=24).mean()
            
            # 计算BBI
            bbi = (ma3 + ma6 + ma12 + ma24) / 4
            
            # 获取最新值
            latest_close = close_prices.iloc[-1]
            latest_bbi = bbi.iloc[-1]
            
            # 判断金叉
            golden_cross = False
            if len(close_prices) >= 2 and len(bbi) >= 2:
                prev_close = close_prices.iloc[-2]
                prev_bbi = bbi.iloc[-2]
                golden_cross = (prev_close <= prev_bbi) and (latest_close > latest_bbi)
            
            return {
                'bbi': latest_bbi,
                'close': latest_close,
                'golden_cross': golden_cross
            }
            
        except Exception as e:
            logger.error(f"计算BBI失败: {e}")
            return {}
    
    # ==================== OBV指标 ====================
    def calculate_obv(self, close_prices: pd.Series, volumes: pd.Series, 
                     ma_period: int = 30) -> Dict:
        """
        计算OBV指标
        
        Args:
            close_prices: 收盘价序列
            volumes: 成交量序列
            ma_period: 移动平均周期
            
        Returns:
            OBV指标字典
        """
        try:
            if len(close_prices) < 2 or len(volumes) < 2:
                return {}
            
            # 计算OBV
            obv = pd.Series(0, index=close_prices.index)
            obv.iloc[0] = volumes.iloc[0]
            
            for i in range(1, len(close_prices)):
                if close_prices.iloc[i] > close_prices.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volumes.iloc[i]
                elif close_prices.iloc[i] < close_prices.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volumes.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            # 计算MAOBV
            maobv = obv.rolling(window=ma_period).mean()
            
            # 获取最新值
            latest_obv = obv.iloc[-1]
            latest_maobv = maobv.iloc[-1]
            
            # 判断是否连续5天在MAOBV上方
            above_ma_5days = False
            if len(obv) >= 5 and len(maobv) >= 5:
                last_5_obv = obv.iloc[-5:]
                last_5_maobv = maobv.iloc[-5:]
                above_ma_5days = all(last_5_obv > last_5_maobv)
            
            return {
                'obv': latest_obv,
                'maobv': latest_maobv,
                'above_ma': latest_obv > latest_maobv,
                'above_ma_5days': above_ma_5days
            }
            
        except Exception as e:
            logger.error(f"计算OBV失败: {e}")
            return {}
    
    # ==================== 换手率 ====================
    def calculate_turnover(self, volumes: pd.Series, total_shares: float) -> Dict:
        """
        计算换手率
        
        Args:
            volumes: 成交量序列（股数）
            total_shares: 总股本
            
        Returns:
            换手率信息
        """
        try:
            if total_shares <= 0:
                return {}
            
            # 计算日换手率
            turnover_rate = volumes / total_shares
            
            # 获取最新值
            latest_turnover = turnover_rate.iloc[-1] if len(turnover_rate) > 0 else 0
            
            return {
                'turnover_rate': latest_turnover,
                'above_5_percent': latest_turnover >= 0.05
            }
            
        except Exception as e:
            logger.error(f"计算换手率失败: {e}")
            return {}
    
    # ==================== 成交量分析 ====================
    def analyze_volume(self, volumes: pd.Series) -> Dict:
        """
        分析成交量
        
        Args:
            volumes: 成交量序列
            
        Returns:
            成交量分析结果
        """
        try:
            if len(volumes) < 2:
                return {}
            
            latest_volume = volumes.iloc[-1]
            prev_volume = volumes.iloc[-2] if len(volumes) >= 2 else 0
            
            # 对比昨日成交量
            vs_yesterday = latest_volume / prev_volume if prev_volume > 0 else 0
            
            # 虚拟成交量（假设全天维持当前分钟成交量）
            # 这里简化处理，使用当前分钟成交量乘以240（交易日分钟数）
            virtual_volume = latest_volume * 240
            
            return {
                'latest_volume': latest_volume,
                'prev_volume': prev_volume,
                'vs_yesterday_ratio': vs_yesterday,
                'virtual_volume': virtual_volume,
                'vs_yesterday_double': vs_yesterday >= 2.0
            }
            
        except Exception as e:
            logger.error(f"分析成交量失败: {e}")
            return {}
    
    # ==================== 综合计算 ====================
    def calculate_all_indicators(self, stock_data: pd.DataFrame) -> Dict:
        """
        计算所有技术指标
        
        Args:
            stock_data: 股票数据DataFrame，包含columns: ['close', 'high', 'low', 'volume']
            
        Returns:
            所有技术指标结果
        """
        try:
            if stock_data.empty:
                return {}
            
            results = {}
            
            # 提取数据序列
            close = stock_data['close']
            high = stock_data['high']
            low = stock_data['low']
            volume = stock_data['volume']
            
            # 计算各项指标
            results['macd'] = self.calculate_macd(close)
            results['rsi'] = self.calculate_rsi(close, period=6)
            results['kdj'] = self.calculate_kdj(high, low, close)
            results['boll'] = self.calculate_boll(close)
            results['dmi'] = self.calculate_dmi(high, low, close)
            results['dpo'] = self.calculate_dpo(close)
            results['bbi'] = self.calculate_bbi(close)
            results['obv'] = self.calculate_obv(close, volume)
            results['volume_analysis'] = self.analyze_volume(volume)
            
            # 假设总股本（这里需要真实数据）
            total_shares = 1000000000  # 10亿股，示例数据
            results['turnover'] = self.calculate_turnover(volume, total_shares)
            
            return results
            
        except Exception as e:
            logger.error(f"计算所有指标失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    calculator = TechnicalIndicatorCalculator()
    
    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    close = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    high = close + np.random.rand(100) * 2
    low = close - np.random.rand(100) * 2
    volume = pd.Series(np.random.randint(1000000, 10000000, 100), index=dates)
    
    # 创建测试DataFrame
    test_data = pd.DataFrame({
        'close': close,
        'high': high,
        'low': low,
        'volume': volume
    })
    
    # 测试各项指标
    print("测试MACD指标:")
    macd_result = calculator.calculate_macd(close)
    print(macd_result)
    
    print("\n测试RSI指标:")
    rsi_result = calculator.calculate_rsi(close)
    print(rsi_result)
    
    print("\n测试KDJ指标:")
    kdj_result = calculator.calculate_kdj(high, low, close)
    print(kdj_result)
    
    print("\n测试所有指标:")
    all_results = calculator.calculate_all_indicators(test_data)
    for key, value in all_results.items():
        print(f"{key}: {value}")