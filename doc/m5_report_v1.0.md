# M5 阶段执行报告

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-10 | 初稿 |

---

> 文档版本：v1.0
> 里程碑：M5 — 文档就绪
> 负责人：Nia（项目助理）
> 编写日期：2026-04-10

---

## 1. 概述

M5 里程碑目标：编写并交付 AIR_Memory 系统的部署手册（`deploy_guide.md`）和用户手册（`user_guide.md`），满足需求文档 SRD v1.0 中 FR-DOC-001 和 FR-DOC-002 的全部要求。

前置里程碑 M4（部署配置就绪）已完成并通过架构评审，系统可在 macOS 和 Windows 上通过 Docker Compose 一键部署。

---

## 2. 工作条目完成情况

| 编号 | 工作内容 | 状态 | 文件路径 |
| --- | --- | --- | --- |
| M5-01 | 编写部署手册：环境前提、macOS 部署步骤、Windows 部署步骤、启动验证方法 | 完成 | `doc/deploy_guide.md` |
| M5-02 | 编写用户手册：Web 管理界面使用说明、AI Agent 接口调用说明（MCP 和 REST API） | 完成 | `doc/user_guide.md` |

---

## 3. 各文件说明

### 3.1 doc/deploy_guide.md（部署手册）

**内容覆盖**：

- **第 2 章：运行环境前提**
  - 硬件最低要求（CPU、内存、磁盘）
  - 软件要求：Docker Engine 27+ 或 Docker Desktop（含版本要求说明）
  - 网络要求：首次构建需访问 HuggingFace Hub 下载 `all-MiniLM-L6-v2` 模型

- **第 3 章：部署步骤**
  - macOS 完整部署步骤（3 步骤：启动 Docker Desktop、运行 `bash start.sh`、确认成功）
  - Windows 完整部署步骤（3 步骤：启动 Docker Desktop、运行 `start.bat`、确认成功）
  - 启动脚本执行流程 Mermaid 图

- **第 4 章：部署后验证**
  - Web 界面访问验证（`http://localhost:8080`）
  - 后端健康检查（`curl /health`）
  - API 文档验证（`/api/v1/docs`）
  - 容器运行状态验证（`docker compose ps`）
  - 验证流程 Mermaid 图

- **第 5 章：服务管理**（常用命令速查表）

- **第 6 章：环境变量配置**（引用 `doc/env_config.md`，18 个配置项快速参考）

- **第 7 章：常见问题排查**（4 类典型故障）

**文档特性**：
- 使用 Mermaid flowchart 绘制部署流程图和验证流程图，符合 `doc/doc_spec_v1.0.md` 规范
- 无 ASCII 字符画
- 全中文，无全角符号

### 3.2 doc/user_guide.md（用户手册）

**内容覆盖**：

- **第 2 章：Web 管理界面使用说明**
  - 界面总览（4 个页面导航，Mermaid graph）
  - 记忆查询（首页 `/`）：快速/深度查询模式说明，结果字段说明
  - 记忆管理（`/memories`）：列表查看与删除操作，含删除流程序列图
  - 操作日志查看（`/logs`）：存储日志和查询日志字段说明
  - 价值评分查看（`/feedback`）：评分规则 Mermaid 流程图，反馈历史字段说明

- **第 3 章：AI Agent 接口调用说明**
  - MCP 接口：接入端点、工具列表（`save_memory`、`query_memory`、`feedback_memory`）、含 Claude Desktop 配置示例
  - MCP 工具调用示例（3 个工具完整请求/响应示例）
  - REST API：基础 URL、数据格式、全量接口文档（含 curl 示例）
  - 系统接口：健康检查、tier-stats、disk-stats
  - AI Agent 完整使用流程序列图

- **第 4 章：分级存储说明**（热层/冷层容量、升降层规则）

**文档特性**：
- 使用 Mermaid sequenceDiagram、graph、flowchart 绘制各类图表
- 含完整的 curl 调用示例和 JSON 请求/响应示例
- 全中文，无全角符号

---

## 4. 验收标准达成情况

| 编号 | 验收标准 | 状态 | 说明 |
| --- | --- | --- | --- |
| M5-AC-01 | 部署手册覆盖 macOS 和 Windows 两个平台的完整部署步骤（满足 FR-DOC-001） | 达成 | `deploy_guide.md` §3.2 和 §3.3 分别覆盖 macOS 和 Windows 的完整 3 步骤部署流程 |
| M5-AC-02 | 部署手册包含：运行环境前提（Docker 版本要求）、一键部署命令、部署后验证步骤 | 达成 | §2（Docker Engine 27+ 要求）、§3（`bash start.sh` / `start.bat`）、§4（验证步骤） |
| M5-AC-03 | 用户手册覆盖 Web 管理界面全部功能的操作说明（满足 FR-DOC-002） | 达成 | `user_guide.md` §2 覆盖记忆查询、记忆删除、操作日志查看（存储/查询日志）、价值评分查看 4 项功能 |
| M5-AC-04 | 用户手册包含 AI Agent 接口的调用示例（含 MCP 工具列表和 REST API 示例请求） | 达成 | §3.1 含完整 MCP 工具列表和 3 个工具调用示例；§3.2 含全量 REST API 及 curl 示例 |
| M5-AC-05 | 文档内容与 M4 完成后的实际部署流程一致，不存在过期的命令或截图 | 达成 | 部署手册基于 M4 实际交付的 `docker-compose.yml`、`start.sh`、`start.bat` 编写；所有端口、命令与实际配置一致 |

---

## 5. 内容来源说明

| 文档内容 | 来源 |
| --- | --- |
| Docker 版本要求、一键启动命令 | `start.sh`、`start.bat`（M4 交付） |
| 容器端口、服务架构 | `docker-compose.yml`、`frontend/nginx.conf`（M4 交付） |
| HuggingFace Hub 要求 | `doc/m4_report_v1.0.md` §5.1（遗留问题说明） |
| 环境变量配置项 | `doc/env_config.md`（M4 交付，18 个配置项） |
| REST API 接口规范 | `doc/sad_v1.8.md` §7.1（全量接口定义） |
| MCP 工具规范 | `doc/sad_v1.8.md` §7.2（3 个工具定义） |
| Web 界面功能说明 | `doc/sad_v1.8.md` §5.2（前端视图定义）、§6.5（UI 操作流程） |
| 价值评分规则 | `doc/sad_v1.8.md` §5.1.5（FeedbackService 设计） |

---

## 6. 遗留问题

本里程碑无遗留问题。

---

## 7. 对后续里程碑的影响评估

| 里程碑 | 影响说明 |
| --- | --- |
| M6（系统确认，Wii） | 验证工程师 Wii 可参考 `deploy_guide.md` 进行部署验证（M6-AC 相关），并依据 `user_guide.md` 设计 Web 界面和 AI Agent 接口的功能验证方案 |

---

## 8. 交付物文件清单

| 文件 | 说明 |
| --- | --- |
| `doc/deploy_guide.md` | 部署手册：环境前提、macOS/Windows 部署步骤、验证方法、服务管理、环境变量配置、故障排查 |
| `doc/user_guide.md` | 用户手册：Web 管理界面使用说明（4 个功能页面）、AI Agent 接口调用说明（MCP + REST API） |
| `doc/m5_report_v1.0.md` | 本文件 |
