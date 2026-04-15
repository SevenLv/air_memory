# AIR_Memory v1.2.7 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.7 为维护性版本，包含启动脚本优化、API 文档补充和发布流程改进，不含功能变更和 Breaking Change，直接升级即可。

---

## 改进项

### 1. 启动脚本优化

**问题描述**

`start.sh` 和 `start.bat` 在安装依赖步骤结束后额外执行了 `pip install --no-deps -e backend/`，该命令在发布包场景下无实际意义（发布包不含 `pyproject.toml` 以外的可编辑安装文件），且会产生不必要的输出。

**修复方案**

移除 `start.sh` 和 `start.bat` 中的 `pip install --quiet --no-deps -e backend/` 命令，保留 `pip install -r backend/requirements.txt` 以安装所有第三方依赖。

**影响**

- 首次启动速度略有提升；
- 启动日志更简洁；
- 功能不受影响，所有业务逻辑依赖已由 `requirements.txt` 覆盖。

---

### 2. REST API charset=UTF-8 调用约束文档

**背景**

为明确 API 调用规范，避免中文内容因客户端未指定 charset 导致乱码，在 OpenAPI 文档和接口描述中补充了显式说明。

**变更内容**

- `backend/src/air_memory/main.py`：在 FastAPI 应用 `description` 中新增 REST API 调用约束说明，强调对所有 JSON 请求必须显式设置 `Content-Type: application/json; charset=UTF-8`；
- `backend/src/air_memory/api/memory.py`：在 `save_memory` 和 `feedback_memory` 两个 POST 接口的 docstring 中补充 Content-Type charset 约束；
- 上述说明在访问 `http://localhost:8080/api/v1/docs` 时可查看。

---

### 3. 发布流程改进（面向开发团队）

**变更内容**

- `.github/workflows/release.yml`：新增 Python 字节码预编译和 zip 发布包构建步骤，发布时自动生成 `air_memory-{tag}.zip` 并上传至 GitHub Release Assets；
- `doc/deploy_guide.md` v1.3：更新获取方式，引导用户从 GitHub Releases 页面下载发布包，不再需要通过 Git 克隆源代码；
- `README.md`：新增"获取发布包"章节，引导用户前往 GitHub Releases 页面下载最新版本。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 文档更新 | 版本号更新至 1.2.7；FastAPI description 新增 charset 约束说明 |
| `backend/src/air_memory/api/memory.py` | 文档更新 | save_memory 和 feedback_memory 接口 docstring 补充 charset 约束 |
| `backend/pyproject.toml` | 版本更新 | version `1.2.6` -> `1.2.7` |
| `frontend/package.json` | 版本更新 | version `1.2.5` -> `1.2.7` |
| `start.sh` | 优化 | 版本号 v1.2.6 -> v1.2.7；移除冗余的 `pip install -e backend/` |
| `start.bat` | 优化 | 版本号 v1.2.6 -> v1.2.7；移除冗余的 `pip install --no-deps -e backend\` |
| `README.md` | 文档更新 | 版本号 v1.2.6 -> v1.2.7；新增"获取发布包"章节；更新目录结构图 |
| `doc/deploy_guide.md` | 文档更新 | v1.3：更新获取方式为从 GitHub Releases 下载发布包 |
| `.github/workflows/release.yml` | 流程改进 | 新增 zip 发布包构建和字节码预编译步骤 |
| `doc/release_notes_v1.2.7.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 v1.2.7 发布包，解压后将旧版本 `data/` 目录复制到新目录下，然后启动服务即可。

**macOS / Linux**：

```bash
unzip air_memory-v1.2.7.zip
cp -r old_dir/data air_memory-v1.2.7/
cd air_memory-v1.2.7
bash start.sh
```

**Windows**：

解压 `air_memory-v1.2.7.zip`，将旧版本 `data\` 目录复制到新目录下，双击 `start.bat` 或在 CMD 中执行：

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。

### 数据影响分析

- 本次记忆管理 UI 需求实现未修改 SQLite 表结构（`save_logs`、`memory_values`、`feedback_logs`、`query_logs` 均保持不变）；
- 新增接口 `GET /api/v1/logs/save/{memory_id}` 仅为读取能力增强，不写入新字段；
- 前端筛选与分页逻辑不改变本地持久化数据格式。

结论：**本次升级无需执行数据库迁移或数据转换**。保留既有 `data/` 目录即可直接升级运行。
