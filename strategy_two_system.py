#!/usr/bin/env python3
"""
二号策略选股系统
DMI + RSI + 换手率组合选股
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicatorV2:
    """技术指标计算器（二号策略专用）"""
    
    @staticmethod
    def calculate_dmi_detailed(highs: List[float], lows: List[float], closes: List[float], period=14):
        """详细计算DMI指标（包含DI1、DI2、ADX、ADXR）"""
        if len(closes) < period + 1:
            return None
        
        # 计算TR、+DM、-DM
        tr_values = []
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(closes)):
            # 真实波幅TR
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
            
            # 方向运动
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
                minus_dm.append(0)
            elif down_move > up_move and down_move > 0:
                plus_dm.append(0)
                minus_dm.append(down_move)
            else:
                plus_dm.append(0)
                minus_dm.append(0)
        
        # 计算平滑后的TR、+DM、-DM
        def smooth(data):
            if len(data) < period:
                return None
            # 前period个值的和
            first_sum = sum(data[:period])
            smoothed = [first_sum]
            
            for i in range(period, len(data)):
                smoothed.append(smoothed[-1] - smoothed[-1]/period + data[i])
            
            return smoothed
        
        tr_smoothed = smooth(tr_values)
        plus_dm_smoothed = smooth(plus_dm)
        minus_dm_smoothed = smooth(minus_dm)
        
        if not (tr_smoothed and plus_dm_smoothed and minus_dm_smoothed):
            return None
        
        # 计算+DI、-DI
        di_plus = []
        di_minus = []
        
        for i in range(len(tr_smoothed)):
            if tr_smoothed[i] == 0:
                di_plus.append(0)
                di_minus.append(0)
            else:
                di_plus.append((plus_dm_smoothed[i] / tr_smoothed[i]) * 100)
                di_minus.append((minus_dm_smoothed[i] / tr_smoothed[i]) * 100)
        
        # 计算DX
        dx_values = []
        for i in range(len(di_plus)):
            if di_plus[i] + di_minus[i] == 0:
                dx_values.append(0)
            else:
                dx_values.append(abs(di_plus[i] - di_minus[i]) / (di_plus[i] + di_minus[i]) * 100)
        
        # 计算ADX（DX的period日平均）
        adx_values = []
        for i in range(period-1, len(dx_values)):
            adx = sum(dx_values[i-period+1:i+1]) / period
            adx_values.append(adx)
        
        # 计算ADXR（ADX的period日平均）
        adxr_values = []
        if len(adx_values) >= period:
            for i in range(period-1, len(adx_values)):
                adxr = (adx_values[i] + adx_values[i-period+1]) / 2
                adxr_values.append(adxr)
        
        # 获取最新值
        current_di_plus = di_plus[-1] if di_plus else 0
        current_di_minus = di_minus[-1] if di_minus else 0
        current_adx = adx_values[-1] if adx_values else 0
        current_adxr = adxr_values[-1] if adxr_values else 0
        
        # 获取前一天的值用于判断金叉
        prev_di_plus = di_plus[-2] if len(di_plus) >= 2 else current_di_plus
        prev_di_minus = di_minus[-2] if len(di_minus) >= 2 else current_di_minus
        prev_adx = adx_values[-2] if len(adx_values) >= 2 else current_adx
        prev_adxr = adxr_values[-2] if len(adxr_values) >= 2 else current_adxr
        
        # 判断条件
        di1_cross_di2 = prev_di_plus <= prev_di_minus and current_di_plus > current_di_minus
        adx_cross_adxr = prev_adx <= prev_adxr and current_adx > current_adxr
        
        return {
            "DI+": round(current_di_plus, 2),
            "DI-": round(current_di_minus, 2),
            "ADX": round(current_adx, 2),
            "ADXR": round(current_adxr, 2),
            "DI1_cross_DI2": di1_cross_di2,
            "ADX_cross_ADXR": adx_cross_adxr,
            "trend_strength": "强" if current_adx > 25 else "中等" if current_adx > 20 else "弱"
        }
    
    @staticmethod
    def calculate_rsi_detailed(prices: List[float], short_period=6, long_period=12):
        """详细计算RSI指标（支持金叉判断）"""
        if len(prices) < long_period + 1:
            return None
        
        def calculate_single_rsi(data, period):
            gains = []
            losses = []
            
            for i in range(1, len(data)):
                change = data[i] - data[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if len(gains) < period:
                return None
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period if losses else 0
            
            if avg_loss == 0:
                return 100
            else:
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))
        
        # 计算RSI6和RSI12
        rsi6 = calculate_single_rsi(prices, short_period)
        rsi12 = calculate_single_rsi(prices, long_period)
        
        if rsi6 is None or rsi12 is None:
            return None
        
        # 获取前一天的RSI值用于判断金叉
        if len(prices) >= short_period + 2:
            prev_prices = prices[:-1]
            prev_rsi6 = calculate_single_rsi(prev_prices, short_period)
            prev_rsi12 = calculate_single_rsi(prev_prices, long_period)
        else:
            prev_rsi6 = rsi6
            prev_rsi12 = rsi12
        
        # 判断RSI金叉（RSI6上穿RSI12）
        rsi_golden_cross = prev_rsi6 <= prev_rsi12 and rsi6 > rsi12
        
        return {
            "RSI6": round(rsi6, 2),
            "RSI12": round(rsi12, 2),
            "golden_cross": rsi_golden_cross,
            "bullish": rsi6 > 50 and rsi12 > 50,
            "oversold": rsi6 < 30 or rsi12 < 30,
            "overbought": rsi6 > 70 or rsi12 > 70
        }
    
    @staticmethod
    def calculate_turnover_rate(volumes: List[int], market_cap: float, days=20):
        """计算换手率（简化版）"""
        if len(volumes) < days or market_cap <= 0:
            return None
        
        # 平均成交量
        avg_volume = sum(volumes[-days:]) / days
        
        # 简化计算：换手率 = 成交量 / 流通股本
        # 这里使用模拟的流通股本
        circulating_shares = market_cap / 10  # 假设流通股占总股本的10%
        
        if circulating_shares > 0:
            turnover = (avg_volume / circulating_shares) * 100
            return round(turnover, 2)
        
        return None
    
    @staticmethod
    def generate_mock_stock_data(symbol: str, days=60) -> Dict:
        """生成模拟股票数据"""
        # 基础价格（根据股票类型）
        base_prices = {
            # 科技股
            "300750.SZ": 180, "300059.SZ": 15, "300124.SZ": 65,
            "688111.SH": 200, "688981.SH": 50, "688599.SH": 30,
            # 消费股
            "000858.SZ": 150, "600519.SH": 1700, "000333.SZ": 55,
            # 金融股
            "000001.SZ": 10.5, "601318.SH": 45, "600036.SH": 35,
            # 医药股
            "600276.SH": 45, "000538.SZ": 90,
            # 新能源
            "002594.SZ": 250, "002460.SZ": 40,
        }
        
        base_price = base_prices.get(symbol, 50.0)
        
        # 生成价格序列
        prices = []
        current = base_price
        
        for i in range(days):
            # 趋势性波动
            trend = random.uniform(-0.005, 0.01)  # 轻微趋势
            noise = random.uniform(-0.02, 0.02)   # 随机噪声
            change = trend + noise
            
            current = current * (1 + change)
            prices.append(round(current, 2))
        
        # 生成成交量（与价格波动相关）
        volumes = []
        base_volume = random.randint(500000, 5000000)
        
        for i in range(days):
            # 成交量与价格变化相关
            if i == 0:
                change_factor = 1.0
            else:
                price_change = abs((prices[i] - prices[i-1]) / prices[i-1])
                change_factor = 1 + price_change * 5
            
            volume = int(base_volume * change_factor * random.uniform(0.8, 1.2))
            volumes.append(volume)
        
        # 生成高低价
        highs = []
        lows = []
        
        for price in prices:
            high = price * (1 + random.uniform(0, 0.03))
            low = price * (1 - random.uniform(0, 0.03))
            highs.append(round(high, 2))
            lows.append(round(low, 2))
        
        # 模拟市值（用于换手率计算）
        market_cap = base_price * random.randint(1000000, 10000000)
        
        return {
            "symbol": symbol,
            "prices": prices,
            "volumes": volumes,
            "highs": highs,
            "lows": lows,
            "closes": prices,
            "current_price": prices[-1],
            "market_cap": market_cap,
            "data_days": days
        }

class StrategyTwoAnalyzer:
    """二号策略分析器"""
    
    def __init__(self):
        self.stock_pool = self._initialize_stock_pool()
        self.indicators = TechnicalIndicatorV2()
        
    def _initialize_stock_pool(self) -> Dict:
        """初始化股票池（侧重趋势性强的股票）"""
        return {
            # 科技成长股（趋势性强）
            "300750.SZ": {"name": "宁德时代", "sector": "新能源", "trend": "growth"},
            "300059.SZ": {"name": "东方财富", "sector": "金融科技", "trend": "growth"},
            "300124.SZ": {"name": "汇川技术", "sector": "工业自动化", "trend": "growth"},
            
            # 科创板（高波动）
            "688111.SH": {"name": "金山办公", "sector": "软件", "trend": "high_volatility"},
            "688981.SH": {"name": "中芯国际", "sector": "半导体", "trend": "high_volatility"},
            "688599.SH": {"name": "天合光能", "sector": "光伏", "trend": "high_volatility"},
            
            # 消费龙头（趋势稳定）
            "000858.SZ": {"name": "五粮液", "sector": "白酒", "trend": "stable"},
            "600519.SH": {"name": "贵州茅台", "sector": "白酒", "trend": "stable"},
            "000333.SZ": {"name": "美的集团", "sector": "家电", "trend": "stable"},
            
            # 医药（防御性）
            "600276.SH": {"name": "恒瑞医药", "sector": "医药", "trend": "defensive"},
            "000538.SZ": {"name": "云南白药", "sector": "医药", "trend": "defensive"},
            
            # 新能源（高成长）
            "002594.SZ": {"name": "比亚迪", "sector": "新能源汽车", "trend": "high_growth"},
            "002460.SZ": {"name": "赣锋锂业", "sector": "锂电池", "trend": "high_growth"},
            
            # 金融（价值）
            "000001.SZ": {"name": "平安银行", "sector": "银行", "trend": "value"},
            "601318.SH": {"name": "中国平安", "sector": "保险", "trend": "value"},
            "600036.SH": {"name": "招商银行", "sector": "银行", "trend": "value"},
        }
    
    def analyze_strategy_two(self, stock_data: Dict) -> Dict:
        """分析二号策略条件"""
        indicators = {}
        conditions = {}
        
        # 1. DMI分析（核心）
        dmi = self.indicators.calculate_dmi_detailed(
            stock_data["highs"], 
            stock_data["lows"], 
            stock_data["closes"]
        )
        
        if dmi:
            indicators["DMI"] = dmi
            
            # 条件1：DI1上穿DI2
            conditions["DI1_cross_DI2"] = dmi["DI1_cross_DI2"]
            
            # 条件2：ADX上穿ADXR线
            conditions["ADX_cross_ADXR"] = dmi["ADX_cross_ADXR"]
            
            # DMI强度
            conditions["DMI_strong"] = dmi["trend_strength"] in ["强", "中等"]
        else:
            conditions["DI1_cross_DI2"] = False
            conditions["ADX_cross_ADXR"] = False
            conditions["DMI_strong"] = False
        
        # 2. RSI分析
        rsi = self.indicators.calculate_rsi_detailed(stock_data["prices"])
        
        if rsi:
            indicators["RSI"] = rsi
            
            # 条件3：RSI金叉（RSI6上穿RSI12）
            conditions["RSI_golden_cross"] = rsi["golden_cross"]
            
            # RSI状态
            conditions["RSI_bullish"] = rsi["bullish"]
            conditions["RSI_not_overbought"] = not rsi["overbought"]
        else:
            conditions["RSI_golden_cross"] = False
            conditions["RSI_bullish"] = False
            conditions["RSI_not_overbought"] = False
        
        # 3. 换手率分析
        turnover = self.indicators.calculate_turnover_rate(
            stock_data["volumes"],
            stock_data["market_cap"]
        )
        
        if turnover is not None:
            indicators["Turnover"] = turnover
            
            # 条件4：换手率大于5%
            conditions["Turnover_gt_5"] = turnover > 5.0
            
            # 换手率等级
            if turnover > 10:
                turnover_level = "非常高"
            elif turnover > 7:
                turnover_level = "高"
            elif turnover > 5:
                turnover_level = "适中"
            elif turnover > 3:
                turnover_level = "较低"
            else:
                turnover_level = "低"
            
            indicators["Turnover_level"] = turnover_level
        else:
            conditions["Turnover_gt_5"] = False
            indicators["Turnover"] = None
            indicators["Turnover_level"] = "未知"
        
        # 计算综合得分
        total_conditions = 4
        met_conditions = sum(1 for cond in conditions.values() if cond)
        
        # 核心条件：DMI的两个条件必须同时满足
        dmi_core_conditions = conditions["DI1_cross_DI2"] and conditions["ADX_cross_ADXR"]
        
        if not dmi_core_conditions:
            score = 0
        else:
            # 其他条件权重
            other_conditions = ["RSI_golden_cross", "Turnover_gt_5"]
            other_met = sum(1 for cond in other_conditions if conditions.get(cond, False))
            score = (other_met / len(other_conditions)) * 100
        
        # 趋势判断
        trend_strength = "弱"
        if dmi and dmi["trend_strength"] == "强":
            trend_strength = "强"
        elif dmi and dmi["trend_strength"] == "中等":
            trend_strength = "中等"
        
        return {
            "indicators": indicators,
            "conditions": conditions,
            "score": round(score, 2),
            "met_conditions": met_conditions,
            "core_conditions_met": dmi_core_conditions,
            "trend_strength": trend_strength,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def select_stocks(self, top_n: int = 10) -> List[Tuple]:
        """执行选股"""
        logger.info("执行二号策略选股分析...")
        
        selected_stocks = []
        
        for symbol, info in self.stock_pool.items():
            # 生成模拟数据
            stock_data = self.indicators.generate_mock_stock_data(symbol)
            stock_data.update(info)  # 添加基本信息
            
            # 分析策略
            analysis = self.analyze_strategy_two(stock_data)
            
            # 只选择核心条件满足的股票
            if analysis["core_conditions_met"]:
                selected_stocks.append((
                    symbol,
                    analysis["score"],
                    stock_data,
                    analysis
                ))
        
        # 按得分排序
        selected_stocks.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前N名
        return selected_stocks[:top_n]
    
    def generate_strategy_report(self, selected_stocks: List[Tuple]) -> str:
        """生成策略报告"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append(f"二号策略选股报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("策略条件：DMI(DI1上穿DI2 + ADX上穿ADXR) + RSI金叉 + 换手率>5%")
        report_lines.append("=" * 80)
        
        if not selected_stocks:
            report_lines.append("\n⚠️ 未找到符合核心条件的股票")
            report_lines.append("核心条件：DMI指标必须同时满足")
            report_lines.append("  1. DI1上穿DI2")
            report_lines.append("  2. ADX上穿ADXR线")
        else:
            report_lines.append(f"\n✅ 找到 {len(selected_stocks)} 只符合核心条件的股票")
            
            for i, (symbol, score, stock_data, analysis) in enumerate(selected_stocks, 1):
                report_lines.append(f"\n{'='*60}")
                report_lines.append(f"{i}. {stock_data['name']} ({symbol})")
                report_lines.append(f"{'='*60}")
                
                # 基本信息
                report_lines.append(f"📊 基本信息:")
                report_lines.append(f"   行业: {stock_data['sector']}")
                report_lines.append(f"   趋势类型: {stock_data['trend']}")
                report_lines.append(f"   当前价格: {stock_data['current_price']}")
                
                # 策略得分
                report_lines.append(f"\n🎯 策略分析:")
                report_lines.append(f"   综合得分: {score}/100")
                report_lines.append(f"   满足条件数: {analysis['met_conditions']}/4")
                report_lines.append(f"   趋势强度: {analysis['trend_strength']}")
                
                # 详细条件
                report_lines.append(f"\n📈 技术指标条件:")
                conditions = analysis['conditions']
                indicators = analysis['indicators']
                
                condition_status = [
                    f"DI1上穿DI2: {'✓' if conditions['DI1_cross_DI2'] else '✗'} "
                    f"(DI+: {indicators['DMI']['DI+'] if 'DMI' in indicators else 'N/A'}, "
                    f"DI-: {indicators['DMI']['DI-'] if 'DMI' in indicators else 'N/A'})",
                    
                    f"ADX上穿ADXR: {'✓' if conditions['ADX_cross_ADXR'] else '✗'} "
                    f"(ADX: {indicators['DMI']['ADX'] if 'DMI' in indicators else 'N/A'}, "
                    f"ADXR: {indicators['DMI']['ADXR'] if 'DMI' in indicators else 'N/A'})",
                    
                    f"RSI金叉: {'✓' if conditions['RSI_golden_cross'] else '✗'} "
                    f"(RSI6: {indicators['RSI']['RSI6'] if 'RSI' in indicators else 'N/A'}, "
                    f"RSI12: {indicators['RSI']['RSI12'] if 'RSI' in indicators else 'N/A'})",
                    
                    f"换手率>5%: {'✓' if conditions['Turnover_gt_5'] else '✗'} "
                    f"({indicators['Turnover'] if indicators['Turnover'] else 'N/A'}%)"
                ]
                
                for status in condition_status:
                    report_lines.append(f"   {status}")
                
                # 技术分析解读
                report_lines.append(f"\n🔍 技术分析解读:")
                
                if 'DMI' in indicators:
                    dmi = indicators['DMI']
                    report_lines.append(f"   DMI趋势: {dmi['trend_strength']}")
                    
                    if dmi['DI+'] > dmi['DI-']:
                        report_lines.append(f"   多头占优: DI+({dmi['DI+']}) > DI-({dmi['DI-']})")
                    else:
                        report_lines.append(f"   空头占优: DI-({dmi['DI-']}) > DI+({dmi['DI+']})")
                
                if 'RSI' in indicators:
                    rsi = indicators['RSI']
                    if rsi['bullish']:
                        report_lines.append(f"   RSI处于多头区域(>50)")
                    elif rsi['oversold']:
                        report_lines.append(f"   RSI处于超卖区域(<30)")
                    elif rsi['overbought']:
                        report_lines.append(f"   RSI处于超买区域(>70)")
                
                if indicators.get('Turnover'):
                    report_lines.append(f"   换手率: {indicators['Turnover']}% ({indicators['Turnover_level']})")
                
                # 投资建议
                report_lines.append(f"\n💡 投资建议:")
                
                if score == 100:
                    report_lines.append(f"   ⭐⭐⭐⭐⭐ 强烈买入 - 所有条件完美符合")
                    report_lines.append(f"   策略信号：趋势启动初期，量价配合良好")
                elif score >= 50:
                    report_lines.append(f"   ⭐⭐⭐⭐ 积极关注 - 主要条件符合")
                    report_lines.append(f"   策略信号：趋势确认，等待进一步确认")
                else:
                    report_lines.append(f"   ⭐⭐⭐ 谨慎观察 - 仅满足核心条件")
                    report_lines.append(f"   策略信号：趋势初现，需观察持续性")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("策略逻辑说明:")
        report_lines.append("1. DMI(DI1上穿DI2)：表示多头力量开始占优")
        report_lines.append("2. DMI(ADX上穿ADXR)：表示趋势强度开始增强")
        report_lines.append("3. RSI金叉：短期动量转强")
        report_lines.append("4. 换手率>5%：市场关注度高，流动性好")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def perform_backtest(self, stock_data: Dict, analysis: Dict, lookback_days: int = 20) -> Dict:
        """执行回测分析"""
        prices = stock_data["prices"]
        
        if len(prices) < lookback_days:
            return {"error": "数据不足"}
        
        # 模拟信号点（假设在分析时点买入）
        signal_index = len(prices) - 1
        signal_price = prices[signal_index]
        
        # 计算后续表现（如果有足够数据）
        future_days = min(10, len(prices) - signal_index - 1)
        
        if future_days > 0:
            future_prices = prices[signal_index:signal_index+future_days+1]
            returns = [(future_prices[i] - future_prices[0]) / future_prices[0] * 100 
                      for i in range(1, len(future_prices))]
        else:
            future_prices = []
            returns = []
        
        # 计算历史波动率
        historical_returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            historical_returns.append(ret)
        
        volatility = math.sqrt(sum([r**2 for r in historical_returns]) / len(historical_returns)) * 100 if historical_returns else 0
        
        return {
            "signal_price": signal_price,
            "signal_time": analysis["analysis_time"],
            "future_returns": [round(r, 2) for r in returns],
            "max_return": round(max(returns) if returns else 0, 2),
            "min_return": round(min(returns) if returns else 0, 2),
            "final_return": round(returns[-1] if returns else 0, 2),
            "volatility": round(volatility, 2),
            "data_points": len(prices),
            "lookback_days": lookback_days,
            "future_days_analyzed": future_days
        }

