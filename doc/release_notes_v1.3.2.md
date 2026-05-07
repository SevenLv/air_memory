# AIR_Memory v1.3.2 发布说明

**发布日期**: 2026-05-06
**版本类型**: Patch Release

---

## 概述

v1.3.2 修复了 `start.bat` / `start.sh` 在系统或用户环境中已设置 Hugging Face 相关环境变量时，启动时仍会触发 Embedding 模型重复下载的问题（Issue #80）。

---

## 问题修复

### start.bat / start.sh 启动时重复下载 Embedding 模型（Issue #80）

**根因**：`start.bat` / `start.sh` 未强制设置 `HF_HUB_CACHE` 环境变量，导致在某些环境下模型缓存路径与 `init.bat` / `init.sh` 初始化时写入的路径不一致，触发重复下载。此外，未设置 `HF_HUB_OFFLINE=1` 和 `TRANSFORMERS_OFFLINE=1`，导致每次启动时均尝试联网检查模型更新。

**修复方案**：

- `start.bat` / `start.sh` 新增强制设置 `HF_HUB_CACHE` 指向项目内 `models/hub` 目录；
- `start.bat` / `start.sh` 新增强制设置 `HF_HUB_OFFLINE=1` 和 `TRANSFORMERS_OFFLINE=1`，确保启动时完全离线运行，不触发任何模型下载或更新检查。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 缺陷修复 | 强制设置 `HF_HUB_CACHE`、`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`；版本号更新至 `v1.3.2` |
| `start.sh` | 缺陷修复 | 强制设置 `HF_HUB_CACHE`、`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`；版本号更新至 `v1.3.2` |
| `doc/release_notes_v1.3.2.md` | 新增 | 本文件 |

---

## 升级说明

### 从 v1.3.1 升级

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.3.2.zip`。

**macOS / Linux**：

```bash
unzip air_memory-v1.3.2.zip
cp -r old_dir/data air_memory-v1.3.2/
cp -r old_dir/models air_memory-v1.3.2/   # 复制已缓存的模型，无需重新下载
cd air_memory-v1.3.2
bash start.sh
```

**Windows**：

解压 `air_memory-v1.3.2.zip`，将旧版本 `data\` 和 `models\` 目录复制到新目录后执行：

```cmd
start.bat
```

> **注意**：如果未复制 `models\` 目录，首次启动前请先运行 `init.bat` 完成模型预下载。

升级不影响已有数据。
