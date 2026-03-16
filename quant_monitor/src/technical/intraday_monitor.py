#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中策略监控器
实时检查一号策略的各个技术条件
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
import yaml
import time
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .indicator_calculator import TechnicalIndicatorCalculator


class IntradayMonitor:
    """盘中策略监控器"""
    
    def __init__(self, config_path: str = "config/strategy_01_technical.yaml"):
        """
        初始化监控器
        
        Args:
            config_path: 策略配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.strategy_config = self.config.get('strategy_01_technical', {})
        self.calculator = TechnicalIndicatorCalculator()
        
        # 监控状态
        self.monitoring_active = False
        self.signals_history = []
        self.stock_signals = {}  # 记录每只股票的触发信号
        
    def check_strategy_conditions(self, stock_data: pd.DataFrame, symbol: str = "") -> Dict:
        """
        检查一号策略的所有条件
        
        Args:
            stock_data: 股票数据DataFrame
            symbol: 股票代码（可选）
            
        Returns:
            策略检查结果
        """
        try:
            if stock_data.empty or len(stock_data) < 50:
                return {'error': '数据不足'}
            
            # 计算所有技术指标
            indicators = self.calculator.calculate_all_indicators(stock_data)
            
            if not indicators:
                return {'error': '指标计算失败'}
            
            # 检查各个条件
            conditions = self._check_all_conditions(indicators)
            
            # 判断是否触发策略
            triggered = self._is_strategy_triggered(conditions)
            
            # 准备结果
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'triggered': triggered,
                'conditions': conditions,
                'indicators_summary': self._get_indicators_summary(indicators)
            }
            
            # 记录信号
            if triggered:
                self._record_signal(result)
                
                # 更新股票信号记录
                if symbol not in self.stock_signals:
                    self.stock_signals[symbol] = []
                self.stock_signals[symbol].append({
                    'time': datetime.now().isoformat(),
                    'conditions': [cond['name'] for cond in conditions.values() if cond['met']]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"检查策略条件失败: {e}")
            return {'error': str(e)}
    
    def _check_all_conditions(self, indicators: Dict) -> Dict:
        """
        检查所有技术条件
        
        Args:
            indicators: 技术指标计算结果
            
        Returns:
            条件检查结果
        """
        conditions = {}
        
        # 条件1：MACD相关（3选1）
        macd_conditions = []
        
        # 1.1 绿柱逐步缩短，有金叉趋势
        macd_info = indicators.get('macd', {})
        green_bar_shrinking = macd_info.get('green_bar_shrinking', False)
        trend_golden = macd_info.get('trend_golden', False)
        macd_conditions.append({
            'name': '绿柱逐步缩短，有金叉趋势',
            'met': green_bar_shrinking and trend_golden,
            'details': {
                'green_bar_shrinking': green_bar_shrinking,
                'trend_golden': trend_golden
            }
        })
        
        # 1.2 金叉
        golden_cross = macd_info.get('golden_cross', False)
        macd_conditions.append({
            'name': '金叉',
            'met': golden_cross,
            'details': {'golden_cross': golden_cross}
        })
        
        # 1.3 底背离最佳
        bottom_divergence = macd_info.get('bottom_divergence', False)
        macd_conditions.append({
            'name': '底背离最佳',
            'met': bottom_divergence,
            'details': {'bottom_divergence': bottom_divergence}
        })
        
        # MACD条件组：3选1
        macd_group_met = any(cond['met'] for cond in macd_conditions)
        conditions['macd_group'] = {
            'name': 'MACD条件组（3选1）',
            'met': macd_group_met,
            'sub_conditions': macd_conditions,
            'details': {
                'above_zero': macd_info.get('above_zero', False),
                'dif': macd_info.get('dif', 0),
                'dea': macd_info.get('dea', 0),
                'macd_bar': macd_info.get('macd_bar', 0)
            }
        }
        
        # 条件2：RSI相关
        rsi_info = indicators.get('rsi', {})
        rsi_golden_cross = rsi_info.get('golden_cross', False)
        rsi6_below_68 = rsi_info.get('below_68', False)
        
        conditions['rsi'] = {
            'name': 'RSI金叉且RSI6≤68',
            'met': rsi_golden_cross and rsi6_below_68,
            'details': {
                'rsi': rsi_info.get('rsi', 0),
                'rsi6': rsi_info.get('rsi6', 0),
                'golden_cross': rsi_golden_cross,
                'below_68': rsi6_below_68
            }
        }
        
        # 条件3：BBI相关
        bbi_info = indicators.get('bbi', {})
        bbi_golden_cross = bbi_info.get('golden_cross', False)
        
        conditions['bbi'] = {
            'name': 'BBI金叉',
            'met': bbi_golden_cross,
            'details': {
                'bbi': bbi_info.get('bbi', 0),
                'close': bbi_info.get('close', 0),
                'golden_cross': bbi_golden_cross
            }
        }
        
        # 条件4：DPO相关
        dpo_info = indicators.get('dpo', {})
        dpo_golden_cross = dpo_info.get('golden_cross', False)
        dpo_angle_gt_20 = dpo_info.get('angle_gt_20', False)
        
        conditions['dpo'] = {
            'name': 'DPO金叉且角度>20度',
            'met': dpo_golden_cross and dpo_angle_gt_20,
            'details': {
                'dpo': dpo_info.get('dpo', 0),
                'madpo': dpo_info.get('madpo', 0),
                'golden_cross': dpo_golden_cross,
                'angle': dpo_info.get('angle', 0),
                'angle_gt_20': dpo_angle_gt_20
            }
        }
        
        # 条件5：OBV相关
        obv_info = indicators.get('obv', {})
        obv_above_ma_5days = obv_info.get('above_ma_5days', False)
        
        conditions['obv'] = {
            'name': 'OBV连续5天在MAOBV上方',
            'met': obv_above_ma_5days,
            'details': {
                'obv': obv_info.get('obv', 0),
                'maobv': obv_info.get('maobv', 0),
                'above_ma': obv_info.get('above_ma', False),
                'above_ma_5days': obv_above_ma_5days
            }
        }
        
        # 条件6：KDJ相关（2选1）
        kdj_info = indicators.get('kdj', {})
        kdj_golden_cross = kdj_info.get('golden_cross', False)
        kdj_trend_golden = kdj_info.get('trend_golden', False)
        
        conditions['kdj'] = {
            'name': 'KDJ金叉或有金叉趋势',
            'met': kdj_golden_cross or kdj_trend_golden,
            'details': {
                'k': kdj_info.get('k', 0),
                'd': kdj_info.get('d', 0),
                'j': kdj_info.get('j', 0),
                'golden_cross': kdj_golden_cross,
                'trend_golden': kdj_trend_golden
            }
        }
        
        # 条件7：DMI相关
        dmi_info = indicators.get('dmi', {})
        di1_cross_adx = dmi_info.get('di1_cross_adx', False)
        
        conditions['dmi'] = {
            'name': 'DI1上穿ADX线',
            'met': di1_cross_adx,
            'details': {
                'plus_di': dmi_info.get('plus_di', 0),
                'minus_di': dmi_info.get('minus_di', 0),
                'adx': dmi_info.get('adx', 0),
                'di1_cross_adx': di1_cross_adx
            }
        }
        
        # 条件8：BOLL相关
        boll_info = indicators.get('boll', {})
        boll_cross_middle = boll_info.get('cross_middle', False)
        boll_trend_up = boll_info.get('trend_up', False)
        
        conditions['boll'] = {
            'name': '股价上穿BOLL中轨且三轨上行',
            'met': boll_cross_middle and boll_trend_up,
            'details': {
                'upper': boll_info.get('upper', 0),
                'middle': boll_info.get('middle', 0),
                'lower': boll_info.get('lower', 0),
                'close': boll_info.get('close', 0),
                'cross_middle': boll_cross_middle,
                'trend_up': boll_trend_up
            }
        }
        
        # 条件9：换手率
        turnover_info = indicators.get('turnover', {})
        turnover_above_5 = turnover_info.get('above_5_percent', False)
        
        conditions['turnover'] = {
            'name': '换手率≥5%',
            'met': turnover_above_5,
            'details': {
                'turnover_rate': turnover_info.get('turnover_rate', 0),
                'above_5_percent': turnover_above_5
            }
        }
        
        # 条件10：成交量
        volume_info = indicators.get('volume_analysis', {})
        vs_yesterday_double = volume_info.get('vs_yesterday_double', False)
        
        conditions['volume'] = {
            'name': '虚拟成交量≥昨日2倍',
            'met': vs_yesterday_double,
            'details': {
                'latest_volume': volume_info.get('latest_volume', 0),
                'prev_volume': volume_info.get('prev_volume', 0),
                'vs_yesterday_ratio': volume_info.get('vs_yesterday_ratio', 0),
                'virtual_volume': volume_info.get('virtual_volume', 0),
                'vs_yesterday_double': vs_yesterday_double
            }
        }
        
        return conditions
    
    def _is_strategy_triggered(self, conditions: Dict) -> bool:
        """
        判断策略是否触发
        
        Args:
            conditions: 所有条件检查结果
            
        Returns:
            是否触发策略
        """
        # 统计满足的条件数量
        met_conditions = [cond for cond in conditions.values() if cond['met']]
        
        # 策略触发逻辑：满足任一条件即可
        return len(met_conditions) > 0
    
    def _get_indicators_summary(self, indicators: Dict) -> Dict:
        """
        获取指标摘要
        
        Args:
            indicators: 所有指标结果
            
        Returns:
            指标摘要
        """
        summary = {}
        
        # MACD摘要
        macd = indicators.get('macd', {})
        summary['macd'] = {
            'dif': round(macd.get('dif', 0), 3),
            'dea': round(macd.get('dea', 0), 3),
            'bar': round(macd.get('macd_bar', 0), 3),
            'above_zero': macd.get('above_zero', False)
        }
        
        # RSI摘要
        rsi = indicators.get('rsi', {})
        summary['rsi'] = {
            'rsi6': round(rsi.get('rsi6', 0), 2),
            'golden_cross': rsi.get('golden_cross', False)
        }
        
        # KDJ摘要
        kdj = indicators.get('kdj', {})
        summary['kdj'] = {
            'k': round(kdj.get('k', 0), 2),
            'd': round(kdj.get('d', 0), 2),
            'j': round(kdj.get('j', 0), 2)
        }
        
        # BOLL摘要
        boll = indicators.get('boll', {})
        summary['boll'] = {
            'upper': round(boll.get('upper', 0), 2),
            'middle': round(boll.get('middle', 0), 2),
            'lower': round(boll.get('lower', 0), 2),
            'close': round(boll.get('close', 0), 2)
        }
        
        # 成交量摘要
        volume = indicators.get('volume_analysis', {})
        summary['volume'] = {
            'vs_yesterday_ratio': round(volume.get('vs_yesterday_ratio', 0), 2),
            'virtual_volume': volume.get('virtual_volume', 0)
        }
        
        return summary
    
    def _record_signal(self, signal_result: Dict):
        """
        记录信号
        
        Args:
            signal_result: 信号结果
        """
        signal = {
            'timestamp': datetime.now().isoformat(),
            'symbol': signal_result.get('symbol', ''),
            'triggered': signal_result.get('triggered', False),
            'met_conditions': [
                cond['name'] for cond in signal_result.get('conditions', {}).values() 
                if cond.get('met', False)
            ],
            'indicators_summary': signal_result.get('indicators_summary', {})
        }
        
        self.signals_history.append(signal)
        
        # 只保留最近1000个信号
        if len(self.signals_history) > 1000:
            self.signals_history = self.signals_history[-1000:]
        
        logger.info(f"策略触发信号记录: {signal}")
    
    def generate_monitoring_report(self, stock_results: List[Dict]) -> str:
        """
        生成监控报告
        
        Args:
            stock_results: 各股票检查结果
            
        Returns:
            监控报告文本
        """
        report_lines = [
            "=" * 70,
            "一号策略 - 盘中实时监控报告",
            "=" * 70,
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"策略名称: {self.strategy_config.get('name', '盘中技术分析一号策略')}",
            ""
        ]
        
        # 统计信息
        triggered_stocks = [r for r in stock_results if r.get('triggered', False)]
        total_stocks = len(stock_results)
        
        report_lines.append("📊 监控统计:")
        report_lines.append("-" * 40)
        report_lines.append(f"  监控股票总数: {total_stocks}")
        report_lines.append(f"  触发策略股票: {len(triggered_stocks)}")
        report_lines.append(f"  触发率: {len(triggered_stocks)/total_stocks*100:.1f}%")
        report_lines.append("")
        
        # 触发股票清单
        if triggered_stocks:
            report_lines.append("🏆 触发策略股票清单:")
            report_lines.append("-" * 40)
            report_lines.append(f"{'排名':<4} {'代码':<8} {'名称':<12} {'触发条件':<30}")
            report_lines.append("-" * 40)
            
            for i, stock in enumerate(triggered_stocks, 1):
                symbol = stock.get('symbol', '')
                conditions = stock.get('conditions', {})
                
                # 获取触发的条件名称
                met_conditions = [
                    cond['name'] for cond in conditions.values() 
                    if cond.get('met', False)
                ]
                
                # 显示前3个触发条件
                display_conditions = ', '.join(met_conditions[:3])
                if len(met_conditions) > 3:
                    display_conditions += f" 等{len(met_conditions)}个条件"
                
                report_lines.append(f"{i:<4} {symbol:<8} {'':<12} {display_conditions:<30}")
            
            report_lines.append("")
            
            # 详细分析前3只股票
            report_lines.append("📋 详细分析（前3只股票）:")
            report_lines.append("-" * 40)
            
            for i, stock in enumerate(triggered_stocks[:3], 1):
                symbol = stock.get('symbol', '')
                conditions = stock.get('conditions', {})
                
                report_lines.append(f"\n{i}. {symbol}:")
                
                # 显示关键指标
                indicators = stock.get('indicators_summary', {})
                
                if 'macd' in indicators:
                    macd = indicators['macd']
                    report_lines.append(f"   MACD: DIF={macd['dif']}, DEA={macd['dea']}, BAR={macd['bar']}")
                
                if 'rsi' in indicators:
                    rsi = indicators['rsi']
                    report_lines.append(f"   RSI6: {rsi['rsi6']}")
                
                if 'volume' in indicators:
                    volume = indicators['volume']
                    report_lines.append(f"   成交量比: {volume['vs_yesterday_ratio']}倍")
                
                # 显示触发的具体条件
                met_conditions = [
                    cond['name'] for cond in conditions.values() 
                    if cond.get('met', False)
                ]
                
                report_lines.append(f"   触发条件: {', '.join(met_conditions)}")
        
        else:
            report_lines.append("⚠️ 当前无股票触发策略")
            report_lines.append("")
            
            # 显示接近触发的股票
            close_stocks = []
            for stock in stock_results:
                conditions = stock.get('conditions', {})
                met_count = sum(1 for cond in conditions.values() if cond.get('met', False))
                if met_count > 0:
                    close_stocks.append((stock.get('symbol', ''), met_count))
            
            if close_stocks:
                close_stocks.sort(key=lambda x: x[1], reverse=True)
                report_lines.append("📈 接近触发的股票:")
                report_lines.append("-" * 40)
                for symbol, count in close_stocks[:5]:
                    report_lines.append(f"  {symbol}: 满足{count}个条件")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def save_signals_history(self, filepath: str = "data/signals_history.json"):
        """
        保存信号历史
        
        Args:
            filepath: 保存路径
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.signals_history, f, ensure_ascii=False, indent=2)
            logger.info(f"信号历史已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存信号历史失败: {e}")
    
    def start_monitoring(self, stock_list: List[str], interval_seconds: int = 60):
        """
        开始实时监控
        
        Args:
            stock_list: 股票代码列表
            interval_seconds: 检查间隔（秒）
        """
        self.monitoring_active = True
        logger.info(f"开始实时监控，监控{len(stock_list)}只股票，间隔{interval_seconds}秒")
        
        try:
            while self.monitoring_active:
                # 检查每只股票
                results = []
                for symbol in stock_list:
                    # 这里需要获取实时数据
                    # 暂时使用模拟数据
                    stock_data = self._get_mock_intraday_data(symbol)
                    
                    result = self.check_strategy_conditions(stock_data, symbol)
                    results.append(result)
                
                # 生成报告
                report = self.generate_monitoring_report(results)
                print(report)
                
                # 保存当前状态
                self.save_signals_history()
                
                # 等待下一次检查
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        except Exception as e:
            logger.error(f"监控过程中出错: {e}")
        finally:
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        logger.info("停止实时监控")
    
    def _get_mock_intraday_data(self, symbol: str) -> pd.DataFrame:
        """
        获取模拟盘中数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            模拟数据DataFrame
        """
        np.random.seed(hash(symbol) % 10000)
        
        # 生成分钟级数据
        periods = 240  # 4小时交易时间，240分钟
        base_price = np.random.uniform(10, 100)
        
        # 生成随机走势
        returns = np.random.randn(periods) * 0.002  # 日波动率约3%
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 0.5
        lows = prices - np.random.rand(periods) * 0.5
        
        # 生成成交量
        volumes = np.random.randint(100000, 1000000, periods)
        
        # 创建DataFrame
        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes
        })
        
        return data


if __name__ == "__main__":
    # 测试代码
    monitor = IntradayMonitor()
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    close = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    high = close + np.random.rand(100) * 2
    low = close - np.random.rand(100) * 2
    volume = pd.Series(np.random.randint(1000000, 10000000, 100), index=dates)
    
    test_data = pd.DataFrame({
        'close': close,
        'high': high,
        'low': low,
        'volume': volume
    })
    
    # 测试策略检查
    print("测试策略条件检查:")
    result = monitor.check_strategy_conditions(test_data, "000001")
    
    print(f"触发状态: {result.get('triggered', False)}")
    print(f"满足的条件:")
    
    conditions = result.get('conditions', {})
    for name, condition in conditions.items():
        if condition.get('met', False):
            print(f"  ✅ {condition['name']}")
        else:
            print(f"  ❌ {condition['name']}")
    
    # 测试报告生成
    print("\n测试报告生成:")
    report = monitor.generate_monitoring_report([result])
    print(report)