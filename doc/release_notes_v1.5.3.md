# AIR_Memory v1.5.3 发布说明

**发布日期**: 2026-05-19  
**版本类型**: Patch Release

---

## 概述

v1.5.3 修复 v1.5.1 中反馈记录查询触发 404 和查询默认返回条数配置不符合新需求的问题，并完成补丁版本发版信息同步。

---

## 主要变更

### 反馈记录查询链路修复

- 反馈记录页面移除已废弃的价值评分接口调用，避免按条件查询时触发 404
- 反馈记录查询统一使用 `GET /api/v1/logs/feedback`

### 查询默认配额同步

- 前端查询接口默认 `top_k` 从 5 调整为 10
- 查询请求不再发送已移除的 `fast_only` 参数

### 发版版本号统一更新

- 后端、前端、启动脚本、版本测试、README 与发布工作流同步更新到 `v1.5.3`
- 发布工作流 `--notes-file` 更新为 `doc/release_notes_v1.5.3.md`

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.5.3.zip`。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `frontend/src/api/index.ts` | 功能修复 | 查询默认参数改为 `top_k=10`，移除 `fast_only` |
| `frontend/src/stores/memory.ts` | 功能修复 | 查询调用参数与新接口对齐 |
| `frontend/src/views/FeedbackView.vue` | 功能修复 | 移除废弃价值评分接口调用，反馈查询仅走 `/logs/feedback` |
| `frontend/tests/FeedbackView.spec.ts` | 测试更新 | 反馈页测试改为校验反馈日志查询链路 |
| `frontend/tests/stores.spec.ts` | 测试更新 | 新增默认 `top_k=10` 断言 |
| `backend/pyproject.toml` | 版本更新 | 版本号更新为 `1.5.3` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新为 `1.5.3` |
| `frontend/package.json` | 版本更新 | 版本号更新为 `1.5.3` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.5.3` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.5.3` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.5.3` |
| `.github/workflows/release.yml` | 发布配置更新 | `--notes-file` 指向 `doc/release_notes_v1.5.3.md` |
| `README.md` | 文档更新 | 当前版本更新为 `v1.5.3` |
