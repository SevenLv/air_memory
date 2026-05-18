#!/usr/bin/env bash
# ==============================================================================
# AIR_Memory 启动脚本（macOS / Linux）
# 用法：bash start.sh [--install | --uninstall]
#   --install    安装 macOS LaunchAgent 自启动
#   --uninstall  卸载 macOS LaunchAgent 自启动
# 说明：首次部署请先运行 init.sh 完成环境初始化，再使用本脚本启动服务。
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
echo " AIR_Memory 启动 v1.5.1"
echo "=========================================="

# 检查虚拟环境是否已初始化
if [ ! -d ".venv" ]; then
    echo "[错误] 未检测到 Python 虚拟环境（.venv），请先运行初始化脚本："
    echo "       bash init.sh"
    exit 1
fi

# 检查 Embedding 模型是否已预下载
if [ ! -d "models/hub" ]; then
    echo "[错误] 未检测到已预下载的 Embedding 模型，请先运行初始化脚本："
    echo "       bash init.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量（未设置时使用默认值）
export CHROMA_COLD_PATH="${CHROMA_COLD_PATH:-${SCRIPT_DIR}/data/chroma_cold}"
export DB_PATH="${DB_PATH:-${SCRIPT_DIR}/data/logs.db}"
export STATIC_DIR="${STATIC_DIR:-${SCRIPT_DIR}/frontend/dist}"
# 强制覆盖 HF_HOME（不使用 ${:-} 默认值），确保始终指向项目内 models/ 目录
# init.sh 将模型缓存到此目录；若此处改为条件赋值，当系统/用户已设置 HF_HOME 指向其他路径时
# start.sh 会在错误位置查找模型，导致重新下载
export HF_HOME="${SCRIPT_DIR}/models"
# 强制覆盖 HF_HUB_CACHE（不使用 ${:-} 默认值）
# huggingface_hub 解析顺序：HF_HUB_CACHE > HUGGINGFACE_HUB_CACHE > HF_HOME/hub
# 若用户系统已设置 HF_HUB_CACHE 指向其他路径，仅设置 HF_HOME 并不能覆盖实际缓存位置
# 因此必须同时强制覆盖 HF_HUB_CACHE，确保模型缓存与 init.sh 预下载位置一致
export HF_HUB_CACHE="${SCRIPT_DIR}/models/hub"
# 强制启用离线模式（不使用 ${:-} 默认值），防止 sentence_transformers/huggingface_hub 在启动时
# 向 HuggingFace Hub 发起网络请求（即便模型已缓存，默认行为仍会进行版本更新检查并可能重新下载）
# init.sh 负责预下载模型；start.sh 只使用本地缓存，无需联网
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
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

echo ""
echo "=========================================="
echo " AIR_Memory 启动成功！"
echo "=========================================="
echo " Web 管理界面：http://localhost:${PORT}"
echo " 后端 API 文档：http://localhost:${PORT}/api/v1/docs"
echo " 停止服务：按 Ctrl+C"
echo "=========================================="
echo ""

# 使用 python -m uvicorn 避免依赖 PATH 中的 shebang 绝对路径
exec python -m uvicorn air_memory.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    --app-dir backend/src \
    --no-access-log \
    --log-level warning
