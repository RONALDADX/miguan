#!/data/data/com.termux/files/usr/bin/bash
echo "📱 中兴手机 Clawdbot 安装脚本"
echo "============================"

# 检测中兴手机特性
echo "检测系统信息："
uname -a
echo "CPU架构：$(getprop ro.product.cpu.abi)"

# 中兴手机可能需要的特殊处理
ZTE_MODEL=$(getprop ro.product.model)
echo "手机型号：$ZTE_MODEL"

# 检查存储权限（中兴可能限制严格）
if [ ! -w "$HOME" ]; then
    echo "⚠️  存储权限可能受限"
    echo "建议："
    echo "1. 给 Termux 存储权限"
    echo "2. 或在设置中允许访问文件"
fi

echo ""
echo "1. 配置适合中兴的源..."
# 使用多个国内源，提高成功率
cat > $PREFIX/etc/apt/sources.list << 'EOF'
# 清华源（主）
deb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main
# 北外源（备）
deb https://mirrors.bfsu.edu.cn/termux/apt/termux-main stable main
# 南京大学源（备）
deb https://mirror.nju.edu.cn/termux/apt/termux-main stable main
EOF

echo "2. 更新系统（可能需要耐心）..."
pkg update -y
if [ $? -ne 0 ]; then
    echo "⚠️  更新失败，尝试跳过..."
fi

echo "3. 安装最小依赖..."
# 先装curl和wget，用于下载
pkg install curl wget -y

echo "4. 检测网络环境..."
# 测试国内网站连通性
if curl -s --connect-timeout 5 https://www.baidu.com > /dev/null; then
    echo "✅ 可以访问国内网络"
    USE_CN_MIRROR=true
else
    echo "⚠️  国内网络访问可能受限"
    USE_CN_MIRROR=false
fi

echo "5. 安装 Node.js..."
if [ "$USE_CN_MIRROR" = true ]; then
    # 使用国内npm镜像
    npm config set registry https://registry.npmmirror.com
    npm config set disturl https://npmmirror.com/dist
    npm config set electron_mirror https://npmmirror.com/mirrors/electron/
fi

pkg install nodejs -y

echo "6. 安装 Clawdbot（使用国内CDN）..."
# 尝试多种安装方式
INSTALLED=false

# 方式1：直接npm安装
echo "尝试方式1: npm install..."
npm install -g clawdbot@latest && INSTALLED=true

# 方式2：使用cnpm
if [ "$INSTALLED" = false ]; then
    echo "方式1失败，尝试方式2: cnpm..."
    npm install -g cnpm --registry=https://registry.npmmirror.com
    cnpm install -g clawdbot && INSTALLED=true
fi

# 方式3：下载预编译包
if [ "$INSTALLED" = false ]; then
    echo "方式2失败，尝试方式3: 预编译包..."
    
    # 根据CPU架构选择
    ARCH=$(uname -m)
    case $ARCH in
        aarch64|arm64)
            FILE="clawdbot-linux-arm64"
            ;;
        armv7l|armv8l)
            FILE="clawdbot-linux-armv7"
            ;;
        x86_64)
            FILE="clawdbot-linux-x64"
            ;;
        *)
            echo "❌ 不支持的架构: $ARCH"
            exit 1
            ;;
    esac
    
    echo "下载 $FILE.tar.gz..."
    
    # 尝试多个国内镜像
    MIRRORS=(
        "https://ghproxy.com/https://github.com/clawdbot/clawdbot/releases/latest/download/$FILE.tar.gz"
        "https://gh.api.99988866.xyz/https://github.com/clawdbot/clawdbot/releases/latest/download/$FILE.tar.gz"
        "https://github.91chi.fun/https://github.com/clawdbot/clawdbot/releases/latest/download/$FILE.tar.gz"
        "https://pd.zwc365.com/seturl/https://github.com/clawdbot/clawdbot/releases/latest/download/$FILE.tar.gz"
    )
    
    for url in "${MIRRORS[@]}"; do
        echo "尝试: $url"
        if wget -O "$FILE.tar.gz" "$url"; then
            echo "✅ 下载成功"
            tar -xzf "$FILE.tar.gz"
            mv "$FILE/clawdbot" $PREFIX/bin/
            chmod +x $PREFIX/bin/clawdbot
            rm -rf "$FILE" "$FILE.tar.gz"
            INSTALLED=true
            break
        fi
    done
fi

if [ "$INSTALLED" = true ]; then
    echo ""
    echo "🎉 安装成功！"
    echo "版本: $(clawdbot --version 2>/dev/null || echo '请运行 clawdbot --version')"
    echo ""
    echo "📋 使用指南："
    echo "1. 初始化: clawdbot init"
    echo "2. 启动服务: clawdbot start"
    echo "3. 访问网页: http://localhost:18888"
    echo ""
    echo "💡 中兴手机提示："
    echo "- 确保给 Termux '存储' 权限"
    echo "- 关闭电池优化（防止后台被杀）"
    echo "- 可能需要允许后台运行"
else
    echo ""
    echo "❌ 所有安装方式都失败了"
    echo ""
    echo "🔧 备用方案："
    echo "1. 使用电脑下载，通过USB传到手机"
    echo "2. 尝试安装 'Aid Learning' 应用"
    echo "3. 考虑使用云服务器部署"
fi