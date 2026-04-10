# ==============================================================================
# AIR_Memory Backend Dockerfile
# 基于 Python 3.11 slim，安装依赖，预下载 Embedding 模型
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# 安装编译时系统依赖（chromadb 等需要 C 扩展）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖文件以利用 Docker 构建缓存
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

# 安装 Python 依赖及后端包
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --no-deps -e .

# 预下载 Embedding 模型（all-MiniLM-L6-v2），打包进镜像避免运行时联网
# HF_HOME 指定模型缓存目录，运行时保持一致
ENV HF_HOME=/app/models

# 构建参数：PREDOWNLOAD_MODEL=true（默认）时在构建期下载模型；
# 设为 false 可跳过（用于无网络的 CI 环境），运行时仍需确保模型可用
ARG PREDOWNLOAD_MODEL=true
RUN if [ "$PREDOWNLOAD_MODEL" = "true" ]; then \
        python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"; \
    fi

# 创建数据目录（冷层 ChromaDB + SQLite）
RUN mkdir -p /app/data

# 暴露服务端口
EXPOSE 8000

# 启动后端服务
CMD ["uvicorn", "air_memory.main:app", "--host", "0.0.0.0", "--port", "8000"]
