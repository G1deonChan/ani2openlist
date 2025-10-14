FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY ani2openlist/ ./ani2openlist/
COPY webui/ ./webui/
COPY run.py .
COPY webui_start.py .
COPY config.yaml.example ./config.yaml.example

# 创建必要的目录
RUN mkdir -p logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露 Web UI 端口（默认 5000）
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# 默认启动 Web UI
CMD ["python", "webui_start.py"]
