# AIR_Memory 技术路线选型报告

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-8 | 初稿 |
| 1.1 | 2026-4-8 | 补充各技术项备选方案及对比分析 |

> 文档编写：Nia（项目助理）；技术内容来源：Lydia（系统架构师）

---

## 一、背景与目标

本报告基于产品定义文档 (pdd_v1.0.md) 进行技术路线选型。AIR_Memory 是一个为 AI Agent 设计的本地部署记忆系统，选型工作需同时满足以下约束：

| 约束 | 来源 |
| --- | --- |
| 支持 macOS / Windows 一键本地部署 | pdd_v1.0.md |
| 保存记忆操作时间 ≤ 100ms | pdd_v1.0.md |
| 查询记忆操作时间 ≤ 100ms | pdd_v1.0.md |
| 系统默认自启动 | pdd_v1.0.md |
| 向 AI Agent 提供标准接口 | pdd_v1.0.md |
| 向人类提供管理 UI | pdd_v1.0.md |

---

## 二、技术选型详细分析

### 2.1 后端语言

#### 2.1.1 候选方案

本项目考察了以下三种主流后端语言：

| 方案 | 运行方式 | 跨平台编译 | 单文件分发 | HTTP 性能 | 系统服务集成 | 部署复杂度 |
| --- | --- | --- | --- | --- | --- | --- |
| **Go 1.22+** | 编译型，无运行时 | ✅ 原生交叉编译 | ✅ 单二进制 | ⭐⭐⭐⭐⭐ | ✅ golang.org/x/sys | 极低 |
| Python 3.12 | 解释型，需 CPython 运行时 | ⚠️ 需 PyInstaller 打包 | ⚠️ 捆绑解释器，体积 > 50MB | ⭐⭐⭐ | ⚠️ 需第三方库 | 中等 |
| Node.js 20 (TypeScript) | 解释型，需 Node 运行时 | ⚠️ 需 pkg/nexe 打包 | ⚠️ 捆绑 V8，体积 > 40MB | ⭐⭐⭐⭐ | ⚠️ 需第三方库 | 中等 |
| Rust 1.77+ | 编译型，无运行时 | ✅ 原生交叉编译 | ✅ 单二进制 | ⭐⭐⭐⭐⭐ | ✅ windows-service crate | 极低 |

#### 2.1.2 对比分析

**Go vs Python**：Python 在 AI/ML 生态上有优势，但 AIR_Memory 本身不需要运行机器学习模型，只需要提供 HTTP 接口和数据库操作。Python 的部署需要将 CPython 解释器一起打包（使用 PyInstaller 或 cx_Freeze），生成的安装包体积较大（通常超过 50MB），且偶发路径问题会导致"一键部署"的用户体验不稳定。

**Go vs Node.js**：Node.js（TypeScript）开发效率高，但同样需要捆绑 V8 引擎进行分发，且 Node.js 的单线程事件循环在高并发下（多个 AI Agent 同时调用）需要额外注意阻塞操作。Go 的 goroutine 并发模型更适合服务端场景。

**Go vs Rust**：Rust 在性能和内存安全上与 Go 相当，但 Rust 的编译时间长、学习曲线陡峭，对 AI 成员团队的开发效率有负面影响。Rust 的异步生态（Tokio）虽然成熟，但代码复杂度明显高于 Go 标准库。

#### 2.1.3 选型结论

**选型：Go 1.22+**

Go 是本项目的最优选择：编译为单一可执行文件、无运行时依赖、原生跨平台交叉编译、goroutine 并发模型、系统服务集成简单，综合满足 AIR_Memory 的所有技术约束，且开发和维护成本最低。

---

### 2.2 AI Agent 接口协议

#### 2.2.1 候选方案

