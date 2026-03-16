#!/usr/bin/env python3
"""
多策略组合选股系统
整合一号策略和二号策略
"""

import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiStrategySystem:
    """多策略组合系统"""
    
    def __init__(self):
        self.stock_pool = self._initialize_stock_pool()
        self.strategies = {
            "strategy_one": {
                "name": "多指标共振策略",
                "weight": 0.6,  # 权重
                "description": "MACD零线以上 + 多技术指标验证"
            },
            "strategy_two": {
                "name": "DMI趋势策略", 
                "weight": 0.4,
                "description": "DMI双重确认 + RSI金叉 + 高换手"
            }
        }
    
    def _initialize_stock_pool(self) -> Dict:
        """初始化股票池"""
        return {
            # 高成长股
            "300750.SZ": {"name": "宁德时代", "sector": "新能源", "style": "growth"},
            "300059.SZ": {"name": "东方财富", "sector": "金融科技", "style": "growth"},
            "300124.SZ": {"name": "汇川技术", "sector": "工业自动化", "style": "growth"},
            
            # 价值股
            "000001.SZ": {"name": "平安银行", "sector": "银行", "style": "value"},
            "601318.SH": {"name": "中国平安", "sector": "保险", "style": "value"},
            "600036.SH": {"name": "招商银行", "sector": "银行", "style": "value"},
            
            # 消费股
            "000858.SZ": {"name": "五粮液", "sector": "白酒", "style": "consumer"},
            "600519.SH": {"name": "贵州茅台", "sector": "白酒", "style": "consumer"},
            "000333.SZ": {"name": "美的集团", "sector": "家电", "style": "consumer"},
            
            # 医药股
            "600276.SH": {"name": "恒瑞医药", "sector": "医药", "style": "healthcare"},
            
            # 科技股
            "688111.SH": {"name": "金山办公", "sector": "软件", "style": "tech"},
            "688981.SH": {"name": "中芯国际", "sector": "半导体", "style": "tech"},
        }
    
    def generate_stock_data(self, symbol: str) -> Dict:
        """生成股票数据（简化）"""
        base_price = {
            "300750.SZ": 180, "300059.SZ": 15, "300124.SZ": 65,
            "000001.SZ": 10.5, "601318.SH": 45, "600036.SH": 35,
            "000858.SZ": 150, "600519.SH": 1700, "000333.SZ": 55,
            "600276.SH": 45, "688111.SH": 200, "688981.SH": 50,
        }.get(symbol, 50)
        
        # 生成价格序列
        prices = []
        current = base_price
        for _ in range(60):
            change = random.uniform(-0.02, 0.03)
            current = current * (1 + change)
            prices.append(round(current, 2))
        
        # 生成成交量
        volumes = [random.randint(1000000, 10000000) for _ in range(60)]
        
        return {
            "symbol": symbol,
            "name": self.stock_pool[symbol]["name"],
            "sector": self.stock_pool[symbol]["sector"],
            "style": self.stock_pool[symbol]["style"],
            "prices": prices,
            "volumes": volumes,
            "current_price": prices[-1],
            "price_change": ((prices[-1] - prices[0]) / prices[0]) * 100
        }
    
    def evaluate_strategy_one(self, stock_data: Dict) -> float:
        """评估一号策略（简化版）"""
        prices = stock_data["prices"]
        
        # 简化评分逻辑
        score = 50  # 基础分
        
        # 1. 价格趋势（最近5天 vs 前5天）
        if len(prices) >= 10:
            recent_avg = sum(prices[-5:]) / 5
            prev_avg = sum(prices[-10:-5]) / 5
            if recent_avg > prev_avg:
                score += 20  # 上涨趋势
        
        # 2. 成交量放大
        volumes = stock_data["volumes"]
        if len(volumes) >= 2:
            if volumes[-1] > volumes[-2] * 1.5:
                score += 15  # 成交量放大
        
        # 3. 波动率（适度波动加分）
        if len(prices) >= 20:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = math.sqrt(sum([r**2 for r in returns[-20:]]) / 20) * 100
            if 1 < volatility < 5:
                score += 10  # 适度波动
        
        return min(score, 100)  # 上限100分
    
    def evaluate_strategy_two(self, stock_data: Dict) -> float:
        """评估二号策略（简化版）"""
        prices = stock_data["prices"]
        
        score = 40  # 基础分（二号策略更严格）
        
        # 1. 趋势强度（最近10天涨幅）
        if len(prices) >= 10:
            change_10d = ((prices[-1] - prices[-10]) / prices[-10]) * 100
            if change_10d > 3:
                score += 25  # 明显上涨趋势
        
        # 2. 动量（最近3天连续上涨）
        if len(prices) >= 3:
            if all(prices[i] > prices[i-1] for i in range(-2, 0)):
                score += 20  # 连续上涨
        
        # 3. 换手率（模拟）
        volumes = stock_data["volumes"]
        avg_volume = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1]
        
        # 模拟换手率计算
        if avg_volume > 5000000:
            score += 15  # 高成交量
        
        return min(score, 100)
    
    def combine_strategies(self, stock_data: Dict) -> Dict:
        """组合策略评估"""
        s1_score = self.evaluate_strategy_one(stock_data)
        s2_score = self.evaluate_strategy_two(stock_data)
        
        # 加权综合得分
        combined_score = (
            s1_score * self.strategies["strategy_one"]["weight"] +
            s2_score * self.strategies["strategy_two"]["weight"]
        )
        
        # 策略一致性
        strategies_consistent = abs(s1_score - s2_score) < 30
        
        # 投资风格匹配
        style_score = {
            "growth": 10 if stock_data["style"] == "growth" else 5,
            "value": 10 if stock_data["style"] == "value" else 5,
            "consumer": 8 if stock_data["style"] == "consumer" else 5,
            "healthcare": 8 if stock_data["style"] == "healthcare" else 5,
            "tech": 10 if stock_data["style"] == "tech" else 5,
        }.get(stock_data["style"], 5)
        
        final_score = combined_score + style_score
        
        return {
            "strategy_one_score": round(s1_score, 1),
            "strategy_two_score": round(s2_score, 1),
            "combined_score": round(combined_score, 1),
            "final_score": round(min(final_score, 100), 1),
            "strategies_consistent": strategies_consistent,
            "style_match": stock_data["style"],
            "style_bonus": style_score
        }
    
    def select_stocks(self, top_n: int = 8) -> List[Tuple]:
        """执行多策略选股"""
        logger.info("执行多策略组合选股...")
        
        scored_stocks = []
        
        for symbol in self.stock_pool.keys():
            stock_data = self.generate_stock_data(symbol)
            evaluation = self.combine_strategies(stock_data)
            
            scored_stocks.append((
                symbol,
                evaluation["final_score"],
                stock_data,
                evaluation
            ))
        
        # 按最终得分排序
        scored_stocks.sort(key=lambda x: x[1], reverse=True)
        
        return scored_stocks[:top_n]
    
    def generate_comprehensive_report(self, selected_stocks: List[Tuple]) -> str:
        """生成综合报告"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append(f"多策略组合选股报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        report_lines.append("\n📊 策略配置:")
        for strategy_id, config in self.strategies.items():
            report_lines.append(f"  {config['name']}: 权重{config['weight']*100}% - {config['description']}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("🏆 选股结果:")
        report_lines.append("=" * 80)
        
        for i, (symbol, final_score, stock_data, evaluation) in enumerate(selected_stocks, 1):
            report_lines.append(f"\n{i}. {stock_data['name']} ({symbol})")
            report_lines.append(f"   行业: {stock_data['sector']} | 风格: {stock_data['style']}")
            report_lines.append(f"   当前价格: {stock_data['current_price']} | 近期涨跌: {stock_data['price_change']:+.2f}%")
            
            report_lines.append(f"\n   策略得分:")
            report_lines.append(f"   一号策略: {evaluation['strategy_one_score']}/100")
            report_lines.append(f"   二号策略: {evaluation['strategy_two_score']}/100")
            report_lines.append(f"   综合得分: {evaluation['combined_score']}/100")
            report_lines.append(f"   风格加分: +{evaluation['style_bonus']}")
            report_lines.append(f"   🔥 最终得分: {evaluation['final_score']}/100")
            
            report_lines.append(f"\n   策略分析:")
            if evaluation['strategies_consistent']:
                report_lines.append(f"   ✅ 策略一致性: 高（两个策略评分接近）")
            else:
                report_lines.append(f"   ⚠️ 策略一致性: 中（策略评分有差异）")
            
            # 投资建议
            if final_score >= 80:
                recommendation = "⭐⭐⭐⭐⭐ 强烈推荐 - 多策略共振"
            elif final_score >= 70:
                recommendation = "⭐⭐⭐⭐ 积极关注 - 策略表现良好"
            elif final_score >= 60:
                recommendation = "⭐⭐⭐ 谨慎关注 - 策略部分符合"
            else:
                recommendation = "⭐⭐ 观察等待 - 策略符合度一般"
            
            report_lines.append(f"   💡 投资建议: {recommendation}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("📈 策略组合优势:")
        report_lines.append("1. 风险分散：多个策略降低单一策略失效风险")
        report_lines.append("2. 适应性强：不同市场环境下总有策略有效")
        report_lines.append("3. 信号确认：多策略共振提高信号可靠性")
        report_lines.append("4. 风格匹配：考虑股票风格与策略的契合度")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

def main():
    """主函数"""
    print("🚀 启动多策略组合选股系统...")
    
    # 创建系统
    system = MultiStrategySystem()
    
    # 执行选股
    selected_stocks = system.select_stocks(top_n=8)
    
    # 生成报告
    report = system.generate_comprehensive_report(selected_stocks)
    
    # 输出报告
    print(report)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"multi_strategy_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: {report_filename}")
    
    # 下一步建议
    print("\n🔧 下一步优化方向:")
    print("1. 接入真实行情数据")
    print("2. 增加更多策略（如三号策略）")
    print("3. 实现动态权重调整")
    print("4. 加入风险控制模块")
    print("5. 设置自动化交易信号")

if __name__ == "__main__":
    main()