#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓位管理系统
包含仓位计算、调整、止损止盈等功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
import yaml
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PositionManager:
    """仓位管理器"""
    
    def __init__(self, config_path: str = "config/position_config.yaml"):
        """
        初始化仓位管理器
        
        Args:
            config_path: 仓位配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.position_strategies = self.config.get('position_strategies', {})
        self.position_limits = self.config.get('position_limits', {})
        self.stop_loss = self.config.get('stop_loss', {})
        self.take_profit = self.config.get('take_profit', {})
        self.sizing_methods = self.config.get('sizing_methods', {})
        self.portfolio_construction = self.config.get('portfolio_construction', {})
        
        # 当前持仓
        self.positions = {}
        # 交易历史
        self.trade_history = []
        # 仓位调整记录
        self.adjustment_history = []
        
    def calculate_position_size(self, capital: float, risk_per_trade: float, 
                               entry_price: float, stop_loss_price: float) -> Tuple[int, float]:
        """
        计算仓位大小（基于固定风险比例）
        
        Args:
            capital: 总资金
            risk_per_trade: 每笔交易风险比例
            entry_price: 入场价格
            stop_loss_price: 止损价格
            
        Returns:
            (数量, 风险金额)
        """
        try:
            # 计算每单位风险
            risk_per_unit = abs(entry_price - stop_loss_price)
            
            if risk_per_unit <= 0:
                logger.warning("止损价格无效")
                return 0, 0
            
            # 计算风险金额
            risk_amount = capital * risk_per_trade
            
            # 计算数量
            quantity = math.floor(risk_amount / risk_per_unit)
            
            # 确保最小交易单位
            if quantity < 1:
                quantity = 1
            
            return quantity, risk_amount
            
        except Exception as e:
            logger.error(f"计算仓位大小失败: {e}")
            return 0, 0
    
    def calculate_kelly_position(self, win_rate: float, win_loss_ratio: float, 
                                capital: float, max_fraction: float = 0.25) -> float:
        """
        计算凯利仓位
        
        Args:
            win_rate: 胜率
            win_loss_ratio: 盈亏比
            capital: 资金
            max_fraction: 最大仓位比例限制
            
        Returns:
            凯利仓位比例
        """
        try:
            # 凯利公式: f* = (bp - q) / b
            # 其中: b = 盈亏比, p = 胜率, q = 1-p
            b = win_loss_ratio
            p = win_rate
            q = 1 - p
            
            if b <= 0:
                return 0
            
            kelly_fraction = (b * p - q) / b
            
            # 应用限制
            kelly_fraction = max(0, min(kelly_fraction, max_fraction))
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"计算凯利仓位失败: {e}")
            return 0
    
    def calculate_volatility_adjusted_position(self, base_position: float, 
                                              volatility: float, 
                                              avg_volatility: float = 0.20) -> float:
        """
        计算波动率调整仓位
        
        Args:
            base_position: 基础仓位比例
            volatility: 当前波动率
            avg_volatility: 平均波动率
            
        Returns:
            调整后的仓位比例
        """
        try:
            if volatility <= 0:
                return base_position
            
            # 波动率调整因子
            volatility_factor = avg_volatility / volatility
            
            # 计算调整后仓位
            adjusted_position = base_position * volatility_factor
            
            # 应用限制
            max_position = self.position_limits.get('max_total_position', 1.0)
            adjusted_position = min(adjusted_position, max_position)
            
            return adjusted_position
            
        except Exception as e:
            logger.error(f"计算波动率调整仓位失败: {e}")
            return base_position
    
    def calculate_trend_position(self, price_series: pd.Series, 
                                base_position: float = 0.10) -> float:
        """
        计算趋势跟踪仓位
        
        Args:
            price_series: 价格序列
            base_position: 基础仓位
            
        Returns:
            趋势仓位比例
        """
        try:
            if len(price_series) < 20:
                return base_position
            
            # 计算趋势指标（简单移动平均）
            short_ma = price_series.rolling(window=10).mean().iloc[-1]
            long_ma = price_series.rolling(window=30).mean().iloc[-1]
            
            # 判断趋势方向
            if short_ma > long_ma:
                # 上升趋势，增加仓位
                trend_factor = 1.5
            else:
                # 下降趋势，减少仓位
                trend_factor = 0.5
            
            trend_position = base_position * trend_factor
            
            # 应用限制
            max_position = self.position_limits.get('max_total_position', 1.0)
            trend_position = min(trend_position, max_position)
            
            return trend_position
            
        except Exception as e:
            logger.error(f"计算趋势仓位失败: {e}")
            return base_position
    
    def check_stop_loss(self, symbol: str, current_price: float, 
                       entry_price: float, position_type: str = 'long') -> bool:
        """
        检查止损条件
        
        Args:
            symbol: 标的代码
            current_price: 当前价格
            entry_price: 入场价格
            position_type: 仓位类型 ('long' or 'short')
            
        Returns:
            是否触发止损
        """
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            
            # 获取止损配置
            stop_config = self.stop_loss
            
            # 检查固定止损
            if stop_config.get('fixed_stop', {}).get('enabled', False):
                stop_loss_pct = stop_config['fixed_stop'].get('stop_loss_pct', 0.08)
                
                if position_type == 'long':
                    stop_price = entry_price * (1 - stop_loss_pct)
                    if current_price <= stop_price:
                        logger.info(f"{symbol} 触发固定止损: {current_price} <= {stop_price}")
                        return True
                else:
                    stop_price = entry_price * (1 + stop_loss_pct)
                    if current_price >= stop_price:
                        logger.info(f"{symbol} 触发固定止损: {current_price} >= {stop_price}")
                        return True
            
            # 检查移动止损
            if stop_config.get('trailing_stop', {}).get('enabled', False):
                trailing_pct = stop_config['trailing_stop'].get('trailing_pct', 0.10)
                activation_pct = stop_config['trailing_stop'].get('activation_pct', 0.05)
                
                # 计算最高价/最低价
                if 'price_history' in position:
                    price_history = position['price_history']
                    if position_type == 'long':
                        highest_price = max(price_history)
                        if current_price >= entry_price * (1 + activation_pct):
                            # 已激活移动止损
                            trailing_stop = highest_price * (1 - trailing_pct)
                            if current_price <= trailing_stop:
                                logger.info(f"{symbol} 触发移动止损: {current_price} <= {trailing_stop}")
                                return True
                    else:
                        lowest_price = min(price_history)
                        if current_price <= entry_price * (1 - activation_pct):
                            trailing_stop = lowest_price * (1 + trailing_pct)
                            if current_price >= trailing_stop:
                                logger.info(f"{symbol} 触发移动止损: {current_price} >= {trailing_stop}")
                                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查止损失败: {e}")
            return False
    
    def check_take_profit(self, symbol: str, current_price: float, 
                         entry_price: float, position_type: str = 'long') -> bool:
        """
        检查止盈条件
        
        Args:
            symbol: 标的代码
            current_price: 当前价格
            entry_price: 入场价格
            position_type: 仓位类型
            
        Returns:
            是否触发止盈
        """
        try:
            if symbol not in self.positions:
                return False
            
            # 获取止盈配置
            tp_config = self.take_profit
            
            # 检查固定止盈
            if tp_config.get('fixed_take_profit', {}).get('enabled', False):
                take_profit_pct = tp_config['fixed_take_profit'].get('take_profit_pct', 0.20)
                
                if position_type == 'long':
                    tp_price = entry_price * (1 + take_profit_pct)
                    if current_price >= tp_price:
                        logger.info(f"{symbol} 触发固定止盈: {current_price} >= {tp_price}")
                        return True
                else:
                    tp_price = entry_price * (1 - take_profit_pct)
                    if current_price <= tp_price:
                        logger.info(f"{symbol} 触发固定止盈: {current_price} <= {tp_price}")
                        return True
            
            # 检查分批止盈
            if tp_config.get('scaling_out', {}).get('enabled', False):
                scale_points = tp_config['scaling_out'].get('scale_points', [0.10, 0.15, 0.20])
                scale_percentages = tp_config['scaling_out'].get('scale_percentages', [0.3, 0.3, 0.4])
                
                position = self.positions[symbol]
                if 'scaled_out' not in position:
                    position['scaled_out'] = []
                
                for i, (point, percentage) in enumerate(zip(scale_points, scale_percentages)):
                    if i in position['scaled_out']:
                        continue
                    
                    tp_price = entry_price * (1 + point) if position_type == 'long' else entry_price * (1 - point)
                    
                    if (position_type == 'long' and current_price >= tp_price) or \
                       (position_type == 'short' and current_price <= tp_price):
                        
                        # 记录分批止盈
                        position['scaled_out'].append(i)
                        logger.info(f"{symbol} 触发第{i+1}批止盈: {current_price} 达到 {point:.1%} 目标")
                        
                        # 如果所有批次都完成，返回True
                        if len(position['scaled_out']) == len(scale_points):
                            return True
                        else:
                            # 部分止盈，不关闭整个仓位
                            return False
            
            return False
            
        except Exception as e:
            logger.error(f"检查止盈失败: {e}")
            return False
    
    def calculate_portfolio_allocation(self, capital: float, 
                                      signals: Dict[str, Dict]) -> Dict[str, float]:
        """
        计算组合分配
        
        Args:
            capital: 总资金
            signals: 交易信号字典 {symbol: {'score': score, 'volatility': vol}}
            
        Returns:
            仓位分配字典 {symbol: allocation_pct}
        """
        try:
            if not signals:
                return {}
            
            # 获取配置
            max_positions = self.portfolio_construction.get('max_positions', 20)
            min_position = self.portfolio_construction.get('min_position_size', 0.01)
            max_position = self.portfolio_construction.get('max_position_size', 0.20)
            
            # 根据信号分数排序
            sorted_signals = sorted(signals.items(), 
                                   key=lambda x: x[1].get('score', 0), 
                                   reverse=True)
            
            # 选择前N个标的
            selected = sorted_signals[:max_positions]
            
            # 计算总分数
            total_score = sum(signal[1].get('score', 0) for signal in selected)
            
            if total_score <= 0:
                return {}
            
            # 计算分配比例
            allocations = {}
            for symbol, signal in selected:
                score = signal.get('score', 0)
                allocation = score / total_score
                
                # 应用最小/最大限制
                allocation = max(min_position, min(allocation, max_position))
                
                allocations[symbol] = allocation
            
            # 归一化
            total_alloc = sum(allocations.values())
            if total_alloc > 0:
                allocations = {k: v/total_alloc for k, v in allocations.items()}
            
            return allocations
            
        except Exception as e:
            logger.error(f"计算组合分配失败: {e}")
            return {}
    
    def execute_trade(self, symbol: str, action: str, quantity: int, 
                     price: float, reason: str = "") -> Dict:
        """
        执行交易
        
        Args:
            symbol: 标的代码
            action: 交易动作 ('buy', 'sell')
            quantity: 数量
            price: 价格
            reason: 交易原因
            
        Returns:
            交易结果
        """
        try:
            trade = {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'value': quantity * price,
                'timestamp': datetime.now().isoformat(),
                'reason': reason
            }
            
            # 更新持仓
            if action == 'buy':
                if symbol in self.positions:
                    self.positions[symbol]['quantity'] += quantity
                    self.positions[symbol]['avg_price'] = (
                        (self.positions[symbol]['avg_price'] * 
                         (self.positions[symbol]['quantity'] - quantity) + 
                         price * quantity) / self.positions[symbol]['quantity']
                    )
                else:
                    self.positions[symbol] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'entry_time': datetime.now().isoformat(),
                        'price_history': [price]
                    }
                    
            elif action == 'sell':
                if symbol in self.positions:
                    current_qty = self.positions[symbol]['quantity']
                    
                    if quantity >= current_qty:
                        # 全部卖出
                        trade['profit'] = (price - self.positions[symbol]['avg_price']) * current_qty
                        trade['profit_pct'] = (price / self.positions[symbol]['avg_price'] - 1) * 100
                        del self.positions[symbol]
                    else:
                        # 部分卖出
                        self.positions[symbol]['quantity'] -= quantity
                        trade['profit'] = (price - self.positions[symbol]['avg_price']) * quantity
                        trade['profit_pct'] = (price / self.positions[symbol]['avg_price'] - 1) * 100
            
            # 记录交易历史
            self.trade_history.append(trade)
            
            # 只保留最近1000条记录
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
            logger.info(f"执行交易: {action.upper()} {quantity} {symbol} @ {price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return {}
    
    def generate_position_report(self) -> str:
        """
        生成仓位报告
        
        Returns:
            仓位报告文本
        """
        try:
            report_lines = [
                "=" * 60,
                "仓位管理报告",
                "=" * 60,
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            if not self.positions:
                report_lines.append("📭 当前无持仓")
                return "\n".join(report_lines)
            
            # 持仓概览
            report_lines.append("📊 当前持仓:")
            report_lines.append("-" * 40)
            
            total_value = 0
            for symbol, position in self.positions.items():
                qty = position.get('quantity', 0)
                avg_price = position.get('avg_price', 0)
                current_value = qty * avg_price  # 这里应该用当前价格，暂时用平均价
                total_value += current_value
                
                report_lines.append(f"  {symbol}:")
                report_lines.append(f"    数量: {qty:,}")
                report_lines.append(f"    均价: {avg_price:.2f}")
                report_lines.append(f"    价值: {current_value:,.2f}")
                report_lines.append(f"    持仓时间: {position.get('entry_time', 'N/A')}")
            
            report_lines.append(f"\n  总持仓价值: {total_value:,.2f}")
            
            # 最近交易
            report_lines.append("")
            report_lines.append("💱 最近交易:")
            report_lines.append("-" * 40)
            
            recent_trades = self.trade_history[-5:] if self.trade_history else []
            for trade in recent_trades:
                action_emoji = {'buy': '🟢', 'sell': '🔴'}.get(trade['action'], '⚪')
                report_lines.append(f"  {action_emoji} {trade['timestamp'][:16]} {trade['action'].upper()} {trade['quantity']} {trade['symbol']} @ {trade['price']:.2f}")
                if 'profit' in trade:
                    profit_sign = '+' if trade['profit'] >= 0 else ''
                    report_lines.append(f"    盈亏: {profit_sign}{trade['profit']:.2f} ({trade.get('profit_pct', 0):.2f}%)")
            
            report_lines.append("")
            report_lines.append("=" * 60)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成仓位报告失败: {e}")
            return f"生成仓位报告时出错: {e}"


if __name__ == "__main__":
    # 测试代码
    pos_mgr = PositionManager()
    
    # 测试仓位计算
    capital = 1000000
    risk_per_trade = 0.02
    entry_price = 100
    stop_loss = 92
    
    quantity, risk_amount = pos_mgr.calculate_position_size(capital, risk_per_trade, entry_price, stop_loss)
    print(f"固定风险仓位计算: 数量={quantity}, 风险金额={risk_amount:.2f}")
    
    # 测试凯利仓位
    win_rate = 0.55
    win_loss_ratio = 2.0
    kelly_fraction = pos_mgr.calculate_kelly_position(win_rate, win_loss_ratio, capital)
    print(f"凯利仓位比例: {kelly_fraction:.2%}")
    
    # 测试波动率调整仓位
    base_position = 0.10
    volatility = 0.25
    avg_volatility = 0.20
    vol_position = pos_mgr.calculate_volatility_adjusted_position(base_position, volatility, avg_volatility)
    print(f"波动率调整仓位: {vol_position:.2%}")
    
    # 测试交易执行
    trade1 = pos_mgr.execute_trade("000001", "buy", 100, 50.5, "测试买入")
    print("交易1:", trade1)
    
    trade2 = pos_mgr.execute_trade("000001", "sell", 50, 55.0, "测试卖出")
    print("交易2:", trade2)
    
    # 测试仓位报告
    report = pos_mgr.generate_position_report()
    print("\n仓位报告测试:")
    print(report)