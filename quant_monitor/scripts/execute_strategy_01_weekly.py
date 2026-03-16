#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行一号策略 - 一周A股筛选
八个条件必须全部满足（简化版：移除了BBI、DPO、BOLL三轨上行）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import yaml
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.technical.indicator_calculator import TechnicalIndicatorCalculator


class Strategy01WeeklyExecutor:
    """一号策略周度执行器"""
    
    def __init__(self):
        """初始化"""
        self.calculator = TechnicalIndicatorCalculator()
        
        # 加载策略配置
        with open("config/strategy_01_technical.yaml", 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 创建输出目录
        os.makedirs('results/weekly_strategy_01', exist_ok=True)
    
    def get_a_stock_universe(self) -> List[Tuple[str, str]]:
        """
        获取A股股票池（一周内活跃股票）
        
        Returns:
            股票列表 [(代码, 名称), ...]
        """
        # 模拟一周内活跃的A股股票
        a_stocks = [
            # 大盘蓝筹（流动性好）

            ('000001', '平安银行'),
            ('000002', '万科A'),
            ('000858', '五粮液'),
            ('600519', '贵州茅台'),
            ('601318', '中国平安'),
            
            # 银行股（近期活跃）

            ('600036', '招商银行'),
            ('601988', '中国银行'),
            ('601328', '交通银行'),
            ('601288', '农业银行'),
            ('601398', '工商银行'),
            
            # 成长股（科技、新能源）

            ('000333', '美的集团'),
            ('002415', '海康威视'),
            ('300750', '宁德时代'),
            ('300059', '东方财富'),
            ('002475', '立讯精密'),
            ('002594', '比亚迪'),
            ('601012', '隆基绿能'),
            
            # 消费股（防御性）

            ('600887', '伊利股份'),
            ('000568', '泸州老窖'),
            ('600276', '恒瑞医药'),
            ('600436', '片仔癀'),
            ('600309', '万华化学'),
            ('603288', '海天味业'),
            ('601888', '中国中免'),
            
            # 科技股（高换手）

            ('000725', '京东方A'),
            ('002049', '紫光国微'),
            ('300124', '汇川技术'),
            ('603986', '兆易创新'),
            ('688981', '中芯国际'),
            
            # 医药股（近期热点）

            ('603259', '药明康德'),
            ('300122', '智飞生物'),
            ('300142', '沃森生物'),
            ('300015', '爱尔眼科'),
            ('300347', '泰格医药'),
            
            # 周期股（资源类）

            ('600585', '海螺水泥'),
            ('601899', '紫金矿业'),
            ('600028', '中国石化'),
            ('601857', '中国石油'),
            ('600111', '北方稀土'),
            
            # 中小盘（弹性大）

            ('002241', '歌尔股份'),
            ('002456', '欧菲光'),
            ('002714', '牧原股份'),
            ('300498', '温氏股份'),
            ('300413', '芒果超媒'),
            
            # 其他活跃股

            ('600030', '中信证券'),
            ('601166', '兴业银行'),
            ('600900', '长江电力'),
            ('601668', '中国建筑'),
            ('601800', '中国交建')
        ]
        
        return a_stocks
    
    def generate_weekly_data(self, symbol: str, days: int = 5) -> pd.DataFrame:
        """
        生成一周模拟数据（5个交易日）
        
        Args:
            symbol: 股票代码
            days: 交易日数量
            
        Returns:
            周度数据DataFrame
        """
        np.random.seed(hash(symbol) % 10000)
        
        # 生成5个交易日数据
        periods = days
        base_price = np.random.uniform(5, 100)
        
        # 生成随机走势（模拟一周行情）
        returns = np.random.randn(periods) * 0.02
        
        # 增加一些趋势性
        trend = np.random.choice([-0.03, -0.01, 0.01, 0.03])
        returns += trend
        
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 2
        lows = prices - np.random.rand(periods) * 2
        
        # 生成成交量（模拟一周活跃度）

        volumes = np.random.randint(1000000, 10000000, periods)
        
        # 创建DataFrame

        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes
        })
        
        return data
    
    def check_strategy_01_conditions(self, indicators: Dict) -> Tuple[bool, Dict]:
        """
        检查一号策略的十个条件
        
        Args:
            indicators: 技术指标计算结果
            
        Returns:
            (是否全部满足, 详细条件结果)
        """
        try:
            conditions = {}
            
            # 条件1：MACD相关（3选1）

            macd_info = indicators.get('macd', {})
            green_shrinking = macd_info.get('green_bar_shrinking', False)
            macd_golden_cross = macd_info.get('golden_cross', False)
            bottom_divergence = macd_info.get('bottom_divergence', False)
            
            macd_condition = green_shrinking or macd_golden_cross or bottom_divergence
            
            conditions['macd'] = {
                'name': 'MACD条件（绿柱缩短/金叉/底背离）',
                'met': macd_condition,
                'details': {
                    'green_bar_shrinking': green_shrinking,
                    'golden_cross': macd_golden_cross,
                    'bottom_divergence': bottom_divergence
                }
            }
            
            # 条件2：RSI金叉

            rsi_info = indicators.get('rsi', {})
            rsi_golden_cross = rsi_info.get('golden_cross', False)
            
            conditions['rsi_golden'] = {
                'name': 'RSI金叉',
                'met': rsi_golden_cross,
                'details': {
                    'rsi_golden_cross': rsi_golden_cross
                }
            }
            
            # 条件3：RSI6≤68

            rsi6_below_68 = rsi_info.get('below_68', False)
            
            conditions['rsi6_limit'] = {
                'name': 'RSI6≤68',

                'met': rsi6_below_68,
                'details': {
                    'rsi6': rsi_info.get('rsi6', 0),
                    'below_68': rsi6_below_68

                }
            }
            
            # 条件4：BBI金叉

            bbi_info = indicators.get('bbi', {})
            bbi_golden_cross = bbi_info.get('golden_cross', False)
            
            conditions['bbi'] = {
                'name': 'BBI金叉',

                'met': bbi_golden_cross,
                'details': {
                    'bbi_golden_cross': bbi_golden_cross


                }
            }
            
            # 条件5：DPO金叉

            dpo_info = indicators.get('dpo', {})
            dpo_golden_cross = dpo_info.get('golden_cross', False)
            
            conditions['dpo_golden'] = {
                'name': 'DPO金叉',


                'met': dpo_golden_cross,
                'details': {
                    'dpo_golden_cross': dpo_golden_cross




                }
            }
            
            # 条件6：DPO角度>20度

            dpo_angle_gt_20 = dpo_info.get('angle_gt_20', False)
            
            conditions['dpo_angle'] = {
                'name': 'DPO角度>20度',



                'met': dpo_angle_gt_20,
                'details': {
                    'dpo_angle': dpo_info.get('angle', 0),
                    'angle_gt_20': dpo_angle_gt_20




                }
            }
            
            # 条件7：OBV连续5天在MAOBV上方


            obv_info = indicators.get('obv', {})
            obv_above_ma_5days = obv_info.get('above_ma_5days', False)
            
            conditions['obv'] = {
                'name': 'OBV连续5天在MAOBV上方',



                'met': obv_above_ma_5days,
                'details': {
                    'obv_above_ma_5days': obv_above_ma_5days




                }
            }
            
            # 条件8：KDJ金叉或有金叉趋势


            kdj_info = indicators.get('kdj', {})
            kdj_golden_cross = kdj_info.get('golden_cross', False)
            kdj_trend_golden = kdj_info.get('trend_golden', False)
            
            kdj_condition = kdj_golden_cross or kdj_trend_golden
            
            conditions['kdj'] = {
                'name': 'KDJ金叉或有金叉趋势',




                'met': kdj_condition,
                'details': {
                    'kdj_golden_cross': kdj_golden_cross,
                    'kdj_trend_golden': kdj_trend_golden




                }
            }
            
            # 条件9：DI1上穿ADX线



            dmi_info = indicators.get('dmi', {})
            di1_cross_adx = dmi_info.get('di1_cross_adx', False)
            
            conditions['dmi'] = {
                'name': 'DI1上穿ADX线',



                'met': di1_cross_adx,
                'details': {
                    'di1_cross_adx': di1_cross_adx




                }
            }
            
            # 条件10：股价上穿BOLL中轨且三轨上行



            boll_info = indicators.get('boll', {})
            boll_cross_middle = boll_info.get('cross_middle', False)
            boll_trend_up = boll_info.get('trend_up', False)
            
            boll_condition = boll_cross_middle and boll_trend_up
            
            conditions['boll'] = {
                'name': '股价上穿BOLL中轨且三轨上行',



                'met': boll_condition,
                'details': {
                    'boll_cross_middle': boll_cross_middle,
                    'boll_trend_up': boll_trend_up




                }
            }
            
            # 条件11：换手率≥5%



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
            
            # 条件12：虚拟成交量≥昨日2倍



            volume_info = indicators.get('volume_analysis', {})
            vs_yesterday_double = volume_info.get('vs_yesterday_double', False)
            
            conditions['volume'] = {
                'name': '虚拟成交量≥昨日2倍',



                'met': vs_yesterday_double,
                'details': {
                    'vs_yesterday_ratio': volume_info.get('vs_yesterday_ratio', 0),
                    'vs_yesterday_double': vs_yesterday_double




                }
            }
            
            # 判断是否全部满足


            all_met = all(cond['met'] for cond in conditions.values())
            
            return all_met, conditions
            
        except Exception as e:
            logger.error(f"检查一号策略条件失败: {e}")
            return False, {'error': str(e)}
    
    def execute_weekly_screening(self) -> Dict:
        """
        执行一周A股筛选


        Returns:
            筛选结果
        """
        print("🚀 开始执行一号策略 - 一周A股筛选")
        print("=" * 80)
        print("策略要求：十个条件必须全部满足")
        print("=" * 80)
        print()
        
        # 获取股票池


        stock_universe = self.get_a_stock_universe()
        print(f"📊 筛选范围: {len(stock_universe)} 只A股股票")
        print("-" * 80)
        print()
        
        results = {
            'screening_time': datetime.now().isoformat(),

            'strategy_name': '一号策略（十个条件全满足）',
            'period': '一周（5个交易日）',
            'total_screened': len(stock_universe),
            'triggered_stocks': [],
            'failed_stocks': [],
            'stock_details': {}
        }
        
        print("🔍 开始逐只分析股票...")
        print("-" * 80)
        
        for i, (symbol, name) in enumerate(stock_universe, 1):
            # 显示进度


            if i % 10 == 0 or i == len(stock_universe):
                print(f"进度: {i}/{len(stock_universe)} ({i/len(stock_universe)*100:.1f}%)")
            
            try:
                # 生成一周数据


                stock_data = self.generate_weekly_data(symbol, days=5)
                
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



                all_met, condition_details = self.check_strategy_01_conditions(indicators)
                
                # 存储详细结果



                stock_result = {
                    'symbol': symbol,
                    'name': name,
                    'all_conditions_met': all_met,
                    'conditions': condition_details,
                    'indicators_summary': self._get_indicators_summary(indicators)
                }
                
                results['stock_details'][symbol] = stock_result
                
                if all_met:
                    results['triggered_stocks'].append({
                        'symbol': symbol,
                        'name': name,
                        'conditions_met': [cond['name'] for cond in condition_details.values() if cond['met']]
                    })
                else:
                    # 统计失败的条件



                    failed_conditions = [cond['name'] for cond in condition_details.values() if not cond['met']]
                    results['failed_stocks'].append({
                        'symbol': symbol,
                        'name': name,
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
        
        # 生成报告



        report = self._generate_weekly_report(results)
        print(report)
        
        # 保存结果



        self._save_weekly_results(results)
        
        return results
    
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
        
        # BOLL摘要



        boll = indicators.get('boll', {})
        summary['boll'] = {
            'upper': round(boll.get('upper', 0), 2),
            'middle': round(boll.get('middle', 0), 2),
            'lower': round(boll.get('lower', 0), 2),
            'close': round(boll.get('close', 0), 2)
        }
        
        # 换手率



        turnover = indicators.get('turnover', {})
        summary['turnover'] = {
            'rate': round(turnover.get('turnover_rate', 0) * 100, 2),
            'above_5': turnover.get('above_5_percent', False)
        }
        
        # 成交量



        volume = indicators.get('volume_analysis', {})
        summary['volume'] = {
            'vs_yesterday_ratio': round(volume.get('vs_yesterday_ratio', 0), 2),
            'vs_yesterday_double': volume.get('vs_yesterday_double', False)
        }
        
        return summary
    
    def _generate_weekly_report(self, results: Dict) -> str:
        """生成周度报告"""

        report_lines = [
            "=" * 80,
            "一号策略 - 一周A股筛选报告",
            "=" * 80,
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"策略名称: {results['strategy_name']}",
            f"分析周期: {results['period']}",
            ""
        ]
        
        # 统计信息



        total = results['total_screened']
        triggered = len(results['triggered_stocks'])
        failed = len(results['failed_stocks'])
        
        report_lines.append("📊 筛选统计:")
        report_lines.append("-" * 40)
        report_lines.append(f"  筛选总数: {total:,}")
        report_lines.append(f"  触发策略: {triggered:,}")
        report_lines.append(f"  未通过数: {failed:,}")
        report_lines.append(f"  触发率: {triggered/total*100:.2f}%")
        report_lines.append("")
        
        # 触发股票清单



        if results['triggered_stocks']:
            report_lines.append("🏆 触发策略股票清单:")
            report_lines.append("=" * 80)
            report_lines.append(f"{'排名':<4} {'代码':<8} {'名称':<12} {'触发条件数':<10} {'关键指标':<30}")
            report_lines.append("-" * 80)
            
            # 按条件满足数量排序



            triggered_stocks = results['triggered_stocks']
            triggered_stocks.sort(key=lambda x: len(x.get('conditions_met', [])), reverse=True)
            
            for i, stock in enumerate(triggered_stocks, 1):
                symbol = stock['symbol']
                name = stock['name']
                conditions_met = stock.get('conditions_met', [])
                
                # 获取详细指标



                details = results['stock_details'].get(symbol, {})
                indicators = details.get('indicators_summary', {})
                
                # 构建关键指标字符串



                key_indicators = []
                if 'macd' in indicators:
                    macd = indicators['macd']
                    key_indicators.append(f"DIF:{macd['dif']}")
                
                if 'rsi' in indicators:
                    rsi = indicators['rsi']
                    key_indicators.append(f"RSI6:{rsi['rsi6']}")
                
                if 'turnover' in indicators:
                    turnover = indicators['turnover']
                    key_indicators.append(f"换手:{turnover['rate']}%")
                
                key_indicators_str = " ".join(key_indicators)
                
                report_lines.append(
                    f"{i:<4} {symbol:<8} {name:<12} "
                    f"{len(conditions_met):<10} {key_indicators_str:<30}"
                )
            
            report_lines.append("")
            
            # 详细分析前5只股票



            if len(triggered_stocks) >= 5:
                report_lines.append("📋 详细分析（前5只股票）:")
                report_lines.append("-" * 40)
                
                for i, stock in enumerate(triggered_stocks[:5], 1):
                    symbol = stock['symbol']
                    name = stock['name']
                    
                    report_lines.append(f"\n{i}. {symbol} - {name}")
                    
                    # 显示关键指标



                    details = results['stock_details'].get(symbol, {})
                    indicators = details.get('indicators_summary', {})
                    
                    for key, values in indicators.items():
                        if key == 'macd':
                            report_lines.append(f"   MACD: DIF={values['dif']}, DEA={values['dea']}, BAR={values['bar']}")
                        elif key == 'rsi':
                            report_lines.append(f"   RSI6: {values['rsi6']}")
                        elif key == 'turnover':
                            report_lines.append(f"   换手率: {values['rate']}%")
                        elif key == 'volume':
                            report_lines.append(f"   成交量比: {values['vs_yesterday_ratio']}倍")
                
                report_lines.append("")
        else:
            report_lines.append("⚠️ 本周无股票触发策略")
            report_lines.append("")
            
            # 显示接近触发的股票



            failed_stocks = results['failed_stocks']
            if failed_stocks:
                # 按失败条件数量排序（失败越少，越接近触发）

                failed_stocks.sort(key=lambda x: x.get('failed_count', 10))
                
                report_lines.append("📈 接近触发的股票（失败条件最少）:")
                report_lines.append("-" * 40)
                
                for i, stock in enumerate(failed_stocks[:10], 1):
                    symbol = stock['symbol']
                    name = stock['name']
                    failed_count = stock.get('failed_count', 10)
                    
                    report_lines.append(f"  {i:2d}. {symbol} - {name}: 仅{10-failed_count}个条件通过")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def _save_weekly_results(self, results: Dict):
        """保存周度结果"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细结果



        detail_file = f"results/weekly_strategy_01/detailed_results_{timestamp}.json"
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 生成并保存CSV清单



        if results['triggered_stocks']:
            csv_data = []
            for stock in results['triggered_stocks']:
                symbol = stock['symbol']
                name = stock['name']
                conditions_met = stock.get('conditions_met', [])
                
                # 获取详细指标



                details = results['stock_details'].get(symbol, {})
                indicators = details.get('indicators_summary', {})
                
                row = {
                    '股票代码': symbol,
                    '股票名称': name,
                    '触发条件数量': len(conditions_met),
                    'MACD_DIF': indicators.get('macd', {}).get('dif', 0),
                    'MACD_DEA': indicators.get('macd', {}).get('dea', 0),
                    'RSI6': indicators.get('rsi', {}).get('rsi6', 0),
                    '换手率': indicators.get('turnover', {}).get('rate', 0),
                    '成交量比': indicators.get('volume', {}).get('vs_yesterday_ratio', 0)
                }
                
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            csv_file = f"results/weekly_strategy_01/triggered_stocks_{timestamp}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            print(f"📊 详细清单已保存到: {csv_file}")
        
        print(f"📋 详细结果已保存到: {detail_file}")


def main():
    """主函数"""
    print("🚀 一号策略周度筛选系统")
    print("=" * 80)
    print("策略要求：十个条件必须全部满足")
    print("1. MACD绿柱缩短/金叉/底背离")

    print("2. RSI金叉")
    print("3. RSI6≤68")
    print("4. BBI金叉")
    print("5. DPO金叉")
    print("6. DPO角度>20度")
    print("7. OBV连续5天在MAOBV上方")
    print("8. KDJ金叉或有金叉趋势")
    print("9. DI1上穿ADX线")
    print("10. 股价上穿BOLL中轨且三轨上行")
    print("11. 换手率≥5%")
    print("12. 虚拟成交量≥昨日2倍")
    print("=" * 80)
    
    executor = Strategy01WeeklyExecutor()
    
    try:
        # 执行周度筛选

        results = executor.execute_weekly_screening()
        
        # 显示最终统计

        print("\n🎯 最终统计:")
        print("-" * 40)
        print(f"  筛选总数: {results['total_screened']:,}")
        print(f"  触发策略: {len(results['triggered_stocks']):,}")
        print(f"  触发率: {len(results['triggered_stocks'])/results['total_screened']*100:.2f}%")
        
        if results['triggered_stocks']:
            print(f"\n  重点关注股票:")
            for stock in results['triggered_stocks'][:5]:
                print(f"    • {stock['symbol']} - {stock['name']}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()