| 方案 | 通用性 | AI Agent 框架支持 | 协议成熟度 | 实现复杂度 | 调试便利性 |
| --- | --- | --- | --- | --- | --- |
| **RESTful HTTP API (JSON)** | ⭐⭐⭐⭐⭐ 所有框架原生支持 | ✅ 全覆盖 | 极成熟 | 低 | 极高（curl/浏览器可直接测试） |
| MCP (Model Context Protocol) | ⭐⭐⭐ 主流框架支持中 | ⚠️ 仅部分框架 | 快速演进中，尚不稳定 | 高 | 低（需专用客户端） |
| gRPC | ⭐⭐⭐⭐ | ⚠️ 需生成客户端代码 | 成熟 | 中 | 低（需 grpcurl 等工具） |
| WebSocket | ⭐⭐⭐ | ⚠️ 需额外适配 | 成熟 | 中 | 中 |

#### 2.2.2 对比分析

**REST vs MCP**：MCP（Model Context Protocol）是 Anthropic 推动的面向 AI Agent 的标准协议，理论上最贴合 AIR_Memory 的定位。但 MCP 目前（2026 年 4 月）仍处于快速迭代阶段，协议规范和 SDK 变化频繁，过早采用存在维护成本高、兼容性风险大的问题。REST API 作为基础层，可以保证所有 AI Agent 框架（LangChain、AutoGen、OpenAI Agents SDK、CrewAI 等）无需额外适配即可调用，同时在未来可以在不破坏现有接口的前提下增加 MCP 适配层。

**REST vs gRPC**：gRPC 提供强类型接口和更高的序列化性能，但 AI Agent 框架调用 gRPC 需要生成客户端存根代码，增加了集成复杂度。对于 AIR_Memory 这样的记忆接口（每次调用数据量小，< 1KB），gRPC 相对于 REST 的性能优势不明显，而集成门槛更高。

#### 2.2.3 选型结论

**选型：RESTful HTTP API (JSON)**

REST API 兼容性最广、集成门槛最低、调试最方便，是当前阶段的最优选择。后续版本可在 REST 基础上增加 MCP 支持层，实现平滑升级。

**接口设计概要：**

| 接口路径 | 方法 | 功能说明 |
| --- | --- | --- |
| `/api/v1/memories` | POST | 保存记忆 |
| `/api/v1/memories/search` | POST | 查询相关记忆（支持关键词） |

---

### 2.3 HTTP 路由框架

#### 2.3.1 候选方案

| 方案 | 类型 | 性能 | 轻量程度 | 学习成本 | 中间件生态 |
| --- | --- | --- | --- | --- | --- |
| **Go 标准库 `net/http` + `chi` v5** | 轻量路由 | ⭐⭐⭐⭐⭐ | 极轻量，无额外依赖 | 低 | 丰富（兼容标准 `net/http`） |
| Gin v1 | 全功能框架 | ⭐⭐⭐⭐⭐ | 轻量 | 低 | 丰富 |
| Echo v4 | 全功能框架 | ⭐⭐⭐⭐⭐ | 轻量 | 低 | 中等 |
| Fiber v2 (基于 fasthttp) | 高性能框架 | ⭐⭐⭐⭐⭐ | 中等 | 中等 | 中等 |

#### 2.3.2 对比分析

**chi vs Gin**：Gin 是 Go 生态中最流行的 HTTP 框架，功能完整，社区活跃。chi 的核心优势在于完全兼容 Go 标准库 `net/http`，中间件和处理函数可以直接与标准库互换，不产生框架绑定。AIR_Memory 的接口数量很少（仅 2 个 AI Agent 接口 + 若干 UI 接口），不需要 Gin 提供的全部功能。chi 的轻量性更符合项目需求。

**chi vs Fiber**：Fiber 基于 `fasthttp` 而非标准库，性能极高，但不兼容标准 `net/http` 中间件生态，且 `fasthttp` 的请求对象与标准库不同，存在一定的学习成本和生态局限。

#### 2.3.3 选型结论

**选型：Go 标准库 `net/http` + `chi` v5**

`chi` 轻量、兼容标准库、路由功能完整，适合 AIR_Memory 这种接口数量少但需要长期维护的项目。

---

### 2.4 数据存储方案

#### 2.4.1 候选方案

