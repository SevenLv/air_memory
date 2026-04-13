# 架构变更验证 - 放弃 Docker 改为 Python 本机直接运行

## 标签

架构变更, Docker, Python, uvicorn, FastAPI, StaticFiles, SPA, LaunchAgent, Task Scheduler, start.sh, start.bat, 验证, sad_v1.11, deploy_guide

## 变更概述

系统从 Docker + Nginx 双容器方案迁移到 Python 本机直接运行单进程方案:
- FastAPI (uvicorn) 在端口 8080 统一提供后端 API + 前端静态文件服务
- 前端 Vue.js 3 预构建产物 `frontend/dist/` 随仓库分发
- 自启动由 macOS LaunchAgent / Windows Task Scheduler 替代 Docker restart policy
- 启动脚本 `start.sh` / `start.bat` 改为 Python venv 方式

## 验证结论

### 1. 架构文档一致性验证 (sad_v1.11.md) - 通过（有小问题）

- 技术栈表格: Docker 相关条目已移除, 替换为 "Python 本机直接运行（uvicorn）" 和 "FastAPI StaticFiles"
- 部署架构图 (第9章): 已正确反映单进程方案（FastAPI Backend + StaticFiles 挂载）, 无 Nginx 层
- 需求分配表 (第13章): FR-DEP-001~004 已正确更新, 指向 Python 本机直接运行和 LaunchAgent/Task Scheduler
- **小问题**: M6-07 任务描述残留 "在容器运行时" 措辞 (应为 "在本机运行时"), 属于遗留 Docker 术语
- **注意**: `docker-compose.yml` 仍存在于仓库根目录 (旧 Docker 双容器配置), 未被删除, 可能引起混淆, 建议删除或添加废弃说明

### 2. 启动脚本功能验证 - 通过

- `start.sh`: 语法正确 (`bash -n` 验证通过)
  - 包含 Python 3.11/3.12/3.13 版本检测
  - 包含 venv 创建和依赖安装
  - 环境变量配置完整 (CHROMA_COLD_PATH, DB_PATH, STATIC_DIR)
  - uvicorn 启动配置正确 (端口 8080)
  - LaunchAgent --install/--uninstall 功能完整
- `start.bat`:
  - 包含 Python 版本检测和 venv 创建
  - 环境变量配置完整 (STATIC_DIR)
  - schtasks /install, /uninstall 自启动功能完整

### 3. 后端代码验证 (main.py) - 通过

- StaticFiles 挂载逻辑正确: 从 STATIC_DIR 环境变量读取目录, 默认 "frontend/dist"
- 目录不存在时跳过挂载 (os.path.isdir 判断)
- SPA 路由回退正确: 非 /api/ 和 /mcp 路径的 404 返回 index.html
- StaticFiles 挂载在所有 API 路由注册之后 (优先级正确)

### 4. 全量测试验证 - 通过

- 后端: 116 个测试全部通过 (含 test_main.py 静态文件和 SPA 路由回退测试)
- 前端: 77 个测试全部通过 (7个测试文件)

### 5. 前端静态文件验证 - 通过

- `frontend/dist/` 目录存在
- 包含 `index.html` 和 `assets/` 目录 (含 index-CCLemJ-_.js 1.07MB, index-ffyidUrc.css 355KB)

### 6. 产品定义符合性验证 (PDD v1.3) - 通过

- macOS 和 Windows 本地一键部署: 通过 (start.sh / start.bat)
- 系统自启动: 通过 (LaunchAgent / Task Scheduler)
- 部署手册完整: 通过 (deploy_guide.md v2.0 覆盖两平台完整步骤)
- 环境变量配置文档: 通过 (env_config.md v1.1 包含 PORT/STATIC_DIR/CORS_ORIGINS)

## 发现的问题

| 编号 | 严重等级 | 描述 | 建议 |
| --- | --- | --- | --- |
| ISSUE-01 | 次要 | `sad_v1.11.md` M6-07 描述残留 "在容器运行时" 措辞 | 改为 "在本机运行时" |
| ISSUE-02 | 次要 | `docker-compose.yml` 仍存在于仓库根目录 (旧 Docker 方案) | 删除或添加废弃说明 (DEPRECATED) |

## 总体验收结论

**通过（有次要问题）** - 架构变更正确、完整, 所有核心功能点验证通过; 发现 2 个次要问题均为文档/遗留文件问题, 不影响系统正常运行。
