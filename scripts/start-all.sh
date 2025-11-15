#!/bin/bash

# 同时启动两个系统
echo "==================================="
echo "启动智能文稿改写系统 - 双系统模式"
echo "==================================="
echo ""
echo "📰 新闻系统: http://localhost:8081/docs"
echo "📄 专利系统: http://localhost:8082/docs"
echo ""
echo "提示: 使用 Ctrl+C 停止所有服务"
echo ""

# 启动新闻系统(后台运行)
echo "[1/2] 启动新闻系统(端口8081)..."
python news_api_main.py > logs/news.log 2>&1 &
NEWS_PID=$!

# 等待新闻系统启动
sleep 3

# 启动专利系统(后台运行)
echo "[2/2] 启动专利系统(端口8082)..."
python patent_api_main.py > logs/patent.log 2>&1 &
PATENT_PID=$!

# 等待专利系统启动
sleep 3

echo ""
echo "✅ 两个系统已启动!"
echo "   新闻系统 PID: $NEWS_PID"
echo "   专利系统 PID: $PATENT_PID"
echo ""
echo "查看日志:"
echo "   tail -f logs/news.log"
echo "   tail -f logs/patent.log"
echo ""

# 等待用户中断
trap "echo '正在停止服务...'; kill $NEWS_PID $PATENT_PID; exit" INT TERM

# 保持脚本运行
wait
