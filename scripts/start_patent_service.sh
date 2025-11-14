#!/bin/bash

# CNIPA发明专利高质量改写系统启动脚本
# 服务端口: 8082

set -e

echo "🚀 启动CNIPA发明专利高质量改写系统..."
echo "====================================="

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，将使用默认配置"
fi

# 检查端口是否被占用
if netstat -tuln 2>/dev/null | grep -q ':8082'; then
    echo "❌ 端口 8082 已被占用"
    echo "请检查是否有其他服务正在运行，或修改 .env 文件中的 PATENT_API_PORT 配置"
    exit 1
fi

# 设置Python路径（如果存在虚拟环境）
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 已激活虚拟环境"
fi

# 启动服务
echo "📝 正在启动服务..."
python patent_api_main.py

echo "✅ CNIPA发明专利高质量改写系统启动完成"
echo "📖 API文档: http://localhost:8082/docs"
echo "🔍 健康检查: http://localhost:8082/health"}