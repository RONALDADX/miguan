#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略管理系统
包含策略定义、股票筛选、评分等功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
import yaml
import json
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyManager:
    """策略管理器"""
    
    def __init__(self, config_path: str = "config/strategies_config.yaml"):
        """
        初始化策略管理器
        
        Args:
            config_path: 策略配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.strategies = self.config.get('strategies', {})
        self.execution = self.config.get('execution', {})
        
        # 策略执行结果缓存
        self.screening_results = {}
        self.strategy_scores = {}
        
    def get_strategy_01_rules(self) -> Dict:
        """
        获取一号策略的具体规则
        
        Returns:
            策略规则字典
        """
        strategy_01 = self.strategies.get('strategy_01', {})
        
        # 提取关键规则
        rules = {
            'name': strategy_01.get('name', '一号策略'),
            'description': strategy_01.get('description', ''),
            
            # 基本面规则
            'fundamental': {
                'pe_ratio': {
                    'range': (strategy_01.get('fundamental', {}).get('pe_ratio', {}).get('min', 5),
                             strategy_01.get('fundamental', {}).get('pe_ratio', {}).get('max', 25)),
                    'weight': strategy_01.get('fundamental', {}).get('pe_ratio', {}).get('weight', 0.15)
                },
                'pb_ratio': {
                    'range': (strategy_01.get('fundamental', {}).get('pb_ratio', {}).get('min', 0.8),
                             strategy_01.get('fundamental', {}).get('pb_ratio', {}).get('max', 3.0)),
                    'weight': strategy_01.get('fundamental', {}).get('pb_ratio', {}).get('weight', 0.15)
                },
                'roe': {
                    'min': strategy_01.get('fundamental', {}).get('roe', {}).get('min', 0.10),
                    'weight': strategy_01.get('fundamental', {}).get('roe', {}).get('weight', 0.20)
                },
                'revenue_growth': {
                    'min': strategy_01.get('fundamental', {}).get('revenue_growth', {}).get('min', 0.15),
                    'weight': strategy_01.get('fundamental', {}).get('revenue_growth', {}).get('weight', 0.15)
                },
                'profit_growth': {
                    'min': strategy_01.get('fundamental', {}).get('profit_growth', {}).get('min', 0.10),
                    'weight': strategy_01.get('fundamental', {}).get('profit_growth', {}).get('weight', 0.15)
                },
                'debt_ratio': {
                    'max': strategy_01.get('fundamental', {}).get('debt_ratio', {}).get('max', 0.60),
                    'weight': strategy_01.get('fundamental', {}).get('debt_ratio', {}).get('weight', 0.10)
                },
                'current_ratio': {
                    'min': strategy_01.get('fundamental', {}).get('current_ratio', {}).get('min', 1.2),
                    'weight': strategy_01.get('fundamental', {}).get('current_ratio', {}).get('weight', 0.10)
                }
            },
            
            # 技术面规则
            'technical': {
                'trend': {
                    'period': strategy_01.get('technical', {}).get('trend', {}).get('period', 20),
                    'weight': strategy_01.get('technical', {}).get('trend', {}).get('weight', 0.30)
                },
                'momentum': {
                    'period': strategy_01.get('technical', {}).get('momentum', {}).get('period', 10),
                    'weight': strategy_01.get('technical', {}).get('momentum', {}).get('weight', 0.20)
                },
                'volatility': {
                    'max': strategy_01.get('technical', {}).get('volatility', {}).get('max', 0.35),
                    'weight': strategy_01.get('technical', {}).get('volatility', {}).get('weight', 0.15)
                },
                'rsi': {
                    'range': (strategy_01.get('technical', {}).get('rsi', {}).get('min', 40),
                             strategy_01.get('technical', {}).get('rsi', {}).get('max', 70)),
                    'weight': strategy_01.get('technical', {}).get('rsi', {}).get('weight', 0.20)
                },
                'volume_ratio': {
                    'min': strategy_01.get('technical', {}).get('volume_ratio', {}).get('min', 1.0),
                    'weight': strategy_01.get('technical', {}).get('volume_ratio', {}).get('weight', 0.15)
                }
            },
            
            # 市场面规则
            'market': {
                'avg_volume': {
                    'min': strategy_01.get('market', {}).get('avg_volume', {}).get('min', 10000000),
                    'weight': strategy_01.get('market', {}).get('avg_volume', {}).get('weight', 0.20)
                },
                'market_cap': {
                    'range': (strategy_01.get('market', {}).get('market_cap', {}).get('min', 1000000000),
                             strategy_01.get('market', {}).get('market_cap', {}).get('max', 50000000000)),
                    'weight': strategy_01.get('market', {}).get('market_cap', {}).get('weight', 0.20)
                },
                'industry_rank': {
                    'min': strategy_01.get('market', {}).get('industry_rank', {}).get('min', 0.6),
                    'weight': strategy_01.get('market', {}).get('industry_rank', {}).get('weight', 0.20)
                },
                'institutional_holding': {
                    'min': strategy_01.get('market', {}).get('institutional_holding', {}).get('min', 0.05),
                    'weight': strategy_01.get('market', {}).get('institutional_holding', {}).get('weight', 0.20)
                },
                'analyst_rating': {
                    'min': strategy_01.get('market', {}).get('analyst_rating', {}).get('min', 3.5),
                    'weight': strategy_01.get('market', {}).get('analyst_rating', {}).get('weight', 0.20)
                }
            },
            
            # 筛选条件
            'screening': strategy_01.get('screening', {}),
            
            # 权重
            'weights': strategy_01.get('weights', {}),
            
            # 交易规则
            'trading': strategy_01.get('trading', {})
        }
        
        return rules
    
    def analyze_pingan_bank(self, stock_data: Dict = None) -> Dict:
        """
        分析平安银行是否符合一号策略
        
        Args:
            stock_data: 股票数据，如果为None则使用模拟数据
            
        Returns:
            分析结果
        """
        try:
            logger.info("开始分析平安银行(000001)是否符合一号策略...")
            
            # 获取策略规则
            rules = self.get_strategy_01_rules()
            
            # 如果没有提供数据，使用模拟数据
            if stock_data is None:
                stock_data = self._get_pingan_bank_mock_data()
            
            # 计算各项评分
            scores = self._calculate_strategy_scores(stock_data, rules)
            
            # 检查必须满足的条件
            must_have_passed = self._check_must_have_conditions(stock_data, rules['screening'])
            
            # 检查排除条件
            excluded = self._check_exclude_conditions(stock_data, rules['screening'])
            
            # 计算综合评分
            total_score = self._calculate_total_score(scores, rules['weights'])
            
            # 判断是否符合策略
            buy_conditions = rules['trading'].get('buy', {})
            meets_buy_criteria = (
                total_score >= buy_conditions.get('total_score', 80) and
                scores['technical']['total'] >= buy_conditions.get('technical_score', 70)
            )
            
            analysis_result = {
                'symbol': '000001',
                'name': '平安银行',
                'analysis_time': datetime.now().isoformat(),
                'strategy': rules['name'],
                
                # 详细评分
                'scores': scores,
                'total_score': total_score,
                
                # 条件检查
                'must_have_passed': must_have_passed,
                'excluded': excluded,
                'meets_buy_criteria': meets_buy_criteria,
                
                # 具体指标
                'indicators': {
                    'pe_ratio': stock_data.get('pe_ratio', 0),
                    'pb_ratio': stock_data.get('pb_ratio', 0),
                    'roe': stock_data.get('roe', 0),
                    'revenue_growth': stock_data.get('revenue_growth', 0),
                    'profit_growth': stock_data.get('profit_growth', 0),
                    'debt_ratio': stock_data.get('debt_ratio', 0),
                    'current_ratio': stock_data.get('current_ratio', 0),
                    'rsi': stock_data.get('rsi', 0),
                    'avg_volume': stock_data.get('avg_volume', 0),
                    'market_cap': stock_data.get('market_cap', 0)
                },
                
                # 结论
                'conclusion': self._generate_conclusion(total_score, meets_buy_criteria, excluded)
            }
            
            # 保存结果
            self.strategy_scores['000001'] = analysis_result
            
            logger.info(f"平安银行分析完成，综合评分: {total_score:.1f}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析平安银行失败: {e}")
            return {'error': str(e)}
    
    def _get_pingan_bank_mock_data(self) -> Dict:
        """
        获取平安银行的模拟数据
        
        Returns:
            模拟数据字典
        """
        # 注：这里使用模拟数据，实际应用中应该从AKShare获取真实数据
        return {
            'symbol': '000001',
            'name': '平安银行',
            
            # 基本面数据（模拟）
            'pe_ratio': 6.5,           # 市盈率 - 较低，符合价值投资
            'pb_ratio': 0.7,           # 市净率 - 低于1，可能破净
            'roe': 0.12,               # 净资产收益率 - 12%，符合要求
            'revenue_growth': 0.08,    # 营收增长 - 8%，低于要求的15%
            'profit_growth': 0.05,     # 利润增长 - 5%，低于要求的10%
            'debt_ratio': 0.92,        # 负债率 - 92%，远高于要求的60%
            'current_ratio': 0.9,      # 流动比率 - 0.9，低于要求的1.2
            
            # 技术面数据（模拟）
            'trend_score': 65,         # 趋势评分 - 中等
            'momentum_score': 60,      # 动量评分 - 中等
            'volatility': 0.28,        # 波动率 - 28%，符合要求
            'rsi': 55,                 # RSI - 55，符合要求
            'volume_ratio': 1.2,       # 成交量比 - 1.2，符合要求
            
            # 市场面数据（模拟）
            'avg_volume': 25000000,    # 日均成交额 - 2500万，符合要求
            'market_cap': 220000000000, # 市值 - 2200亿，在范围内
            'industry_rank': 0.7,      # 行业排名 - 前30%，符合要求
            'institutional_holding': 0.65, # 机构持股 - 65%，符合要求
            'analyst_rating': 4.2,     # 分析师评级 - 4.2星，符合要求
            
            # 其他
            'st_risk': False,          # 非ST股票
            'suspended': False         # 非停牌
        }
    
    def _calculate_strategy_scores(self, stock_data: Dict, rules: Dict) -> Dict:
        """
        计算策略各项评分
        
        Args:
            stock_data: 股票数据
            rules: 策略规则
            
        Returns:
            评分字典
        """
        scores = {
            'fundamental': {'total': 0, 'details': {}},
            'technical': {'total': 0, 'details': {}},
            'market': {'total': 0, 'details': {}}
        }
        
        # 计算基本面评分
        fund_rules = rules['fundamental']
        fund_score = 0
        fund_details = {}
        
        for indicator, rule in fund_rules.items():
            value = stock_data.get(indicator, 0)
            weight = rule.get('weight', 0)
            
            # 根据规则计算单项得分
            indicator_score = self._calculate_indicator_score(value, rule)
            
            # 加权得分
            weighted_score = indicator_score * weight
            
            fund_score += weighted_score
            fund_details[indicator] = {
                'value': value,
                'score': indicator_score,
                'weight': weight,
                'weighted_score': weighted_score
            }
        
        scores['fundamental']['total'] = fund_score * 100  # 转换为百分制
        scores['fundamental']['details'] = fund_details
        
        # 计算技术面评分
        tech_rules = rules['technical']
        tech_score = 0
        tech_details = {}
        
        for indicator, rule in tech_rules.items():
            if indicator.endswith('_score'):
                value = stock_data.get(indicator, 0) / 100  # 假设已经是0-1的分数
            else:
                value = stock_data.get(indicator, 0)
            
            weight = rule.get('weight', 0)
            
            # 根据规则计算单项得分
            indicator_score = self._calculate_indicator_score(value, rule)
            
            # 加权得分
            weighted_score = indicator_score * weight
            
            tech_score += weighted_score
            tech_details[indicator] = {
                'value': value,
                'score': indicator_score,
                'weight': weight,
                'weighted_score': weighted_score
            }
        
        scores['technical']['total'] = tech_score * 100
        scores['technical']['details'] = tech_details
        
        # 计算市场面评分
        market_rules = rules['market']
        market_score = 0
        market_details = {}
        
        for indicator, rule in market_rules.items():
            value = stock_data.get(indicator, 0)
            weight = rule.get('weight', 0)
            
            # 根据规则计算单项得分
            indicator_score = self._calculate_indicator_score(value, rule)
            
            # 加权得分
            weighted_score = indicator_score * weight
            
            market_score += weighted_score
            market_details[indicator] = {
                'value': value,
                'score': indicator_score,
                'weight': weight,
                'weighted_score': weighted_score
            }
        
        scores['market']['total'] = market_score * 100
        scores['market']['details'] = market_details
        
        return scores
    
    def _calculate_indicator_score(self, value: float, rule: Dict) -> float:
        """
        计算单个指标的得分
        
        Args:
            value: 指标值
            rule: 指标规则
            
        Returns:
            得分（0-1）
        """
        # 检查是否有范围限制
        if 'range' in rule:
            min_val, max_val = rule['range']
            if min_val <= value <= max_val:
                # 在范围内，得满分
                return 1.0
            else:
                # 不在范围内，根据偏离程度扣分
                if value < min_val:
                    deviation = (min_val - value) / min_val
                else:
                    deviation = (value - max_val) / max_val
                
                # 偏离越多，得分越低
                return max(0, 1.0 - deviation)
        
        # 检查最小值限制
        elif 'min' in rule:
            min_val = rule['min']
            if value >= min_val:
                return 1.0
            else:
                deviation = (min_val - value) / min_val
                return max(0, 1.0 - deviation)
        
        # 检查最大值限制
        elif 'max' in rule:
            max_val = rule['max']
            if value <= max_val:
                return 1.0
            else:
                deviation = (value - max_val) / max_val
                return max(0, 1.0 - deviation)
        
        # 没有限制，得满分
        return 1.0
    
    def _check_must_have_conditions(self, stock_data: Dict, screening: Dict) -> Dict:
        """
        检查必须满足的条件
        
        Args:
            stock_data: 股票数据
            screening: 筛选条件
            
        Returns:
            检查结果
        """
        must_have = screening.get('must_have', [])
        results = {}
        
        for condition in must_have:
            # 简单的条件解析
            if '>=' in condition:
                var, val = condition.split('>=')
                var = var.strip()
                val = float(val.strip())
                results[condition] = stock_data.get(var, 0) >= val
            elif '<=' in condition:
                var, val = condition.split('<=')
                var = var.strip()
                val = float(val.strip())
                results[condition] = stock_data.get(var, 0) <= val
            elif '=' in condition:
                var, val = condition.split('=')
                var = var.strip()
                val = val.strip()
                results[condition] = stock_data.get(var, '') == val
        
        # 计算通过率
        passed = sum(results.values())
        total = len(results)
        
        return {
            'results': results,
            'passed': passed,
            'total': total,
            'pass_rate': passed / total if total > 0 else 0
        }
    
    def _check_exclude_conditions(self, stock_data: Dict, screening: Dict) -> Dict:
        """
        检查排除条件
        
        Args:
            stock_data: 股票数据
            screening: 筛选条件
            
        Returns:
            排除检查结果
        """
        exclude = screening.get('exclude', [])
        results = {}
        
        for condition in exclude:
            if '=' in condition:
                var, val = condition.split('=')
                var = var.strip()
                val = val.strip().lower() == 'true'
                results[condition] = stock_data.get(var, False) == val
            elif '<' in condition:
                var, val = condition.split('<')
                var = var.strip()
                val = float(val.strip())
                results[condition] = stock_data.get(var, 0) < val
        
        # 计算是否被排除
        is_excluded = any(results.values())
        
        return {
            'results': results,
            'is_excluded': is_excluded,
            'exclusion_reasons': [cond for cond, result in results.items() if result]
        }
    
    def _calculate_total_score(self, scores: Dict, weights: Dict) -> float:
        """
        计算综合评分
        
        Args:
            scores: 各项评分
            weights: 权重
            
        Returns:
            综合评分（百分制）
        """
        total = 0
        
        for category, weight in weights.items():
            category_score = scores.get(category, {}).get('total', 0)
            total += category_score * weight
        
        return total
    
    def _generate_conclusion(self, total_score: float, meets_buy_criteria: bool, excluded: Dict) -> str:
        """
        生成分析结论
        
        Args:
            total_score: 综合评分
            meets_buy_criteria: 是否满足买入条件
            excluded: 排除检查结果
            
        Returns:
            结论文本
        """
        if excluded.get('is_excluded', False):
            reasons = excluded.get('exclusion_reasons', [])
            return f"❌ 不符合策略：触发排除条件 - {', '.join(reasons)}"
        
        elif meets_buy_criteria:
            return f"✅ 符合策略：综合评分{total_score:.1f}，建议买入"
        
        elif total_score >= 70:
            return f"⚠️ 基本符合策略：综合评分{total_score:.1f}，但未完全满足买入条件"
        
        elif total_score >= 60:
            return f"⚠️ 部分符合策略：综合评分{total_score:.1f}，需谨慎考虑"
        
        else:
            return f"❌ 不符合策略：综合评分{total_score:.1f}过低"
    
    def screen_stocks_weekly(self, stock_universe: List[str] = None) -> Dict:
        """
        执行一周股票筛选
        
        Args:
            stock_universe: 股票池，如果为None则使用默认
            
        Returns:
            筛选结果
        """
        try:
            logger.info("开始执行一周股票筛选...")
            
            # 如果没有提供股票池，使用模拟数据
            if stock_universe is None:
                stock_universe = self._get_weekly_stock_universe()
            
            # 获取策略规则
            rules = self.get_strategy_01_rules()
            
            # 筛选结果
            results = {
                'screening_time': datetime.now().isoformat(),
                'strategy': rules['name'],
                'total_screened': len(stock_universe),
                'passed_stocks': [],
                'failed_stocks': [],
                'excluded_stocks': [],
                'top_candidates': []
            }
            
            # 遍历股票池
            for symbol in stock_universe:
                # 获取股票数据（这里使用模拟数据）
                stock_data = self._get_mock_stock_data(symbol)
                
                # 分析股票
                analysis = self.analyze_stock(stock_data, rules)
                
                # 分类结果
                if analysis.get('excluded', {}).get('is_excluded', False):
                    results['excluded_stocks'].append({
                        'symbol': symbol,
                        'reason': analysis['excluded']['exclusion_reasons']
                    })
                elif analysis.get('meets_buy_criteria', False):
                    results['passed_stocks'].append({
                        'symbol': symbol,
                        'name': stock_data.get('name', ''),
                        'total_score': analysis['total_score'],
                        'scores': analysis['scores']
                    })
                else:
                    results['failed_stocks'].append({
                        'symbol': symbol,
                        'name': stock_data.get('name', ''),
                        'total_score': analysis['total_score'],
                        'reason': analysis['conclusion']
                    })
            
            # 按评分排序
            results['passed_stocks'].sort(key=lambda x: x['total_score'], reverse=True)
            
            # 选取前10名作为推荐
            results['top_candidates'] = results['passed_stocks'][:10]
            
            # 保存结果
            self.screening_results['weekly'] = results
            
            logger.info(f"一周股票筛选完成，共筛选{results['total_screened']}只股票，"
                       f"通过{len(results['passed_stocks'])}只，"
                       f"排除{len(results['excluded_stocks'])}只")
            
            return results
            
        except Exception as e:
            logger.error(f"执行股票筛选失败: {e}")
            return {'error': str(e)}
    
    def analyze_stock(self, stock_data: Dict, rules: Dict) -> Dict:
        """
        分析单只股票
        
        Args:
            stock_data: 股票数据
            rules: 策略规则
            
        Returns:
            分析结果
        """
        # 计算各项评分
        scores = self._calculate_strategy_scores(stock_data, rules)
        
        # 检查必须满足的条件
        must_have_passed = self._check_must_have_conditions(stock_data, rules['screening'])
        
        # 检查排除条件
        excluded = self._check_exclude_conditions(stock_data, rules['screening'])
        
        # 计算综合评分
        total_score = self._calculate_total_score(scores, rules['weights'])
        
        # 判断是否符合策略
        buy_conditions = rules['trading'].get('buy', {})
        meets_buy_criteria = (
            total_score >= buy_conditions.get('total_score', 80) and
            scores['technical']['total'] >= buy_conditions.get('technical_score', 70)
        )
        
        return {
            'symbol': stock_data.get('symbol', ''),
            'name': stock_data.get('name', ''),
            'scores': scores,
            'total_score': total_score,
            'must_have_passed': must_have_passed,
            'excluded': excluded,
            'meets_buy_criteria': meets_buy_criteria,
            'conclusion': self._generate_conclusion(total_score, meets_buy_criteria, excluded)
        }
    
    def _get_weekly_stock_universe(self) -> List[str]:
        """
        获取一周筛选的股票池（模拟）
        
        Returns:
            股票代码列表
        """
        # 模拟一些常见的A股股票
        return [
            '000001', '000002', '000858', '600519', '601318',  # 大盘股
            '000333', '002415', '300750', '300059', '002475',  # 成长股
            '600036', '601988', '601328', '601288', '601398',  # 银行股
            '000725', '002049', '300122', '300142', '300124',  # 科技股
            '600887', '000568', '600276', '600436', '600309'   # 消费股
        ]
    
    def _get_mock_stock_data(self, symbol: str) -> Dict:
        """
        获取模拟股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            模拟数据字典
        """
        # 根据股票代码生成不同的模拟数据
        np.random.seed(hash(symbol) % 10000)
        
        return {
            'symbol': symbol,
            'name': f'模拟股票{symbol}',
            
            # 基本面数据（随机生成）
            'pe_ratio': np.random.uniform(5, 30),
            'pb_ratio': np.random.uniform(0.5, 4),
            'roe': np.random.uniform(0.05, 0.25),
            'revenue_growth': np.random.uniform(0.05, 0.30),
            'profit_growth': np.random.uniform(0.03, 0.25),
            'debt_ratio': np.random.uniform(0.3, 0.9),
            'current_ratio': np.random.uniform(0.8, 2.5),
            
            # 技术面数据
            'trend_score': np.random.randint(40, 90),
            'momentum_score': np.random.randint(40, 90),
            'volatility': np.random.uniform(0.15, 0.40),
            'rsi': np.random.randint(30, 75),
            'volume_ratio': np.random.uniform(0.8, 1.5),
            
            # 市场面数据
            'avg_volume': np.random.randint(5000000, 50000000),
            'market_cap': np.random.randint(500000000, 100000000000),
            'industry_rank': np.random.uniform(0.4, 0.9),
            'institutional_holding': np.random.uniform(0.1, 0.8),
            'analyst_rating': np.random.uniform(3.0, 5.0),
            
            # 其他
            'st_risk': np.random.random() < 0.05,  # 5%概率是ST
            'suspended': np.random.random() < 0.02  # 2%概率停牌
        }
    
    def generate_screening_report(self, results: Dict) -> str:
        """
        生成筛选报告
        
        Args:
            results: 筛选结果
            
        Returns:
            报告文本
        """
        try:
            report_lines = [
                "=" * 60,
                "一号策略 - 一周股票筛选报告",
                "=" * 60,
                f"筛选时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"策略名称: {results.get('strategy', '一号策略')}",
                ""
            ]
            
            # 筛选统计
            report_lines.append("📊 筛选统计:")
            report_lines.append("-" * 40)
            report_lines.append(f"  筛选总数: {results.get('total_screened', 0):,}")
            report_lines.append(f"  通过数量: {len(results.get('passed_stocks', [])):,}")
            report_lines.append(f"  排除数量: {len(results.get('excluded_stocks', [])):,}")
            report_lines.append(f"  未通过数: {len(results.get('failed_stocks', [])):,}")
            
            # 排除原因统计
            excluded = results.get('excluded_stocks', [])
            if excluded:
                report_lines.append("")
                report_lines.append("🚫 排除原因统计:")
                report_lines.append("-" * 40)
                exclusion_counts = {}
                for stock in excluded:
                    for reason in stock.get('reason', []):
                        exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
                
                for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
                    report_lines.append(f"  {reason}: {count}只")
            
            # 推荐股票
            top_candidates = results.get('top_candidates', [])
            if top_candidates:
                report_lines.append("")
                report_lines.append("🏆 推荐股票 (Top 10):")
                report_lines.append("-" * 40)
                
                for i, stock in enumerate(top_candidates, 1):
                    symbol = stock.get('symbol', '')
                    name = stock.get('name', '')
                    score = stock.get('total_score', 0)
                    
                    # 获取详细评分
                    scores = stock.get('scores', {})
                    fund_score = scores.get('fundamental', {}).get('total', 0)
                    tech_score = scores.get('technical', {}).get('total', 0)
                    market_score = scores.get('market', {}).get('total', 0)
                    
                    report_lines.append(f"  {i:2d}. {symbol} - {name}")
                    report_lines.append(f"      综合评分: {score:.1f}")
                    report_lines.append(f"      基本面: {fund_score:.1f} | 技术面: {tech_score:.1f} | 市场面: {market_score:.1f}")
            
            # 详细评分示例
            if top_candidates:
                report_lines.append("")
                report_lines.append("📋 评分示例 (第一只股票):")
                report_lines.append("-" * 40)
                
                first_stock = top_candidates[0]
                scores = first_stock.get('scores', {})
                
                # 基本面详细评分
                fund_details = scores.get('fundamental', {}).get('details', {})
                if fund_details:
                    report_lines.append("  基本面指标:")
                    for indicator, detail in list(fund_details.items())[:3]:  # 显示前3个
                        value = detail.get('value', 0)
                        score = detail.get('score', 0) * 100
                        report_lines.append(f"    {indicator}: {value:.2f} → {score:.1f}分")
            
            report_lines.append("")
            report_lines.append("=" * 60)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成筛选报告失败: {e}")
            return f"生成报告时出错: {e}"


if __name__ == "__main__":
    # 测试代码
    strategy_mgr = StrategyManager()
    
    # 测试平安银行分析
    pingan_analysis = strategy_mgr.analyze_pingan_bank()
    print("平安银行分析结果:")
    print(f"综合评分: {pingan_analysis.get('total_score', 0):.1f}")
    print(f"结论: {pingan_analysis.get('conclusion', '')}")
    
    # 测试一周股票筛选
    weekly_results = strategy_mgr.screen_stocks_weekly()
    report = strategy_mgr.generate_screening_report(weekly_results)
    print("\n一周股票筛选报告:")
    print(report)