def main():
    """主函数"""
    print("🚀 启动二号策略选股系统...")
    
    # 创建分析器
    analyzer = StrategyTwoAnalyzer()
    
    # 执行选股
    selected_stocks = analyzer.select_stocks(top_n=8)
    
    # 生成详细报告
    report = analyzer.generate_strategy_report(selected_stocks)
    
    # 输出报告
    print(report)
    
    # 执行回测分析
    if selected_stocks:
        print("\n" + "=" * 80)
        print("回测分析结果:")
        print("=" * 80)
        
        for symbol, score, stock_data, analysis in selected_stocks[:3]:  # 只分析前3只
            backtest = analyzer.perform_backtest(stock_data, analysis)
            
            print(f"\n📊 {stock_data['name']} ({symbol}) - 得分: {score}/100")
            print(f"   信号价格: {backtest['signal_price']}")
            print(f"   信号时间: {backtest['signal_time']}")
            print(f"   历史波动率: {backtest['volatility']}%")
            
            if backtest['future_returns']:
                print(f"   未来{len(backtest['future_returns'])}天收益:")
                for day, ret in enumerate(backtest['future_returns'], 1):
                    print(f"     第{day}天: {ret:+.2f}%")
                print(f"   最终收益: {backtest['final_return']:+.2f}%")
            else:
                print(f"   未来收益: 数据不足")
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"strategy_two_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: {report_filename}")
    
    # 策略对比分析
    print("\n🔍 策略对比分析:")
    print("一号策略 vs 二号策略:")
    print("  一号策略: 多指标共振，筛选严格，适合趋势确认")
    print("  二号策略: DMI核心，侧重趋势启动，适合早期介入")
    print("  建议: 根据市场环境选择策略，或两者结合使用")

if __name__ == "__main__":
    main()