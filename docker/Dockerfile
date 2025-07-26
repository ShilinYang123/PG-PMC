FROM python:3.12.7-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 复制依赖文件
COPY docker/requirements.txt .

# 配置pip使用国内镜像源并安装Python依赖
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 300 --retries 3

# 先复制必要的配置文件
COPY project/ ./project/
COPY tools/ ./tools/
COPY data/ ./data/
COPY docs/ ./docs/

# 复制其他必要文件
COPY *.py ./
COPY *.md ./
COPY *.json ./
COPY *.yaml ./
COPY *.yml ./

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# 启动命令
CMD ["python", "tools/start.py"]