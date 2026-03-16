#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控模块
监控A股股票，执行一号和二号策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.execute_strategies_main import StrategyExecutor, get_a_stock_universe
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import threading
from queue import Queue
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealTimeMonitor:
    """实时监控器"""
    
    def __init__(self, stock_list=None):
        """
        初始化实时监控器
        
        Args:
            stock_list: 股票列表，如果为None则使用默认A股股票池
        """
        self.executor = StrategyExecutor()
        self.stock_list = stock_list or get_a_stock_universe()
        
        # 监控状态
        self.monitoring = False
        self.interval = 60  # 默认60秒检查一次
        self.signal_queue = Queue()
        
        # 信号历史
        self.signals_today = []
        self.stock_signals = {}  # 每只股票的信号记录
        
        # 创建输出目录
        os.makedirs('logs/realtime', exist_ok=True)
        os.makedirs('data/realtime', exist_ok=True)
    
    def start_monitoring(self, interval_seconds: int = 60):
        """
        开始实时监控
        
        Args:
            interval_seconds: 检查间隔（秒）
        """
        self.interval = interval_seconds
        self.monitoring = True
        
        print("🚀 开始实时监控")
        print("=" * 70)
        print(f"监控股票: {len(self.stock_list)} 只")
        print(f"检查间隔: {interval_seconds} 秒")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 启动信号处理线程
        signal_thread = threading.Thread(target=self._signal_processor)
        signal_thread.daemon = True
        signal_thread.start()
        
        return monitor_thread, signal_thread
    
    def _monitoring_loop(self):
        """监控循环"""
        cycle_count = 0
        
        while self.monitoring:
            try:
                cycle_count += 1
                current_time = datetime.now()
                
                print(f"\n🔄 第{cycle_count}次检查 ({current_time.strftime('%H:%M:%S')})")
                print("-" * 40)
                
                # 检查每只股票
                triggered_stocks = []
                
                for symbol, name in self.stock_list:
                    # 获取实时数据（这里使用模拟数据）
                    realtime_data = self._get_realtime_mock_data(symbol)
                    
                    # 分析股票
                    analysis = self.executor.analyze_stock(symbol, realtime_data)
                    
                    if 'error' in analysis:
                        continue
                    
                    # 检查是否触发策略
                    strategy_01_triggered = analysis['strategy_01']['triggered']
                    strategy_02_triggered = analysis['strategy_02']['triggered']
                    
                    if strategy_01_triggered or strategy_02_triggered:
                        triggered_info = {
                            'symbol': symbol,
                            'name': name,
                            'time': current_time.isoformat(),
                            'strategy_01': strategy_01_triggered,
                            'strategy_02': strategy_02_triggered,
                            'indicators': analysis.get('indicators', {})
                        }
                        
                        triggered_stocks.append(triggered_info)
                        
                        # 发送到信号队列
                        self.signal_queue.put(triggered_info)
                
                # 显示本周期结果
                if triggered_stocks:
                    print(f"✅ 发现 {len(triggered_stocks)} 只股票触发策略:")
                    for stock in triggered_stocks[:5]:  # 只显示前5只
                        strategies = []
                        if stock['strategy_01']:
                            strategies.append("一号策略")
                        if stock['strategy_02']:
                            strategies.append("二号策略")
                        
                        print(f"  {stock['symbol']} - {stock['name']}: {', '.join(strategies)}")
                    
                    if len(triggered_stocks) > 5:
                        print(f"  ... 等{len(triggered_stocks)}只股票")
                else:
                    print("⚠️ 本周期无股票触发策略")
                
                # 保存周期结果
                self._save_cycle_results(cycle_count, triggered_stocks)
                
                # 等待下一次检查
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ 监控被用户中断")
                self.monitoring = False
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(10)  # 出错后等待10秒
    
    def _signal_processor(self):
        """信号处理器"""
        while self.monitoring:
            try:
                # 从队列获取信号
                signal = self.signal_queue.get(timeout=1)
                
                # 处理信号
                self._process_signal(signal)
                
                # 标记任务完成
                self.signal_queue.task_done()
                
            except Exception as e:
                # 队列为空时继续等待
                continue
    
    def _process_signal(self, signal: dict):
        """处理信号"""
        symbol = signal['symbol']
        name = signal['name']
        
        # 记录信号
        self.signals_today.append(signal)
        
        # 更新股票信号记录
        if symbol not in self.stock_signals:
            self.stock_signals[symbol] = []
        
        self.stock_signals[symbol].append({
            'time': signal['time'],
            'strategy_01': signal['strategy_01'],
            'strategy_02': signal['strategy_02']
        })
        
        # 生成警报
        self._generate_alert(signal)
        
        # 保存信号记录
        self._save_signal_record(signal)
    
    def _generate_alert(self, signal: dict):
        """生成警报"""
        symbol = signal['symbol']
        name = signal['name']
        strategies = []
        
        if signal['strategy_01']:
            strategies.append("一号策略")
        if signal['strategy_02']:
            strategies.append("二号策略")
        
        alert_message = f"🚨 {symbol} - {name} 触发策略: {', '.join(strategies)}"
        
        # 打印警报
        print(f"\n🔔 {alert_message}")
        
        # 记录到日志文件
        log_file = f"logs/realtime/alerts_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {alert_message}\n")
        
        # 这里可以添加其他警报方式，如邮件、短信等
        # 例如：send_email_alert(alert_message)
        # 例如：send_sms_alert(alert_message)
    
    def _save_cycle_results(self, cycle: int, triggered_stocks: list):
        """保存周期结果"""
        try:
            result = {
                'cycle': cycle,
                'time': datetime.now().isoformat(),
                'total_stocks': len(self.stock_list),
                'triggered_count': len(triggered_stocks),
                'triggered_stocks': triggered_stocks
            }
            
            # 保存到文件
            filename = f"data/realtime/cycle_{cycle}_{datetime.now().strftime('%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"保存周期结果失败: {e}")
    
    def _save_signal_record(self, signal: dict):
        """保存信号记录"""
        try:
            # 按股票保存
            symbol = signal['symbol']
            signal_file = f"data/realtime/signals_{symbol}.json"
            
            # 读取现有记录
            signals = []
            if os.path.exists(signal_file):
                with open(signal_file, 'r', encoding='utf-8') as f:
                    signals = json.load(f)
            
            # 添加新信号
            signals.append(signal)
            
            # 只保留最近100条记录
            if len(signals) > 100:
                signals = signals[-100:]
            
            # 保存
            with open(signal_file, 'w', encoding='utf-8') as f:
                json.dump(signals, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"保存信号记录失败: {e}")
    
    def _get_realtime_mock_data(self, symbol: str) -> pd.DataFrame:
        """
        获取模拟实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时数据DataFrame
        """
        np.random.seed(hash(symbol) % 10000 + int(time.time()) % 1000)
        
        # 生成最近240分钟的数据（4小时交易时间）
        periods = 240
        base_price = np.random.uniform(5, 100)
        
        # 生成随机走势
        returns = np.random.randn(periods) * 0.001  # 分钟级波动
        prices = base_price * (1 + returns.cumsum())
        
        # 生成高低价
        highs = prices + np.random.rand(periods) * 0.1
        lows = prices - np.random.rand(periods) * 0.1
        
        # 生成成交量
        volumes = np.random.randint(10000, 100000, periods)
        
        # 创建DataFrame
        data = pd.DataFrame({
            'close': prices,
            'high': highs,
            'low': lows,
            'volume': volumes
        })
        
        return data
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        print("\n⏹️ 停止实时监控")
        
        # 生成今日监控报告
        self._generate_daily_report()
    
    def _generate_daily_report(self):
        """生成今日监控报告"""
        try:
            if not self.signals_today:
                print("📭 今日无策略触发信号")
                return
            
            report_lines = [
                "=" * 70,
                "今日实时监控报告",
                "=" * 70,
                f"报告日期: {datetime.now().strftime('%Y-%m-%d')}",
                f"监控股票: {len(self.stock_list)} 只",
                f"检查间隔: {self.interval} 秒",
                f"信号总数: {len(self.signals_today)}",
                ""
            ]
            
            # 按股票统计
            stock_stats = {}
            for signal in self.signals_today:
                symbol = signal['symbol']
                if symbol not in stock_stats:
                    stock_stats[symbol] = {
                        'name': signal['name'],
                        'strategy_01_count': 0,
                        'strategy_02_count': 0,
                        'total': 0,
                        'last_time': signal['time']
                    }
                
                stock_stats[symbol]['total'] += 1
                if signal['strategy_01']:
                    stock_stats[symbol]['strategy_01_count'] += 1
                if signal['strategy_02']:
                    stock_stats[symbol]['strategy_02_count'] += 1
            
            # 按触发次数排序
            sorted_stocks = sorted(stock_stats.items(), key=lambda x: x[1]['total'], reverse=True)
            
            report_lines.append("📊 股票触发统计:")
            report_lines.append("-" * 40)
            report_lines.append(f"{'排名':<4} {'代码':<8} {'名称':<12} {'总次数':<6} {'一号策略':<8} {'二号策略':<8} {'最后触发':<12}")
            report_lines.append("-" * 40)
            
            for i, (symbol, stats) in enumerate(sorted_stocks[:20], 1):
                last_time = datetime.fromisoformat(stats['last_time']).strftime('%H:%M:%S')
                report_lines.append(
                    f"{i:<4} {symbol:<8} {stats['name']:<12} "
                    f"{stats['total']:<6} {stats['strategy_01_count']:<8} "
                    f"{stats['strategy_02_count']:<8} {last_time:<12}"
                )
            
            report_lines.append("")
            
            # 策略对比
            total_strategy_01 = sum(s['strategy_01_count'] for s in stock_stats.values())
            total_strategy_02 = sum(s['strategy_02_count'] for s in stock_stats.values())
            
            report_lines.append("📈 策略对比:")
            report_lines.append("-" * 40)
            report_lines.append(f"  一号策略总触发: {total_strategy_01} 次")
            report_lines.append(f"  二号策略总触发: {total_strategy_02} 次")
            report_lines.append(f"  双策略同时触发: {sum(1 for s in self.signals_today if s['strategy_01'] and s['strategy_02'])} 次")
            report_lines.append("")
            
            # 重点关注股票
            if sorted_stocks:
                report_lines.append("🎯 重点关注股票:")
                report_lines.append("-" * 40)
                for symbol, stats in sorted_stocks[:5]:
                    report_lines.append(f"  {symbol} - {stats['name']}: 触发{stats['total']}次")
                report_lines.append("")
            
            report_lines.append("=" * 70)
            
            report_text = "\n".join(report_lines)
            
            # 保存报告
            report_file = f"logs/realtime/daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            print(f"📋 今日监控报告已保存到: {report_file}")
            print(report_text)
            
        except Exception as e:
            logger.error(f"生成今日报告失败: {e}")


def main():
    """主函数"""
    print("🚀 A股实时策略监控系统")
    print("=" * 70)
    
    # 创建监控器
    monitor = RealTimeMonitor()
    
    try:
        # 开始监控
        monitor.start_monitoring(interval_seconds=60)  # 60秒检查一次
        
        # 保持主线程运行
        while True:
            command = input("\n输入 'stop' 停止监控，'status' 查看状态: ").strip().lower()
            
            if command == 'stop':
                monitor.stop_monitoring()
                break
            elif command == 'status':
                print(f"监控状态: {'运行中' if monitor.monitoring else '已停止'}")
                print(f"今日信号数: {len(monitor.signals_today)}")
            else:
                print("❌ 未知命令")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ 系统出错: {e}")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()