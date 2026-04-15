# AIR_Memory v1.2.10 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.10 在记忆管理页面新增删除操作、自动过滤已删除记忆、展示评价值列，并同步更新了后端日志接口与用户手册。本次发布不涉及存储结构变化，可直接升级。

---

## 新增功能

### 记忆管理页面增强

**记忆删除**

- 列表操作列新增"删除"按钮，点击后弹出确认框，确认后调用 `DELETE /api/v1/memories/{id}` 删除记忆。
- 删除成功后记忆自动从列表移除，分页重置至第 1 页。

**过滤已删除记忆**

- 列表默认过滤 `memory_deleted=true` 的记录，仅展示有效记忆，避免已删除数据干扰浏览。

**评价值列**

- 列表新增"评价值"列，展示该记忆当前价值评分（保留两位小数）；尚未评价的记忆显示 `--`。
- 后端 `GET /api/v1/logs/save` 接口通过 `save_logs LEFT JOIN memory_values` 返回 `value_score` 字段。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/log/service.py` | 功能更新 | `get_save_logs` / `get_latest_save_log` 加入 `LEFT JOIN memory_values` 返回 `value_score` |
| `backend/src/air_memory/models/log.py` | 模型更新 | `SaveLog` 新增 `value_score: float | None` 字段 |
| `backend/tests/test_log_service.py` | 测试更新 | 新增 `value_score` 字段回归测试 |
| `frontend/src/api/types.ts` | 类型更新 | `SaveLog` 接口新增 `value_score?: number | null` |
| `frontend/src/views/MemoriesView.vue` | 功能更新 | 新增评价值列、删除按钮、已删除过滤逻辑 |
| `frontend/tests/MemoriesView.spec.ts` | 测试更新 | 新增删除行为、过滤已删除、评价值展示断言 |
| `doc/user_guide.md` | 文档更新 | v1.7：2.3 节补充删除操作、过滤说明、评价值列说明 |
| `backend/src/air_memory/main.py` | 版本更新 | 版本号更新至 `1.2.10` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.9` -> `1.2.10` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.2.10` |
| `frontend/package.json` | 版本更新 | version `1.2.9` -> `1.2.10` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.2.10` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.2.10` |
| `README.md` | 文档更新 | 当前版本与发布说明文件索引更新为 `v1.2.10` |
| `.github/workflows/release.yml` | 工作流更新 | `--notes-file` 指向 `doc/release_notes_v1.2.10.md` |
| `frontend/dist/index.html` | 构建产物更新 | 同步最新前端页面产物 |
| `frontend/dist/assets/index-Cx_8Ng7-.js` | 构建产物更新 | 同步最新前端脚本产物 |
| `frontend/dist/assets/index-DEXse-sT.css` | 构建产物更新 | 同步最新前端样式产物 |
| `doc/release_notes_v1.2.10.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.2.10.zip`，将旧版本 `data/` 目录复制到新目录后启动。

**macOS / Linux**:

```bash
unzip air_memory-v1.2.10.zip
cp -r old_dir/data air_memory-v1.2.10/
cd air_memory-v1.2.10
bash start.sh
```

**Windows**:

解压 `air_memory-v1.2.10.zip`，将旧版本 `data\` 目录复制到新目录后执行:

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
