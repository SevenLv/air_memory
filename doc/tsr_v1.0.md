# AIR_Memory 技术路线选型报告

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-8 | 初稿 |

## 一、背景与目标

本报告基于产品定义文档 (pdd_v1.0.md) 进行技术路线选型。AIR_Memory 是一个为 AI Agent 设计的本地部署记忆系统，核心目标如下：

- 跨平台 (macOS / Windows) 一键本地部署；
- 向 AI Agent 提供记忆存储与查询接口，响应时间均不超过 100ms；
- 向人类用户提供 UI 管理界面；
- 系统默认自启动。

---

## 二、技术选型

### 2.1 后端语言

**选型：Go 1.22+**

| 评估维度 | 说明 |
| --- | --- |
| 跨平台 | 原生支持 macOS / Windows 交叉编译，单二进制产物，无运行时依赖 |
| 性能 | 编译型语言，HTTP 服务性能优秀，轻松满足 100ms 响应要求 |
| 并发 | goroutine 模型天然支持 AI Agent 与 UI 的并发请求 |
| 系统集成 | 可通过标准库和 `golang.org/x/sys` 集成 launchd (macOS) 和 Windows Service |
| 依赖管理 | Go Modules，依赖管理简洁，构建产物干净 |

### 2.2 AI Agent 接口

**选型：RESTful HTTP API (JSON)**

AI Agent 通过标准 HTTP 请求调用 AIR_Memory 的记忆存储和查询接口。选用 REST 的原因：

- 通用性强，所有主流 AI Agent 框架 (LangChain、AutoGen、OpenAI Agents SDK 等) 均原生支持 HTTP 调用；
- 接口简单直观，便于 AI Agent 集成和调试；
- 后续可在 REST 基础上扩展支持 MCP (Model Context Protocol)。

**接口设计概要：**

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/memories` | POST | 保存记忆 |
| `/api/v1/memories/search` | POST | 查询相关记忆 |

### 2.3 存储方案

**选型：SQLite (嵌入式) + FTS5 全文搜索**

| 评估维度 | 说明 |
| --- | --- |
| 本地嵌入 | 无需安装外部数据库服务，单文件存储，符合本地部署要求 |
| 查询性能 | FTS5 (BM25 算法) 全文搜索，在万级数据量下响应时间 < 10ms，完全满足 100ms 要求 |
| 可维护性 | 数据文件单一，备份和迁移简便 |
| Go 集成 | 使用 `modernc.org/sqlite` (纯 Go 实现，无 CGO 依赖)，跨平台编译无障碍 |

**存储结构概要：**

- `memories` 表：存储记忆原始内容、时间戳、来源 Agent 标识；
- `memories_fts` 虚拟表：FTS5 索引，用于全文检索；
- `save_logs` 表：记录 AI Agent 保存记忆的操作日志；
- `query_logs` 表：记录 AI Agent 查询记忆的操作日志（含查询条件和返回结果）。

> **后续版本扩展**：如需语义向量搜索，可引入 `chromem-go`（纯 Go 内存向量数据库，`github.com/philippgille/chromem-go`），配合本地 ONNX 嵌入模型实现语义检索，且无需外部服务。

### 2.4 人类管理 UI

**选型：Vue 3 + TypeScript，由 Go 后端静态托管**

| 评估维度 | 说明 |
| --- | --- |
| 架构简洁 | 前端编译产物由 Go HTTP 服务器直接托管，无需独立前端服务 |
| 跨平台 | 基于浏览器访问，macOS 和 Windows 无差异 |
| 开发效率 | Vue 3 Composition API + TypeScript 提供良好的开发体验 |
| 构建工具 | Vite 提供快速的热重载和生产构建 |

**UI 功能模块：**

- 记忆数据查询与展示；
- 指定记忆数据删除；
- AI 保存记忆操作日志查看（时间 / 原始内容）；
- AI 查询记忆操作日志查看（时间 / 查询条件 / 返回结果）。

### 2.5 自启动方案

| 操作系统 | 方案 | 说明 |
| --- | --- | --- |
| macOS | launchd plist | 安装至 `~/Library/LaunchAgents/`，用户登录后自动启动 |
| Windows | Windows Service | 通过 `golang.org/x/sys/windows/svc` 注册为系统服务，随系统启动 |

### 2.6 打包与分发

| 操作系统 | 方案 | 说明 |
| --- | --- | --- |
| macOS | `.pkg` 安装包 | 使用 `pkgbuild` + `productbuild` 制作，包含安装后脚本自动注册 launchd |
| Windows | `.msi` 安装包 | 使用 WiX Toolset 制作，包含 Windows Service 自动注册 |

### 2.7 构建与持续集成

**选型：GitHub Actions**

- 使用 `matrix` 策略同时构建 macOS (darwin/amd64 + darwin/arm64) 和 Windows (windows/amd64) 产物；
- 前端在 CI 中先执行 `vite build`，产物内嵌至 Go 二进制（通过 `embed.FS`）；
- CI 产物直接上传至 GitHub Release。

---

## 三、技术栈汇总

| 层次 | 技术 | 版本要求 |
| --- | --- | --- |
| 后端语言 | Go | 1.22+ |
| HTTP 框架 | Go 标准库 `net/http` + `chi` 路由 | chi v5 |
| 数据库 | SQLite (modernc.org/sqlite) | latest |
| 全文搜索 | SQLite FTS5 | 内置 |
| 前端框架 | Vue 3 + TypeScript | Vue 3.x |
| 前端构建 | Vite | 5.x |
| 前端组件库 | Element Plus | 2.x |
| 系统服务 | golang.org/x/sys | latest |
| CI/CD | GitHub Actions | - |
| 打包 (macOS) | pkgbuild / productbuild | 系统内置 |
| 打包 (Windows) | WiX Toolset | 4.x |

---

## 四、关键技术决策说明

### 4.1 为何选择 Go 而非 Python / Node.js

Python 和 Node.js 均需要运行时环境，本地一键部署时需同时打包运行时，增加安装包体积和部署复杂度。Go 编译为单一可执行文件，用户体验更佳。

### 4.2 为何选择 REST 而非 MCP

MCP (Model Context Protocol) 目前仍处于快速演进阶段，协议复杂度较高。REST API 作为基础层，兼容所有 AI Agent 框架，后续可在不破坏现有接口的前提下增加 MCP 支持层。

### 4.3 为何选择 SQLite 而非独立向量数据库

独立向量数据库 (如 Qdrant、ChromaDB) 需要独立进程，增加本地部署复杂度。SQLite FTS5 在小规模数据集上性能完全满足需求，且与主进程同生命周期，部署更简单。

### 4.4 为何前端内嵌至 Go 二进制

通过 Go 的 `embed.FS` 将编译后的前端静态文件内嵌至 Go 可执行文件，实现真正的"单文件部署"，用户无需配置 Web 服务器或前端运行环境。

---

## 五、待确认事项

- [ ] 项目经理审批本技术路线；
- [ ] 审批通过后，由 Lydia 补充 Mia (前端)、Neo (后端)、Sparrow (测试) 的技能定义至 tbp_v1.0.md。
