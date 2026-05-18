# AIR_Memory v1.5.1 发布说明

**发布日期**: 2026-05-18  
**版本类型**: Patch Release

---

## 概述

v1.5.1 修复 v1.5.0 中 Web 管理界面未完整落地需求变更的问题，补齐输入信息管理页面，并修复记忆详情页跳转 404。

---

## 主要变更

### Web UI 补齐输入信息管理

- 新增输入信息列表页：`/inputs`
- 新增输入信息详情页：`/inputs/:inputId`
- 侧边导航新增“输入信息管理”入口

### 记忆详情页 404 修复

- 记忆管理列表跳转改为命名路由 + params
- 详情页读取路由参数时增加 URL 解码，避免编码 ID 导致查询失败

### 发版版本号统一更新

- 后端、前端、启动脚本、版本测试与发布工作流统一更新到 `v1.5.1`

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.5.1.zip`。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/pyproject.toml` | 版本更新 | 版本号更新为 `1.5.1` |
| `backend/src/air_memory/main.py` | 版本更新 | `APP_VERSION` 更新为 `1.5.1` |
| `frontend/package.json` | 版本更新 | 版本号更新为 `1.5.1` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.5.1` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.5.1` |
| `backend/tests/test_main.py` | 测试更新 | 版本号断言更新为 `1.5.1` |
| `.github/workflows/release.yml` | 发布配置更新 | `--notes-file` 指向 `doc/release_notes_v1.5.1.md` |
| `README.md` | 文档更新 | 当前版本更新为 `v1.5.1` |
