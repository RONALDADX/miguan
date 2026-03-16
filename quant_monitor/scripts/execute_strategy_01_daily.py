#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行一号策略 - 最近一天A股筛选
简化版条件（已调整）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.technical.indicator_calculator import TechnicalIndicatorCalculator


class Strategy01DailyExecutor:
    """一号策略日度执行器"""
    
    def __init__(self):
        """初始化"""
        self.calculator = TechnicalIndicatorCalculator()
        
        # 创建输出目录
        os.makedirs('results/daily_strategy_01', exist_ok=True)
    
    def get_recent_active_stocks(self) -> List[Tuple[str, str]]:
        """
        获取最近活跃的A股股票
        
        Returns:
            股票列表 [(代码, 名称), ...]
        """
        # 选择最近可能活跃的股票
        active_stocks = [
            # 高换手率股票
            ('300750', '宁德时代'),
            ('300059', '东方财富'),
            ('000725', '京东方A'),
            ('002475', '立讯精密'),
            ('002594', '比亚迪'),
            
            # 大盘活跃股
            ('600519', '贵州茅台'),
            ('601318', '中国平安'),
            ('000858', '五粮液'),
            ('000333', '美的集团'),
            ('600036', '招商银行'),
            
            # 科技活跃股
            ('603986', '兆易创新'),
            ('688981', '中芯国际'),
            ('002049', '紫光国微'),
            ('300124', '汇川技术'),
            ('002415', '海康威视'),
            
            # 消费活跃股
            ('600887', '伊利股份'),
            ('000568', '泸州老窖'),
            ('603288', '海天味业'),
            ('601888', '中国中免'),
            ('600276', '恒瑞医药'),
            
            # 新能源活跃股
            ('601012', '隆基绿能'),
            ('002460', '赣锋锂业'),
            ('300750', '宁德时代'),
            ('002594', '比亚迪'),
            ('601633', '长城汽车'),
            
            # 医药活跃股
            ('603259', '药明康德'),
            ('300122', '智飞生物'),
            ('300142', '沃森生物'),
            ('300015', '爱尔眼科'),
            ('600276', '恒瑞医药'),
        ]
        
        # 去重
        unique_stocks = []
        seen = set()
        for symbol, name in active_stocks:
            if symbol not in seen:
                seen.add(symbol)
                unique_stocks.append((symbol, name))
        
        return unique_stocks
    
    def generate_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        生成最近一天模拟数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            日度数据DataFrame
        """
        np.random.seed(hash(symbol) % 10000 + int(time.time()) % 1000)
        
        # 生成最近20个交易日数据（用于计算指标）
        periods = 20
        base_price = np.random.uniform(10, 200)
        
        # 生成随机走势
        returns = np.random.randn(periods) * 0.02
        
        # 根据股票特性调整波动
        if symbol.startswith('300') or symbol.startswith('688'):
            # 创业板/科创板波动更大
            returns *= 1.5
        
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 2
        lows = prices - np.random.rand(periods) * 2
        
        # 生成成交量（模拟活跃度）
        base_volume = 1000000
        if symbol.startswith('300') or symbol.startswith('688'):
            base_volume *= 2  # 创业板/科创板成交量更大
        
        volumes = np.random.randint(base_volume, base_volume * 10, periods)
        
        # 创建DataFrame
        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes
        })
        
        return data
    
    def check_strategy_01_conditions_simplified(self, indicators: Dict) -> Tuple[bool, Dict]:
        """
        检查简化版一号策略条件
        
        Args:
            indicators: 技术指标计算结果
            
        Returns:
            (是否全部满足, 详细条件结果)
        """
        try:
            conditions = {}
            
            # 条件1：MACD相关（3选1）
            macd_info = indicators.get('macd', {})
            green_shrinking = bool(macd_info.get('green_bar_shrinking', False))
            macd_golden_cross = bool(macd_info.get('golden_cross', False))
            bottom_divergence = bool(macd_info.get('bottom_divergence', False))
            
            macd_condition = green_shrinking or macd_golden_cross or bottom_divergence
            
            conditions['macd'] = {
                'name': 'MACD条件（绿柱缩短/金叉/底背离）',
                'met': macd_condition,
                'details': {
                    'green_shrinking': green_shrinking,
                    'golden_cross': macd_golden_cross,
                    'bottom_divergence': bottom_divergence
                }
            }
            
            # 条件2：RSI金叉
            rsi_info = indicators.get('rsi', {})
            rsi_golden_cross = bool(rsi_info.get('golden_cross', False))
            
            conditions['rsi_golden'] = {
                'name': 'RSI金叉',
                'met': rsi_golden_cross,
                'details': {
                    'rsi_golden_cross': rsi_golden_cross
                }
            }
            
            # 条件3：RSI6≤68
            rsi6_below_68 = bool(rsi_info.get('below_68', False))
            
            conditions['rsi6_limit'] = {
                'name': 'RSI6≤68',
                'met': rsi6_below_68,
                'details': {
                    'rsi6': float(rsi_info.get('rsi6', 0)),
                    'below_68': rsi6_below_68
                }
            }
            
            # 条件4：BBI金叉
            bbi_info = indicators.get('bbi', {})
            bbi_golden_cross = bool(bbi_info.get('golden_cross', False))
            
            conditions['bbi'] = {
                'name': 'BBI金叉',
                'met': bbi_golden_cross,
                'details': {
                    'bbi_golden_cross': bbi_golden_cross
                }
            }
            
            # 条件5：DPO金叉（移除了角度条件）
            dpo_info = indicators.get('dpo', {})
            dpo_golden_cross = bool(dpo_info.get('golden_cross', False))
            
            conditions['dpo'] = {
                'name': 'DPO金叉',
                'met': dpo_golden_cross,
                'details': {
                    'dpo_golden_cross': dpo_golden_cross
                }
            }
            
            # 条件6：OBV在MAOBV上方（简化版）
            obv_info = indicators.get('obv', {})
            obv_above_ma = bool(obv_info.get('above_ma', False))
            
            conditions['obv'] = {
                'name': 'OBV在MAOBV上方',
                'met': obv_above_ma,
                'details': {
                    'obv_above_ma': obv_above_ma
                }
            }
            
            # 条件7：KDJ金叉或有金叉趋势
            kdj_info = indicators.get('kdj', {})
            kdj_golden_cross = bool(kdj_info.get('golden_cross', False))
            kdj_trend_golden = bool(kdj_info.get('trend_golden', False))
            
            kdj_condition = kdj_golden_cross or kdj_trend_golden
            
            conditions['kdj'] = {
                'name': 'KDJ金叉或有金叉趋势',
                'met': kdj_condition,
                'details': {
                    'kdj_golden_cross': kdj_golden_cross,
                    'kdj_trend_golden': kdj_trend_golden
                }
            }
            
            # 条件8：DI1上穿ADX线
            dmi_info = indicators.get('dmi', {})
            di1_cross_adx = bool(dmi_info.get('di1_cross_adx', False))
            
            conditions['dmi'] = {
                'name': 'DI1上穿ADX线',
                'met': di1_cross_adx,
                'details': {
                    'di1_cross_adx': di1_cross_adx
                }
            }
            
            # 条件9：股价上穿BOLL中轨且三轨上行
            boll_info = indicators.get('boll', {})
            boll_cross_middle = bool(boll_info.get('cross_middle', False))
            boll_trend_up = bool(boll_info.get('trend_up', False))
            
            boll_condition = boll_cross_middle and boll_trend_up
            
            conditions['boll'] = {
                'name': '股价上穿BOLL中轨且三轨上行',
                'met': boll_condition,
                'details': {
                    'boll_cross_middle': boll_cross_middle,
                    'boll_trend_up': boll_trend_up
                }
            }
            
            # 条件10：换手率≥5%
            turnover_info = indicators.get('turnover', {})
            turnover_above_5 = bool(turnover_info.get('above_5_percent', False))
            
            conditions['turnover'] = {
                'name': '换手率≥5%',
                'met': turnover_above_5,
                'details': {
                    'turnover_rate': float(turnover_info.get('turnover_rate', 0)),
                    'above_5_percent': turnover_above_5
                }
            }
            
            # 条件11：虚拟成交量≥昨日2倍
            volume_info = indicators.get('volume_analysis', {})
            vs_yesterday_double = bool(volume_info.get('vs_yesterday_double', False))
            
            conditions['volume'] = {
                'name': '虚拟成交量≥昨日2倍',
                'met': vs_yesterday_double,
                'details': {
                    'vs_yesterday_ratio': float(volume_info.get('vs_yesterday_ratio', 0)),
                    'vs_yesterday_double': vs_yesterday_double
                }
            }
            
            # 判断是否全部满足
            all_met = all(cond['met'] for cond in conditions.values())
            
            return all_met, conditions
            
        except Exception as e:
            logger.error(f"检查一号策略条件失败: {e}")
            return False, {'error': str(e)}
    
    def execute_daily_screening(self) -> Dict:
        """
        执行最近一天A股筛选
        
        Returns:
            筛选结果
        """
        print("🚀 开始执行一号策略 - 最近一天A股筛选")
        print("=" * 80)
        print("策略要求：简化版条件（已调整）")
        print("=" * 80)
        print()
        
        # 获取股票池
        stock_universe = self.get_recent_active_stocks()
        print(f"📊 筛选范围: {len(stock_universe)} 只活跃A股股票")
        print("-" * 80)
        print()
        
        results = {
            'screening_time': datetime.now().isoformat(),
            'strategy_name': '一号策略（简化版）',
            'period': '最近一天',
            'total_screened': len(stock_universe),
            'triggered_stocks': [],
            'failed_stocks': [],
            'stock_details': {}
        }
        
        print("🔍 开始逐只分析股票...")
        print("-" * 80)
        
        for i, (symbol, name) in enumerate(stock_universe, 1):
            # 显示进度
            if i % 5 == 0 or i == len(stock_universe):
                print(f"进度: {i}/{len(stock_universe)} ({i/len(stock_universe)*100:.1f}%)")
            
            try:
                # 生成最近一天数据
                stock_data = self.generate_daily_data(symbol)
                
                # 计算技术指标
                indicators = self.calculator.calculate_all_indicators(stock_data)
                
                if not indicators:
                    results['failed_stocks'].append({
                        'symbol': symbol,
                        'name': name,
                        'reason': '指标计算失败'
                    })
                    continue
                
                # 检查策略条件
                all_met, condition_details = self.check_strategy_01_conditions_simplified(indicators)
                
                # 统计满足的条件数量
                met_count = sum(1 for cond in condition_details.values() if cond.get('met', False))
                
                # 存储详细结果
                stock_result = {
                    'symbol': symbol,
                    'name': name,
                    'all_conditions_met': all_met,
                    'met_conditions_count': met_count,
                    'total_conditions': len(condition_details),
                    'conditions': condition_details,
                    'indicators_summary': self._get_indicators_summary(indicators)
                }
                
                results['stock_details'][symbol] = stock_result
                
                if all_met:
                    results['triggered_stocks'].append({
                        'symbol': symbol,
                        'name': name,
                        'met_conditions_count': met_count,
                        'conditions_met': [cond['name'] for cond in condition_details.values() if cond.get('met', False)]
                    })
                else:
                    # 统计失败的条件
                    failed_conditions = [cond['name'] for cond in condition_details.values() if not cond.get('met', False)]
                    results['failed_stocks'].append({
                        'symbol': symbol,
                        'name': name,
                        'met_conditions_count': met_count,
                        'failed_conditions': failed_conditions,
                        'failed_count': len(failed_conditions)
                    })
                    
            except Exception as e:
                logger.error(f"分析股票{symbol}时出错: {e}")
                results['failed_stocks'].append({
                    'symbol': symbol,
                    'name': name,
                    'reason': f'分析出错: {str(e)}'
                })
        
        print()
        print("✅ 筛选完成!")
        print("=" * 80)
        
        return results
    
    def _get_indicators_summary(self, indicators: Dict) -> Dict:
        """获取指标摘要"""
        summary = {}
        
        # DMI摘要
        dmi = indicators.get('dmi', {})
        summary['dmi'] = {
            'plus_di': float(dmi.get('plus_di', 0)),
            'minus_di': float(dmi.get('minus_di', 0)),
            'adx': float(dmi.get('adx', 0))
        }
        
        # RSI摘要
        rsi = indicators.get('rsi', {})
        summary['rsi'] = {
            'rsi6': float(rsi.get('rsi6', 0)),
            'golden_cross': bool(rsi.get('golden_cross', False))
        }
        
        # MACD摘要
        macd = indicators.get('macd', {})
        summary['macd'] = {
            'dif': float(macd.get('dif', 0)),
            'dea': float(macd.get('dea', 0)),
            'bar': float(macd.get('macd_bar', 0))
        }
        
        # BOLL摘要
        boll = indicators.get('boll', {})
        summary['boll'] = {
            'upper': float(boll.get('upper', 0)),
            'middle': float(boll.get('middle', 0)),
            'lower': float(boll.get('lower', 0)),
            'close': float(boll.get('close', 0))
        }
        
        # 换手率
        turnover = indicators.get('turnover', {})
        summary['turnover'] = {
            'rate': float(turnover.get('turnover_rate', 0)) * 100,
            'above_5': bool(turnover.get('above_5_percent', False))
        }
        
        # 成交量
        volume = indicators.get('volume_analysis', {})
        summary['volume'] = {
            'vs_yesterday_ratio': float(volume.get('vs_yesterday_ratio', 0)),
            'vs_yesterday_double': bool(volume.get('vs_yesterday_double', False))
        }
        
        return summary
    
    def generate_report(self, results: Dict) -> str:
        """生成报告"""
        report_lines = [
            "=" * 80,
            "一号策略 - 最近一天A股筛选报告",
            "=" * 80,
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"策略名称: {results['strategy_name']}",
            f"分析周期: {results['period']}",
            ""
        ]
        
        # 统计信息
        total = results['total_screened']
        triggered = len(results['triggered_stocks'])
        
        report_lines.append("📊 筛选统计:")
        report_lines.append("-" * 40)
        report_lines.append(f"  筛选总数: {total:,}")
        report_lines.append(f"  触发策略: {triggered:,}")
        report_lines.append(f"  未通过数: {total - triggered:,}")
        report_lines.append(f"  触发率: {triggered/total*100:.2f}%" if total > 0 else "  触发率: 0.00%")
        report_lines.append("")
        
        # 触发股票清单
        if results['triggered_stocks']:
            report_lines.append("🏆 触发策略股票清单:")
            report_lines.append("=" * 80)
            report_lines.append(f"{'排名':<4} {'代码':<8} {'名称':<12} {'满足条件':<8} {'关键指标':<30}")
            report_lines.append("-" * 80)
            
            # 按条件满足数量排序
            triggered_stocks = results['triggered_stocks']
            triggered_stocks.sort(key=lambda x: x.get('met_conditions_count', 0), reverse=True)
            
            for i, stock in enumerate(triggered_stocks, 1):
                symbol = stock['symbol']
                name = stock['name']
                met_count = stock.get('met_conditions_count', 0)
                
                # 获取详细指标
                details = results['stock_details'].get(symbol, {})
                indicators = details.get('indicators_summary', {})
                
                # 构建关键指标字符串
                key_indicators = []
                if 'macd' in indicators:
                    macd = indicators['macd']
                    key_indicators.append(f"DIF:{macd['dif']:.3f}")
                
                if 'rsi' in indicators:
                    rsi = indicators['rsi']
                    key_indicators.append(f"RSI6:{rsi['rsi6']:.1f}")
                
                if 'turnover' in indicators:
                    turnover = indicators['turnover']
                    key_indicators.append(f"换手:{turnover['rate']:.1f}%")
                
                key_indicators_str = " ".join(key_indicators)
                
                report_lines.append(
                    f"{i:<4} {symbol:<8} {name:<12} "
                    f"{met_count}/11{'':<4} {key_indicators_str:<30}"
                )
            
            report_lines.append("")
        else:
            report_lines.append("⚠️ 最近一天无股票触发策略")
            report_lines.append("")
            
            # 显示接近触发的股票
            failed_stocks = results['failed_stocks']
            if failed_stocks:
                # 按满足条件数量排序
                failed_stocks.sort(key=lambda x: x.get('met_conditions_count', 0), reverse=True)
                
                report_lines.append("📈 接近触发的股票（满足条件最多）:")
                report_lines.append("-" * 40)
                
                for i, stock in enumerate(failed_stocks[:10], 1):
                    symbol = stock['symbol']
                    name = stock['name']
                    met_count = stock.get('met_conditions_count', 0)
                    
                    report_lines.append(f"  {i:2d}. {symbol} - {name}: 满足{met_count}/11个条件")
                
                report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_results(self, results: Dict):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 转换结果为可JSON序列化的格式
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_to_serializable(results)
        
        # 保存详细结果
        detail_file = f"results/daily_strategy_01/detailed_results_{timestamp}.json"
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"📋 详细结果已保存到: {detail_file}")


def main():
    """主函数"""
    print("🚀 一号策略日度筛选系统")
    print("=" * 80)
    print("策略要求：简化版条件（已调整）")
    print("1. MACD绿柱缩短/金叉/底背离（3选1）")
    print("2. RSI金叉")
    print("3. RSI6≤68")
    print("4. BBI金叉")
    print("5. DPO金叉")
    print("6. OBV在MAOBV上方")
    print("7. KDJ金叉或有金叉趋势")
    print("8. DI1上穿ADX线")
    print("9. 股价上穿BOLL中轨且三轨上行")
    print("10. 换手率≥5%")
    print("11. 虚拟成交量≥昨日2倍")
    print("=" * 80)
    
    executor = Strategy01DailyExecutor()
    
    try:
        # 执行日度筛选
        results = executor.execute_daily_screening()
        
        # 生成报告
        report = executor.generate_report(results)
        print(report)
        
        # 保存结果
        executor.save_results(results)
        
        # 显示最终统计
        print("\n🎯 最终统计:")
        print("-" * 40)
        print(f"  筛选总数: {results['total_screened']:,}")
        print(f"  触发策略: {len(results['triggered_stocks']):,}")
        
        if results['triggered_stocks']:
            print(f"  触发率: {len(results['triggered_stocks'])/results['total_screened']*100:.2f}%")
            print(f"\n  重点关注股票:")
            for stock in results['triggered_stocks'][:5]:
                print(f"    • {stock['symbol']} - {stock['name']}")
        else:
            print(f"  触发率: 0.00%")
            
            # 显示满足条件最多的股票
            failed_stocks = results['failed_stocks']
            if failed_stocks:
                failed_stocks.sort(key=lambda x: x.get('met_conditions_count', 0), reverse=True)
                print(f"\n  接近触发股票（满足条件最多）:")
                for stock in failed_stocks[:5]:
                    print(f"    • {stock['symbol']} - {stock['name']}: 满足{stock.get('met_conditions_count', 0)}/11个条件")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import time
    main()