@echo off
chcp 65001 >nul 2>&1
REM ==============================================================================
REM AIR_Memory 一键启动脚本(Windows)
REM 用法:双击运行 start.bat,或在命令提示符中执行 start.bat
REM 首次运行将自动构建 Docker 镜像并启动所有服务
REM ==============================================================================

setlocal enabledelayedexpansion

REM 切换到脚本所在目录(即项目根目录)
cd /d "%~dp0"

echo ==========================================
echo  AIR_Memory 一键启动
echo ==========================================

REM 检查 Docker 是否已安装
where docker >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker,请先安装 Docker Desktop.
    echo        下载地址:https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM 检查 Docker 守护进程是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 守护进程未运行,请先启动 Docker Desktop.
    pause
    exit /b 1
)

REM 检查 docker compose v2 是否可用
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 docker compose v2,请升级 Docker Desktop 至最新版本.
    pause
    exit /b 1
)

echo [1/3] 构建 Docker 镜像(首次构建耗时较长,约 5~15 分钟)...
docker compose build
if errorlevel 1 (
    echo [错误] 镜像构建失败,请检查网络连接并重试.
    pause
    exit /b 1
)

echo [2/3] 启动所有服务...
docker compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败,请查看日志:docker compose logs
    pause
    exit /b 1
)

echo [3/3] 等待服务就绪...
timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo  启动成功!
echo ==========================================
echo  Web 管理界面:http://localhost:8080
echo  停止服务:docker compose stop
echo  查看日志:docker compose logs -f
echo ==========================================
echo.

pause
