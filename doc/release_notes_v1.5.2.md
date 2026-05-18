# AIR_Memory v1.5.2 发布说明

**发布日期**: 2026-05-18  
**版本类型**: Patch Release

---

## 概述

v1.5.2 修复 Web 管理界面“记忆管理”列表进入详情时触发 404 的问题，并完成补丁版本发版信息同步。

---

## 主要变更

### 记忆详情页 404 修复

- 详情页不再调用已移除的 `GET /api/v1/memories/{id}/value-score` 接口
- 详情页评分改为读取 `GET /api/v1/logs/save/{memory_id}` 返回字段 `total_association_score`
- 保留对历史字段 `value_score` 的兼容回退显示

### 发版版本号统一更新

- 后端、前端、启动脚本、版本测试、README 与发布工作流同步更新到 `v1.5.2`
- 发布工作流 `--notes-file` 更新为 `doc/release_notes_v1.5.2.md`

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.5.2.zip`。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `frontend/src/views/MemoryDetailView.vue` | 功能修复 | 移除旧接口调用，改为使用日志详情字段展示评分 |
| `frontend/src/api/types.ts` | 类型同步 | `SaveLog` 补充 `total_association_score` 字段 |
| `frontend/tests/MemoryDetailView.spec.ts` | 测试更新 | 详情页测试改用 `total_association_score` |
| `backend/pyproject.toml` | 版本更新 | 版本号更新为 `1.5.2` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新为 `1.5.2` |
| `frontend/package.json` | 版本更新 | 版本号更新为 `1.5.2` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.5.2` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.5.2` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.5.2` |
| `.github/workflows/release.yml` | 发布配置更新 | `--notes-file` 指向 `doc/release_notes_v1.5.2.md` |
| `README.md` | 文档更新 | 当前版本更新为 `v1.5.2` |
