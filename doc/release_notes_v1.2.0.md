# AIR_Memory v1.2.0 发布说明

**发布日期**: 2026-04-14
**版本类型**: Minor Release

---

## 概述

v1.2.0 修复了四个影响用户体验的问题: 启动脚本显示的 UI 地址在浏览器无法直接访问、系统各处均未显示版本号、.gitignore 缺失运行时目录配置、以及 Windows 上随 CMD 控制台输出浏览器任务栏不断闪烁的问题. 本次发布不包含任何 Breaking Change, 直接升级即可.

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

### 3. .gitignore 未忽略 data 和 models 目录 (Issue #29)

**问题描述**

`.gitignore` 中未配置 `data/` 和 `models/` 目录的忽略规则. 这两个目录在服务首次启动时自动创建, 属于运行时数据, 不应纳入版本控制.

**修复方案**

在 `.gitignore` 中追加 `data/` 和 `models/` 规则.

---

### 4. Windows 上浏览器在切换到别的程序时不断激活 (Issue #30)

**问题描述**

在 Windows 上使用 Edge 浏览器访问管理 UI, 切换到其他程序后, 任务栏的 AIR Memory 相关窗口持续闪烁, 干扰正常使用.

**根因分析**

uvicorn 默认开启访问日志 (access log), 每次 HTTP 请求都会向 CMD 控制台写入一行日志. 在 Windows 上, 后台控制台窗口收到新输出时, Windows 会调用 `FlashWindowEx(FLASHW_TRAY)` 使该窗口的任务栏按钮橙色闪烁. 由于 Vue 前端每次导航和加载都会触发多个 HTTP 请求, 闪烁频繁出现, 用户将其感知为"浏览器不断激活自身". 此行为是 Windows 专属行为.

**修复方案**

在 `start.bat` 和 `start.sh` 中的 uvicorn 启动命令追加 `--no-access-log` 参数. 服务启动信息和 WARNING/ERROR 级别日志仍正常输出, 不影响调试能力.

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 修复 | uvicorn host 改为 `127.0.0.1`; Banner 新增版本号 v1.2.0; 新增 `--no-access-log` |
| `start.sh` | 修复 | uvicorn host 改为 `127.0.0.1`; Banner 新增版本号 v1.2.0; 新增 `--no-access-log` |
| `backend/src/air_memory/main.py` | 修复 | 新增 `APP_VERSION = "1.2.0"` 常量; FastAPI 元数据引用常量; 新增 `GET /api/v1/version` 端点 |
| `backend/pyproject.toml` | 修复 | version 同步至 `1.2.0` |
| `frontend/src/api/types.ts` | 修复 | 新增 `AppVersion` 接口 |
| `frontend/src/api/index.ts` | 修复 | 新增 `getVersion()` 函数 |
| `frontend/src/App.vue` | 修复 | Header 动态显示版本号 |
| `frontend/package.json` | 修复 | version 同步至 `1.2.0` |
| `frontend/dist/` | 重构建 | 前端重新构建产物 |
| `.gitignore` | 修复 | 新增 `data/` 和 `models/` 忽略规则 |

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
