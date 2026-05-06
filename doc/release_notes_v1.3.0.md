# AIR_Memory v1.3.0 发布说明

**发布日期**: 2026-05-06
**版本类型**: Minor Release

---

## 概述

v1.3.0 将环境初始化逻辑从启动脚本中剥离，新增独立的初始化脚本（`init.sh` / `init.bat`），并将查询记忆 API 的 `fast_only` 默认值由 `false` 改为 `true`（默认仅搜索热层）。

---

## 新功能

### 初始化脚本与启动脚本分离

**背景**：旧版本的 `start.sh` / `start.bat` 在每次启动时均会检查 Python 版本、创建虚拟环境并安装依赖，导致每次启动耗时较长，也不利于将已初始化的目录迁移到其他计算机。

**变更**：

- 新增 `init.sh`（macOS / Linux）和 `init.bat`（Windows）初始化脚本，负责以下一次性操作：
  - 检查 Python 3.11+ 是否已安装
  - 以 `--copies` 模式创建虚拟环境（将 Python 二进制复制而非符号链接，支持目录跨机器迁移）
  - 安装 Python 依赖（`pip install -r backend/requirements.txt`）
  - 预下载 Embedding 模型（`all-MiniLM-L6-v2`，约 90 MB），模型缓存至 `./models/` 目录
- 简化 `start.sh` / `start.bat`：移除环境初始化逻辑，仅激活已有虚拟环境并启动 uvicorn

**可移植性**：完成初始化后，整个项目目录可复制到相同 OS 和 CPU 架构的其他计算机上，执行 `start.sh` / `start.bat` 即可直接启动，无需联网或重新初始化。

### 查询 API 默认仅搜索热层

`GET /memories` REST API 和 MCP `query_memory` 工具的 `fast_only` 参数默认值由 `false` 改为 `true`。

| 参数 | 旧默认值 | 新默认值 |
| --- | --- | --- |
| `fast_only` | `false`（搜索热层 + 冷层） | `true`（仅搜索热层） |

**影响**：

- 不传 `fast_only` 参数时，默认仅检索热层（低延迟，≤ 100ms），适合 AI Agent 日常使用场景
- 需要深度检索（热层 + 冷层）时，请显式传入 `fast_only=false`

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `init.sh` | 新增 | macOS / Linux 初始化脚本 |
| `init.bat` | 新增 | Windows 初始化脚本 |
| `start.sh` | 功能更新 | 移除 env 初始化逻辑；版本号更新至 v1.3.0 |
| `start.bat` | 功能更新 | 移除 env 初始化逻辑；版本号更新至 v1.3.0 |
| `backend/src/air_memory/api/memory.py` | 行为变更 | `fast_only` 默认值 `False` -> `True` |
| `backend/src/air_memory/mcp/server.py` | 行为变更 | `fast_only` 默认值 `False` -> `True` |
| `doc/deploy_guide.md` | 文档更新 | 新增初始化步骤说明（v1.4） |
| `doc/release_notes_v1.3.0.md` | 新增 | 本文件 |
| `.github/workflows/release.yml` | 工作流更新 | 新增 `init.sh` / `init.bat` 到发布包；`--notes-file` 指向本文件 |

---

## 升级说明

### 从 v1.2.x 升级

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.3.0.zip`。

**macOS / Linux**：

```bash
unzip air_memory-v1.3.0.zip
cp -r old_dir/data air_memory-v1.3.0/
cd air_memory-v1.3.0
bash init.sh      # 首次在新目录运行，完成环境初始化
bash start.sh     # 启动服务
```

**Windows**：

解压 `air_memory-v1.3.0.zip`，将旧版本 `data\` 目录复制到新目录后执行：

```cmd
init.bat          REM 首次在新目录运行，完成环境初始化
start.bat         REM 启动服务
```

> **注意**：如果旧版本 `start.sh` / `start.bat` 已创建了 `.venv` 目录，建议删除后重新运行 `init.sh` / `init.bat`，以确保虚拟环境使用 `--copies` 模式创建（支持目录迁移）。

### 破坏性变更提示

`fast_only` 默认值变更为 `true`。若现有调用方依赖不传 `fast_only` 时同时检索热层和冷层的行为，需在调用时显式传入 `fast_only=false`。
