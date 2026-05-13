# AIR_Memory v1.4.0 发布说明

**发布日期**: 2026-05-14
**版本类型**: Minor Release

---

## 概述

v1.4.0 对关联评分体系进行全面重构，引入 `input_memory_links` 表统一管理输入信息与记忆的关联评分，替换原有 `memory_values`/`value_score` 方案。新增 `inputs` API，支持查看输入信息列表及详情。查询接口移除 `fast_only`/`query_mode` 参数，统一执行关联5+热3+冷2分层溢出填充检索。系统启动时自动执行一次性旧数据迁移，升级过程对用户透明。

---

## 重大变更

### 关联评分体系重构

**背景**：原有 `memory_values` 表与记忆的 `value_score` 字段耦合度高，难以支持多输入信息与多记忆之间的多对多关联评分管理。

**变更**：

- 新增 `input_memory_links` 表，统一存储输入信息（`input_id`）与记忆（`memory_id`）之间的关联评分（`association_score`）；
- 废弃 `memory_values` 表与记忆的 `value_score` 字段；
- 淘汰/升级排序依据由 `value_score` 改为 `total_association_score`（即该记忆所有关联的评分之和）。

### 查询接口参数精简

移除 `GET /api/v1/memories`（及 MCP `query_memory` 工具）中的 `fast_only` 与 `query_mode` 参数，查询接口现统一执行分层溢出填充检索：

- 关联记忆最多 5 条；
- 热层固定 3 条，若关联记忆不足 5 条则热层可补充至关联+热层合计 8 条；
- 冷层固定 2 条，若关联+热层合计不足 8 条则冷层可补充所有缺口；
- 合并去重后总数最多 10 条。

---

## 新功能

### inputs API

新增以下两个 REST API 端点，供人类用户及 Web UI 查看输入信息：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/v1/inputs` | 获取输入信息列表，支持分页 |
| `GET` | `/api/v1/inputs/{input_id}` | 获取指定输入信息详情，包含关联记忆及对应评分 |

### 旧数据自动迁移

新增 `DataMigrationManager`，系统启动时自动检测并将旧版本数据（`memory_values`/`value_score`）一次性迁移至新 `input_memory_links` 表结构，迁移完成后再启动主要功能。迁移为幂等操作，重复启动不会重复执行。

---

## 不兼容变更

| 变更项 | 影响 | 处理建议 |
| --- | --- | --- |
| `fast_only` 参数已移除 | 调用 `GET /api/v1/memories` 或 MCP `query_memory` 时传入该参数将被忽略或报错 | 移除调用方中的 `fast_only` 参数 |
| `query_mode` 参数已移除 | 同上 | 移除调用方中的 `query_mode` 参数 |
| `value_score` 字段已废弃 | 记忆对象中不再返回 `value_score` 字段 | 改用 `total_association_score` 字段 |
| 淘汰/升级排序字段变更 | 系统自动淘汰最旧低关联评分记忆时，以 `total_association_score` 为排序依据 | 无需手动操作，系统自动处理 |

---

## 升级说明

> **重要提示**：本版本包含数据库 Schema 迁移，请在升级前备份 `data/` 目录。

### 从 v1.3.x 升级

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.4.0.zip`。

**macOS / Linux**：

```bash
unzip air_memory-v1.4.0.zip
cp -r old_dir/data air_memory-v1.4.0/
cp -r old_dir/models air_memory-v1.4.0/   # 复制已缓存的模型，无需重新下载
cd air_memory-v1.4.0
bash init.sh      # 首次在新目录运行，完成环境初始化
bash start.sh     # 启动服务（首次启动将自动执行旧数据迁移）
```

**Windows**：

解压 `air_memory-v1.4.0.zip`，将旧版本 `data\` 和 `models\` 目录复制到新目录后执行：

```cmd
init.bat          REM 首次在新目录运行，完成环境初始化
start.bat         REM 启动服务（首次启动将自动执行旧数据迁移）
```

> **注意**：首次启动时系统将自动检测旧版本数据并完成迁移，迁移期间服务暂不对外提供接口，完成后自动恢复正常运行。如果未复制 `models\` 目录，请先运行 `init.bat` / `init.sh` 完成模型预下载。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/pyproject.toml` | 版本更新 | 版本号更新至 `1.4.0` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新至 `1.4.0` |
| `backend/src/air_memory/db/` | 功能更新 | 新增 `input_memory_links` 表；废弃 `memory_values` 表与 `value_score` 字段 |
| `backend/src/air_memory/api/inputs.py` | 新增 | `GET /api/v1/inputs` 与 `GET /api/v1/inputs/{input_id}` 接口 |
| `backend/src/air_memory/api/memory.py` | 不兼容变更 | 移除 `fast_only`/`query_mode` 参数；统一分层溢出填充检索 |
| `backend/src/air_memory/migration/` | 新增 | `DataMigrationManager` 旧数据迁移模块 |
| `doc/release_notes_v1.4.0.md` | 新增 | 本文件 |
