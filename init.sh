#!/usr/bin/env bash
# ==============================================================================
# AIR_Memory 初始化脚本（macOS / Linux）
# 用法：bash init.sh
# 说明：首次部署或迁移到新机器时执行一次，完成 Python 虚拟环境创建、依赖安装
#       以及 Embedding 模型预下载。初始化完成后，整个目录可复制到相同 OS
#       和 CPU 架构的其他计算机上直接运行（执行 start.sh 即可启动，无需联网）。
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo " AIR_Memory 初始化 v1.3.0"
echo "=========================================="

# ---------- 1. 检查 Python 3.11+ ----------
echo "[1/4] 检查 Python 3.11+..."
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
    echo "[错误] 未检测到 Python 3.11+，请先安装后重新运行本脚本。"
    echo "       macOS 安装：brew install python@3.11"
    echo "       官方下载：https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VER=$("$PYTHON3" --version)
echo "       使用 ${PYTHON_VER} (${PYTHON3})"

# ---------- 2. 创建虚拟环境 ----------
echo "[2/4] 创建 Python 虚拟环境（--copies 模式，支持目录迁移）..."
if [ -d ".venv" ]; then
    echo "       .venv 已存在，跳过创建。如需重建请先删除 .venv 目录。"
else
    # --copies：将 Python 二进制复制而非符号链接，确保 venv 随目录迁移后仍可用
    "$PYTHON3" -m venv --copies .venv
    echo "       虚拟环境创建成功。"
fi

# 激活虚拟环境
source .venv/bin/activate

# ---------- 3. 安装 Python 依赖 ----------
echo "[3/4] 安装 Python 依赖（首次约 2~5 分钟）..."
python -m pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
pip install --quiet --no-deps -e backend/
echo "       依赖安装完成。"

# ---------- 4. 预下载 Embedding 模型 ----------
echo "[4/4] 预下载 Embedding 模型（all-MiniLM-L6-v2，约 90 MB）..."
echo "       模型将缓存至 ${SCRIPT_DIR}/models/（HF_HOME 指向项目目录）"

export HF_HOME="${SCRIPT_DIR}/models"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-all-MiniLM-L6-v2}"

python - <<'PYEOF'
import os, sys
model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
try:
    from sentence_transformers import SentenceTransformer
    print(f"       正在下载模型 {model_name} ...")
    SentenceTransformer(model_name)
    print("       模型下载完成。")
except Exception as e:
    print(f"[警告] 模型下载失败：{e}", file=sys.stderr)
    print("       请检查网络连接后重新运行本脚本，或手动下载并放置到 ./models/ 目录。", file=sys.stderr)
    sys.exit(1)
PYEOF

# ---------- 准备数据目录 ----------
mkdir -p data/chroma_cold

echo ""
echo "=========================================="
echo " AIR_Memory 初始化完成！"
echo "=========================================="
echo " 后续启动：bash start.sh"
echo " 可移植性：本目录可复制到相同 OS/架构的"
echo "            其他计算机，直接运行 start.sh"
echo "            即可启动，无需重新初始化。"
echo "=========================================="
