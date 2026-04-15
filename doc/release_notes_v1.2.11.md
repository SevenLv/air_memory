# AIR_Memory v1.2.11 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.11 在日志页补齐时间范围筛选与分页能力（存储日志 / 查询日志 Tab 均与反馈记录页对齐），并在记忆管理列表引入按评价值分级行背景色以直观展示记忆价值层次。本次发布不涉及存储结构与后端接口变化，可直接升级。

---

## 新增功能

### 日志页：统一时间筛选与分页（`/logs`）

- 存储日志 Tab 新增时间范围筛选（`datetimerange`）与分页控件（页码 + page size）。
- 查询日志 Tab 同步新增等同能力，交互模式与反馈记录列表对齐。
- "共 N 条"统计改为展示筛选后的结果总数，而非原始全集。
- 支持重置筛选条件恢复全量视图。

### 记忆管理页：按评价值分级行背景色（`/memories`）

- 列表按评价值自动设置行背景色：
  - 高分（`>= 0.7`）：绿色系
  - 中分（`>= 0.4`）：橙色系
  - 低分（`< 0.4`）：红色系
- 每个分级均定义对应的 hover 加深色，hover 时不丢失价值分层语义。

### 其他优化

- 查询结果摘要解析增加空值兜底，空字符串或非字符串时显示 `--`，避免无效 JSON 解析噪音。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `frontend/src/views/LogsView.vue` | 功能更新 | 存储/查询日志 Tab 新增时间筛选与分页 |
| `frontend/src/views/MemoriesView.vue` | 功能更新 | 新增按评价值分级行背景色与 hover 样式 |
| `frontend/tests/LogsView.spec.ts` | 测试更新 | 新增时间筛选、分页、摘要兜底断言 |
| `frontend/tests/MemoriesView.spec.ts` | 测试更新 | 清理冗余类型断言 |
| `doc/user_guide.md` | 文档更新 | v1.8：补充日志页时间筛选/分页说明及记忆分级背景色说明 |
| `backend/src/air_memory/main.py` | 版本更新 | 版本号更新至 `1.2.11` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.10` -> `1.2.11` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.2.11` |
| `frontend/package.json` | 版本更新 | version `1.2.10` -> `1.2.11` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.2.11` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.2.11` |
| `README.md` | 文档更新 | 当前版本与发布说明文件索引更新为 `v1.2.11` |
| `.github/workflows/release.yml` | 工作流更新 | `--notes-file` 指向 `doc/release_notes_v1.2.11.md` |
| `frontend/dist/index.html` | 构建产物更新 | 同步最新前端页面产物 |
| `frontend/dist/assets/index-BnP2FBf_.js` | 构建产物更新 | 同步最新前端脚本产物 |
| `frontend/dist/assets/index-CNOUWRMW.css` | 构建产物更新 | 同步最新前端样式产物 |
| `doc/release_notes_v1.2.11.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.2.11.zip`，将旧版本 `data/` 目录复制到新目录后启动。

**macOS / Linux**:

```bash
unzip air_memory-v1.2.11.zip
cp -r old_dir/data air_memory-v1.2.11/
cd air_memory-v1.2.11
bash start.sh
```

**Windows**:

解压 `air_memory-v1.2.11.zip`，将旧版本 `data\` 目录复制到新目录后执行:

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
