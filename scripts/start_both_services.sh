#!/bin/bash

# 同时启动两个服务的脚本
# 东方烟草报系统: 8081
# CNIPA专利系统: 8082

set -e

echo "🚀 同时启动两个服务系统..."
echo "===================================="
echo "📰 东方烟草报风格改写系统将运行在端口 8081"
echo "📋 CNIPA发明专利高质量改写系统将运行在端口 8082"
echo ""

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，将使用默认配置"
fi

# 检查端口是否被占用
for port in 8081 8082; do
    if netstat -tuln 2>/dev/null | grep -q ":$port"; then
        echo "❌ 端口 $port 已被占用"
        echo "请检查是否有其他服务正在运行，或修改 .env 文件中的端口配置"
        exit 1
    fi
done

# 设置Python路径（如果存在虚拟环境）
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 已激活虚拟环境"
fi

# 启动新闻服务（后台）
echo "📝 正在启动东方烟草报风格改写系统..."
nohup python news_api_main.py > news_service.log 2>&1 &
NEWS_PID=$!
echo "✅ 新闻服务已启动，PID: $NEWS_PID"

# 等待新闻服务启动
sleep 3

# 启动专利服务（后台）
echo "📝 正在启动CNIPA发明专利高质量改写系统..."
nohup python patent_api_main.py > patent_service.log 2>&1 &
PATENT_PID=$!
echo "✅ 专利服务已启动，PID: $PATENT_PID"

# 等待两个服务都启动
sleep 5

# 验证服务是否正常运行
echo ""
echo "🔍 验证服务状态..."

# 检查新闻服务
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ 东方烟草报风格改写系统运行正常"
else
    echo "❌ 东方烟草报风格改写系统启动失败"
    kill $NEWS_PID 2>/dev/null || true
    kill $PATENT_PID 2>/dev/null || true
    exit 1
fi

# 检查专利服务
if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    echo "✅ CNIPA发明专利高质量改写系统运行正常"
else
    echo "❌ CNIPA发明专利高质量改写系统启动失败"
    kill $NEWS_PID 2>/dev/null || true
    kill $PATENT_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 两个服务都已成功启动！"
echo "===================================="
echo "📰 东方烟草报风格改写系统:"
echo "   - 服务地址: http://localhost:8081"
echo "   - API文档: http://localhost:8081/docs"
echo "   - 健康检查: http://localhost:8081/health"
echo "   - 日志文件: news_service.log"
echo ""
echo "📋 CNIPA发明专利高质量改写系统:"
echo "   - 服务地址: http://localhost:8082"
echo "   - API文档: http://localhost:8082/docs"
echo "   - 健康检查: http://localhost:8082/health"
echo "   - 日志文件: patent_service.log"
echo ""
echo "🔧 管理命令:"
echo "   - 停止新闻服务: kill $NEWS_PID"
echo "   - 停止专利服务: kill $PATENT_PID"
echo "   - 停止两个服务: kill $NEWS_PID $PATENT_PID"
echo ""
echo "🧪 运行验证测试:"
echo "   python scripts/validate_service_separation.py"

# 保存PID到文件
echo $NEWS_PID > news_service.pid
echo $PATENT_PID > patent_service.pid

echo ""
echo "服务PID已保存到 news_service.pid 和 patent_service.pid"