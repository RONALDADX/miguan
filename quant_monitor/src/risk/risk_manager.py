#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理系统
包含最大回撤、波动率、VaR等风险指标计算和监控
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import yaml
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config_path: str = "config/risk_config.yaml"):
        """
        初始化风险管理器
        
        Args:
            config_path: 风险配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.risk_limits = self.config.get('risk_limits', {})
        self.risk_indicators = self.config.get('risk_indicators', {})
        self.alert_settings = self.config.get('alert_settings', {})
        
        # 风险指标缓存
        self.risk_metrics = {}
        self.alert_history = []
        
    def calculate_max_drawdown(self, prices: pd.Series) -> Dict:
        """
        计算最大回撤
        
        Args:
            prices: 价格序列
            
        Returns:
            最大回撤相关信息
        """
        try:
            if len(prices) < 2:
                return {'max_drawdown': 0, 'drawdown_duration': 0, 'peak': 0, 'trough': 0}
            
            # 计算累积收益
            cumulative = (prices / prices.iloc[0]) - 1
            
            # 计算回撤
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / (running_max + 1)
            
            # 最大回撤
            max_dd = drawdown.min()
            max_dd_idx = drawdown.idxmin()
            
            # 找到峰值
            peak_idx = cumulative.loc[:max_dd_idx].idxmax()
            peak = cumulative[peak_idx]
            trough = cumulative[max_dd_idx]
            
            # 计算回撤持续时间
            if isinstance(max_dd_idx, (int, np.integer)):
                drawdown_duration = len(prices) - max_dd_idx
            else:
                drawdown_duration = (prices.index[-1] - max_dd_idx).days
            
            return {
                'max_drawdown': float(abs(max_dd)),
                'drawdown_duration': int(drawdown_duration),
                'peak_value': float(peak),
                'trough_value': float(trough),
                'peak_date': str(peak_idx),
                'trough_date': str(max_dd_idx)
            }
            
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return {'max_drawdown': 0, 'drawdown_duration': 0, 'peak': 0, 'trough': 0}
    
    def calculate_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """
        计算波动率
        
        Args:
            returns: 收益率序列
            annualize: 是否年化
            
        Returns:
            波动率
        """
        try:
            if len(returns) < 2:
                return 0.0
            
            volatility = returns.std()
            
            if annualize:
                # 假设252个交易日
                volatility *= np.sqrt(252)
            
            return float(volatility)
            
        except Exception as e:
            logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95, 
                     method: str = 'historical') -> Dict:
        """
        计算在险价值(VaR)
        
        Args:
            returns: 收益率序列
            confidence: 置信水平
            method: 计算方法 ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            VaR相关信息
        """
        try:
            if len(returns) < 10:
                return {'var': 0, 'cvar': 0, 'confidence': confidence}
            
            if method == 'historical':
                # 历史模拟法
                var = np.percentile(returns, (1 - confidence) * 100)
                cvar = returns[returns <= var].mean()
                
            elif method == 'parametric':
                # 参数法（正态分布假设）
                mu = returns.mean()
                sigma = returns.std()
                var = stats.norm.ppf(1 - confidence, mu, sigma)
                cvar = mu - sigma * stats.norm.pdf(stats.norm.ppf(1 - confidence)) / (1 - confidence)
                
            else:
                # 蒙特卡洛模拟
                mu = returns.mean()
                sigma = returns.std()
                simulated = np.random.normal(mu, sigma, 10000)
                var = np.percentile(simulated, (1 - confidence) * 100)
                cvar = simulated[simulated <= var].mean()
            
            return {
                'var': float(abs(var)),
                'cvar': float(abs(cvar)),
                'confidence': confidence,
                'method': method
            }
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return {'var': 0, 'cvar': 0, 'confidence': confidence}
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率
            
        Returns:
            夏普比率
        """
        try:
            if len(returns) < 2:
                return 0.0
            
            excess_returns = returns - risk_free_rate / 252  # 日化无风险利率
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"计算夏普比率失败: {e}")
            return 0.0
    
    def calculate_correlation_matrix(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算相关性矩阵
        
        Args:
            price_data: 价格数据DataFrame，每列为一个标的
            
        Returns:
            相关性矩阵
        """
        try:
            if len(price_data) < 2:
                return pd.DataFrame()
            
            # 计算收益率
            returns = price_data.pct_change().dropna()
            
            if len(returns) < 2:
                return pd.DataFrame()
            
            # 计算相关性矩阵
            corr_matrix = returns.corr()
            
            return corr_matrix
            
        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return pd.DataFrame()
    
    def check_risk_limits(self, portfolio_data: Dict) -> List[Dict]:
        """
        检查风险限制
        
        Args:
            portfolio_data: 组合数据
            
        Returns:
            风险检查结果列表
        """
        alerts = []
        
        try:
            # 检查最大回撤
            if 'max_drawdown' in portfolio_data:
                current_dd = portfolio_data['max_drawdown']
                max_dd_limit = self.risk_limits.get('max_drawdown', 0.10)
                
                if current_dd > max_dd_limit:
                    alerts.append({
                        'type': 'max_drawdown_breach',
                        'level': 'critical',
                        'message': f"最大回撤 {current_dd:.2%} 超过限制 {max_dd_limit:.2%}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 检查波动率
            if 'volatility' in portfolio_data:
                current_vol = portfolio_data['volatility']
                max_vol_limit = self.risk_limits.get('max_volatility', 0.30)
                
                if current_vol > max_vol_limit:
                    alerts.append({
                        'type': 'high_volatility',
                        'level': 'warning',
                        'message': f"波动率 {current_vol:.2%} 超过限制 {max_vol_limit:.2%}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 检查VaR
            if 'var' in portfolio_data:
                current_var = portfolio_data['var']
                max_var_limit = self.risk_limits.get('max_var', 0.05)
                
                if current_var > max_var_limit:
                    alerts.append({
                        'type': 'var_breach',
                        'level': 'critical',
                        'message': f"VaR {current_var:.2%} 超过限制 {max_var_limit:.2%}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 检查流动性
            if 'liquidity' in portfolio_data:
                current_liq = portfolio_data['liquidity']
                min_liq_limit = self.risk_limits.get('min_liquidity', 1000000)
                
                if current_liq < min_liq_limit:
                    alerts.append({
                        'type': 'liquidity_warning',
                        'level': 'warning',
                        'message': f"流动性 {current_liq:,.0f} 低于限制 {min_liq_limit:,.0f}",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 检查价格异常
            if 'price_deviation' in portfolio_data:
                current_dev = portfolio_data['price_deviation']
                dev_threshold = self.risk_indicators.get('price_deviation_threshold', 3.0)
                
                if abs(current_dev) > dev_threshold:
                    alerts.append({
                        'type': 'price_anomaly',
                        'level': 'warning',
                        'message': f"价格偏离 {current_dev:.2f}σ 超过阈值 {dev_threshold}σ",
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 保存预警历史
            if alerts:
                self.alert_history.extend(alerts)
                # 只保留最近100条记录
                if len(self.alert_history) > 100:
                    self.alert_history = self.alert_history[-100:]
            
            return alerts
            
        except Exception as e:
            logger.error(f"检查风险限制失败: {e}")
            return []
    
    def calculate_portfolio_risk(self, positions: Dict, price_data: pd.DataFrame) -> Dict:
        """
        计算组合风险
        
        Args:
            positions: 持仓字典 {symbol: {'quantity': qty, 'price': price}}
            price_data: 价格数据DataFrame
            
        Returns:
            组合风险指标
        """
        try:
            if not positions or price_data.empty:
                return {}
            
            # 提取相关标的的价格
            symbols = list(positions.keys())
            relevant_prices = price_data[symbols].dropna() if all(s in price_data.columns for s in symbols) else pd.DataFrame()
            
            if relevant_prices.empty:
                return {}
            
            # 计算组合价值
            portfolio_values = []
            for symbol, pos in positions.items():
                if symbol in relevant_prices.columns:
                    qty = pos.get('quantity', 0)
                    price_series = relevant_prices[symbol]
                    position_value = price_series * qty
                    portfolio_values.append(position_value)
            
            if not portfolio_values:
                return {}
            
            # 计算总组合价值
            total_portfolio = pd.concat(portfolio_values, axis=1).sum(axis=1)
            
            # 计算组合收益率
            portfolio_returns = total_portfolio.pct_change().dropna()
            
            if len(portfolio_returns) < 2:
                return {}
            
            # 计算各项风险指标
            risk_metrics = {
                'portfolio_value': float(total_portfolio.iloc[-1]),
                'volatility': self.calculate_volatility(portfolio_returns),
                'max_drawdown': self.calculate_max_drawdown(total_portfolio)['max_drawdown'],
                'sharpe_ratio': self.calculate_sharpe_ratio(portfolio_returns),
                'var_95': self.calculate_var(portfolio_returns, confidence=0.95)['var'],
                'var_99': self.calculate_var(portfolio_returns, confidence=0.99)['var']
            }
            
            # 计算相关性风险
            corr_matrix = self.calculate_correlation_matrix(relevant_prices)
            if not corr_matrix.empty:
                risk_metrics['avg_correlation'] = float(corr_matrix.mean().mean())
                risk_metrics['max_correlation'] = float(corr_matrix.max().max())
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"计算组合风险失败: {e}")
            return {}
    
    def generate_risk_report(self, risk_metrics: Dict) -> str:
        """
        生成风险报告
        
        Args:
            risk_metrics: 风险指标
            
        Returns:
            风险报告文本
        """
        try:
            report_lines = [
                "=" * 60,
                "风险监控报告",
                "=" * 60,
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ""
            ]
            
            if not risk_metrics:
                report_lines.append("⚠️ 无有效的风险数据")
                return "\n".join(report_lines)
            
            # 添加风险指标
            report_lines.append("📊 风险指标概览:")
            report_lines.append("-" * 40)
            
            metrics_mapping = {
                'portfolio_value': ('组合价值', '{:,.2f}'),
                'volatility': ('年化波动率', '{:.2%}'),
                'max_drawdown': ('最大回撤', '{:.2%}'),
                'sharpe_ratio': ('夏普比率', '{:.2f}'),
                'var_95': ('95%置信度VaR', '{:.2%}'),
                'var_99': ('99%置信度VaR', '{:.2%}'),
                'avg_correlation': ('平均相关性', '{:.3f}'),
                'max_correlation': ('最大相关性', '{:.3f}')
            }
            
            for key, (name, fmt) in metrics_mapping.items():
                if key in risk_metrics:
                    value = risk_metrics[key]
                    report_lines.append(f"  {name}: {fmt.format(value)}")
            
            # 添加风险限制检查
            report_lines.append("")
            report_lines.append("🔍 风险限制检查:")
            report_lines.append("-" * 40)
            
            alerts = self.check_risk_limits(risk_metrics)
            if alerts:
                for alert in alerts:
                    level_emoji = {'warning': '⚠️', 'critical': '🚨'}.get(alert['level'], 'ℹ️')
                    report_lines.append(f"  {level_emoji} {alert['message']}")
            else:
                report_lines.append("  ✅ 所有风险指标均在限制范围内")
            
            report_lines.append("")
            report_lines.append("=" * 60)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            return f"生成风险报告时出错: {e}"


if __name__ == "__main__":
    # 测试代码
    risk_mgr = RiskManager()
    
    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    
    # 测试最大回撤
    drawdown_info = risk_mgr.calculate_max_drawdown(prices)
    print("最大回撤测试:", drawdown_info)
    
    # 测试波动率
    returns = prices.pct_change().dropna()
    volatility = risk_mgr.calculate_volatility(returns)
    print(f"年化波动率: {volatility:.2%}")
    
    # 测试VaR
    var_info = risk_mgr.calculate_var(returns)
    print("VaR测试:", var_info)
    
    # 测试夏普比率
    sharpe = risk_mgr.calculate_sharpe_ratio(returns)
    print(f"夏普比率: {sharpe:.2f}")
    
    # 测试风险报告
    test_metrics = {
        'portfolio_value': 1000000,
        'volatility': 0.25,
        'max_drawdown': 0.12,
        'sharpe_ratio': 1.5,
        'var_95': 0.04,
        'var_99': 0.06
    }
    
    report = risk_mgr.generate_risk_report(test_metrics)
    print("\n风险报告测试:")
    print(report)