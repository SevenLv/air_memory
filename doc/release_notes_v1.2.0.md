# AIR_Memory v1.2.0 发布说明

**发布日期**: 2026-04-14
**版本类型**: Minor Release

---

## 概述

v1.2.0 修复了两个影响用户体验的问题: 启动脚本显示的 UI 地址在浏览器无法直接访问, 以及系统各处均未显示版本号. 本次发布不包含任何 Breaking Change, 直接升级即可.

---

## 修复问题

### 1. 启动脚本提示的 UI 地址无法在浏览器访问 (Issue #28)

**问题描述**

执行 `start.bat` 或 `start.sh` 启动服务后, uvicorn 在控制台打印 `http://0.0.0.0:8080`, 将该地址复制至浏览器后无法访问.

**根因分析**

uvicorn 以 `--host 0.0.0.0` 绑定时, 其自身日志打印的是监听绑定地址 `http://0.0.0.0:8080`. 该地址表示"监听所有网络接口", 不是一个可在浏览器直接访问的 URL.

**修复方案**

将 `start.bat` 和 `start.sh` 中的 uvicorn 启动参数由 `--host 0.0.0.0` 改为 `--host 127.0.0.1`. 修改后 uvicorn 日志打印 `http://127.0.0.1:8080`, 与脚本 echo 的 `http://localhost:PORT` 语义一致, 均可直接在浏览器打开.

---

### 2. UI 和启动脚本未显示系统版本号 (Issue #27)

**问题描述**

启动脚本 Banner 和 Web 管理界面均未显示当前系统版本号, 用户无法确认运行的是哪个版本.

**修复方案**

- **后端**: 新增 `APP_VERSION` 常量作为版本号唯一来源, 同步更新 FastAPI 元数据版本号, 并新增 `GET /api/v1/version` 端点供前端查询.
- **前端**: 管理界面 Header 右侧动态显示版本号 (通过 `/api/v1/version` 接口获取), 获取失败时静默处理, 不影响主功能.
- **启动脚本**: `start.bat` 和 `start.sh` Banner 中新增版本号显示.

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 修复 | uvicorn host 改为 `127.0.0.1`; Banner 新增版本号 v1.2.0 |
| `start.sh` | 修复 | uvicorn host 改为 `127.0.0.1`; Banner 新增版本号 v1.2.0 |
| `backend/src/air_memory/main.py` | 修复 | 新增 `APP_VERSION = "1.2.0"` 常量; FastAPI 元数据引用常量; 新增 `GET /api/v1/version` 端点 |
| `backend/pyproject.toml` | 修复 | version 同步至 `1.2.0` |
| `frontend/src/api/types.ts` | 修复 | 新增 `AppVersion` 接口 |
| `frontend/src/api/index.ts` | 修复 | 新增 `getVersion()` 函数 |
| `frontend/src/App.vue` | 修复 | Header 动态显示版本号 |
| `frontend/package.json` | 修复 | version 同步至 `1.2.0` |
| `frontend/dist/` | 重构建 | 前端重新构建产物 |

---

## 升级说明

直接拉取最新代码并重新启动即可:

```bash
git pull
```

**macOS / Linux**:

```bash
bash start.sh
```

**Windows**:

```cmd
start.bat
```

升级不影响已有数据, `data/` 目录完整保留.
