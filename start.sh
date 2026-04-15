#!/usr/bin/env bash
# ==============================================================================
# AIR_Memory 一键启动脚本（macOS / Linux）
# 用法：bash start.sh [--install | --uninstall]
#   --install    安装 macOS LaunchAgent 自启动
#   --uninstall  卸载 macOS LaunchAgent 自启动
# ==============================================================================

set -euo pipefail

# 切换到脚本所在目录（即项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PLIST_LABEL="com.air-memory"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

# ---------- 安装自启动 ----------
if [ "${1:-}" = "--install" ]; then
    echo "=========================================="
    echo " 安装 AIR_Memory LaunchAgent 自启动"
    echo "=========================================="

    PYTHON3=$(command -v python3 || true)
    if [ -z "$PYTHON3" ]; then
        echo "[错误] 未检测到 python3，请先安装 Python 3.11+。"
        exit 1
    fi

    cat > "$PLIST_PATH" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${SCRIPT_DIR}/start.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/data/air_memory.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/data/air_memory_error.log</string>
</dict>
</plist>
PLIST_EOF

    launchctl load "$PLIST_PATH"
    echo "[成功] AIR_Memory LaunchAgent 已安装，系统重启后将自动启动。"
    echo "       卸载自启动：bash start.sh --uninstall"
    exit 0
fi

# ---------- 卸载自启动 ----------
if [ "${1:-}" = "--uninstall" ]; then
    echo "=========================================="
    echo " 卸载 AIR_Memory LaunchAgent 自启动"
    echo "=========================================="
    if [ -f "$PLIST_PATH" ]; then
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        rm -f "$PLIST_PATH"
        echo "[成功] AIR_Memory LaunchAgent 已卸载。"
    else
        echo "[提示] 未找到已安装的 LaunchAgent，无需卸载。"
    fi
    exit 0
fi

# ---------- 正常启动 ----------
echo "=========================================="
echo " AIR_Memory 一键启动 v1.2.10"
echo "=========================================="

# 检查 Python 3.11+
PYTHON3=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(sys.version_info >= (3, 11))" 2>/dev/null || echo "False")
        if [ "$VER" = "True" ]; then
            PYTHON3="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON3" ]; then
    echo "[错误] 未检测到 Python 3.11+，请先安装。"
    echo "       macOS 安装：brew install python@3.11"
    echo "       官方下载：https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VER=$("$PYTHON3" --version)
echo "[检查] 使用 ${PYTHON_VER} (${PYTHON3})"

# 创建虚拟环境（如不存在）
if [ ! -d ".venv" ]; then
    echo "[1/4] 创建 Python 虚拟环境..."
    "$PYTHON3" -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装 / 更新依赖
echo "[2/4] 安装 Python 依赖（首次约 2~5 分钟）..."
python -m pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
pip install --quiet --no-deps -e backend/

# 准备数据目录
echo "[3/4] 准备数据目录..."
mkdir -p data/chroma_cold

# 设置环境变量（未设置时使用默认值）
export CHROMA_COLD_PATH="${CHROMA_COLD_PATH:-${SCRIPT_DIR}/data/chroma_cold}"
export DB_PATH="${DB_PATH:-${SCRIPT_DIR}/data/logs.db}"
export STATIC_DIR="${STATIC_DIR:-${SCRIPT_DIR}/frontend/dist}"
export HF_HOME="${HF_HOME:-${SCRIPT_DIR}/models}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-all-MiniLM-L6-v2}"
export HOT_MEMORY_BUDGET_MB="${HOT_MEMORY_BUDGET_MB:-6144}"
export DISK_TRIGGER_GB="${DISK_TRIGGER_GB:-38}"
export DISK_SAFE_GB="${DISK_SAFE_GB:-35}"
export DISK_MAX_GB="${DISK_MAX_GB:-40}"
export DISK_CHECK_INTERVAL_S="${DISK_CHECK_INTERVAL_S:-3600}"
export MEMORY_PROTECT_HOURS="${MEMORY_PROTECT_HOURS:-168}"
export PROMOTE_THRESHOLD="${PROMOTE_THRESHOLD:-0.6}"
export DEMOTE_THRESHOLD="${DEMOTE_THRESHOLD:-0.3}"
export INITIAL_VALUE_SCORE="${INITIAL_VALUE_SCORE:-0.6}"
export FEEDBACK_STEP="${FEEDBACK_STEP:-0.1}"
export HOT_COLLECTION="${HOT_COLLECTION:-hot_memories}"
export COLD_COLLECTION="${COLD_COLLECTION:-cold_memories}"
export STORE_RESPONSE_LIMIT_MS="${STORE_RESPONSE_LIMIT_MS:-100}"
export QUERY_RESPONSE_LIMIT_MS="${QUERY_RESPONSE_LIMIT_MS:-100}"
PORT="${PORT:-8080}"
# 强制 Python 使用 UTF-8 模式，确保中文内容在任何平台上均不因 locale 编码而损坏
# 注意：此处强制覆盖（不使用 ${:-} 默认值），防止系统设置 PYTHONUTF8=0 导致中文乱码
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

echo "[4/4] 启动 AIR_Memory 服务..."
echo ""
echo "=========================================="
echo " AIR_Memory 启动成功！"
echo "=========================================="
echo " Web 管理界面：http://localhost:${PORT}"
echo " 后端 API 文档：http://localhost:${PORT}/api/v1/docs"
echo " 停止服务：按 Ctrl+C"
echo "=========================================="
echo ""

# 启动 uvicorn
exec uvicorn air_memory.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --app-dir backend/src \
    --no-access-log \
    --log-level warning
