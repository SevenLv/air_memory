# AIR_Memory v1.2.9 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.9 修复了 v1.2.8 发布包中记忆管理页面未更新的问题。本次发布不涉及接口变化和数据结构变化，可直接升级。

---

## 修复内容

### 修复发布包前端产物未同步问题

**问题现象**

v1.2.8 的 `frontend/src` 已包含记忆管理页面增强功能，但发布包实际使用的 `frontend/dist` 为旧构建产物，导致页面功能未按预期展示。

**修复方案**

- 重新执行前端构建，更新 `frontend/dist` 产物。
- 保持业务源码不变，仅同步最新构建结果到发布包。

**修复后结果**

- `/memories` 页面可正常展示记忆列表、分页与筛选功能。
- 记忆详情页路由可正常访问。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 版本更新 | 版本号更新至 `1.2.9` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.8` -> `1.2.9` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.2.9` |
| `frontend/package.json` | 版本更新 | version `1.2.8` -> `1.2.9` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.2.9` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.2.9` |
| `README.md` | 文档更新 | 当前版本与发布说明文件索引更新为 `v1.2.9` |
| `.github/workflows/release.yml` | 工作流更新 | `--notes-file` 指向 `doc/release_notes_v1.2.9.md` |
| `frontend/dist/index.html` | 构建产物更新 | 同步最新前端页面产物 |
| `frontend/dist/assets/index-BSVgmdRw.js` | 构建产物更新 | 同步最新前端脚本产物 |
| `frontend/dist/assets/index-DLK3G3l5.css` | 构建产物更新 | 同步最新前端样式产物 |
| `doc/release_notes_v1.2.9.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.2.9.zip`，将旧版本 `data/` 目录复制到新目录后启动。

**macOS / Linux**:

```bash
unzip air_memory-v1.2.9.zip
cp -r old_dir/data air_memory-v1.2.9/
cd air_memory-v1.2.9
bash start.sh
```

**Windows**:

解压 `air_memory-v1.2.9.zip`，将旧版本 `data\` 目录复制到新目录后执行:

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
