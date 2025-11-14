#!/bin/bash

# 服务分离验证测试脚本
# 自动验证两个服务是否完全分离运行

set -e

echo "🔍 运行服务分离验证测试..."
echo "===================================="

# 检查Python环境
if ! command -v python3 > /dev/null 2>&1; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查服务是否运行
NEWS_RUNNING=false
PATENT_RUNNING=false

if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    NEWS_RUNNING=true
    echo "✅ 东方烟草报风格改写系统正在运行"
fi

if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    PATENT_RUNNING=true
    echo "✅ CNIPA发明专利高质量改写系统正在运行"
fi

if [ "$NEWS_RUNNING" = false ] && [ "$PATENT_RUNNING" = false ]; then
    echo "❌ 两个服务都未运行"
    echo "请先启动服务，然后运行此脚本"
    exit 1
fi

# 运行Python验证脚本
echo ""
echo "🧪 执行Python验证脚本..."
if python3 scripts/validate_service_separation.py; then
    echo ""
    echo "🎉 所有验证测试通过！"
    echo "✅ 服务分离验证成功"
else
    echo ""
    echo "❌ 验证测试失败"
    echo "请查看错误信息并修复问题"
    exit 1
fi

# 可选：运行额外的端口检查
echo ""
echo "🔍 检查端口占用情况..."
if command -v netstat > /dev/null 2>&1; then
    echo "端口监听状态:"
    netstat -tuln | grep -E ':8081|:8082' || echo "未找到监听中的服务端口"
fi

echo ""
echo "📊 验证完成总结:"
echo "===================================="
if [ "$NEWS_RUNNING" = true ]; then
    echo "✅ 东方烟草报风格改写系统 - 运行正常 (端口 8081)"
fi
if [ "$PATENT_RUNNING" = true ]; then
    echo "✅ CNIPA发明专利高质量改写系统 - 运行正常 (端口 8082)"
fi
echo ""
echo "🔗 服务访问链接:"
echo "   📰 新闻系统: http://localhost:8081/docs"
echo "   📋 专利系统: http://localhost:8082/docs"