| 方案 | 类型 | 部署复杂度 | 查询性能（万级数据） | 语义搜索 | 跨平台 | Go 集成 |
| --- | --- | --- | --- | --- | --- | --- |
| **SQLite + FTS5** | 嵌入式关系型 + 全文索引 | 极低（单文件） | < 10ms（FTS5 BM25） | ❌（仅关键词） | ✅ | modernc.org/sqlite（纯 Go） |
| PostgreSQL | 独立关系型数据库 | 高（需单独安装/启动） | < 5ms | ❌ | ✅ | pgx v5 |
| Qdrant | 独立向量数据库 | 高（需 Docker 或安装包） | < 5ms | ✅（语义向量） | ✅ | REST API 调用 |
| ChromaDB | 独立向量数据库 | 高（需 Python 环境） | < 10ms | ✅（语义向量） | ✅ | REST API 调用 |
| BoltDB / bbolt | 嵌入式 KV | 极低（单文件） | ⚠️ 无全文索引，需全扫描 | ❌ | ✅ | 原生 Go |
| BadgerDB | 嵌入式 KV | 极低（目录） | ⚠️ 无全文索引 | ❌ | ✅ | 原生 Go |

#### 2.4.2 对比分析

**SQLite vs PostgreSQL**：PostgreSQL 功能强大，但需要独立的数据库服务进程，用户必须先安装并启动 PostgreSQL，违背"一键部署"的产品要求。AIR_Memory 是单机本地服务，没有多节点并发写入的需求，PostgreSQL 的优势无法体现。

**SQLite vs 向量数据库（Qdrant / ChromaDB）**：向量数据库能提供语义相似度搜索，从理论上看最贴合"记忆查询"场景。但其缺点明显：需要独立进程（违背一键部署要求）、需要本地嵌入模型（增加首次启动时间和资源消耗）、在万级记忆数量的场景下相对 FTS5 并无明显优势。AIR_Memory v1.0 以关键词全文搜索为主，满足基本使用需求；语义搜索可作为后续版本的增强功能，届时可引入 `chromem-go`（纯 Go 内存向量库，`github.com/philippgille/chromem-go`）无需外部服务。

**SQLite vs BoltDB / BadgerDB**：BoltDB 和 BadgerDB 是纯 Go 的嵌入式 KV 存储，无运行时依赖，但均不提供全文搜索能力，实现"查询相关记忆"需要加载全量数据在应用层过滤，无法满足 100ms 响应时间要求（在记忆数量增长后）。SQLite FTS5 提供数据库层面的全文索引，查询性能远优于 KV 全扫描。

**SQLite CGO vs `modernc.org/sqlite`**：标准的 Go SQLite 驱动（如 `mattn/go-sqlite3`）基于 CGO，跨平台交叉编译需要配置 C 工具链，在 GitHub Actions 中配置复杂。`modernc.org/sqlite` 是纯 Go 实现的 SQLite 驱动，无需 CGO，可直接交叉编译，是本项目的最优选择。

#### 2.4.3 选型结论

**选型：SQLite + FTS5（`modernc.org/sqlite` 纯 Go 驱动）**

SQLite 单文件、无需独立服务、FTS5 全文检索性能充分满足 100ms 要求，且通过纯 Go 驱动实现无 CGO 跨平台编译。这是在部署简单性和查询性能之间的最优平衡点。

**存储结构概要：**

| 表名 | 用途 |
| --- | --- |
| `memories` | 存储记忆原始内容、时间戳、来源 Agent 标识 |
| `memories_fts` | FTS5 虚拟表，对 `memories` 内容建立全文索引 |
| `save_logs` | 记录 AI Agent 保存记忆的操作日志（时间 / 原始内容） |
| `query_logs` | 记录 AI Agent 查询记忆的操作日志（时间 / 查询条件 / 返回结果） |

---

### 2.5 人类管理 UI 框架

#### 2.5.1 候选方案

