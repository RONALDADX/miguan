#!/bin/bash
# A股实时监控系统安装脚本

echo "🚀 A股实时监控系统安装程序"
echo "="*60

# 检查Python版本
echo "检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ 未找到Python3，请先安装Python3.8+"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv_monitor
source venv_monitor/bin/activate

# 安装依赖包
echo "安装依赖包..."
pip install --upgrade pip

# 核心依赖
echo "安装核心依赖..."
pip install aiohttp pandas numpy schedule

# 可选依赖（用于更高级功能）
echo "安装可选依赖..."
pip install sqlite3  # Python内置，确保可用
pip install requests  # 备用数据源

# 检查AKShare（推荐但可选）
echo "检查AKShare..."
pip install akshare || echo "⚠️ AKShare安装失败，将使用备用数据源"

# 创建配置文件
echo "创建配置文件..."
cat > config.json << 'EOF'
{
  "monitor": {
    "symbols": [
      "000001.SZ",
      "600519.SH", 
      "300750.SZ",
      "000858.SZ",
      "600036.SH",
      "601318.SH",
      "300059.SZ",
      "600276.SH",
      "688111.SH",
      "002594.SZ"
    ],
    "check_interval": 300,
    "data_source": "sina",
    "enable_alerts": true,
    "enable_risk_control": true
  },
  "strategies": {
    "strategy_one": {
      "enabled": true,
      "weight": 0.35
    },
    "strategy_two": {
      "enabled": true, 
      "weight": 0.30
    },
    "strategy_three": {
      "enabled": true,
      "weight": 0.35
    }
  },
  "risk_control": {
    "max_daily_loss": 0.02,
    "max_position_per_stock": 0.2,
    "stop_loss_ratio": 0.08,
    "take_profit_ratio": 0.2,
    "min_risk_reward": 2.0
  },
  "alerts": {
    "price_breakout": 5.0,
    "volume_spike": 3.0,
    "volatility_warning": 8.0,
    "strategy_signal": 80
  }
}
EOF

# 创建启动脚本
echo "创建启动脚本..."
cat > start_monitor.sh << 'EOF'
#!/bin/bash
# 启动A股实时监控系统

echo "🚀 启动A股实时监控系统..."
echo "="*60

# 激活虚拟环境
source venv_monitor/bin/activate

# 检查依赖
echo "检查依赖..."
python3 -c "import aiohttp, pandas, numpy, schedule, sqlite3; print('✅ 依赖检查通过')"

# 运行监控系统
echo "启动监控主程序..."
python3 a股实时监控系统.py

# 如果主程序退出，显示错误信息
if [ $? -ne 0 ]; then
    echo "❌ 监控系统启动失败"
    echo "请检查："
    echo "1. Python依赖是否正确安装"
    echo "2. 网络连接是否正常"
    echo "3. 配置文件是否正确"
fi
EOF

chmod +x start_monitor.sh

# 创建停止脚本
echo "创建停止脚本..."
cat > stop_monitor.sh << 'EOF'
#!/bin/bash
# 停止A股实时监控系统

echo "🛑 停止A股实时监控系统..."

# 查找并杀死监控进程
pkill -f "a股实时监控系统.py" || true
pkill -f "python3.*监控" || true

echo "✅ 监控系统已停止"
EOF

chmod +x stop_monitor.sh

# 创建定时任务脚本
echo "创建定时任务脚本..."
cat > schedule_tasks.sh << 'EOF'
#!/bin/bash
# 定时任务管理

case "$1" in
    start)
        echo "⏰ 启动定时任务..."
        # 每30分钟检查一次系统状态
        (crontab -l 2>/dev/null; echo "*/30 * * * * cd $(pwd) && ./check_system.sh") | crontab -
        # 每天9:00生成报告
        (crontab -l 2>/dev/null; echo "0 9 * * * cd $(pwd) && ./generate_daily_report.sh") | crontab -
        echo "✅ 定时任务已启动"
        ;;
    stop)
        echo "🛑 停止定时任务..."
        crontab -l | grep -v "$(pwd)" | crontab -
        echo "✅ 定时任务已停止"
        ;;
    status)
        echo "📋 当前定时任务:"
        crontab -l | grep -A2 -B2 "$(pwd)" || echo "无相关定时任务"
        ;;
    *)
        echo "使用方法: $0 {start|stop|status}"
        exit 1
        ;;
esac
EOF

chmod +x schedule_tasks.sh

# 创建系统检查脚本
echo "创建系统检查脚本..."
cat > check_system.sh << 'EOF'
#!/bin/bash
# 系统状态检查

echo "🔍 系统状态检查 - $(date)"
echo "="*50

# 检查Python进程
echo "检查Python进程:"
ps aux | grep -E "(a股实时监控系统|python3.*监控)" | grep -v grep || echo "无监控进程运行"

