#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主监控系统
集成数据采集、风险控制、仓位管理的核心监控循环
"""

import time
import schedule
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import yaml
import pandas as pd
import threading
from queue import Queue
import signal
import sys

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.akshare_client import AKShareClient
from risk.risk_manager import RiskManager
from position.position_manager import PositionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quant_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QuantMonitor:
    """量化监控系统"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化监控系统
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        
        # 加载配置文件
        self.market_config = self._load_config("market_config.yaml")
        self.risk_config = self._load_config("risk_config.yaml")
        self.position_config = self._load_config("position_config.yaml")
        
        # 初始化组件
        self.data_client = AKShareClient(f"{config_dir}/market_config.yaml")
        self.risk_manager = RiskManager(f"{config_dir}/risk_config.yaml")
        self.position_manager = PositionManager(f"{config_dir}/position_config.yaml")
        
        # 数据缓存
        self.market_data = {}
        self.risk_metrics = {}
        self.alerts = []
        
        # 运行状态
        self.running = False
        self.data_queue = Queue()
        
        # 创建日志目录
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def _load_config(self, filename: str) -> Dict:
        """加载配置文件"""
        try:
            path = os.path.join(self.config_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件 {filename} 失败: {e}")
            return {}
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False
        sys.exit(0)
    
    def update_market_data(self):
        """更新市场数据"""
        try:
            logger.info("开始更新市场数据...")
            
            # 获取所有市场数据
            all_data = self.data_client.update_all_mets()
            
            if all_data:
                self.market_data = all_data
                
                # 保存数据
                self.data_client.save_to_json("data/latest_market_data.json")
                
                # 记录更新
                update_count = sum(len(data) for data in all_data.values())
                logger.info(f"市场数据更新完成，共 {update_count} 个标的")
                
                # 触发数据处理
                self.process_market_data()
                
            else:
                logger.warning("未获取到市场数据")
                
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    def process_market_data(self):
        """处理市场数据"""
        try:
            if not self.market_data:
                return
            
            # 转换为DataFrame格式用于分析
            price_data = {}
            for market, symbols_data in self.market_data.items():
                for symbol, data in symbols_data.items():
                    if 'price' in data:
                        price_data[symbol] = data['price']
            
            if price_data:
                # 创建价格DataFrame
                df = pd.DataFrame(list(price_data.items()), columns=['symbol', 'price'])
                
                # 这里可以添加更多的数据处理逻辑
                # 例如：计算技术指标、检测异常等
                
                # 触发风险计算
                self.calculate_risk_metrics()
                
                # 触发仓位检查
                self.check_positions()
                
        except Exception as e:
            logger.error(f"处理市场数据失败: {e}")
    
    def calculate_risk_metrics(self):
        """计算风险指标"""
        try:
            logger.info("开始计算风险指标...")
            
            # 这里使用模拟数据演示
            # 实际应用中应该使用真实的历史数据
            
            # 模拟组合数据
            portfolio_data = {
                'portfolio_value': 1000000,
                'volatility': 0.22,
                'max_drawdown': 0.08,
                'sharpe_ratio': 1.8,
                'var_95': 0.035,
                'var_99': 0.052
            }
            
            # 计算风险指标
            self.risk_metrics = portfolio_data
            
            # 检查风险限制
            alerts = self.risk_manager.check_risk_limits(portfolio_data)
            
            if alerts:
                self.alerts.extend(alerts)
                logger.warning(f"发现 {len(alerts)} 个风险预警")
                
                # 处理预警
                for alert in alerts:
                    self.handle_alert(alert)
            
            # 生成风险报告
            risk_report = self.risk_manager.generate_risk_report(portfolio_data)
            
            # 保存报告
            with open('logs/risk_report.txt', 'w', encoding='utf-8') as f:
                f.write(risk_report)
            
            logger.info("风险指标计算完成")
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
    
    def check_positions(self):
        """检查持仓"""
        try:
            logger.info("开始检查持仓...")
            
            # 获取当前持仓
            positions = self.position_manager.positions
            
            if not positions:
                logger.info("当前无持仓")
                return
            
            # 检查每个持仓的止损止盈
            for symbol, position in positions.items():
                if symbol in self.market_data.get('a_stock', {}):
                    current_price = self.market_data['a_stock'][symbol]['price']
                    entry_price = position.get('avg_price', 0)
                    
                    # 检查止损
                    if self.position_manager.check_stop_loss(symbol, current_price, entry_price):
                        # 执行止损
                        quantity = position.get('quantity', 0)
                        self.position_manager.execute_trade(
                            symbol, 'sell', quantity, current_price, 
                            "触发止损"
                        )
                    
                    # 检查止盈
                    elif self.position_manager.check_take_profit(symbol, current_price, entry_price):
                        # 执行止盈
                        quantity = position.get('quantity', 0)
                        self.position_manager.execute_trade(
                            symbol, 'sell', quantity, current_price,
                            "触发止盈"
                        )
            
            # 生成仓位报告
            position_report = self.position_manager.generate_position_report()
            
            # 保存报告
            with open('logs/position_report.txt', 'w', encoding='utf-8') as f:
                f.write(position_report)
            
            logger.info("持仓检查完成")
            
        except Exception as e:
            logger.error(f"检查持仓失败: {e}")
    
    def handle_alert(self, alert: Dict):
        """处理预警"""
        try:
            alert_type = alert.get('type', 'unknown')
            level = alert.get('level', 'info')
            message = alert.get('message', '')
            
            # 根据预警级别采取不同措施
            if level == 'critical':
                # 紧急预警：立即采取措施
                logger.critical(f"紧急预警: {message}")
                
                # 这里可以添加紧急措施，如：
                # 1. 发送短信/邮件通知
                # 2. 自动平仓
                # 3. 降低仓位
                
                # 示例：自动降低仓位
                self.auto_reduce_position()
                
            elif level == 'warning':
                # 警告：记录并通知
                logger.warning(f"警告: {message}")
                
                # 发送通知
                self.send_notification(f"⚠️ 风险警告: {message}")
                
            else:
                # 信息：仅记录
                logger.info(f"信息: {message}")
            
            # 保存预警记录
            self.save_alert_history(alert)
            
        except Exception as e:
            logger.error(f"处理预警失败: {e}")
    
    def auto_reduce_position(self):
        """自动降低仓位"""
        try:
            logger.warning("执行自动降仓...")
            
            # 获取当前持仓
            positions = self.position_manager.positions
            
            if not positions:
                return
            
            # 计算需要降低的仓位比例
            reduce_pct = 0.5  # 降低50%仓位
            
            for symbol, position in positions.items():
                current_qty = position.get('quantity', 0)
                
                if current_qty > 0:
                    # 获取当前价格
                    current_price = None
                    for market_data in self.market_data.values():
                        if symbol in market_data:
                            current_price = market_data[symbol]['price']
                            break
                    
                    if current_price:
                        # 计算卖出数量
                        sell_qty = int(current_qty * reduce_pct)
                        
                        if sell_qty > 0:
                            # 执行卖出
                            self.position_manager.execute_trade(
                                symbol, 'sell', sell_qty, current_price,
                                "自动降仓"
                            )
            
            logger.info("自动降仓完成")
            
        except Exception as e:
            logger.error(f"自动降仓失败: {e}")
    
    def send_notification(self, message: str):
        """发送通知"""
        try:
            # 这里可以实现各种通知方式
            # 如：邮件、短信、Telegram、企业微信等
            
            # 示例：记录到日志文件
            with open('logs/notifications.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
            
            logger.info(f"已发送通知: {message}")
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    def save_alert_history(self, alert: Dict):
        """保存预警历史"""
        try:
            alert['saved_at'] = datetime.now().isoformat()
            
            # 读取现有历史
            history = []
            if os.path.exists('data/alert_history.json'):
                with open('data/alert_history.json', 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 添加新预警
            history.append(alert)
            
            # 只保留最近1000条
            if len(history) > 1000:
                history = history[-1000:]
            
            # 保存
            with open('data/alert_history.json', 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"保存预警历史失败: {e}")
    
    def generate_daily_report(self):
        """生成日报"""
        try:
            logger.info("生成每日报告...")
            
            report_lines = [
                "=" * 60,
                "量化监控系统 - 每日报告",
                "=" * 60,
                f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            # 市场概况
            report_lines.append("📈 市场概况:")
            report_lines.append("-" * 40)
            
            if self.market_data:
                total_symbols = sum(len(data) for data in self.market_data.values())
                report_lines.append(f"  监控标的: {total_symbols} 个")
                
                # 添加主要指数信息
                if 'market_overview' in self.market_data:
                    overview = self.market_data['market_overview']
                    for market, data in overview.items():
                        if market != 'timestamp':
                            report_lines.append(f"  {market.upper()}: {data.get('index', 0):.2f} ({data.get('change', 0):.2%})")
            else:
                report_lines.append("  暂无市场数据")
            
            # 风险状况
            report_lines.append("")
            report_lines.append("⚠️ 风险状况:")
            report_lines.append("-" * 40)
            
            if self.risk_metrics:
                report_lines.append(f"  组合价值: {self.risk_metrics.get('portfolio_value', 0):,.2f}")
                report_lines.append(f"  年化波动率: {self.risk_metrics.get('volatility', 0):.2%}")
                report_lines.append(f"  最大回撤: {self.risk_metrics.get('max_drawdown', 0):.2%}")
                report_lines.append(f"  夏普比率: {self.risk_metrics.get('sharpe_ratio', 0):.2f}")
            else:
                report_lines.append("  暂无风险数据")
            
            # 预警统计
            report_lines.append("")
            report_lines.append("🚨 预警统计:")
            report_lines.append("-" * 40)
            
            if self.alerts:
                critical_count = sum(1 for a in self.alerts if a.get('level') == 'critical')
                warning_count = sum(1 for a in self.alerts if a.get('level') == 'warning')
                
                report_lines.append(f"  今日预警总数: {len(self.alerts)}")
                report_lines.append(f"  紧急预警: {critical_count}")
                report_lines.append(f"  警告: {warning_count}")
            else:
                report_lines.append("  今日无预警")
            
            # 交易统计
            report_lines.append("")
            report_lines.append("💱 交易统计:")
            report_lines.append("-" * 40)
            
            trade_history = self.position_manager.trade_history
            today = datetime.now().date()
            today_trades = [t for t in trade_history if datetime.fromisoformat(t['timestamp']).date() == today]
            
            if today_trades:
                buy_count = sum(1 for t in today_trades if t['action'] == 'buy')
                sell_count = sum(1 for t in today_trades if t['action'] == 'sell')
                total_value = sum(t['value'] for t in today_trades)
                
                report_lines.append(f"  今日交易次数: {len(today_trades)}")
                report_lines.append(f"  买入: {buy_count} 次")
                report_lines.append(f"  卖出: {sell_count} 次")
                report_lines.append(f"  交易总额: {total_value:,.2f}")
            else:
                report_lines.append("  今日无交易")
            
            report_lines.append("")
            report_lines.append("=" * 60)
            
            report_text = "\n".join(report_lines)
            
            # 保存报告
            report_filename = f"logs/daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            # 发送报告
            self.send_notification(f"📊 每日报告已生成: {report_filename}")
            
            logger.info(f"每日报告生成完成: {report_filename}")
            
            return report_text
            
        except Exception as e:
            logger.error(f"生成日报失败: {e}")
            return f"生成日报时出错: {e}"
    
    def setup_schedule(self):
        """设置定时任务"""
        try:
            # 清除现有任务
            schedule.clear()
            
            # 根据市场配置设置更新频率
            for market_name, market_config in self.market_config.get('markets', {}).items():
                if market_config.get('enabled', False):
                    interval = market_config.get('update_interval', 60)
                    
                    if interval >= 60:
                        # 分钟级更新
                        minutes = interval // 60
                        schedule.every(minutes).minutes.do(self.update_market_data)
                        logger.info(f"设置 {market_name} 每 {minutes} 分钟更新")
                    else:
                        # 秒级更新
                        schedule.every(interval).seconds.do(self.update_market_data)
                        logger.info(f"设置 {market_name} 每 {interval} 秒更新")
            
            # 每日报告
            schedule.every().day.at("18:00").do(self.generate_daily_report)
            logger.info("设置每日18:00生成报告")
            
            # 每小时风险检查
            schedule.every().hour.do(self.calculate_risk_metrics)
            logger.info("设置每小时风险检查")
            
            # 每30分钟持仓检查
            schedule.every(30).minutes.do(self.check_positions)
            logger.info("设置每30分钟持仓检查")
            
        except Exception as e:
            logger.error(f"设置定时任务失败: {e}")
    
    def run(self):
        """运行监控系统"""
        try:
            logger.info("启动量化监控系统...")
            self.running = True
            
            # 初始数据更新
            self.update_market_data()
            
            # 设置定时任务
            self.setup_schedule()
            
            # 主循环
            while self.running:
                try:
                    # 运行定时任务
                    schedule.run_pending()
                    
                    # 处理队列中的数据
                    self.process_data_queue()
                    
                    # 休眠1秒
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    logger.info("收到键盘中断信号")
                    self.running = False
                    break
                    
                except Exception as e:
                    logger.error(f"主循环出错: {e}")
                    time.sleep(5)  # 出错后等待5秒
            
            logger.info("量化监控系统已停止")
            
        except Exception as e:
            logger.error(f"运行监控系统失败: {e}")
            self.running = False
    
    def process_data_queue(self):
        """处理数据队列"""
        try:
            while not self.data_queue.empty():
                data = self.data_queue.get()
                # 处理数据
                logger.debug(f"处理队列数据: {data}")
                self.data_queue.task_done()
                
        except Exception as e:
            logger.error(f"处理数据队列失败: {e}")


def main():
    """主函数"""
    # 创建监控系统实例
    monitor = QuantMonitor()
    
    # 运行监控系统
    monitor.run()


if __name__ == "__main__":
    main()