| 方案 | 类型 | 开发效率 | TypeScript 支持 | 生态成熟度 | 组件库丰富度 |
| --- | --- | --- | --- | --- | --- |
| **Vue 3 + TypeScript + Vite** | SPA 前端框架 | ⭐⭐⭐⭐⭐ | ✅ 一等公民 | 成熟 | Element Plus / Naive UI 等 |
| React 18 + TypeScript + Vite | SPA 前端框架 | ⭐⭐⭐⭐ | ✅ 一等公民 | 极成熟 | Ant Design / MUI 等 |
| Svelte 4 + TypeScript | 编译型前端框架 | ⭐⭐⭐⭐ | ✅ | 较成熟 | 相对有限 |
| Wails v2（Go + Vue/React） | 桌面应用框架 | ⭐⭐⭐ | ✅ | 中等 | 依赖前端框架 |
| Tauri（Rust + Vue/React） | 桌面应用框架 | ⭐⭐⭐ | ✅ | 中等 | 依赖前端框架 |

#### 2.5.2 对比分析

**Vue 3 vs React**：React 和 Vue 3 在能力上基本对等。Vue 3 的 Composition API 语法更简洁，模板语法对后端工程师更友好，学习成本略低。两者对 AI 成员（Mia）均可支持；Vue 3 在国内 AI Agent 生态中更常见，选型更自然。

**SPA 前端框架 vs 桌面应用框架（Wails / Tauri）**：
- **Wails**（Go + 前端）方案可以构建真正的桌面应用，但 Wails 会强制要求系统安装 WebView2（Windows）/ WebKit（macOS），增加用户安装前置条件，与"一键部署"目标有冲突。
- **Tauri** 依赖 Rust 工具链，与后端 Go 语言不统一，增加 CI/CD 复杂度。
- **SPA + Go 静态托管**方案：前端编译产物通过 Go `embed.FS` 内嵌至 Go 二进制，用户直接打开浏览器访问 `http://localhost:PORT` 即可使用，无需安装任何桌面运行时，部署最简单。

**Vite vs Webpack**：Vite 提供极快的冷启动和热更新（基于 ESM），开发体验显著优于 Webpack。Vue 3 官方推荐 Vite，两者配合最佳。

#### 2.5.3 选型结论

**选型：Vue 3 + TypeScript + Vite，由 Go 后端通过 `embed.FS` 静态托管**

Vue 3 开发效率高，SPA + Go 静态托管方案实现真正的单文件部署，无需浏览器以外的任何前置安装。选用 **Element Plus 2.x** 作为 UI 组件库，提供完整的表格、表单、分页等管理后台所需组件。

---

### 2.6 系统自启动方案

#### 2.6.1 候选方案

**macOS：**

| 方案 | 启动时机 | 权限要求 | 管理方式 | 适用场景 |
| --- | --- | --- | --- | --- |
| **launchd plist（LaunchAgents）** | 用户登录后启动 | 用户权限（无需 root） | launchctl 命令 | ✅ 推荐：用户级服务 |
| launchd plist（LaunchDaemons） | 系统启动（开机） | 需要 root 权限 | launchctl 命令 | 过度，无需系统级权限 |
| 登录项（Login Items） | 用户登录后启动 | 用户权限 | 系统偏好设置 | GUI 应用更适合，服务不推荐 |

**Windows：**

| 方案 | 启动时机 | 权限要求 | 管理方式 | 适用场景 |
| --- | --- | --- | --- | --- |
| **Windows Service** | 系统启动（开机） | 需要管理员权限安装 | SCM 服务管理器 | ✅ 推荐：后台服务 |
| 注册表 Run 键 | 用户登录后启动 | 用户权限 | 注册表 | 不够正式，不易管理 |
| 计划任务（Task Scheduler） | 按触发器启动 | 可配置 | 任务计划程序 | 配置复杂，不如 Service |

#### 2.6.2 选型结论

| 操作系统 | 选型 | 说明 |
| --- | --- | --- |
| macOS | **launchd plist（LaunchAgents）** | 安装至 `~/Library/LaunchAgents/`，用户登录后自动启动，无需 root 权限 |
| Windows | **Windows Service** | 通过 `golang.org/x/sys/windows/svc` 注册为系统服务，随系统启动，安装阶段需要管理员权限 |

---

### 2.7 安装包打包方案

#### 2.7.1 候选方案

**macOS：**