# 检查数据库
echo -e "\n检查数据库:"
if [ -f "stock_monitor.db" ]; then
    size=$(du -h stock_monitor.db | cut -f1)
    echo "数据库大小: $size"
    # 检查表数量
    tables=$(sqlite3 stock_monitor.db ".tables" | wc -w)
    echo "数据表数量: $tables"
else
    echo "数据库文件不存在"
fi

# 检查日志文件
echo -e "\n检查日志文件:"
if [ -f "stock_monitor.log" ]; then
    size=$(du -h stock_monitor.log | cut -f1)
    echo "日志大小: $size"
    echo "最近错误:"
    tail -5 stock_monitor.log | grep -i error || echo "无错误记录"
else
    echo "日志文件不存在"
fi

# 检查网络连接
echo -e "\n检查网络连接:"
ping -c 2 hq.sinajs.cn >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 数据源连接正常"
else
    echo "❌ 数据源连接失败"
fi

echo -e "\n系统检查完成"
EOF

chmod +x check_system.sh

# 创建每日报告脚本
echo "创建每日报告脚本..."
cat > generate_daily_report.sh << 'EOF'
#!/bin/bash
# 生成每日报告

echo "📊 生成每日报告 - $(date +%Y-%m-%d)"
echo "="*60

# 激活虚拟环境
source venv_monitor/bin/activate

# 运行报告生成
python3 -c "
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 连接数据库
conn = sqlite3.connect('stock_monitor.db')

# 获取今日日期
today = datetime.now().strftime('%Y-%m-%d')

# 查询今日信号
print('📈 今日交易信号汇总:')
signals_df = pd.read_sql_query(f'''
    SELECT symbol, signal, COUNT(*) as count, 
           AVG(price) as avg_price, MAX(timestamp) as last_signal
    FROM trade_signals 
    WHERE DATE(timestamp) = '{today}'
    GROUP BY symbol, signal
    ORDER BY symbol, signal
''', conn)

if not signals_df.empty:
    for _, row in signals_df.iterrows():
        print(f'  {row[\"symbol\"]}: {row[\"signal\"]} x{row[\"count\"]}次')
else:
    print('  今日无交易信号')

# 查询今日预警
print('\n⚠️ 今日预警汇总:')
alerts_df = pd.read_sql_query(f'''
    SELECT symbol, alert_type, level, COUNT(*) as count,
           GROUP_CONCAT(DISTINCT message) as messages
    FROM alerts
    WHERE DATE(timestamp) = '{today}' AND acknowledged = 0
    GROUP BY symbol, alert_type, level
    ORDER BY level DESC, count DESC
''', conn)

if not alerts_df.empty:
    for _, row in alerts_df.iterrows():
        level_icon = '🔴' if row['level'] == 'warning' else '🟡' if row['level'] == 'important' else '🔵'
        print(f'  {level_icon} {row[\"symbol\"]}: {row[\"alert_type\"]} ({row[\"count\"]}次)')
else:
    print('  今日无预警')

# 查询系统状态
print('\n💾 系统状态:')
stats_df = pd.read_sql_query('''
    SELECT 
        (SELECT COUNT(DISTINCT symbol) FROM stock_data) as total_stocks,
        (SELECT COUNT(*) FROM stock_data WHERE DATE(timestamp) = DATE('now')) as today_records,
        (SELECT COUNT(*) FROM strategy_results WHERE DATE(timestamp) = DATE('now')) as today_strategies,
        (SELECT COUNT(*) FROM trade_signals WHERE DATE(timestamp) = DATE('now')) as today_signals
''', conn)

print(f'  监控股票数: {stats_df.iloc[0][\"total_stocks\"]}')
print(f'  今日数据记录: {stats_df.iloc[0][\"today_records\"]}')
print(f'  今日策略评估: {stats_df.iloc[0][\"today_strategies\"]}')
print(f'  今日交易信号: {stats_df.iloc[0][\"today_signals\"]}')

conn.close()

print('\n' + '='*60)
print('报告生成完成')
"

# 保存报告到文件
report_file="daily_report_$(date +%Y%m%d).txt"
python3 -c "
import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect('stock_monitor.db')
today = datetime.now().strftime('%Y-%m-%d')

