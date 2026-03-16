#!/usr/bin/env python3
"""
一号策略选股系统
MACD零线以上 + 多技术指标组合选股
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

class TechnicalIndicator:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_macd(prices: List[float], fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标"""
        if len(prices) < slow_period:
            return None
            
        # 计算EMA
        def ema(data, period):
            alpha = 2 / (period + 1)
            ema_value = data[0]
            for price in data[1:]:
                ema_value = price * alpha + ema_value * (1 - alpha)
            return ema_value
        
        # 简化计算（实际应使用完整EMA序列）
        fast_ema = sum(prices[-fast_period:]) / fast_period
        slow_ema = sum(prices[-slow_period:]) / slow_period
        dif = fast_ema - slow_ema
        dea = dif * 0.2  # 简化信号线计算
        macd = (dif - dea) * 2
        
        return {
            "DIF": round(dif, 4),
            "DEA": round(dea, 4),
            "MACD": round(macd, 4),
            "above_zero": dif > 0,  # MACD是否在零线以上
            "histogram_trend": "shortening" if abs(macd) < 0.01 else "expanding",  # 柱状图趋势
            "golden_cross": dif > dea and (dif - dea) > 0.005,  # 金叉
            "divergence": False  # 底背离检测（简化）
        }
    
    @staticmethod
    def calculate_rsi(prices: List[float], period=14):
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None
            
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 单独计算RSI6
        rsi6 = None
        if len(prices) >= 7:
            gains6 = []
            losses6 = []
            for i in range(max(1, len(prices)-6), len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains6.append(change)
                    losses6.append(0)
                else:
                    gains6.append(0)
                    losses6.append(abs(change))
            
            if gains6:
                avg_gain6 = sum(gains6) / len(gains6)
                avg_loss6 = sum(losses6) / len(losses6) if losses6 else 0
                
                if avg_loss6 == 0:
                    rsi6 = 100
                else:
                    rs6 = avg_gain6 / avg_loss6
                    rsi6 = 100 - (100 / (1 + rs6))
        
        return {
            "RSI": round(rsi, 2),
            "RSI6": round(rsi6, 2) if rsi6 else None,
            "golden_cross": False,  # RSI金叉需要前后点比较
            "condition_met": rsi6 <= 68 if rsi6 else True
        }
    
    @staticmethod
    def calculate_bbi(prices: List[float]):
        """计算BBI指标（多空指标）"""
        if len(prices) < 30:
            return None
            
        # BBI = (MA3 + MA6 + MA12 + MA24) / 4
        ma3 = sum(prices[-3:]) / 3
        ma6 = sum(prices[-6:]) / 6
        ma12 = sum(prices[-12:]) / 12
        ma24 = sum(prices[-24:]) / 24
        
        bbi = (ma3 + ma6 + ma12 + ma24) / 4
        current_price = prices[-1]
        
        return {
            "BBI": round(bbi, 4),
            "price": round(current_price, 4),
            "golden_cross": current_price > bbi,
            "angle": random.uniform(10, 30)  # 角度模拟
        }
    
    @staticmethod
    def calculate_dpo(prices: List[float], period=20):
        """计算DPO指标（区间震荡线）"""
        if len(prices) < period * 2:
            return None
            
        # DPO = 收盘价 - 前(period/2+1)日的period日移动平均
        ma_period = period
        shift = period // 2 + 1
        
        dpo_values = []
        for i in range(len(prices) - period - shift + 1):
            ma = sum(prices[i:i+period]) / period
            dpo = prices[i+period+shift-1] - ma
            dpo_values.append(dpo)
        
        current_dpo = dpo_values[-1] if dpo_values else 0
        madpo = sum(dpo_values[-period:]) / len(dpo_values[-period:]) if len(dpo_values) >= period else 0
        
        return {
            "DPO": round(current_dpo, 4),
            "MADPO": round(madpo, 4),
            "golden_cross": current_dpo > madpo,
            "angle": random.uniform(15, 40)  # 角度模拟
        }
    
    @staticmethod
    def calculate_obv(prices: List[float], volumes: List[float], period=30):
        """计算OBV能量潮"""
        if len(prices) < 2:
            return None
            
        obv = 0
        obv_values = []
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volumes[i]
            elif prices[i] < prices[i-1]:
                obv -= volumes[i]
            obv_values.append(obv)
        
        # 计算MAOBV
        maobv = sum(obv_values[-period:]) / len(obv_values[-period:]) if len(obv_values) >= period else obv
        
        # 检查最近5天是否都在MAOBV上方
        recent_obv = obv_values[-5:] if len(obv_values) >= 5 else obv_values
        recent_maobv = maobv
        
        above_ma = all(obv > recent_maobv for obv in recent_obv) if recent_obv else False
        
        return {
            "OBV": obv,
            "MAOBV": maobv,
            "above_ma": above_ma,
            "values": obv_values[-10:]  # 最近10个值
        }
    
    @staticmethod
    def calculate_kdj(highs: List[float], lows: List[float], closes: List[float], period=9):
        """计算KDJ指标"""
        if len(closes) < period:
            return None
            
        # 简化计算
        recent_high = max(highs[-period:])
        recent_low = min(lows[-period:])
        
        if recent_high == recent_low:
            k = 50
            d = 50
        else:
            rsv = ((closes[-1] - recent_low) / (recent_high - recent_low)) * 100
            k = 2/3 * 50 + 1/3 * rsv  # 简化计算
            d = 2/3 * 50 + 1/3 * k
        
        j = 3 * k - 2 * d
        
        # 判断金叉趋势
        golden_cross = k > d and (k - d) > 1
        cross_trend = (k - d) > -2 and (k - d) < 2  # 接近金叉
        
        return {
            "K": round(k, 2),
            "D": round(d, 2),
            "J": round(j, 2),
            "golden_cross": golden_cross,
            "cross_trend": cross_trend
        }
    
    @staticmethod
    def calculate_dmi(highs: List[float], lows: List[float], closes: List[float], period=14):
        """计算DMI指标"""
        if len(closes) < period + 1:
            return None
            
        # 简化计算
        tr_values = []
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
            
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
        
        # 计算DI
        atr = sum(tr_values[-period:]) / period if len(tr_values) >= period else 1
        di_plus = (sum(plus_dm[-period:]) / period / atr) * 100 if plus_dm else 25
        di_minus = (sum(minus_dm[-period:]) / period / atr) * 100 if minus_dm else 25
        
        # 计算ADX（简化）
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 0
        adx = dx * 0.8 + 20 * 0.2  # 简化
        
        return {
            "DI+": round(di_plus, 2),
            "DI-": round(di_minus, 2),
            "ADX": round(adx, 2),
            "DI1_above_ADX": di_plus > adx,
            "ADX_above_20": adx > 20
        }
    
    @staticmethod
    def calculate_boll(prices: List[float], period=20):
        """计算布林带指标"""
        if len(prices) < period:
            return None
            
        middle = sum(prices[-period:]) / period
        
        # 计算标准差
        variance = sum((x - middle) ** 2 for x in prices[-period:]) / period
        std_dev = math.sqrt(variance)
        
        upper = middle + 2 * std_dev
        lower = middle - 2 * std_dev
        
        # 判断趋势
        recent_middle = middle
        prev_middle = sum(prices[-period-1:-1]) / period if len(prices) > period else middle
        
        trend_up = recent_middle > prev_middle
        price_above_middle = prices[-1] > middle
        
        return {
            "upper": round(upper, 4),
            "middle": round(middle, 4),
            "lower": round(lower, 4),
            "price_above_middle": price_above_middle,
            "trend_up": trend_up,
            "bands_up": trend_up  # 三轨整体上行
        }

class StrategyOneAnalyzer:
    """一号策略分析器"""
    
    def __init__(self):
        self.stock_pool = self._initialize_stock_pool()
        self.indicators = TechnicalIndicator()
        
    def _initialize_stock_pool(self) -> Dict:
        """初始化股票池（A股为主）"""
        return {
            # 主板
            "000001.SZ": {"name": "平安银行", "sector": "银行"},
            "000858.SZ": {"name": "五粮液", "sector": "白酒"},
            "000333.SZ": {"name": "美的集团", "sector": "家电"},
            "000651.SZ": {"name": "格力电器", "sector": "家电"},
            
            # 创业板
            "300750.SZ": {"name": "宁德时代", "sector": "新能源"},
            "300059.SZ": {"name": "东方财富", "sector": "金融科技"},
            "300124.SZ": {"name": "汇川技术", "sector": "工业自动化"},
            
            # 科创板
            "688111.SH": {"name": "金山办公", "sector": "软件"},
            "688981.SH": {"name": "中芯国际", "sector": "半导体"},
            "688599.SH": {"name": "天合光能", "sector": "光伏"},
            
            # 上证
            "600519.SH": {"name": "贵州茅台", "sector": "白酒"},
            "601318.SH": {"name": "中国平安", "sector": "保险"},
            "600036.SH": {"name": "招商银行", "sector": "银行"},
            "600276.SH": {"name": "恒瑞医药", "sector": "医药"},
        }
    
    def generate_mock_data(self, symbol: str, days=60) -> Dict:
        """生成模拟历史数据"""
        base_price = {
            "000001.SZ": 10.5,
            "000858.SZ": 150.0,
            "300750.SZ": 180.0,
            "600519.SH": 1700.0,
            "601318.SH": 45.0,
            "000333.SZ": 55.0,
            "000651.SZ": 40.0,
            "300059.SZ": 15.0,
            "300124.SZ": 65.0,
            "688111.SH": 200.0,
            "688981.SH": 50.0,
            "688599.SH": 30.0,
            "600036.SH": 35.0,
            "600276.SH": 45.0,
        }.get(symbol, 50.0)
        
        prices = []
        volumes = []
        highs = []
        lows = []
        
        current = base_price
        for i in range(days):
            # 价格波动
            change = random.uniform(-0.03, 0.03)
            current = current * (1 + change)
            
            # 生成高低价
            high = current * (1 + random.uniform(0, 0.02))
            low = current * (1 - random.uniform(0, 0.02))
            
            # 成交量
            volume = random.randint(1000000, 10000000)
            
            prices.append(round(current, 2))
            highs.append(round(high, 2))
            lows.append(round(low, 2))
            volumes.append(volume)
        
        # 计算换手率（模拟）
        turnover_rate = random.uniform(3.0, 8.0)
        
        # 虚拟成交量（盘中）
        virtual_volume = volumes[-1] * random.uniform(0.8, 2.5)
        avg_15d_volume = sum(volumes[-15:]) / 15 if len(volumes) >= 15 else virtual_volume
        
        return {
            "symbol": symbol,
            "name": self.stock_pool[symbol]["name"],
            "sector": self.stock_pool[symbol]["sector"],
            "prices": prices,
            "volumes": volumes,
            "highs": highs,
            "lows": lows,
            "closes": prices,  # 简化，收盘价=最后价格
            "current_price": prices[-1],
            "turnover_rate": round(turnover_rate, 2),
            "virtual_volume": int(virtual_volume),
            "avg_15d_volume": int(avg_15d_volume),
            "volume_condition": virtual_volume >= avg_15d_volume * 1.0,  # 高于15日均量
            "volume_double": virtual_volume >= volumes[-2] * 2.0 if len(volumes) >= 2 else False
        }
    
    def analyze_strategy_one(self, stock_data: Dict) -> Dict:
        """分析一号策略条件"""
        indicators = {}
        conditions = {}
        
        # 1. MACD分析
        macd = self.indicators.calculate_macd(stock_data["prices"])
        if macd:
            indicators["MACD"] = macd
            
            # MACD零线以上条件
            if macd["above_zero"]:
                # 三个符合一个即可
                macd_conditions = [
                    macd["histogram_trend"] == "shortening",  # 绿柱逐步缩短
                    macd["golden_cross"],  # 金叉
                    macd["divergence"]  # 底背离
                ]
                conditions["MACD_condition"] = any(macd_conditions)
            else:
                conditions["MACD_condition"] = False
        else:
            conditions["MACD_condition"] = False
        
        # 2. RSI分析
        rsi = self.indicators.calculate_rsi(stock_data["prices"])
        if rsi:
            indicators["RSI"] = rsi
            conditions["RSI_condition"] = rsi["condition_met"]  # RSI6不高于68
        else:
            conditions["RSI_condition"] = False
        
        # 3. BBI分析
        bbi = self.indicators.calculate_bbi(stock_data["prices"])
        if bbi:
            indicators["BBI"] = bbi
            conditions["BBI_condition"] = bbi["golden_cross"]  # BBI金叉
        else:
            conditions["BBI_condition"] = False
        
        # 4. DPO分析
        dpo = self.indicators.calculate_dpo(stock_data["prices"])
        if dpo:
            indicators["DPO"] = dpo
            dpo_conditions = [
                dpo["golden_cross"],  # DPO金叉
                dpo["angle"] > 20  # 角度大于20度
            ]
            conditions["DPO_condition"] = all(dpo_conditions)
        else:
            conditions["DPO_condition"] = False
        
        # 5. OBV分析
        obv = self.indicators.calculate_obv(stock_data["prices"], stock_data["volumes"])
        if obv:
            indicators["OBV"] = obv
            conditions["OBV_condition"] = obv["above_ma"]  # 5天在MAOBV上方
        else:
            conditions["OBV_condition"] = False
        
        # 6. KDJ分析
        kdj = self.indicators.calculate_kdj(stock_data["highs"], stock_data["lows"], stock_data["closes"])
        if kdj:
            indicators["KDJ"] = kdj
            kdj_conditions = [
                kdj["golden_cross"],  # 金叉
                kdj["cross_trend"]  # 有金叉趋势
            ]
            conditions["KDJ_condition"] = any(kdj_conditions)
        else:
            conditions["KDJ_condition"] = False
        
        # 7. DMI分析
        dmi = self.indicators.calculate_dmi(stock_data["highs"], stock_data["lows"], stock_data["closes"])
        if dmi:
            indicators["DMI"] = dmi
            dmi_conditions = [
                dmi["DI1_above_ADX"],  # DI1上穿ADX线
                dmi["ADX_above_20"]  # ADX大于20
            ]
            conditions["DMI_condition"] = all(dmi_conditions)
        else:
            conditions["DMI_condition"] = False
        
        # 8. 布林带分析
        boll = self.indicators.calculate_boll(stock_data["prices"])
        if boll:
            indicators["BOLL"] = boll
            boll_conditions = [
                boll["price_above_middle"],  # 价格上穿中轨
                boll["bands_up"]  # 三轨整体上行
            ]
            conditions["BOLL_condition"] = all(boll_conditions)
        else:
            conditions["BOLL_condition"] = False
        
        # 9. 换手率条件
        conditions["turnover_condition"] = stock_data["turnover_rate"] >= 5.0
        
        # 10. 成交量条件
        volume_conditions = [
            stock_data["volume_double"],  # 高于前一日一倍
            stock_data["volume_condition"]  # 高于15日平均数
        ]
        conditions["volume_condition"] = any(volume_conditions)
        
        # 计算总得分
        total_conditions = 10
        met_conditions = sum(1 for cond in conditions.values() if cond)
        
        # 核心条件：MACD必须在零线以上且满足三个条件之一
        core_condition = conditions.get("MACD_condition", False)
        
        if not core_condition:
            score = 0
        else:
            # 其他条件权重
            other_conditions_met = met_conditions - 1  # 减去MACD条件
            score = (other_conditions_met / (total_conditions - 1)) * 100
        
        return {
            "indicators": indicators,
            "conditions": conditions,
            "score": round(score, 2),
            "met_conditions": met_conditions,
            "core_condition_met": core_condition,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def select_stocks(self, top_n: int = 10) -> List[Tuple]:
        """执行选股"""
        logger.info("执行一号策略选股分析...")
        
        selected_stocks = []
        
        for symbol in self.stock_pool.keys():
            # 生成模拟数据
            stock_data = self.generate_mock_data(symbol)
            
            # 分析策略
            analysis = self.analyze_strategy_one(stock_data)
            
            # 只选择核心条件满足的股票
            if analysis["core_condition_met"]:
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
    
    def generate_detailed_report(self, selected_stocks: List[Tuple]) -> str:
        """生成详细分析报告"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append(f"一号策略选股报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("策略条件：MACD零线以上 + 多技术指标组合")
        report_lines.append("=" * 80)
        
        if not selected_stocks:
            report_lines.append("\n⚠️ 未找到符合核心条件的股票")
            report_lines.append("核心条件：MACD必须在零线以上且满足三个条件之一")
            report_lines.append("  1. 绿柱逐步缩短")
            report_lines.append("  2. 有金叉趋势")
            report_lines.append("  3. 金叉")
            report_lines.append("  4. 底背离（最佳）")
        else:
            report_lines.append(f"\n✅ 找到 {len(selected_stocks)} 只符合核心条件的股票")
            
            for i, (symbol, score, stock_data, analysis) in enumerate(selected_stocks, 1):
                report_lines.append(f"\n{'='*60}")
                report_lines.append(f"{i}. {stock_data['name']} ({symbol})")
                report_lines.append(f"{'='*60}")
                
                # 基本信息
                report_lines.append(f"📊 基本信息:")
                report_lines.append(f"   行业: {stock_data['sector']}")
                report_lines.append(f"   当前价格: {stock_data['current_price']}")
                report_lines.append(f"   换手率: {stock_data['turnover_rate']}%")
                report_lines.append(f"   虚拟成交量: {stock_data['virtual_volume']:,}")
                report_lines.append(f"   15日均量: {stock_data['avg_15d_volume']:,}")
                report_lines.append(f"   成交量条件: {'满足' if any([stock_data['volume_double'], stock_data['volume_condition']]) else '不满足'}")
                
                # 策略得分
                report_lines.append(f"\n🎯 策略分析:")
                report_lines.append(f"   综合得分: {score}/100")
                report_lines.append(f"   满足条件数: {analysis['met_conditions']}/10")
                
                # 详细条件
                report_lines.append(f"\n📈 技术指标条件:")
                conditions = analysis['conditions']
                
                condition_status = {
                    "MACD_condition": f"MACD零线以上条件: {'✓' if conditions['MACD_condition'] else '✗'}",
                    "RSI_condition": f"RSI6≤68: {'✓' if conditions['RSI_condition'] else '✗'}",
                    "BBI_condition": f"BBI金叉: {'✓' if conditions['BBI_condition'] else '✗'}",
                    "DPO_condition": f"DPO金叉且角度>20°: {'✓' if conditions['DPO_condition'] else '✗'}",
                    "OBV_condition": f"OBV5天在MA上方: {'✓' if conditions['OBV_condition'] else '✗'}",
                    "KDJ_condition": f"KDJ金叉/趋势: {'✓' if conditions['KDJ_condition'] else '✗'}",
                    "DMI_condition": f"DMI:DI1>ADX>20: {'✓' if conditions['DMI_condition'] else '✗'}",
                    "BOLL_condition": f"布林:上穿中轨+三轨上行: {'✓' if conditions['BOLL_condition'] else '✗'}",
                    "turnover_condition": f"换手率≥5%: {'✓' if conditions['turnover_condition'] else '✗'}",
                    "volume_condition": f"成交量条件: {'✓' if conditions['volume_condition'] else '✗'}"
                }
                
                for status in condition_status.values():
                    report_lines.append(f"   {status}")
                
                # 关键指标值
                report_lines.append(f"\n🔢 关键指标值:")
                indicators = analysis['indicators']
                
                if 'MACD' in indicators:
                    macd = indicators['MACD']
                    report_lines.append(f"   MACD DIF: {macd['DIF']}, DEA: {macd['DEA']}, 柱状图: {macd['histogram_trend']}")
                
                if 'RSI' in indicators:
                    rsi = indicators['RSI']
                    report_lines.append(f"   RSI: {rsi['RSI']}, RSI6: {rsi['RSI6']}")
                
                # 投资建议
                report_lines.append(f"\n💡 投资建议:")
                if score >= 80:
                    report_lines.append(f"   ⭐⭐⭐⭐⭐ 强烈关注 - 技术面全面向好")
                elif score >= 60:
                    report_lines.append(f"   ⭐⭐⭐⭐ 积极关注 - 多个技术指标共振")
                elif score >= 40:
                    report_lines.append(f"   ⭐⭐⭐ 谨慎关注 - 部分指标转好")
                else:
                    report_lines.append(f"   ⭐⭐ 观察等待 - 仅满足核心条件")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("策略说明:")
        report_lines.append("1. 核心：MACD零线以上，且满足绿柱缩短/金叉/底背离之一")
        report_lines.append("2. 辅助：RSI、BBI、DPO、OBV、KDJ、DMI、布林带等多指标验证")
        report_lines.append("3. 量能：换手率≥5%，成交量放大（前日1倍或高于15日均量）")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def track_and_review(self, selected_stocks: List[Tuple], days: int = 5):
        """跟踪和复盘"""
        logger.info(f"开始跟踪{len(selected_stocks)}只股票，回溯{days}天...")
        
        review_report = []
        review_report.append("=" * 80)
        review_report.append(f"股票跟踪复盘报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        review_report.append(f"跟踪周期: {days}天")
        review_report.append("=" * 80)
        
        for symbol, score, stock_data, analysis in selected_stocks:
            prices = stock_data['prices']
            if len(prices) >= days:
                recent_prices = prices[-days:]
                start_price = recent_prices[0]
                end_price = recent_prices[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                
                # 计算波动率
                returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] for i in range(1, len(recent_prices))]
                volatility = math.sqrt(sum([r**2 for r in returns]) / len(returns)) * 100 if returns else 0
                
                review_report.append(f"\n📈 {stock_data['name']} ({symbol}):")
                review_report.append(f"   期初价格: {start_price:.2f}")
                review_report.append(f"   期末价格: {end_price:.2f}")
                review_report.append(f"   期间涨跌: {change_pct:+.2f}%")
                review_report.append(f"   波动率: {volatility:.2f}%")
                review_report.append(f"   选股得分: {score}/100")
                
                # 表现评价
                if change_pct > 5:
                    review_report.append(f"   📊 表现: 强势上涨")
                elif change_pct > 0:
                    review_report.append(f"   📊 表现: 小幅上涨")
                elif change_pct > -5:
                    review_report.append(f"   📊 表现: 小幅回调")
                else:
                    review_report.append(f"   📊 表现: 明显下跌")
        
        review_report.append("\n" + "=" * 80)
        review_report.append("复盘总结:")
        review_report.append("1. 关注选股得分与后续表现的相关性")
        review_report.append("2. 分析技术指标的有效性")
        review_report.append("3. 优化策略参数和权重")
        review_report.append("=" * 80)
        
        return "\n".join(review_report)

def main():
    """主函数"""
    print("🚀 启动一号策略选股系统...")
    
    # 创建分析器
    analyzer = StrategyOneAnalyzer()
    
    # 执行选股
    selected_stocks = analyzer.select_stocks(top_n=8)
    
    # 生成详细报告
    report = analyzer.generate_detailed_report(selected_stocks)
    
    # 输出报告
    print(report)
    
    # 跟踪复盘
    if selected_stocks:
        review = analyzer.track_and_review(selected_stocks, days=5)
        print("\n" + review)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"strategy_one_report_{timestamp}.txt"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
        if selected_stocks:
            f.write("\n\n" + review)
    
    print(f"\n📄 报告已保存到: {report_filename}")
    
    # 策略优化建议
    print("\n🔧 策略优化建议:")
    print("1. 接入真实行情数据（Tushare、AKShare等）")
    print("2. 增加更多技术指标验证")
    print("3. 设置动态参数调整机制")
    print("4. 加入基本面筛选条件")
    print("5. 实现自动化实时监控")

if __name__ == "__main__":
    main()