| 方案 | 安装包格式 | 安装后脚本 | 原生集成度 | 构建工具 |
| --- | --- | --- | --- | --- |
| **pkgbuild + productbuild** | `.pkg` | ✅ postinstall 脚本 | ✅ macOS 原生 | 系统内置，无需安装 |
| DMG + 拖放安装 | `.dmg` | ❌ 无法自动注册服务 | 中等 | create-dmg 等 |
| Homebrew Cask | 依赖 Homebrew | ❌ 需用户手动配置自启 | 中等 | 需维护 Cask 描述文件 |

**Windows：**

| 方案 | 安装包格式 | 服务注册 | 原生集成度 | 构建工具 |
| --- | --- | --- | --- | --- |
| **WiX Toolset 4.x** | `.msi` | ✅ ServiceInstall 元素 | ✅ Windows 原生 | WiX 工具链 |
| NSIS | `.exe` 安装包 | ✅ 脚本实现 | 中等 | NSIS 脚本 |
| Inno Setup | `.exe` 安装包 | ✅ 脚本实现 | 中等 | Inno Setup 脚本 |

#### 2.7.2 选型结论

| 操作系统 | 选型 | 说明 |
| --- | --- | --- |
| macOS | **`.pkg`（pkgbuild + productbuild）** | macOS 系统原生支持的安装包格式，postinstall 脚本可自动注册 launchd 并启动服务 |
| Windows | **`.msi`（WiX Toolset 4.x）** | Windows 官方推荐安装包格式，ServiceInstall 元素可声明式注册 Windows Service |

---

### 2.8 持续集成与构建

#### 2.8.1 候选方案

| 方案 | 托管类型 | 与 GitHub 集成 | 跨平台构建支持 | 免费额度 |
| --- | --- | --- | --- | --- |
| **GitHub Actions** | 云端（GitHub 托管） | ✅ 原生集成 | ✅ matrix 跨平台 | ✅ 公开仓库免费 |
| GitLab CI/CD | 云端 | ⚠️ 需迁移仓库 | ✅ | 有限制 |
| CircleCI | 云端 | ✅ | ✅ | 有限制 |
| 本地 Jenkins | 自托管 | ✅ | ✅ 需自备 runner | 自维护成本高 |

#### 2.8.2 选型结论

**选型：GitHub Actions**

项目已托管于 GitHub，GitHub Actions 是最自然的选择，无需额外配置集成，且 `matrix` 策略可同时构建多平台产物。

**构建流程概要：**

1. 前端：在 CI 中执行 `npm run build`（Vite 构建），产物输出至 `frontend/dist/`；
2. 后端：通过 Go `embed.FS` 将 `frontend/dist/` 内嵌至 Go 可执行文件，执行 `GOOS=darwin/windows GOARCH=amd64/arm64 go build`；
3. 打包：在对应 runner 上使用 `pkgbuild`（macOS）和 WiX（Windows）制作安装包；
4. 发布：CI 产物上传至 GitHub Release。

---

## 三、技术栈汇总

| 层次 | 技术选型 | 版本要求 | 备注 |
| --- | --- | --- | --- |
| 后端语言 | Go | 1.22+ | 跨平台单二进制 |
| HTTP 路由 | chi | v5 | 兼容标准 net/http |
| 数据库驱动 | modernc.org/sqlite | latest | 纯 Go，无 CGO |
| 全文搜索 | SQLite FTS5 | 内置 | BM25 算法 |
| 前端框架 | Vue 3 + TypeScript | Vue 3.x | Composition API |
| 前端构建 | Vite | 5.x | 前端构建工具 |
| 前端组件库 | Element Plus | 2.x | 管理 UI 组件 |
| 前端静态托管 | Go embed.FS | 标准库 | 内嵌至二进制 |
| 系统服务 | golang.org/x/sys | latest | launchd / Windows Service |
| CI/CD | GitHub Actions | - | matrix 多平台构建 |
| 打包 (macOS) | pkgbuild / productbuild | 系统内置 | `.pkg` 格式 |
| 打包 (Windows) | WiX Toolset | 4.x | `.msi` 格式 |

---

## 四、待确认事项

- [ ] 项目经理审批本技术路线；
- [ ] 审批通过后，由 Lydia 补充 Mia（前端）、Neo（后端）、Sparrow（测试）的技能定义至 tbp_v1.0.md。
