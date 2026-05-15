# AIR_Memory v1.5.0 发布说明

**发布日期**: 2026-05-15
**版本类型**: Minor Release

---

## 概述

v1.5.0 聚焦记忆分级存储规则简化：热/冷层迁移由阈值驱动调整为“是否存在输入信息关联”驱动。系统现在仅将存在至少一条 `input_memory_links` 关联记录的记忆保留在热层；新记忆保存时默认进入冷层，首次建立关联后再迁移到热层。

---

## 主要变更

### 热/冷层划分规则调整

- 热层准入条件统一为 `total_association_score > 0`；
- 无关联记忆（`total_association_score == 0`）保留在冷层；
- 移除基于 `PROMOTE_THRESHOLD` / `DEMOTE_THRESHOLD` 的迁移逻辑。

### 新记忆初始落层调整

- `save()` 默认仅写入冷层，不再同步写入热层；
- 记忆在收到正向反馈并建立关联后自动升入热层。

### 启动恢复与迁移策略更新

- `restore_hot_tier()` 启动恢复阶段仅加载有输入关联的记忆；
- `_maybe_migrate()` 统一按“有无关联”判断升降级。

### 配置项清理

移除以下已废弃配置项，避免与新规则冲突：

- `PROMOTE_THRESHOLD`
- `DEMOTE_THRESHOLD`
- `INITIAL_VALUE_SCORE`
- `FEEDBACK_STEP`

---

## 升级说明

### 从 v1.4.x 升级

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.5.0.zip`。

**macOS / Linux**：

```bash
unzip air_memory-v1.5.0.zip
cp -r old_dir/data air_memory-v1.5.0/
cp -r old_dir/models air_memory-v1.5.0/
cd air_memory-v1.5.0
bash init.sh
bash start.sh
```

**Windows**：

解压 `air_memory-v1.5.0.zip`，将旧版本 `data\` 与 `models\` 目录复制到新目录后执行：

```cmd
init.bat
start.bat
```

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/pyproject.toml` | 版本更新 | 版本号更新至 `1.5.0` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新至 `1.5.0` |
| `backend/src/air_memory/memory/service.py` | 功能更新 | `save()` 改为仅写入冷层 |
| `backend/src/air_memory/memory/tier_manager.py` | 功能更新 | 启动恢复仅加载 `total_association_score > 0` 记忆 |
| `backend/src/air_memory/feedback/service.py` | 功能更新 | 迁移逻辑改为按有无关联判断 |
| `.github/workflows/release.yml` | 发布配置更新 | `--notes-file` 指向本发布说明 |
| `doc/release_notes_v1.5.0.md` | 新增 | 本文件 |

