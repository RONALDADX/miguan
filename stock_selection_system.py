#!/usr/bin/env python3
"""
智能选股系统
基于实时数据和自定义策略进行股票选择
"""

import requests
import json
import math
import random
from datetime import datetime, timedelta
import time
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockSelectionSystem:
    """智能选股系统"""
    
    def __init__(self):
        self.stock_pool = self._initialize_stock_pool()
        self.strategy_weights = {
            'momentum': 0.3,      # 动量因子
            'value': 0.25,        # 价值因子
            'growth': 0.25,       # 成长因子
            'quality': 0.2        # 质量因子
        }
        self.market_condition = "normal"  # normal, bullish, bearish, volatile
        
    def _initialize_stock_pool(self) -> Dict:
        """初始化股票池（示例）"""
        return {
            # A股
            "000001.SZ": {"name": "平安银行", "sector": "金融"},
            "000858.SZ": {"name": "五粮液", "sector": "消费"},
            "300750.SZ": {"name": "宁德时代", "sector": "新能源"},
            "600519.SH": {"name": "贵州茅台", "sector": "消费"},
            "601318.SH": {"name": "中国平安", "sector": "金融"},
            
            # 港股
            "0700.HK": {"name": "腾讯控股", "sector": "科技"},
            "9988.HK": {"name": "阿里巴巴", "sector": "科技"},
            "3690.HK": {"name": "美团", "sector": "科技"},
            
            # 美股
            "AAPL": {"name": "苹果", "sector": "科技"},
            "MSFT": {"name": "微软", "sector": "科技"},
            "TSLA": {"name": "特斯拉", "sector": "汽车"},
            "NVDA": {"name": "英伟达", "sector": "半导体"},
        }
    
    def get_real_time_data(self, symbol: str) -> Optional[Dict]:
        """获取实时股票数据（模拟）"""
        # 在实际应用中，这里应该调用真实的API
        # 为了演示，我们使用模拟数据
        
        try:
            # 模拟数据生成
            base_price = {
                "000001.SZ": 10.5,
                "000858.SZ": 150.0,
                "300750.SZ": 180.0,
                "600519.SH": 1700.0,
                "601318.SH": 45.0,
                "0700.HK": 300.0,
                "9988.HK": 80.0,
                "3690.HK": 120.0,
                "AAPL": 180.0,
                "MSFT": 400.0,
                "TSLA": 200.0,
                "NVDA": 800.0,
            }.get(symbol, 100.0)
            
            # 添加随机波动
            change_percent = random.uniform(-0.03, 0.03)  # -3%到+3%
            current_price = base_price * (1 + change_percent)
            
            volume = random.randint(1000000, 10000000)
            
            return {
                "symbol": symbol,
                "price": round(current_price, 2),
                "change": round(current_price - base_price, 2),
                "change_percent": round(change_percent * 100, 2),
                "volume": volume,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "high": round(current_price * 1.02, 2),
                "low": round(current_price * 0.98, 2),
                "open": round(base_price * (1 + random.uniform(-0.01, 0.01)), 2)
            }
            
        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {e}")
            return None
    
    def analyze_market_condition(self, market_data: List[Dict]) -> str:
        """分析市场状况"""
        if not market_data:
            return "normal"
        
        changes = [stock["change_percent"] for stock in market_data if stock]
        
        if not changes:
            return "normal"
            
        avg_change = sum(changes) / len(changes)
        
        # 计算标准差
        variance = sum((x - avg_change) ** 2 for x in changes) / len(changes)
        volatility = math.sqrt(variance)
        
        if avg_change > 1.5 and volatility < 1.0:
            return "bullish"  # 牛市
        elif avg_change < -1.5 and volatility < 1.0:
            return "bearish"  # 熊市
        elif volatility > 2.0:
            return "volatile"  # 波动市
        else:
            return "normal"    # 正常市
    
    def adjust_strategy_weights(self, market_condition: str) -> Dict:
        """根据市场状况调整策略权重"""
        base_weights = self.strategy_weights.copy()
        
        adjustments = {
            "bullish": {"momentum": 0.1, "growth": 0.1, "value": -0.1, "quality": -0.1},
            "bearish": {"momentum": -0.1, "value": 0.15, "quality": 0.15, "growth": -0.2},
            "volatile": {"quality": 0.2, "value": 0.1, "momentum": -0.15, "growth": -0.15},
            "normal": {}  # 保持原权重
        }
        
        adjustment = adjustments.get(market_condition, {})
        
        # 应用调整
        for factor, adj in adjustment.items():
            base_weights[factor] += adj
        
        # 确保权重和为1
        total = sum(base_weights.values())
        base_weights = {k: v/total for k, v in base_weights.items()}
        
        logger.info(f"市场状况: {market_condition}, 调整后权重: {base_weights}")
        return base_weights
    
    def calculate_factors(self, stock_data: Dict) -> Dict:
        """计算各种因子得分"""
        price = stock_data["price"]
        change_percent = stock_data["change_percent"]
        volume = stock_data["volume"]
        
        # 动量因子（近期表现）
        momentum_score = min(max(change_percent / 3, -1), 1)  # 归一化到[-1, 1]
        
        # 价值因子（基于价格，简化版）
        # 在实际应用中，这里应该使用PE、PB等指标
        value_score = 1.0 if price < 100 else 0.5 if price < 500 else 0.0
        
        # 成长因子（基于价格变化，简化版）
        growth_score = min(max(change_percent / 5, 0), 1)  # 0到1
        
        # 质量因子（基于成交量，简化版）
        quality_score = min(volume / 5000000, 1)  # 成交量越大，质量越高
        
        return {
            "momentum": momentum_score,
            "value": value_score,
            "growth": growth_score,
            "quality": quality_score
        }
    
    def apply_selection_strategy(self, stock_data: Dict, weights: Dict) -> float:
        """应用选股策略，计算综合得分"""
        factors = self.calculate_factors(stock_data)
        
        total_score = 0
        for factor, weight in weights.items():
            total_score += factors[factor] * weight
        
        # 添加额外调整（例如行业偏好）
        sector_bonus = {
            "科技": 0.1,
            "新能源": 0.08,
            "消费": 0.05,
            "金融": 0.0
        }.get(stock_data.get("sector", ""), 0.0)
        
        total_score += sector_bonus
        
        return round(total_score, 4)
    
    def select_stocks(self, top_n: int = 5) -> List[Tuple[str, float, Dict]]:
        """选择股票"""
        logger.info("开始选股分析...")
        
        # 1. 获取所有股票数据
        all_stock_data = []
        for symbol, info in self.stock_pool.items():
            data = self.get_real_time_data(symbol)
            if data:
                data.update(info)  # 添加基本信息
                all_stock_data.append(data)
        
        # 2. 分析市场状况
        self.market_condition = self.analyze_market_condition(all_stock_data)
        
        # 3. 根据市场状况调整策略权重
        adjusted_weights = self.adjust_strategy_weights(self.market_condition)
        
        # 4. 对每只股票应用策略
        scored_stocks = []
        for stock_data in all_stock_data:
            score = self.apply_selection_strategy(stock_data, adjusted_weights)
            scored_stocks.append((
                stock_data["symbol"],
                score,
                stock_data
            ))
        
        # 5. 按得分排序
        scored_stocks.sort(key=lambda x: x[1], reverse=True)
        
        # 6. 返回前N名
        selected = scored_stocks[:top_n]
        
        logger.info(f"选股完成，市场状况: {self.market_condition}")
        return selected
    
    def generate_report(self, selected_stocks: List[Tuple]) -> str:
        """生成选股报告"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append(f"智能选股报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"市场状况: {self.market_condition}")
        report_lines.append("=" * 60)
        
        for i, (symbol, score, data) in enumerate(selected_stocks, 1):
            report_lines.append(f"\n{i}. {data['name']} ({symbol})")
            report_lines.append(f"   综合得分: {score:.4f}")
            report_lines.append(f"   当前价格: {data['price']}")
            report_lines.append(f"   涨跌幅: {data['change_percent']}%")
            report_lines.append(f"   成交量: {data['volume']:,}")
            report_lines.append(f"   行业: {data.get('sector', 'N/A')}")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("选股策略说明:")
        report_lines.append("1. 动量因子: 关注近期价格表现")
        report_lines.append("2. 价值因子: 关注估值合理性")
        report_lines.append("3. 成长因子: 关注增长潜力")
        report_lines.append("4. 质量因子: 关注基本面质量")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)

# 策略配置接口
class StrategyConfig:
    """策略配置管理器"""
    
    @staticmethod
    def get_custom_strategy(strategy_name: str):
        """获取自定义策略"""
        strategies = {
            "aggressive": {  # 激进策略
                "momentum": 0.4,
                "growth": 0.3,
                "value": 0.2,
                "quality": 0.1
            },
            "conservative": {  # 保守策略
                "value": 0.4,
                "quality": 0.4,
                "momentum": 0.1,
                "growth": 0.1
            },
            "balanced": {  # 平衡策略
                "momentum": 0.25,
                "value": 0.25,
                "growth": 0.25,
                "quality": 0.25
            }
        }
        return strategies.get(strategy_name, strategies["balanced"])

def main():
    """主函数"""
    print("🚀 启动智能选股系统...")
    
    # 创建选股系统
    system = StockSelectionSystem()
    
    # 执行选股
    selected_stocks = system.select_stocks(top_n=8)
    
    # 生成报告
    report = system.generate_report(selected_stocks)
    
    # 输出报告
    print(report)
    
    # 保存报告到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"stock_selection_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: {report_filename}")
    
    # 提供策略建议
    print("\n💡 策略建议:")
    if system.market_condition == "bullish":
        print("  市场处于牛市，建议增加成长股和动量股的配置")
    elif system.market_condition == "bearish":
        print("  市场处于熊市，建议关注价值股和防御性板块")
    elif system.market_condition == "volatile":
        print("  市场波动较大，建议控制仓位，关注质量因子")
    else:
        print("  市场正常，建议均衡配置")

if __name__ == "__main__":
    main()