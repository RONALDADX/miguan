#!/usr/bin/env python3
"""
A股实时监控系统
功能：实时数据 + 自动监控 + 风险控制
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import schedule
import threading
from dataclasses import dataclass
from enum import Enum
import sqlite3
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_PATH = "stock_monitor.db"

class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"

class TradeSignal(Enum):
    """交易信号"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"

@dataclass
class StockData:
    """股票数据结构"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    amount: float
    high: float
    low: float
    open: float
    pre_close: float
    timestamp: datetime
    pe: float = 0.0
    pb: float = 0.0
    market_cap: float = 0.0
    circulating_cap: float = 0.0

@dataclass
class StrategyResult:
    """策略结果"""
    strategy_name: str
    score: float
    conditions_met: int
    total_conditions: int
    signals: List[str]
    recommendation: str
    confidence: float

@dataclass
class RiskAssessment:
    """风险评估"""
    risk_level: RiskLevel
    max_position: float  # 最大仓位比例
    stop_loss: float  # 止损比例
    take_profit: float  # 止盈比例
    risk_reward_ratio: float  # 风险收益比
    volatility: float  # 波动率
    drawdown: float  # 最大回撤

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            price REAL,
            change REAL,
            change_percent REAL,
            volume INTEGER,
            amount REAL,
            high REAL,
            low REAL,
            open REAL,
            pre_close REAL,
            pe REAL,
            pb REAL,
            market_cap REAL,
            circulating_cap REAL,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
        ''')
        
        # 创建策略结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            score REAL,
            conditions_met INTEGER,
            total_conditions INTEGER,
            signals TEXT,
            recommendation TEXT,
            confidence REAL,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建交易信号表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            signal TEXT NOT NULL,
            price REAL,
            reason TEXT,
            risk_level TEXT,
            position_size REAL,
            stop_loss REAL,
            take_profit REAL,
            timestamp DATETIME,
            executed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建监控配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitor_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            strategy_enabled BOOLEAN DEFAULT 1,
            alert_enabled BOOLEAN DEFAULT 1,
            check_interval INTEGER DEFAULT 300,
            max_position REAL DEFAULT 0.1,
            stop_loss REAL DEFAULT 0.08,
            take_profit REAL DEFAULT 0.2,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建预警记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT,
            level TEXT,
            data TEXT,
            timestamp DATETIME,
            acknowledged BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    
    def save_stock_data(self, stock_data: StockData):
        """保存股票数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO stock_data 
        (symbol, name, price, change, change_percent, volume, amount, 
         high, low, open, pre_close, pe, pb, market_cap, circulating_cap, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stock_data.symbol, stock_data.name, stock_data.price, stock_data.change,
            stock_data.change_percent, stock_data.volume, stock_data.amount,
            stock_data.high, stock_data.low, stock_data.open, stock_data.pre_close,
            stock_data.pe, stock_data.pb, stock_data.market_cap, stock_data.circulating_cap,
            stock_data.timestamp
        ))
        
        conn.commit()
        conn.close()
    
    def save_strategy_result(self, symbol: str, result: StrategyResult):
        """保存策略结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO strategy_results 
        (symbol, strategy_name, score, conditions_met, total_conditions, 
         signals, recommendation, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, result.strategy_name, result.score, result.conditions_met,
            result.total_conditions, json.dumps(result.signals), result.recommendation,
            result.confidence, datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def save_trade_signal(self, symbol: str, signal: TradeSignal, price: float, 
                         reason: str, risk_assessment: RiskAssessment):
        """保存交易信号"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO trade_signals 
        (symbol, signal, price, reason, risk_level, position_size, 
         stop_loss, take_profit, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, signal.value, price, reason, risk_assessment.risk_level.value,
            risk_assessment.max_position, risk_assessment.stop_loss,
            risk_assessment.take_profit, datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def save_alert(self, symbol: str, alert_type: str, message: str, 
                  level: str = "info", data: Dict = None):
        """保存预警记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO alerts 
        (symbol, alert_type, message, level, data, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol, alert_type, message, level, 
            json.dumps(data) if data else None, datetime.now()
        ))
        
        conn.commit()
        conn.close()

class RealTimeDataFetcher:
    """实时数据获取器"""
    
    def __init__(self):
        self.session = None
        self.base_urls = {
            "akshare": "https://push2.eastmoney.com/api",
            "sina": "https://hq.sinajs.cn",
            "tencent": "https://qt.gtimg.cn"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_stock_data(self, symbol: str) -> Optional[StockData]:
        """获取股票实时数据"""
        try:
            # 使用新浪财经API（免费，稳定）
            url = f"{self.base_urls['sina']}/list={self._format_symbol(symbol)}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    return self._parse_sina_data(symbol, text)
        
        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {e}")
        
        return None
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码"""
        if symbol.endswith('.SH'):
            return f"sh{symbol[:-3]}"
        elif symbol.endswith('.SZ'):
            return f"sz{symbol[:-3]}"
        return symbol
    
    def _parse_sina_data(self, symbol: str, text: str) -> Optional[StockData]:
        """解析新浪财经数据"""
        try:
            # 新浪数据格式：var hq_str_sh600519="贵州茅台,1799.01,1800.00,1798.50,...";
            data_str = text.split('="')[1].split('"')[0]
            data = data_str.split(',')
            
            if len(data) < 30:
                return None
            
            name = data[0]
            open_price = float(data[1])
            pre_close = float(data[2])
            price = float(data[3])
            high = float(data[4])
            low = float(data[5])
            volume = int(float(data[8]))
            amount = float(data[9])
            
            change = price - pre_close
            change_percent = (change / pre_close) * 100
            
            return StockData(
                symbol=symbol,
                name=name,
                price=price,
                change=change,
                change_percent=change_percent,
                volume=volume,
                amount=amount,
                high=high,
                low=low,
                open=open_price,
                pre_close=pre_close,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"解析{symbol}数据失败: {e}")
            return None
    
    async def fetch_batch_data(self, symbols: List[str]) -> Dict[str, StockData]:
        """批量获取股票数据"""
        tasks = [self.fetch_stock_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        stock_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, StockData):
                stock_data[symbol] = result
            elif result is not None:
                logger.error(f"获取{symbol}数据异常: {result}")
        
        return stock_data

class StrategyEngine:
    """策略引擎"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # 策略配置
        self.strategies = {
            "strategy_one": {
                "name": "多指标共振策略",
                "weight": 0.35,
                "conditions": self._strategy_one_conditions
            },
            "strategy_two": {
                "name": "DMI趋势策略",
                "weight": 0.30,
                "conditions": self._strategy_two_conditions
            },
            "strategy_three": {
                "name": "趋势启动策略",
                "weight": 0.35,
                "conditions": self._strategy_three_conditions
            }
        }
    
    def _strategy_one_conditions(self, stock_data: StockData, 
                                historical_data: List[StockData]) -> Dict[str, Any]:
        """一号策略条件判断"""
        conditions = {}
        
        # 这里需要历史数据计算技术指标
        # 简化版本，实际需要完整的历史K线数据
        
        # 模拟条件判断
        conditions["macd_above_zero"] = stock_data.change_percent > 0
        conditions["rsi_condition"] = abs(stock_data.change_percent) < 5
        conditions["volume_condition"] = stock_data.volume > 1000000
        conditions["trend_condition"] = stock_data.price > stock_data.open
        
        return conditions
    
    def _strategy_two_conditions(self, stock_data: StockData,
                                historical_data: List[StockData]) -> Dict[str, Any]:
        """二号策略条件判断"""
        conditions = {}
        
        # DMI相关条件（需要历史数据计算）
        conditions["trend_strength"] = stock_data.change_percent > 1
        conditions["momentum"] = stock_data.volume > stock_data.pre_close * 10000
        conditions["breakout"] = stock_data.price > stock_data.high * 0.98
        
        return conditions
    
    def _strategy_three_conditions(self, stock_data: StockData,
                                  historical_data: List[StockData]) -> Dict[str, Any]:
        """三号策略条件判断"""
        conditions = {}
        
        conditions["price_action"] = stock_data.price > stock_data.pre_close
        conditions["volume_spike"] = stock_data.volume > 5000000
        conditions["volatility"] = (stock_data.high - stock_data.low) / stock_data.price < 0.05
        
        return conditions
    
    def evaluate_strategy(self, strategy_id: str, stock_data: StockData,
                         historical_data: List[StockData]) -> StrategyResult:
        """评估策略"""
        strategy = self.strategies[strategy_id]
        conditions = strategy["conditions"](stock_data, historical_data)
        
        # 计算得分
        total_conditions = len(conditions)
        met_conditions = sum(1 for cond in conditions.values() if cond)
        score = (met_conditions / total_conditions) * 100 if total_conditions > 0 else 0
        
        # 生成信号
        signals = []
        if score >= 80:
            signals.append("强烈买入信号")
            recommendation = "强烈推荐"
            confidence = 0.8
        elif score >= 60:
            signals.append("买入信号")
            recommendation = "推荐"
            confidence = 0.6
        elif score >= 40:
            signals.append("观望信号")
            recommendation = "观望"
            confidence = 0.4
        else:
            signals.append("回避信号")
            recommendation = "回避"
            confidence = 0.2
        
        return StrategyResult(
            strategy_name=strategy["name"],
            score=score,
            conditions_met=met_conditions,
            total_conditions=total_conditions,
            signals=signals,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def evaluate_all_strategies(self, stock_data: StockData,
                               historical_data: List[StockData]) -> Dict[str, StrategyResult]:
        """评估所有策略"""
        results = {}
        for strategy_id in self.strategies:
            result = self.evaluate_strategy(strategy_id, stock_data, historical_data)
            results[strategy_id] = result
            self.db.save_strategy_result(stock_data.symbol, result)
        
        return results

class RiskManager:
    """风险管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # 风险参数
        self.risk_params = {
            "max_daily_loss": 0.02,  # 单日最大亏损
            "max_position_per_stock": 0.2,  # 单只股票最大仓位
            "max_portfolio_risk": 0.1,  # 组合最大风险
            "stop_loss_ratio": 0.08,  # 止损比例
            "take_profit_ratio": 0.2,  # 止盈比例
            "min_risk_reward": 2.0,  # 最小风险收益比
        }
    
    def assess_risk(self, stock_data: StockData, 
                   strategy_results: Dict[str, StrategyResult]) -> RiskAssessment:
        """风险评估"""
        # 计算波动率（基于价格变化）
        volatility = abs(stock_data.change_percent)
        
        # 计算风险等级
        if volatility < 2:
            risk_level = RiskLevel.LOW
            max_position = 0.2
            stop_loss = 0.05
        elif volatility < 5:
            risk_level = RiskLevel.MEDIUM
            max_position = 0.15
            stop_loss = 0.08
        elif volatility < 10:
            risk_level = RiskLevel.HIGH
            max_position = 0.1
            stop_loss = 0.12
        else:
            risk_level = RiskLevel.VERY_HIGH
            max_position = 0.05
            stop_loss = 0.15
        
        # 根据策略结果调整
        avg_score = np.mean([r.score for r in strategy_results.values()])
        if avg_score >= 80:
            max_position *= 1.2
            stop_loss *= 0.8
        elif avg_score >= 60:
            max_position *= 1.0
        else:
            max_position *= 0.8
            stop_loss *= 1.2
        
        # 计算风险收益比
        take_profit = stop_loss * self.risk_params["min_risk_reward"]
        risk_reward_ratio = take_profit / stop_loss if stop_loss > 0 else 0
        
        # 计算回撤（简化）
        drawdown = min(0, stock_data.change_percent)
        
        return RiskAssessment(
            risk_level=risk_level,
            max_position=min(max_position, self.risk_params["max_position_per_stock"]),
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
            volatility=volatility,
            drawdown=drawdown
        )
    
    def generate_trade_signal(self, stock_data: StockData,
                             strategy_results: Dict[str, StrategyResult],
                             risk_assessment: RiskAssessment) -> Optional[TradeSignal]:
        """生成交易信号"""
        avg_score = np.mean([r.score for r in strategy_results.values()])
        
        if avg_score >= 80:
            signal = TradeSignal.STRONG_BUY
        elif avg_score >= 70:
            signal = TradeSignal.BUY
        elif avg_score >= 50:
            signal = TradeSignal.HOLD
        elif avg_score >= 30:
            signal = TradeSignal.SELL
        else:
            signal = TradeSignal.STRONG_SELL
        
        # 保存信号
        reason = f"综合得分: {avg_score:.1f}, 风险等级: {risk_assessment.risk_level.value}"
        self.db.save_trade_signal(
            stock_data.symbol, signal, stock_data.price,
            reason, risk_assessment
        )
        
        return signal
    
    def check_portfolio_risk(self, positions: Dict[str, float]) -> bool:
        """检查组合风险"""
        total_value = sum(positions.values())
        if total_value == 0:
            return True
        
        # 检查单只股票仓位
        for symbol, value in positions.items():
            position_ratio = value / total_value
            if position_ratio > self.risk_params["max_position_per_stock"]:
                logger.warning(f"{symbol}仓位过高: {position_ratio:.1%}")
                return False
        
        return True

class AlertManager:
    """预警管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.alert_rules = self._init_alert_rules()
    
    def _init_alert_rules(self) -> Dict[str, Dict]:
        """初始化预警规则"""
        return {
            "price_breakout": {
                "name": "价格突破",
                "condition": lambda data: data["change_percent"] > 5,
                "message": "{name}涨幅超过5%，当前{price}元"
            },
            "volume_spike": {
                "name": "成交量异动",
                "condition": lambda data: data["volume_ratio"] > 3,
                "message": "{name}成交量放大{volume_ratio}倍"
            },
            "strategy_signal": {
                "name": "策略信号",
                "condition": lambda data: data["score"] >= 80,
                "message": "{name}策略得分{score}，发出{signal}信号"
            },
            "risk_warning": {
                "name": "风险预警",
                "condition": lambda data: data["volatility"] > 8,
                "message": "{name}波动率过高({volatility}%)，请注意风险"
            }
        }
    
    def check_alerts(self, stock_data: StockData, 
                    strategy_results: Dict[str, StrategyResult],
                    risk_assessment: RiskAssessment):
        """检查预警条件"""
        alerts = []
        
        # 价格突破预警
        if abs(stock_data.change_percent) > 5:
            self.db.save_alert(
                stock_data.symbol,
                "price_breakout",
                f"{stock_data.name}价格{'上涨' if stock_data.change_percent > 0 else '下跌'}{abs(stock_data.change_percent):.1f}%",
                "warning" if abs(stock_data.change_percent) > 7 else "info",
                {
                    "price": stock_data.price,
                    "change_percent": stock_data.change_percent,
                    "volume": stock_data.volume
                }
            )
        
        # 策略信号预警
        avg_score = np.mean([r.score for r in strategy_results.values()])
        if avg_score >= 80:
            self.db.save_alert(
                stock_data.symbol,
                "strategy_signal",
                f"{stock_data.name}综合策略得分{avg_score:.1f}，发出强烈买入信号",
                "important",
                {
                    "score": avg_score,
                    "recommendation": "强烈买入"
                }
            )
        
        # 风险预警
        if risk_assessment.volatility > 8:
            self.db.save_alert(
                stock_data.symbol,
                "risk_warning",
                f"{stock_data.name}波动率过高({risk_assessment.volatility:.1f}%)，风险等级{risk_assessment.risk_level.value}",
                "warning",
                {
                    "volatility": risk_assessment.volatility,
                    "risk_level": risk_assessment.risk_level.value,
                    "stop_loss": risk_assessment.stop_loss
                }
            )
        
        return alerts

class StockMonitor:
    """股票监控主类"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.data_fetcher = RealTimeDataFetcher()
        self.strategy_engine = StrategyEngine(self.db)
        self.risk_manager = RiskManager(self.db)
        self.alert_manager = AlertManager(self.db)
        
        # 监控配置
        self.monitor_symbols = [
            "000001.SZ",  # 平安银行
            "600519.SH",  # 贵州茅台
            "300750.SZ",  # 宁德时代
            "000858.SZ",  # 五粮液
            "600036.SH",  # 招商银行
            "601318.SH",  # 中国平安
            "300059.SZ",  # 东方财富
            "600276.SH",  # 恒瑞医药
            "688111.SH",  # 金山办公
            "002594.SZ",  # 比亚迪
        ]
        
        self.check_interval = 300  # 检查间隔（秒）
        self.running = False
        
        logger.info("股票监控系统初始化完成")
    
    async def monitor_single_stock(self, symbol: str):
        """监控单只股票"""
        try:
            # 获取实时数据
            async with self.data_fetcher as fetcher:
                stock_data = await fetcher.fetch_stock_data(symbol)
            
            if not stock_data:
                logger.warning(f"无法获取{symbol}的实时数据")
                return
            
            # 保存数据
            self.db.save_stock_data(stock_data)
            
            # 获取历史数据（简化，实际需要从数据库获取）
            historical_data = []  # 这里应该从数据库获取历史数据
            
            # 策略评估
            strategy_results = self.strategy_engine.evaluate_all_strategies(
                stock_data, historical_data
            )
            
            # 风险评估
            risk_assessment = self.risk_manager.assess_risk(
                stock_data, strategy_results
            )
            
            # 生成交易信号
            signal = self.risk_manager.generate_trade_signal(
                stock_data, strategy_results, risk_assessment
            )
            
            # 检查预警
            self.alert_manager.check_alerts(
                stock_data, strategy_results, risk_assessment
            )
            
            # 打印结果
            self._print_monitor_result(
                stock_data, strategy_results, risk_assessment, signal
            )
            
        except Exception as e:
            logger.error(f"监控{symbol}时发生错误: {e}")
    
    def _print_monitor_result(self, stock_data: StockData,
                             strategy_results: Dict[str, StrategyResult],
                             risk_assessment: RiskAssessment,
                             signal: TradeSignal):
        """打印监控结果"""
        print(f"\n{'='*80}")
        print(f"📈 股票监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"股票: {stock_data.name} ({stock_data.symbol})")
        print(f"价格: {stock_data.price:.2f} ({stock_data.change:+.2f}, {stock_data.change_percent:+.2f}%)")
        print(f"成交量: {stock_data.volume:,} 成交额: {stock_data.amount/10000:.1f}万")
        print(f"最高: {stock_data.high:.2f} 最低: {stock_data.low:.2f} 开盘: {stock_data.open:.2f}")
        
        print(f"\n🎯 策略评估:")
        for strategy_id, result in strategy_results.items():
            print(f"  {result.strategy_name}: {result.score:.1f}/100 ({result.recommendation})")
        
        print(f"\n⚠️ 风险评估:")
        print(f"  风险等级: {risk_assessment.risk_level.value}")
        print(f"  波动率: {risk_assessment.volatility:.2f}%")
        print(f"  最大仓位: {risk_assessment.max_position:.1%}")
        print(f"  止损: {risk_assessment.stop_loss:.1%} 止盈: {risk_assessment.take_profit:.1%}")
        print(f"  风险收益比: 1:{risk_assessment.risk_reward_ratio:.1f}")
        
        print(f"\n📢 交易信号: {signal.value}")
        print(f"{'='*80}")
    
    async def monitor_all_stocks(self):
        """监控所有股票"""
        logger.info(f"开始监控{len(self.monitor_symbols)}只股票...")
        
        tasks = []
        for symbol in self.monitor_symbols:
            task = asyncio.create_task(self.monitor_single_stock(symbol))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        logger.info("本轮监控完成")
    
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while self.running:
                try:
                    loop.run_until_complete(self.monitor_all_stocks())
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"监控循环错误: {e}")
                    time.sleep(60)
            
            loop.close()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=run_async, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"股票监控已启动，检查间隔: {self.check_interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=10)
        logger.info("股票监控已停止")
    
    def generate_daily_report(self):
        """生成每日报告"""
        conn = sqlite3.connect(DB_PATH)
        
        # 获取今日交易信号
        today = datetime.now().strftime('%Y-%m-%d')
        signals_df = pd.read_sql_query(f'''
            SELECT symbol, signal, price, reason, risk_level, position_size,
                   stop_loss, take_profit, timestamp
            FROM trade_signals
            WHERE DATE(timestamp) = '{today}'
            ORDER BY timestamp DESC
        ''', conn)
        
        # 获取今日预警
        alerts_df = pd.read_sql_query(f'''
            SELECT symbol, alert_type, message, level, timestamp
            FROM alerts
            WHERE DATE(timestamp) = '{today}' AND acknowledged = 0
            ORDER BY timestamp DESC
        ''', conn)
        
        conn.close()
        
        # 生成报告
        report = []
        report.append(f"📊 每日监控报告 - {today}")
        report.append("="*60)
        
        if not signals_df.empty:
            report.append("\n📈 今日交易信号:")
            for _, row in signals_df.iterrows():
                report.append(f"  {row['symbol']}: {row['signal']} @ {row['price']:.2f}")
                report.append(f"     理由: {row['reason']}")
                report.append(f"     风险等级: {row['risk_level']}, 建议仓位: {row['position_size']:.1%}")
        
        if not alerts_df.empty:
            report.append("\n⚠️ 今日预警:")
            for _, row in alerts_df.iterrows():
                level_icon = "🔴" if row['level'] == "warning" else "🟡" if row['level'] == "important" else "🔵"
                report.append(f"  {level_icon} {row['symbol']}: {row['message']}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🚀 A股实时监控系统")
    print("="*60)
    print("功能特性:")
    print("  1. 📈 实时数据获取（新浪财经API）")
    print("  2. 🎯 三策略并行评估")
    print("  3. ⚠️ 智能风险控制")
    print("  4. 📢 自动预警系统")
    print("  5. 💾 数据持久化存储")
    print("="*60)
    
    # 创建监控系统
    monitor = StockMonitor()
    
    try:
        # 启动监控
        monitor.start_monitoring()
        
        # 保持主线程运行
        while True:
            time.sleep(60)
            
            # 每小时生成一次报告
            if datetime.now().minute == 0:
                report = monitor.generate_daily_report()
                print("\n" + report)
                
                # 保存报告到文件
                with open(f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", "w") as f:
                    f.write(report)
    
    except KeyboardInterrupt:
        print("\n\n正在停止监控系统...")
        monitor.stop_monitoring()
        print("监控系统已停止")
    except Exception as e:
        logger.error(f"系统运行错误: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    # 检查依赖
    try:
        import aiohttp
        import pandas as pd
        import numpy as np
    except ImportError as e:
        print(f"缺少依赖包: {e}")
        print("请安装: pip install aiohttp pandas numpy schedule")
        exit(1)
    
    main()