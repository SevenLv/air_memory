#!/usr/bin/env bash
# ==============================================================================
# AIR_Memory 一键启动脚本（macOS / Linux）
# 用法：bash start.sh
# 首次运行将自动构建 Docker 镜像并启动所有服务
# ==============================================================================

set -euo pipefail

# 切换到脚本所在目录（即项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo " AIR_Memory 一键启动"
echo "=========================================="

# 检查 Docker 是否已安装并运行
if ! command -v docker &>/dev/null; then
    echo "[错误] 未检测到 Docker，请先安装 Docker Engine 27+ 或 Docker Desktop。"
    echo "       下载地址：https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "[错误] Docker 守护进程未运行，请先启动 Docker。"
    exit 1
fi

# 检查 docker compose（v2）是否可用
if ! docker compose version &>/dev/null; then
    echo "[错误] 未检测到 docker compose v2，请升级 Docker 至 27+ 或安装 Compose 插件。"
    exit 1
fi

echo "[1/3] 构建 Docker 镜像（首次构建耗时较长，约 5~15 分钟）..."
docker compose build

echo "[2/3] 启动所有服务..."
docker compose up -d

echo "[3/3] 等待服务就绪..."
sleep 5

# 检查容器运行状态
BACKEND_STATUS=$(docker compose ps --status running --format "{{.Name}}" 2>/dev/null | grep "backend" || true)
FRONTEND_STATUS=$(docker compose ps --status running --format "{{.Name}}" 2>/dev/null | grep "frontend" || true)

if [ -n "$BACKEND_STATUS" ] && [ -n "$FRONTEND_STATUS" ]; then
    echo ""
    echo "=========================================="
    echo " 启动成功！"
    echo "=========================================="
    echo " Web 管理界面：http://localhost:8080"
    echo " 后端 API 文档：http://localhost:8080/api/v1/docs (通过 Nginx 代理)"
    echo " 停止服务：docker compose stop"
    echo " 查看日志：docker compose logs -f"
    echo "=========================================="
else
    echo ""
    echo "[警告] 部分服务可能未正常启动，请检查日志："
    docker compose ps
    echo ""
    echo "查看详细日志：docker compose logs"
fi
