@echo off
chcp 65001 >nul 2>&1
REM ==============================================================================
REM AIR_Memory 一键启动脚本 (Windows)
REM 用法: 双击运行 start.bat,或在命令提示符中执行
REM   start.bat          正常启动
REM   start.bat /install   安装 Task Scheduler 自启动(需管理员权限)
REM   start.bat /uninstall 卸载 Task Scheduler 自启动(需管理员权限)
REM ==============================================================================

setlocal enabledelayedexpansion

REM 切换到脚本所在目录(即项目根目录)
cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
REM 去掉末尾斜杠
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"

REM ---------- 安装自启动 ----------
if /i "%1"=="/install" goto :install_task
if /i "%1"=="/uninstall" goto :uninstall_task

REM ---------- 正常启动 ----------
echo ==========================================
echo  AIR_Memory 一键启动 v1.2.5
echo ==========================================

REM 检查 Python 3.11+
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python,请先安装 Python 3.11+.
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 Python 版本是否 >= 3.11
python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 版本不满足要求,请安装 Python 3.11+.
    python --version
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo [检查] 使用 !PYVER!

REM 创建虚拟环境(如不存在)
if not exist ".venv" (
    echo [1/4] 创建 Python 虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败.
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 安装/更新依赖
echo [2/4] 安装 Python 依赖^(首次约 2^~5 分钟^)...
python -m pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败,请检查网络连接后重试.
    pause
    exit /b 1
)
pip install --quiet --no-deps -e backend\

REM 准备数据目录
echo [3/4] 准备数据目录...
if not exist "data\chroma_cold" mkdir "data\chroma_cold"

REM 设置环境变量(未设置时使用默认值)
if not defined CHROMA_COLD_PATH set "CHROMA_COLD_PATH=!SCRIPT_DIR!\data\chroma_cold"
if not defined DB_PATH set "DB_PATH=!SCRIPT_DIR!\data\logs.db"
if not defined STATIC_DIR set "STATIC_DIR=!SCRIPT_DIR!\frontend\dist"
if not defined HF_HOME set "HF_HOME=!SCRIPT_DIR!\models"
if not defined EMBEDDING_MODEL set "EMBEDDING_MODEL=all-MiniLM-L6-v2"
if not defined HOT_MEMORY_BUDGET_MB set "HOT_MEMORY_BUDGET_MB=6144"
if not defined DISK_TRIGGER_GB set "DISK_TRIGGER_GB=38"
if not defined DISK_SAFE_GB set "DISK_SAFE_GB=35"
if not defined DISK_MAX_GB set "DISK_MAX_GB=40"
if not defined DISK_CHECK_INTERVAL_S set "DISK_CHECK_INTERVAL_S=3600"
if not defined MEMORY_PROTECT_HOURS set "MEMORY_PROTECT_HOURS=168"
if not defined PROMOTE_THRESHOLD set "PROMOTE_THRESHOLD=0.6"
if not defined DEMOTE_THRESHOLD set "DEMOTE_THRESHOLD=0.3"
if not defined INITIAL_VALUE_SCORE set "INITIAL_VALUE_SCORE=0.6"
if not defined FEEDBACK_STEP set "FEEDBACK_STEP=0.1"
if not defined HOT_COLLECTION set "HOT_COLLECTION=hot_memories"
if not defined COLD_COLLECTION set "COLD_COLLECTION=cold_memories"
if not defined STORE_RESPONSE_LIMIT_MS set "STORE_RESPONSE_LIMIT_MS=100"
if not defined QUERY_RESPONSE_LIMIT_MS set "QUERY_RESPONSE_LIMIT_MS=100"
if not defined PORT set "PORT=8080"
REM 强制 Python 使用 UTF-8 模式,确保中文内容在 Windows 上不因 ANSI 代码页而损坏
REM chcp 65001 仅影响控制台 OEM 代码页(CMD 显示),不影响 Python 的 locale 感知编码
REM PYTHONUTF8=1 才能覆盖 locale.getpreferredencoding() 并修正 open() 默认编码
if not defined PYTHONUTF8 set "PYTHONUTF8=1"
if not defined PYTHONIOENCODING set "PYTHONIOENCODING=utf-8"

echo [4/4] 启动 AIR_Memory 服务...
echo.
echo ==========================================
echo  AIR_Memory 启动成功!
echo ==========================================
echo  Web 管理界面: http://localhost:!PORT!
echo  后端 API 文档: http://localhost:!PORT!/api/v1/docs
echo  停止服务: 关闭此窗口或按 Ctrl+C
echo ==========================================
echo.

uvicorn air_memory.main:app --host 127.0.0.1 --port !PORT! --app-dir backend\src --no-access-log
goto :eof

REM ---------- 安装 Task Scheduler 自启动 ----------
:install_task
echo ==========================================
echo  安装 AIR_Memory Task Scheduler 自启动
echo ==========================================

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 需要管理员权限,请以管理员身份运行命令提示符后重试.
    pause
    exit /b 1
)

set "TASK_NAME=AIR_Memory"
set "TASK_CMD=%~f0"

schtasks /create /tn "!TASK_NAME!" /tr "\"!TASK_CMD!\"" /sc ONLOGON /ru "%USERNAME%" /f >nul 2>&1
if errorlevel 1 (
    echo [错误] Task Scheduler 任务创建失败.
    pause
    exit /b 1
)

echo [成功] AIR_Memory 自启动任务已安装,用户登录后将自动启动.
echo        卸载自启动: start.bat /uninstall
pause
goto :eof

REM ---------- 卸载 Task Scheduler 自启动 ----------
:uninstall_task
echo ==========================================
echo  卸载 AIR_Memory Task Scheduler 自启动
echo ==========================================

set "TASK_NAME=AIR_Memory"

schtasks /delete /tn "!TASK_NAME!" /f >nul 2>&1
if errorlevel 1 (
    echo [提示] 未找到已安装的任务,无需卸载.
) else (
    echo [成功] AIR_Memory 自启动任务已卸载.
)
pause
goto :eof
