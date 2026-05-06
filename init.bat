@echo off
chcp 65001 >nul 2>&1
REM ==============================================================================
REM AIR_Memory 初始化脚本 (Windows)
REM 用法: 双击运行 init.bat,或在命令提示符中执行
REM 说明: 首次部署或迁移到新机器时执行一次,完成 Python 虚拟环境创建、依赖安装
REM       以及 Embedding 模型预下载。初始化完成后,整个目录可复制到相同 OS
REM       和 CPU 架构的其他计算机上直接运行(执行 start.bat 即可启动,无需联网)。
REM ==============================================================================

setlocal enabledelayedexpansion

REM 切换到脚本所在目录(即项目根目录)
cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
REM 去掉末尾斜杠
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"

echo ==========================================
echo  AIR_Memory 初始化 v1.3.0
echo ==========================================

REM ---------- 1. 检查 Python 3.11+ ----------
echo [1/4] 检查 Python 3.11+...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python,请先安装 Python 3.11+.
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 版本不满足要求,请安装 Python 3.11+.
    python --version
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo        使用 !PYVER!

REM ---------- 2. 创建虚拟环境 ----------
echo [2/4] 创建 Python 虚拟环境^(--copies 模式,支持目录迁移^)...
if exist ".venv" (
    echo        .venv 已存在,跳过创建。如需重建请先删除 .venv 目录.
) else (
    REM --copies: 将 Python 二进制复制而非符号链接,确保 venv 随目录迁移后仍可用
    python -m venv --copies .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败.
        pause
        exit /b 1
    )
    echo        虚拟环境创建成功.
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM ---------- 3. 安装 Python 依赖 ----------
echo [3/4] 安装 Python 依赖^(首次约 2^~5 分钟^)...
python -m pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败,请检查网络连接后重试.
    pause
    exit /b 1
)
pip install --quiet --no-deps -e backend\
echo        依赖安装完成.

REM ---------- 4. 预下载 Embedding 模型 ----------
echo [4/4] 预下载 Embedding 模型^(all-MiniLM-L6-v2,约 90 MB^)...
echo        模型将缓存至 !SCRIPT_DIR!\models\^(HF_HOME 指向项目目录^)

if not defined EMBEDDING_MODEL set "EMBEDDING_MODEL=all-MiniLM-L6-v2"
set "HF_HOME=!SCRIPT_DIR!\models"

python -c "import os,sys; model=os.environ.get('EMBEDDING_MODEL','all-MiniLM-L6-v2'); print(f'       正在下载模型 {model} ...'); from sentence_transformers import SentenceTransformer; SentenceTransformer(model); print('       模型下载完成.')"
if errorlevel 1 (
    echo [警告] 模型下载失败,请检查网络连接后重新运行本脚本.
    echo        或手动下载并放置到 .\models\ 目录.
    pause
    exit /b 1
)

REM ---------- 准备数据目录 ----------
if not exist "data\chroma_cold" mkdir "data\chroma_cold"

echo.
echo ==========================================
echo  AIR_Memory 初始化完成!
echo ==========================================
echo  后续启动: start.bat
echo  可移植性: 本目录可复制到相同 OS/架构的
echo             其他计算机,直接运行 start.bat
echo             即可启动,无需重新初始化.
echo ==========================================
pause
