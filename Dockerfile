# Dockerfile for Railway/Render deployment
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements-cloud.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements-cloud.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 启动命令
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]