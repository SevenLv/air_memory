# AIR_Memory v1.2.12 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.12 修复了 AI 工具调用框架（如 Claude tool_call）在调用 REST API 时不设置或错误设置 `charset` 导致中文记忆内容乱码的问题。本次通过在服务端新增 `_ForceUTF8JSONMiddleware` 纯 ASGI 中间件解决该问题，客户端无需做任何适配调整，可直接升级。

---

## 问题修复

### 服务端 UTF-8 强制中间件（Issue #charset fix）

**根因**：HTTP RFC 7231 规定 `Content-Type` 中的 `charset` 参数由客户端声明，但部分 AI 工具调用框架不设置 charset 或错误设置为 `iso-8859-1` 等非 UTF-8 编码。根据 JSON RFC 8259，JSON 默认编码为 UTF-8，服务端应主动按 UTF-8 处理，而非依赖客户端声明。

**修复方案**：在 FastAPI 应用中新增 `_ForceUTF8JSONMiddleware` 纯 ASGI 中间件。该中间件在请求进入路由层之前，将所有 `Content-Type: application/json` 请求的 charset 强制覆写为 `utf-8`，覆盖场景包括：

- 客户端发送 `Content-Type: application/json`（无 charset）-> 自动添加 `charset=utf-8`
- 客户端发送 `Content-Type: application/json; charset=iso-8859-1`（错误 charset）-> 覆写为 `charset=utf-8`
- 客户端发送 `Content-Type: application/json; charset=UTF-8`（正确）-> 保持不变

**客户端影响**：无破坏性变更。客户端请求 `Content-Type: application/json` 时不再需要显式设置 `charset=UTF-8`，服务端会自动处理。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 功能更新 | 新增 `_ForceUTF8JSONMiddleware` 纯 ASGI 中间件；更新 OpenAPI description 说明；版本号更新至 `1.2.12` |
| `backend/src/air_memory/api/memory.py` | 文档更新 | 移除 `save_memory`、`feedback_memory` 接口 docstring 中强制设置 charset 的要求 |
| `backend/tests/test_encoding.py` | 测试更新 | 新增 3 个测试：无 charset 场景、错误 charset 场景、中间件单元测试 |
| `backend/tests/test_main.py` | 测试更新 | 新增 4 个 `_ForceUTF8JSONMiddleware` 单元测试；版本号断言更新为 `1.2.12` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.11` -> `1.2.12` |
| `frontend/package.json` | 版本更新 | version `1.2.11` -> `1.2.12` |
| `frontend/package-lock.json` | 版本更新 | 与 `package.json` 版本保持一致 |
| `start.sh` | 版本更新 | 启动横幅版本号更新为 `v1.2.12` |
| `start.bat` | 版本更新 | 启动横幅版本号更新为 `v1.2.12` |
| `README.md` | 文档更新 | 当前版本与发布说明文件索引更新为 `v1.2.12` |
| `.github/workflows/release.yml` | 工作流更新 | `--notes-file` 指向 `doc/release_notes_v1.2.12.md` |
| `doc/sad_v1.13.md` | 新增 | 系统架构设计说明书 v1.13：新增 UTF-8 强制中间件说明、更新接口规范 Content-Type 说明、更新安全设计章节 |
| `doc/release_notes_v1.2.12.md` | 新增 | 本文件 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 `air_memory-v1.2.12.zip`，将旧版本 `data/` 目录复制到新目录后启动。

**macOS / Linux**:

```bash
unzip air_memory-v1.2.12.zip
cp -r old_dir/data air_memory-v1.2.12/
cd air_memory-v1.2.12
bash start.sh
```

**Windows**:

解压 `air_memory-v1.2.12.zip`，将旧版本 `data\` 目录复制到新目录后执行:

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。
