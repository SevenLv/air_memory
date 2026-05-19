# AIR_Memory v1.5.4 发布说明

**发布日期**: 2026-05-19  
**版本类型**: Patch Release

---

## 概述

v1.5.4 修复升级场景下查询日志 schema 兼容性问题：当历史数据库 `query_logs` 仍包含 legacy `fast_only` 列时，新版本查询日志可能无法写入，导致日志列表不显示新增查询记录。

---

## 主要变更

### 查询日志升级兼容修复

- 新增数据迁移 `M004`，在启动迁移阶段自动检测并处理 legacy `query_logs.fast_only` 结构
- 自动重建 `query_logs` 为当前 schema（`id/input_id/query/results/created_at`）
- 迁移并保留历史查询日志数据，恢复新版本查询日志持续写入能力

### 回归测试补充

- 新增 legacy schema 迁移兼容测试，覆盖：
  - 含 `fast_only NOT NULL` 的旧表升级
  - 升级后字段校验（移除 `fast_only`、存在 `input_id`）
  - 升级后新查询日志可正常写入与读取

### 发版版本号统一更新

- 后端、前端、启动脚本、版本测试、README 与发布工作流同步更新到 `v1.5.4`
- 发布工作流 `--notes-file` 更新为 `doc/release_notes_v1.5.4.md`

---

## 升级说明

- 建议升级前备份 `data/logs.db`
- 升级后首次启动会自动执行数据库迁移（幂等）
- 无需手动执行 SQL

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/data_migration.py` | 功能修复 | 新增 `M004` 迁移，兼容 legacy `query_logs.fast_only` |
| `backend/tests/test_log_service.py` | 测试更新 | 新增 legacy `query_logs` 升级兼容回归测试 |
| `backend/pyproject.toml` | 版本更新 | 版本号更新为 `1.5.4` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新为 `1.5.4` |
| `frontend/package.json` | 版本更新 | 版本号更新为 `1.5.4` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.5.4` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.5.4` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.5.4` |
| `.github/workflows/release.yml` | 发布配置更新 | `--notes-file` 指向 `doc/release_notes_v1.5.4.md` |
| `README.md` | 文档更新 | 当前版本与发布说明索引更新为 `v1.5.4` |