with open('$report_file', 'w') as f:
    f.write(f'每日监控报告 - {today}\\n')
    f.write('='*60 + '\\n\\n')
    
    # 写入信号
    signals_df = pd.read_sql_query(f'''
        SELECT * FROM trade_signals 
        WHERE DATE(timestamp) = '{today}'
        ORDER BY timestamp DESC
    ''', conn)
    
    if not signals_df.empty:
        f.write('📈 详细交易信号:\\n')
        for _, row in signals_df.iterrows():
            f.write(f'  {row[\"timestamp\"]} {row[\"symbol\"]}: {row[\"signal\"]} @ {row[\"price\"]:.2f}\\n')
            f.write(f'      理由: {row[\"reason\"]}\\n')
            f.write(f'      风险等级: {row[\"risk_level\"]}, 仓位: {row[\"position_size\"]:.1%}\\n')
            f.write(f'      止损: {row[\"stop_loss\"]:.1%}, 止盈: {row[\"take_profit\"]:.1%}\\n\\n')
    
    # 写入预警
    alerts_df = pd.read_sql_query(f'''
        SELECT * FROM alerts
        WHERE DATE(timestamp) = '{today}'
        ORDER BY timestamp DESC
    ''', conn)
    
    if not alerts_df.empty:
        f.write('⚠️ 详细预警记录:\\n')
        for _, row in alerts_df.iterrows():
            f.write(f'  {row[\"timestamp\"]} {row[\"symbol\"]} [{row[\"alert_type\"]}]:\\n')
            f.write(f'      {row[\"message\"]}\\n\\n')

conn.close()
"

echo "✅ 报告已保存到: $report_file"
EOF

chmod +x generate_daily_report.sh

