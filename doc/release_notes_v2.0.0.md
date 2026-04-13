# AIR_Memory v2.0.0 发布说明

**发布日期**: 2026-04-10
**版本类型**: Major Release
**变更类型**: Breaking Change

---

## 概述

v2.0.0 是一次重大架构升级，系统部署方式从 **Docker + Nginx 双容器方案**彻底迁移为 **Python 本机直接运行单进程方案**。用户无需安装 Docker，仅需安装 Python 3.11+ 即可完成部署。此次变更显著降低了部署门槛，并节省约 3.7 GB 磁盘空间。

> **Breaking Change 说明**：v2.0.0 的部署方式与 v1.x 不兼容。从 v1.x 升级时需停止旧的 Docker 容器并按新方式重新部署，但**原有数据无需迁移**（`data/` 目录完整保留）。

---

## 主要变更

### 1. 放弃 Docker，改为 Python 本机直接运行

**变更前（v1.x）**：系统通过 `docker compose up` 启动，依赖 Docker Desktop 和 Nginx 容器。

**变更后（v2.0.0）**：系统通过 Python 虚拟环境（venv）直接运行 FastAPI（uvicorn），无需 Docker 或任何容器运行时。

- 环境前提从"安装 Docker Desktop"简化为"安装 Python 3.11+"
- FastAPI（uvicorn）在端口 `8080` 统一提供后端 API、MCP 服务和前端静态文件服务
- SPA 路由回退通过自定义 Starlette 异常处理器实现，前端页面刷新不再返回 404

### 2. 全新一键启动方式

| 平台 | 命令 | 说明 |
| --- | --- | --- |
| macOS / Linux | `bash start.sh` | 自动完成环境检查、venv 创建、依赖安装和服务启动 |
| Windows | `start.bat` | 同上（双击或 CMD 执行均可） |

启动脚本将依次执行：Python 版本检查 → venv 创建（首次）→ 依赖安装 → 环境变量配置 → uvicorn 启动。

### 3. 新增自启动安装功能

支持通过参数一键安装/卸载操作系统级自启动服务，无需手动配置：

| 平台 | 安装命令 | 卸载命令 | 实现方式 |
| --- | --- | --- | --- |
| macOS | `bash start.sh --install` | `bash start.sh --uninstall` | LaunchAgent（`~/Library/LaunchAgents/com.air-memory.plist`） |
| Windows | `start.bat /install` | `start.bat /uninstall` | Task Scheduler（`schtasks` 计划任务） |

### 4. 前端静态文件预构建随仓库分发

前端 Vue.js 3 应用已预先构建为静态文件（`frontend/dist/`）并随仓库一同分发。

- 用户部署时**无需安装 Node.js**，无需执行 `npm install` 或 `npm run build`
- FastAPI 通过 `StaticFiles` 直接挂载 `frontend/dist/` 目录对外提供服务

### 5. 磁盘空间节省约 3.7 GB

去除 Docker 镜像（后端镜像约 2.5 GB + Nginx 镜像约 0.2 GB + 构建层缓存约 1 GB）后，系统整体磁盘占用显著减少，在初始部署阶段节省约 **3.7 GB** 磁盘空间。

---

## 影响范围

| 平台 | 是否受影响 | 说明 |
| --- | --- | --- |
| macOS | 是 | 需重新部署，按 v2.0 部署步骤操作 |
| Windows | 是 | 需重新部署，按 v2.0 部署步骤操作 |

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.sh` | 重写 | 从 Docker 启动改为 Python venv 启动；新增 `--install` / `--uninstall` LaunchAgent 自启动支持 |
| `start.bat` | 重写 | 从 Docker 启动改为 Python venv 启动；新增 `/install` / `/uninstall` Task Scheduler 自启动支持 |
| `backend/main.py` | 修改 | 新增 `StaticFiles` 挂载（`frontend/dist/`）；新增 SPA 路由回退处理器 |
| `frontend/dist/` | 新增 | 预构建前端静态文件，随仓库分发 |
| `doc/sad_v1.11.md` | 更新 | 架构说明更新至 v1.11，反映 Python 本机直接运行方案 |
| `doc/deploy_guide.md` | 重写 | 部署手册更新至 v2.0，覆盖 macOS 和 Windows 完整新部署步骤 |

---

## 升级说明

### 从 v1.x 升级至 v2.0.0

> **原有数据（`data/` 目录）无需迁移**，完整保留所有记忆数据和日志。

**步骤一：停止旧服务**

```bash
docker compose stop
```

**步骤二：（可选）卸载 Docker 自启动**

如果 v1.x 配置了 Docker 自动重启策略，请确认旧容器已完全停止：

```bash
docker compose down
```

**步骤三：拉取最新代码**

```bash
git pull
```

**步骤四：按新方式启动**

macOS：

```bash
bash start.sh
```

Windows：

```cmd
start.bat
```

首次启动时，脚本将自动创建 Python 虚拟环境并安装依赖，约需 2～5 分钟，请耐心等待。

**步骤五：（可选）配置自启动**

如需系统重启后自动恢复运行，请参阅 `doc/deploy_guide.md` 第 5 节"自启动配置"。

---

## 注意事项

- Docker Desktop 在 v2.0.0 后**不再是必要依赖**，可根据个人需要选择是否保留
- `docker-compose.yml` 文件将在后续版本中移除，v2.0.0 保留但已废弃
- 如遇首次启动依赖安装失败，请参阅 `doc/deploy_guide.md` 第 8 节"常见问题排查"
