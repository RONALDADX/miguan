#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略执行主程序
同时执行一号和二号策略，支持A股实时监控和历史分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.technical.intraday_monitor import IntradayMonitor
from src.technical.indicator_calculator import TechnicalIndicatorCalculator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import yaml
import time
import logging
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyExecutor:
    """策略执行器"""
    
    def __init__(self):
        """初始化策略执行器"""
        # 初始化策略监控器
        self.strategy_01_monitor = IntradayMonitor("config/strategy_01_technical.yaml")
        self.strategy_02_monitor = IntradayMonitor("config/strategy_02_technical.yaml")
        self.calculator = TechnicalIndicatorCalculator()
        
        # 加载二号策略配置
        with open("config/strategy_02_technical.yaml", 'r', encoding='utf-8') as f:
            self.strategy_02_config = yaml.safe_load(f)
        
        # 结果存储
        self.results = {}
        self.history_analysis = {}
        
        # 创建输出目录
        os.makedirs('results/strategy_reports', exist_ok=True)
        os.makedirs('data/history_analysis', exist_ok=True)
    
    def check_strategy_02_conditions(self, indicators: Dict) -> Dict:
        """
        检查二号策略条件
        
        Args:
            indicators: 技术指标计算结果
            
        Returns:
            策略检查结果
        """
        try:
            conditions = {}
            
            # 条件1：DMI指标
            dmi_info = indicators.get('dmi', {})
            plus_di = dmi_info.get('plus_di', 0)
            minus_di = dmi_info.get('minus_di', 0)
            
            # DI1上穿DI2（+DI上穿-DI）
            di1_cross_di2 = False
            if 'prev_plus_di' in dmi_info and 'prev_minus_di' in dmi_info:
                prev_plus_di = dmi_info['prev_plus_di']
                prev_minus_di = dmi_info['prev_minus_di']
                di1_cross_di2 = (prev_plus_di <= prev_minus_di) and (plus_di > minus_di)
            
            # ADX上穿ADXR（简化：ADX大于某个阈值）
            adx = dmi_info.get('adx', 0)
            adx_cross_adxr = adx > 20  # 简化处理
            
            conditions['dmi'] = {
                'name': 'DMI指标',
                'met': di1_cross_di2 and adx_cross_adxr,
                'details': {
                    'di1_cross_di2': di1_cross_di2,
                    'adx_cross_adxr': adx_cross_adxr,
                    'plus_di': plus_di,
                    'minus_di': minus_di,
                    'adx': adx
                }
            }
            
            # 条件2：换手率
            turnover_info = indicators.get('turnover', {})
            turnover_above_5 = turnover_info.get('above_5_percent', False)
            
            conditions['turnover'] = {
                'name': '换手率>5%',
                'met': turnover_above_5,
                'details': {
                    'turnover_rate': turnover_info.get('turnover_rate', 0),
                    'above_5_percent': turnover_above_5
                }
            }
            
            # 条件3：RSI指标
            rsi_info = indicators.get('rsi', {})
            rsi_golden_cross = rsi_info.get('golden_cross', False)
            
            conditions['rsi'] = {
                'name': 'RSI金叉',
                'met': rsi_golden_cross,
                'details': {
                    'rsi': rsi_info.get('rsi', 0),
                    'rsi6': rsi_info.get('rsi6', 0),
                    'golden_cross': rsi_golden_cross
                }
            }
            
            # 判断是否触发策略（所有条件必须同时满足）
            all_met = all(cond['met'] for cond in conditions.values())
            
            return {
                'conditions': conditions,
                'triggered': all_met,
                'met_conditions': [cond['name'] for cond in conditions.values() if cond['met']]
            }
            
        except Exception as e:
            logger.error(f"检查二号策略条件失败: {e}")
            return {'error': str(e)}
    
    def analyze_stock(self, symbol: str, stock_data: pd.DataFrame) -> Dict:
        """
        分析单只股票
        
        Args:
            symbol: 股票代码
            stock_data: 股票数据
            
        Returns:
            分析结果
        """
        try:
            # 计算所有技术指标
            indicators = self.calculator.calculate_all_indicators(stock_data)
            
            if not indicators:
                return {'error': '指标计算失败'}
            
            # 检查一号策略
            strategy_01_result = self.strategy_01_monitor.check_strategy_conditions(stock_data, symbol)
            
            # 检查二号策略
            strategy_02_result = self.check_strategy_02_conditions(indicators)
            
            # 综合结果
            result = {
                'symbol': symbol,
                'analysis_time': datetime.now().isoformat(),
                'data_period': f"{len(stock_data)}个交易日",
                'strategy_01': {
                    'triggered': strategy_01_result.get('triggered', False),
                    'met_conditions': strategy_01_result.get('conditions', {}),
                    'summary': strategy_01_result.get('indicators_summary', {})
                },
                'strategy_02': strategy_02_result,
                'indicators': self._get_indicators_summary(indicators)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析股票{symbol}失败: {e}")
            return {'error': str(e)}
    
    def _get_indicators_summary(self, indicators: Dict) -> Dict:
        """获取指标摘要"""
        summary = {}
        
        # DMI摘要
        dmi = indicators.get('dmi', {})
        summary['dmi'] = {
            'plus_di': round(dmi.get('plus_di', 0), 2),
            'minus_di': round(dmi.get('minus_di', 0), 2),
            'adx': round(dmi.get('adx', 0), 2)
        }
        
        # RSI摘要
        rsi = indicators.get('rsi', {})
        summary['rsi'] = {
            'rsi6': round(rsi.get('rsi6', 0), 2),
            'golden_cross': rsi.get('golden_cross', False)
        }
        
        # MACD摘要
        macd = indicators.get('macd', {})
        summary['macd'] = {
            'dif': round(macd.get('dif', 0), 3),
            'dea': round(macd.get('dea', 0), 3),
            'bar': round(macd.get('macd_bar', 0), 3)
        }
        
        # 换手率
        turnover = indicators.get('turnover', {})
        summary['turnover'] = {
            'rate': round(turnover.get('turnover_rate', 0) * 100, 2),
            'above_5': turnover.get('above_5_percent', False)
        }
        
        return summary
    
    def analyze_a_stock_universe(self, stock_list: List[Tuple[str, str]]) -> Dict:
        """
        分析A股股票池
        
        Args:
            stock_list: 股票列表 [(代码, 名称), ...]
            
        Returns:
            分析结果
        """
        print(f"🔍 开始分析A股股票池，共{len(stock_list)}只股票")
        print("=" * 70)
        
        results = {
            'analysis_time': datetime.now().isoformat(),
            'total_stocks': len(stock_list),
            'strategy_01_triggered': [],
            'strategy_02_triggered': [],
            'both_strategies_triggered': [],
            'stock_details': {}
        }
        
        for i, (symbol, name) in enumerate(stock_list, 1):
            # 显示进度
            if i % 10 == 0 or i == len(stock_list):
                print(f"进度: {i}/{len(stock_list)} ({i/len(stock_list)*100:.1f}%)")
            
            try:
                # 获取模拟数据（实际应用应使用真实数据）
                stock_data = self._get_mock_stock_data(symbol)
                
                # 分析股票
                analysis = self.analyze_stock(symbol, stock_data)
                
                if 'error' in analysis:
                    continue
                
                # 存储详细结果
                results['stock_details'][symbol] = analysis
                
                # 统计触发情况
                strategy_01_triggered = analysis['strategy_01']['triggered']
                strategy_02_triggered = analysis['strategy_02']['triggered']
                
                if strategy_01_triggered:
                    results['strategy_01_triggered'].append({
                        'symbol': symbol,
                        'name': name,
                        'met_conditions': analysis['strategy_01'].get('met_conditions', {})
                    })
                
                if strategy_02_triggered:
                    results['strategy_02_triggered'].append({
                        'symbol': symbol,
                        'name': name,
                        'met_conditions': analysis['strategy_02'].get('met_conditions', [])
                    })
                
                if strategy_01_triggered and strategy_02_triggered:
                    results['both_strategies_triggered'].append({
                        'symbol': symbol,
                        'name': name
                    })
                    
            except Exception as e:
                logger.error(f"分析股票{symbol}时出错: {e}")
                continue
        
        print()
        print("✅ 分析完成!")
        print("=" * 70)
        
        # 保存结果
        self._save_analysis_results(results)
        
        return results
    
    def _get_mock_stock_data(self, symbol: str) -> pd.DataFrame:
        """
        获取模拟股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            模拟数据DataFrame
        """
        np.random.seed(hash(symbol) % 10000)
        
        # 生成60个交易日数据
        periods = 60
        base_price = np.random.uniform(5, 100)
        
        # 生成随机走势
        returns = np.random.randn(periods) * 0.02
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 2
        lows = prices - np.random.rand(periods) * 2
        
        # 生成成交量
        volumes = np.random.randint(1000000, 10000000, periods)
        
        # 创建DataFrame
        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes
        })
        
        return data
    
    def _save_analysis_results(self, results: Dict):
        """保存分析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细结果
        detail_file = f"results/strategy_reports/detailed_analysis_{timestamp}.json"
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 生成并保存报告
        report = self._generate_analysis_report(results)
        report_file = f"results/strategy_reports/analysis_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 详细结果已保存到: {detail_file}")
        print(f"📋 分析报告已保存到: {report_file}")
        
        return report
    
    def _generate_analysis_report(self, results: Dict) -> str:
        """生成分析报告"""
        report_lines = [
            "=" * 70,
            "A股策略分析报告",
            "=" * 70,
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"分析股票总数: {results['total_stocks']}",
            ""
        ]
        
        # 策略触发统计
        report_lines.append("📊 策略触发统计:")
        report_lines.append("-" * 40)
        report_lines.append(f"  一号策略触发: {len(results['strategy_01_triggered'])} 只")
        report_lines.append(f"  二号策略触发: {len(results['strategy_02_triggered'])} 只")
        report_lines.append(f"  双策略触发: {len(results['both_strategies_triggered'])} 只")
        report_lines.append("")
        
        # 一号策略触发股票
        if results['strategy_01_triggered']:
            report_lines.append("🏆 一号策略触发股票:")
            report_lines.append("-" * 40)
            for i, stock in enumerate(results['strategy_01_triggered'][:10], 1):
                symbol = stock['symbol']
                name = stock['name']
                conditions = stock.get('met_conditions', {})
                
                # 统计触发的条件数量
                met_count = sum(1 for cond in conditions.values() if cond.get('met', False))
                report_lines.append(f"  {i:2d}. {symbol} - {name} (触发{met_count}个条件)")
            
            if len(results['strategy_01_triggered']) > 10:
                report_lines.append(f"  ... 等{len(results['strategy_01_triggered'])}只股票")
            report_lines.append("")
        
        # 二号策略触发股票
        if results['strategy_02_triggered']:
            report_lines.append("🏆 二号策略触发股票:")
            report_lines.append("-" * 40)
            for i, stock in enumerate(results['strategy_02_triggered'][:10], 1):
                symbol = stock['symbol']
                name = stock['name']
                met_conditions = stock.get('met_conditions', [])
                
                report_lines.append(f"  {i:2d}. {symbol} - {name}")
                if met_conditions:
                    report_lines.append(f"      触发条件: {', '.join(met_conditions)}")
            
            if len(results['strategy_02_triggered']) > 10:
                report_lines.append(f"  ... 等{len(results['strategy_02_triggered'])}只股票")
            report_lines.append("")
        
        # 双策略触发股票
        if results['both_strategies_triggered']:
            report_lines.append("🎯 双策略同时触发股票（重点关注）:")
            report_lines.append("-" * 40)
            for i, stock in enumerate(results['both_strategies_triggered'], 1):
                symbol = stock['symbol']
                name = stock['name']
                report_lines.append(f"  {i:2d}. {symbol} - {name}")
            
            report_lines.append("")
        
        # 策略对比
        report_lines.append("📈 策略对比分析:")
        report_lines.append("-" * 40)
        report_lines.append("  一号策略特点:")
        report_lines.append("    • 任一技术条件满足即可触发")
        report_lines.append("    • 包含10个条件组（MACD、RSI、KDJ、BOLL等）")
        report_lines.append("    • 信号相对较多，适合短线交易")
        report_lines.append("")
        report_lines.append("  二号策略特点:")
        report_lines.append("    • 所有条件必须同时满足")
        report_lines.append("    • 包含3个条件（DMI、RSI、换手率）")
        report_lines.append("    • 信号相对较少，质量可能更高")
        report_lines.append("")
        
        # 投资建议
        report_lines.append("💡 投资建议:")
        report_lines.append("-" * 40)
        if results['both_strategies_triggered']:
            report_lines.append("  1. 优先关注双策略触发股票")
            report_lines.append("  2. 建议构建3-5只股票的组合")
            report_lines.append("  3. 设置止损止盈：止损6-8%，止盈15-25%")
        else:
            report_lines.append("  1. 关注策略触发较多的股票")
            report_lines.append("  2. 建议等待更多确认信号")
            report_lines.append("  3. 控制仓位，谨慎操作")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)


def get_a_stock_universe() -> List[Tuple[str, str]]:
    """
    获取A股股票池
    
    Returns:
        股票列表 [(代码, 名称), ...]
    """
    # 常见A股股票（模拟数据）
    a_stocks = [
        # 大盘蓝筹
        ('000001', '平安银行'),
        ('000002', '万科A'),
        ('000858', '五粮液'),
        ('600519', '贵州茅台'),
        ('601318', '中国平安'),
        
        # 银行股
        ('600036', '招商银行'),
        ('601988', '中国银行'),
        ('601328', '交通银行'),
        ('601288', '农业银行'),
        ('601398', '工商银行'),
        
        # 成长股
        ('000333', '美的集团'),
        ('002415', '海康威视'),
        ('300750', '宁德时代'),
        ('300059', '东方财富'),
        ('002475', '立讯精密'),
        
        # 消费股
        ('600887', '伊利股份'),
        ('000568', '泸州老窖'),
        ('600276', '恒瑞医药'),
        ('600436', '片仔癀'),
        ('600309', '万华化学'),
        
        # 科技股
        ('000725', '京东方A'),
        ('002049', '紫光国微'),
        ('300124', '汇川技术'),
        ('603986', '兆易创新'),
        ('688981', '中芯国际'),
        
        # 其他
        ('002594', '比亚迪'),
        ('601012', '隆基绿能'),
        ('603259', '药明康德'),
        ('603288', '海天味业'),
        ('601888', '中国中免')
    ]
    
    return a_stocks


def main():
    """主函数"""
    print("🚀 A股策略分析系统")
    print("=" * 70)
    print("策略配置:")
    print("  一号策略: 盘中技术分析（任一条件满足）")
    print("  二号策略: DMI+RSI组合（全条件满足）")
    print()
    
    # 创建执行器
    executor = StrategyExecutor()
    
    # 获取A股股票池
    stock_universe = get_a_stock_universe()
    
    print(f"📊 股票池: {len(stock_universe)} 只A股股票")
    print("=" * 70)
    print()
    
    while True:
        print("请选择操作:")
        print("1. 执行策略分析（全股票池）")
        print("2. 分析指定股票")
        print("3. 查看策略详情")
        print("4. 查看历史分析结果")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == '1':
            # 执行全股票池分析
            results = executor.analyze_a_stock_universe(stock_universe)
            
            # 显示报告
            report = executor._generate_analysis_report(results)
            print("\n" + report)
            
        elif choice == '2':
            # 分析指定股票
            symbol = input("请输入股票代码（如000001）: ").strip()
            
            # 查找股票名称
            stock_name = "未知股票"
            for code, name in stock_universe:
                if code == symbol:
                    stock_name = name
                    break
            
            print(f"分析股票: {symbol} - {stock_name}")
            
            # 获取数据并分析
            stock_data = executor._get_mock_stock_data(symbol)
            analysis = executor.analyze_stock(symbol, stock_data)
            
            if 'error' in analysis:
                print(f"❌ 分析失败: {analysis['error']}")
            else:
                print(f"\n✅ 分析完成!")
                print(f"一号策略触发: {'是' if analysis['strategy_01']['triggered'] else '否'}")
                print(f"二号策略触发: {'是' if analysis['strategy_02']['triggered'] else '否'}")
                
                # 显示详细指标
                print("\n📊 技术指标摘要:")
                indicators = analysis.get('indicators', {})
                for key, values in indicators.items():
                    print(f"  {key.upper()}: {values}")
        
        elif choice == '3':
            # 查看策略详情
            print("\n📋 策略详情:")
            print("-" * 40)
            print("一号策略（盘中技术分析）:")
            print("  • MACD相关（3选1）: 绿柱缩短/金叉/底背离")
            print("  • RSI金叉且RSI6≤68")
            print("  • BBI金叉")
            print("  • DPO金叉且角度>20度")
            print("  • OBV连续5天在MAOBV上方")
            print("  • KDJ金叉或有金叉趋势")
            print("  • DI1上穿ADX线")
            print("  • 股价上穿BOLL中轨且三轨上行")
            print("  • 换手率≥5%")
            print("  • 虚拟成交量≥昨日2倍")
            print("  → 任一条件满足即可触发")
            print()
            print("二号策略（DMI+RSI组合）:")
            print("  • DI1上穿DI2线")
            print("  • ADX上穿ADXR线")
            print("  • 换手率>5%")
            print("  • RSI金叉")
            print("  → 所有条件必须同时满足")
            print()
        
        elif choice == '4':
            # 查看历史分析结果
            results_dir = "results/strategy_reports"
            if os.path.exists(results_dir):
                files = [f for f in os.listdir(results_dir) if f.endswith('.txt')]
                if files:
                    files.sort(reverse=True)
                    print(f"\n📁 最近的分析报告:")
                    for i, file in enumerate(files[:5], 1):
                        print(f"  {i}. {file}")
                    
                    view = input("\n查看报告编号 (1-5) 或按回车返回: ").strip()
                    if view.isdigit() and 1 <= int(view) <= len(files[:5]):
                        filepath = os.path.join(results_dir, files[int(view)-1])
                        with open(filepath, 'r', encoding='utf-8') as f:
                            print(f"\n{f.read()}")
                else:
                    print("暂无历史分析报告")
            else:
                print("暂无历史分析报告")
        
        elif choice == '5':
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选项，请重新输入")


if __name__ == "__main__":
    main()