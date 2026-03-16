# 量化交易监控系统

基于AKShare实时数据的交易监控、风险控制和仓位控制系统。

## 功能特性

### 1. 数据接入层
- AKShare实时数据采集
- 多市场数据源支持（A股、港股、美股、期货、加密货币）
- WebSocket实时数据流
- 历史数据回填

### 2. 监控系统
- 实时价格监控
- 技术指标计算
- 异常波动检测
- 市场情绪分析
- 交易信号生成

### 3. 风险控制系统
- 最大回撤控制
- 波动率监控
- 相关性风险
- 流动性风险
- 黑天鹅事件预警

### 4. 仓位控制系统
- 动态仓位调整
- 风险预算分配
- 止损止盈策略
- 资金管理模型

## 系统架构

```
├── data/                    # 数据存储
├── config/                  # 配置文件
├── src/
│   ├── data/               # 数据采集模块
│   ├── monitor/            # 监控模块
│   ├── risk/               # 风险控制模块
│   ├── position/           # 仓位控制模块
│   ├── alert/              # 预警模块
│   └── dashboard/          # 可视化面板
├── tests/                  # 测试文件
└── scripts/               # 运行脚本
```

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量：`cp .env.example .env`
3. 运行监控系统：`python src/main.py`

## 配置说明

- `config/market_config.yaml`: 市场配置
- `config/risk_config.yaml`: 风险参数配置
- `config/position_config.yaml`: 仓位策略配置