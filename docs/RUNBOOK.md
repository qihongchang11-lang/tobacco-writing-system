# RUNBOOK（Windows）

## 启动服务
```bash
cd %USERPROFILE%\tobacco-writing-pipeline
.\.venv\Scripts\activate
python -m uvicorn api_main:app --host 0.0.0.0 --port 8081 --log-level info --reload
```

## 健康检查
```bash
curl http://localhost:8081/health
```

## 改写测试
```bash
curl -X POST http://localhost:8081/rewrite \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"测试文本\",\"column_id\":\"news_general\"}"
```

## 停止服务
- Ctrl+C 在运行终端
- 或使用任务管理器结束 Python 进程

## 日志位置
- 终端输出（实时）
- logs/app.log（如已配置）

## 故障排查
1. 端口 8081 被占用：`netstat -ano | findstr :8081`
2. 虚拟环境未激活：检查提示符是否显示 (.venv)
3. 依赖缺失：`pip install -r requirements.txt`