# 创建Web监控界面（可选）
echo "创建Web监控界面..."
cat > web_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
简单的Web监控界面
"""

from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('stock_monitor.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """主页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>A股实时监控系统</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #4CAF50; color: white; padding: 15px; border-radius: 5px; }
            .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }
            .signal-buy { color: green; font-weight: bold; }
            .signal-sell { color: red; font-weight: bold; }
            .signal-hold { color: orange; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .alert-warning { background-color: #fff3cd; border-color: #ffeaa7; }
            .alert-danger { background-color: #f8d7da; border-color: #f5c6cb; }
            .alert-info { background-color: #d1ecf1; border-color: #bee5eb; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 A股实时监控系统</h1>
            <p>最后更新: <span id="update-time">加载中...</span></p>
        </div>
        
        <div class="card">
            <h2>📈 实时监控</h2>
            <div id="monitor-status">加载中...</div>
        </div>
        
        <div class="card">
            <h2>📊 今日信号</h2>
            <div id="today-signals">加载中...</div>
        </div>
        
        <div class="card">
            <h2>⚠️ 今日预警</h2>
            <div id="today-alerts">加载中...</div>
        </div>
        
        <script>
            function updateData() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('update-time').textContent = data.timestamp;
                        
                        // 更新监控状态
                        let statusHtml = '<table>';
                        data.monitor_status.forEach(stock => {
                            statusHtml += `
                                <tr>
                                    <td>${stock.symbol}</td>
                                    <td>${stock.name}</td>
                                    <td>${stock.price}</td>
                                    <td class="${stock.change >= 0 ? 'signal-buy' : 'signal-sell'}">
                                        ${stock.change >= 0 ? '+' : ''}${stock.change} (${stock.change_percent}%)
                                    </td>
                                    <td>${stock.signal || '无'}</td>
                                </tr>
                            `;
                        });
                        statusHtml += '</table>';
                        document.getElementById('monitor-status').innerHTML = statusHtml;
                        
                        // 更新信号
                        let signalsHtml = '<table>';
                        data.today_signals.forEach(signal => {
                            const signalClass = signal.signal.includes('买入') ? 'signal-buy' : 
                                              signal.signal.includes('卖出') ? 'signal-sell' : 'signal-hold';
                            signalsHtml += `
                                <tr>
                                    <td>${signal.timestamp}</td>
                                    <td>${signal.symbol}</td>
                                    <td class="${signalClass}">${signal.signal}</td>
                                    <td>${signal.price}</td>
                                    <td>${signal.reason}</td>
                                </tr>
                            `;
                        });
                        signalsHtml += '</table>';
                        document.getElementById('today-signals').innerHTML = signalsHtml;
                        
                        // 更新预警
                        let alertsHtml = '';
                        data.today_alerts.forEach(alert => {
                            const alertClass = alert.level === 'warning' ? 'alert-danger' :
                                              alert.level === 'important' ? 'alert-warning' : 'alert-info';
                            alertsHtml += `
                                <div class="card ${alertClass}">
                                    <strong>${alert.symbol} [${alert.alert_type}]</strong><br>
                                    ${alert.message}<br>
                                    <small>${alert.timestamp}</small>
                                </div>
                            `;
                        });
                        document.getElementById('today-alerts').innerHTML = alertsHtml || '今日无预警';
                    });
            }
            
            // 初始加载
            updateData();
            
            // 每30秒更新一次
            setInterval(updateData, 30000);
        </script>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API接口：获取系统状态"""
    conn = get_db_connection()
    
    # 获取最新股票数据
    stocks_df = pd.read_sql_query('''
        SELECT s1.* FROM stock_data s1
        INNER JOIN (
            SELECT symbol, MAX(timestamp) as max_time
            FROM stock_data
            GROUP BY symbol
        ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_time
        ORDER BY s1.symbol
    ''', conn)
    
    # 获取今日信号
    today = datetime.now().strftime('%Y-%m-%d')
    signals_df = pd.read_sql_query(f'''
        SELECT * FROM trade_signals
        WHERE DATE(timestamp) = '{today}'
        ORDER BY timestamp DESC
        LIMIT 20
    ''', conn)
    
    # 获取今日预警
    alerts_df = pd.read_sql_query(f'''
        SELECT * FROM alerts
        WHERE DATE(timestamp) = '{today}'
        ORDER BY timestamp DESC
        LIMIT 20
    ''', conn)
    
    conn.close()
    
    return jsonify({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'monitor_status': stocks_df.to_dict('records'),
        'today_signals': signals_df.to_dict('records'),
        'today_alerts': alerts_df.to_dict('records')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

echo "创建README文件..."
cat > README.md << 'EOF'
# 🚀 A股实时监控系统

## 功能特性

### 📈 实时数据监控
- 支持A股实时行情获取
- 多数据源支持（新浪财经、腾讯财经等）
- 自动数据更新和存储

### 🎯 智能策略评估
- 三策略并行评估（多指标共振、DMI趋势、趋势启动）
- 实时策略得分计算
- 综合推荐信号生成

### ⚠️ 风险控制系统
- 智能风险评估（低、中、高、极高）
- 自动仓位控制建议
- 止损止盈策略生成
- 风险收益比计算

### 📢 预警通知系统
- 价格突破预警
- 成交量异动预警
- 策略信号预警
- 风险预警

### 💾 数据管理
- SQLite数据库存储
- 完整历史记录
- 数据备份和恢复

## 快速开始

### 1. 安装系统
```bash
# 运行安装脚本
bash setup_monitor_system.sh
```

### 2. 启动监控
```bash
# 启动监控系统
./start_monitor.sh
```

### 3. 访问Web界面
```bash
# 启动Web监控界面（可选）
python3 web_monitor.py
```
然后在浏览器中访问：http://localhost:5000

## 系统配置

### 监控股票列表
编辑 `config.json` 文件中的 `monitor.symbols` 部分：
```json
{
  "monitor": {
    "symbols": [
      "000001.SZ",  # 平安银行
      "600519.SH",  # 贵州茅台
      "300750.SZ"   # 宁德时代
    ]
  }
}
```

### 策略参数调整
编辑 `config.json` 文件中的 `strategies` 部分：
```json
{
  "strategies": {
    "strategy_one": {
      "enabled": true,
      "weight": 0.35
    }
  }
}
```

### 风险控制参数
编辑 `config.json` 文件中的 `risk_control` 部分：
```json
{
  "risk_control": {
    "max_daily_loss": 0.02,
    "stop_loss_ratio": 0.08
  }
}
```

## 系统管理

### 启动/停止监控
```bash
# 启动
./start_monitor.sh

# 停止
./stop_monitor.sh
```

### 定时任务管理
```bash
# 启动定时任务
./schedule_tasks.sh start

# 停止定时任务
./schedule_tasks.sh stop

# 查看状态
./schedule_tasks.sh status
```

### 系统状态检查
```bash
# 手动检查系统状态
./check_system.sh

# 生成每日报告
./generate_daily_report.sh
```

## 数据源说明

### 默认数据源：新浪财经
- 免费、稳定、实时性好
- 支持A股所有股票
- 无需API密钥

### 备用数据源：AKShare
- 需要额外安装：`pip install akshare`
- 数据更全面
- 包含财务数据和更多指标

## 故障排除

### 常见问题

1. **无法获取数据**
   - 检查网络连接
   - 确认数据源可用性
   - 查看日志文件 `stock_monitor.log`

2. **数据库错误**
   - 检查数据库文件权限
   - 确保磁盘空间充足
   - 尝试删除并重新创建数据库

3. **策略评估异常**
   - 检查历史数据完整性
   - 验证技术指标计算参数
   - 查看策略配置是否正确

### 日志文件
- 系统日志：`stock_monitor.log`
- 数据库文件：`stock_monitor.db`
- 每日报告：`daily_report_YYYYMMDD.txt`

## 安全建议

1. **定期备份数据库**
2. **监控系统资源使用**
3. **设置适当的防火墙规则**
4. **定期更新依赖包**

## 许可证

本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 查看项目文档
- 参考代码注释
EOF

echo "安装完成！"
echo "="*60
echo "✅ 系统安装完成"
echo ""
echo "接下来可以："
echo "1. 启动监控系统：./start_monitor.sh"
echo "2. 查看Web界面：python3 web_monitor.py"
echo "3. 检查系统状态：./check_system.sh"
echo ""
echo "详细说明请查看 README.md"
echo "="*60