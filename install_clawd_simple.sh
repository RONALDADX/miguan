#!/bin/bash
echo "🦌 Clawdbot 极简安装脚本（国内特供）"
echo "=================================="

# 检查是否在安卓
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ 请在 Termux 中运行此脚本"
    echo "如果无法安装 Termux，请尝试："
    echo "1. 下载 'Aid Learning' 应用"
    echo "2. 在 Aid Learning 中打开终端"
    echo "3. 重新运行此脚本"
    exit 1
fi

echo "1. 使用清华源更新..."
sed -i 's@^\(deb.*stable main\)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main@' $PREFIX/etc/apt/sources.list

echo "2. 安装基础工具..."
pkg update -y && pkg upgrade -y
pkg install wget curl tar -y

echo "3. 下载预编译的 Clawdbot..."
# 尝试多个国内可访问的源
for url in \
    "https://ghproxy.com/https://github.com/clawdbot/clawdbot/releases/latest/download/clawdbot-linux-arm64.tar.gz" \
    "https://gh.api.99988866.xyz/https://github.com/clawdbot/clawdbot/releases/latest/download/clawdbot-linux-arm64.tar.gz" \
    "https://github.91chi.fun/https://github.com/clawdbot/clawdbot/releases/latest/download/clawdbot-linux-arm64.tar.gz"
do
    echo "尝试下载: $url"
    if wget -O clawdbot.tar.gz "$url"; then
        echo "✅ 下载成功"
        break
    fi
done

if [ ! -f "clawdbot.tar.gz" ]; then
    echo "❌ 所有下载源都失败"
    echo "请手动下载："
    echo "1. 用电脑访问 https://github.com/clawdbot/clawdbot/releases"
    echo "2. 下载 clawdbot-linux-arm64.tar.gz"
    echo "3. 传到手机，放在当前目录"
    echo "4. 重新运行此脚本"
    exit 1
fi

echo "4. 解压安装..."
tar -xzf clawdbot.tar.gz
chmod +x clawdbot/clawdbot

echo "5. 移动到系统路径..."
mv clawdbot/clawdbot $PREFIX/bin/
rm -rf clawdbot.tar.gz clawdbot/

echo "✅ 安装完成！"
echo ""
echo "使用命令："
echo "  clawdbot --version    # 查看版本"
echo "  clawdbot init         # 初始化配置"
echo ""
echo "💡 首次运行建议："
echo "   clawdbot init --model local  # 使用本地模型"
echo "   或配置国内模型 API"