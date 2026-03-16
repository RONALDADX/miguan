#!/data/data/com.termux/files/usr/bin/bash

echo "🇨🇳 Clawdbot 中国区安装脚本"
echo "=========================="

# 配置国内源
echo "1. 配置 Termux 国内源..."
cp $PREFIX/etc/apt/sources.list $PREFIX/etc/apt/sources.list.bak 2>/dev/null
echo "deb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main" > $PREFIX/etc/apt/sources.list

# 更新安装
echo "2. 更新系统..."
pkg update -y && pkg upgrade -y

echo "3. 安装 Node.js..."
pkg install nodejs -y

echo "4. 配置 npm 镜像..."
npm config set registry https://registry.npmmirror.com
npm config set disturl https://npmmirror.com/dist
npm config set cache $HOME/.npm-cache

echo "5. 安装 Clawdbot..."
npm install -g clawdbot@latest --verbose

echo "6. 验证安装..."
if command -v clawdbot &> /dev/null; then
    echo "✅ 安装成功！"
    echo "版本信息："
    clawdbot --version
    echo ""
    echo "使用命令："
    echo "  clawdbot init    # 初始化配置"
    echo "  clawdbot start   # 启动服务"
    echo "  clawdbot status  # 查看状态"
else
    echo "❌ 安装失败，尝试备用方案..."
    
    # 备用方案：使用 cnpm
    echo "尝试使用 cnpm..."
    npm install -g cnpm --registry=https://registry.npmmirror.com
    cnpm install -g clawdbot
    
    if command -v clawdbot &> /dev/null; then
        echo "✅ 通过 cnpm 安装成功！"
    else
        echo "❌ 所有安装方法都失败"
        echo "请尝试："
        echo "1. 检查网络连接"
        echo "2. 使用代理"
        echo "3. 手动下载预编译包"
    fi
fi

echo ""
echo "📱 后续步骤："
echo "1. 运行 'clawdbot init' 初始化"
echo "2. 按提示配置模型（建议使用国内模型）"
echo "3. 运行 'clawdbot start' 启动"
echo ""
echo "💡 提示：中国大陆用户建议配置："
echo "   - 深度求索 API"
echo "   - 智谱 AI"
echo "   - 月之暗面 Kimi（如有 API）"