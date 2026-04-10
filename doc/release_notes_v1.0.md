# AIR_Memory v1.0.0 发布说明

**发布日期**：2026-04-10

---

## 概述

AIR_Memory 是一款面向 AI Agent 的记忆管理系统，提供记忆存储、语义查询、价值评分和分级存储等核心能力。本次发布为第一个正式版本（v1.0.0）。

---

## 主要功能

- **MCP 协议接口**：AI Agent 可通过 MCP 工具（`save_memory`、`query_memory`、`feedback_memory`）对记忆进行存储、查询和反馈；
- **REST API 接口**：提供完整的 HTTP REST API，支持与任意 HTTP 客户端集成；
- **分级记忆存储**：热层（内存，快速访问）+ 冷层（磁盘，持久化）双层架构，按价值评分自动迁移；
- **价值评分机制**：通过反馈接口对记忆价值进行评分，驱动分级迁移；
- **Web 管理界面**：提供记忆查询、删除、操作日志查看、价值评分查看等功能；
- **一键部署**：支持 macOS 和 Windows 平台，基于 Docker Compose 容器化部署。

---

## 系统要求

| 资源 | 最低要求 | 推荐配置 |
| --- | --- | --- |
| CPU | 4 核 | 8 核及以上 |
| 内存 | 8 GB | 16 GB |
| 磁盘空间 | 50 GB | 100 GB 及以上 |
| 操作系统 | macOS 13+ 或 Windows 10/11 | - |
| Docker | 27.0 及以上（含 Compose v2 插件） | - |

---

## 快速部署

### macOS

```bash
git clone <仓库地址>
cd air_memory
bash start.sh
```

### Windows

```bat
git clone <仓库地址>
cd air_memory
start.bat
```

部署完成后访问 `http://localhost:8080` 打开 Web 管理界面。

---

## 随附文件

| 文件 | 说明 |
| --- | --- |
| `deploy_guide.md` | 部署手册，覆盖 macOS/Windows 完整部署步骤、验证方法、服务管理和常见问题排查 |
| `user_guide.md` | 用户手册，覆盖 Web 管理界面操作说明及 AI Agent 接口调用说明 |

---

## 验收状态

本版本已通过 M6 系统确认验收（报告见 `doc/m6_report_v1.0.md`）：

- SRD v1.0 全部 30 条需求验证覆盖；
- 后端 108 个单元测试全部通过；
- 前端 77 个单元测试全部通过；
- 发现的 4 条缺陷（DEF-001~DEF-004）已全部修复。
