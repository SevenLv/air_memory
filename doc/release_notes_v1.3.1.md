# AIR_Memory v1.3.1 发布说明

**发布日期**: 2026-05-06
**版本类型**: Patch Release

---

## 概述

v1.3.1 修复了 v1.3.0 中 `start.bat` / `start.sh` 在系统或用户已设置 `HF_HOME` 环境变量的场景下，启动时仍然触发 Embedding 模型重新下载的问题。

---

## 问题修复

### start.bat / start.sh 启动时重新下载 Embedding 模型（Issue #v130-fix-start-bat-issue）

**根因**：`init.bat` / `init.sh` 无条件将 `HF_HOME` 设置为项目内 `models/` 目录，确保模型始终缓存到该位置。但 `start.bat` / `start.sh` 使用条件赋值（`if not defined` / `${HF_HOME:-...}`），当系统或用户环境中已定义 `HF_HOME`（指向其他路径）时，启动脚本会沿用该外部路径查找模型缓存，因为 `init.bat` / `init.sh` 已将模型写入项目 `models/` 目录，导致查找失败并触发重新下载。

**修复方案**：与 `PYTHONUTF8=1` 的处理原则一致，将 `start.bat` / `start.sh` 中的 `HF_HOME` 改为无条件赋值，强制指向项目内 `models/` 目录：

- `start.bat`：`if not defined HF_HOME set "HF_HOME=..."` → `set "HF_HOME=..."`
- `start.sh`：`export HF_HOME="${HF_HOME:-...}"` → `export HF_HOME="..."`

**新增启动检查**：在 `start.bat` / `start.sh` 中增加对 `models/hub` 目录的存在性检查，若不存在则提示用户先运行初始化脚本。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 缺陷修复 | `HF_HOME` 改为无条件赋值；新增 `models\hub` 目录存在性检查；版本号更新至 `v1.3.1` |
| `start.sh` | 缺陷修复 | `HF_HOME` 改为无条件赋值；新增 `models/hub` 目录存在性检查；版本号更新至 `v1.3.1` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新至 `1.3.1` |
| `doc/release_notes_v1.3.1.md` | 新增 | 本文件 |

---

## 升级说明

### 从 v1.3.0 升级

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.3.1.zip`。

**macOS / Linux**：

```bash
unzip air_memory-v1.3.1.zip
cp -r old_dir/data air_memory-v1.3.1/
cp -r old_dir/models air_memory-v1.3.1/   # 复制已缓存的模型，无需重新下载
cd air_memory-v1.3.1
bash start.sh
```

**Windows**：

解压 `air_memory-v1.3.1.zip`，将旧版本 `data\` 和 `models\` 目录复制到新目录后执行：

```cmd
start.bat
```

> **注意**：如果未复制 `models\` 目录，首次启动前请先运行 `init.bat` 完成模型预下载。

升级不影响已有数据。
