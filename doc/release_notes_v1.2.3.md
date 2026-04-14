# AIR_Memory v1.2.3 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.3 为纯文档修正版本，不含任何代码变更。本次修正了自 v1.2.0 起引入但未同步更新的两处文档问题：用户手册未记录 Header 版本号显示功能、MCP `query_memory` 返回格式示例有误；部署手册 Windows 启动成功 Banner 缺少"后端 API 文档"行。不包含 Breaking Change，直接升级即可。

---

## 修正问题

### 1. 用户手册未记录 Header 版本号显示功能

**问题描述**

v1.2.0 新增了管理界面 Header 右侧动态显示系统版本号的功能，但用户手册 2.1 节未作任何说明，用户无法从文档中得知该功能的存在。

**修正内容**

在用户手册 2.1 节"界面总览"中补充版本号显示说明：顶部导航栏右侧动态显示当前系统版本号（通过 `GET /api/v1/version` 接口获取）。

---

### 2. 用户手册 MCP query_memory 返回示例格式有误

**问题描述**

v1.2.0 将 MCP `query_memory` 工具的返回类型由 `list[dict]` 改为 JSON 字符串（`json.dumps(results, ensure_ascii=False)`），使返回内容为记忆条目的平铺列表。但用户手册 3.1.3 节的返回示例仍沿用修改前的 REST API 格式（含 `memories`、`count`、`query_mode` 字段的对象），与实际返回不符。

**修正内容**

将用户手册 3.1.3 节 `query_memory` 返回示例更正为平铺列表格式，并新增说明以区分 MCP 与 REST API 的响应结构差异。

---

### 3. 部署手册 Windows 启动成功 Banner 缺少"后端 API 文档"行

**问题描述**

v1.2.0 在 `start.bat` 启动成功 Banner 中新增了"后端 API 文档：http://localhost:PORT/api/v1/docs"输出行，但部署手册 3.3 节的 Banner 示例未同步更新，与实际输出不一致。

**修正内容**

在部署手册 3.3 节"确认启动成功"的 Banner 示例中补充"后端 API 文档"行。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `doc/user_guide.md` | 文档修正 | 2.1 节补充 Header 版本号显示说明；3.1.3 节修正 MCP query_memory 返回示例格式；变更记录更新至 1.1 |
| `doc/deploy_guide.md` | 文档修正 | 3.3 节 Windows Banner 示例补充"后端 API 文档"行；变更记录更新至 1.2 |

---

## 升级说明

直接拉取最新代码即可，无需重启服务：

```bash
git pull
```

升级不影响已有数据和运行中的服务。
