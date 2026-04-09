# AIR_Memory 技术路线选型报告

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-9 | 初稿 |
| 1.1 | 2026-4-9 | 项目经理审批通过，确认选用方案一；更新选型结论 |

## 1. 技术需求分析

根据 `/doc/pdd_v1.0.md` 中的产品定义，提炼出以下关键技术需求：

| 需求类别 | 具体要求 |
| --- | --- |
| 部署平台 | 支持 macOS 和 Windows 本地一键部署，默认自启动 |
| 接口协议 | 向 AI Agent 提供记忆存储接口和记忆查询接口 |
| 性能指标 | 记忆存储操作 ≤ 100ms；记忆查询操作 ≤ 100ms |
| 管理 UI | 供人类使用的 Web UI，支持查询/删除记忆、查看存取日志 |
| 文档 | 提供完整的部署手册和用户手册 |

## 2. 技术选型维度

| 维度 | 说明 |
| --- | --- |
| 跨平台支持 | 必须同时支持 macOS 和 Windows，且部署步骤尽可能简单 |
| 性能 | 100ms 以内的存储和查询响应；向量相似度搜索须高效 |
| 可维护性 | 代码可读性、生态成熟度、社区活跃度 |
| 部署复杂度 | 本地一键部署，自启动，尽量减少外部依赖 |
| AI Agent 接口 | 支持 MCP（Model Context Protocol）和/或 REST API |
| 开发效率 | AI 研发团队（Mia/Neo/Sparrow）的上手难度与工具链完善程度 |

## 3. 核心技术组件分析

### 3.1 记忆存储引擎

AI Agent 的记忆需要支持语义相似度检索（向量搜索），同时需要满足 100ms 的响应时间。

| 方案 | 描述 | 嵌入式 | 向量搜索 | 跨平台 |
| --- | --- | --- | --- | --- |
| **ChromaDB** | Python 原生嵌入式向量数据库 | ✅ | ✅ | ✅ |
| **LanceDB** | Rust 实现的嵌入式向量数据库，有 Python/JS SDK | ✅ | ✅ | ✅ |
| **SQLite + sqlite-vec** | SQLite 扩展，支持向量搜索 | ✅ | ✅ | ✅ |
| **Qdrant (embedded)** | Rust 实现，支持嵌入式模式 | ✅ | ✅ | ✅ |
| **Weaviate / Milvus** | 需要独立服务，部署复杂 | ❌ | ✅ | ✅ |

> **注意**：向量搜索需要 Embedding 模型生成向量。为保证 100ms 内响应，应使用本地轻量级 Embedding 模型（如 `nomic-embed-text`、`all-MiniLM-L6-v2`）或直接使用关键字/BM25 搜索（不需要 Embedding）。如果使用远程 Embedding API（如 OpenAI），网络延迟将无法保证 100ms 以内。

### 3.2 AI Agent 接口协议

| 协议 | 描述 | 适用场景 |
| --- | --- | --- |
| **MCP（Model Context Protocol）** | Anthropic 推出的 AI Agent 工具标准协议，Claude/Cursor 等原生支持 | AI Agent 工具调用首选 |
| **REST API（HTTP/JSON）** | 通用性最强，几乎所有 AI Agent 均可调用 | 广泛兼容 |
| **gRPC** | 高性能，但需要客户端生成代码，AI Agent 集成复杂 | 不推荐作为主要接口 |

> 推荐同时提供 **MCP** 和 **REST API** 两种接口，以最大化兼容性。

### 3.3 后端框架

| 语言/框架 | 性能 | 开发效率 | 跨平台 | 生态 |
| --- | --- | --- | --- | --- |
| **Python + FastAPI** | 中 | 高 | ✅ | 丰富（AI/ML 生态最完善）|
| **Go + Gin** | 高 | 中 | ✅ | 良好 |
| **Node.js + Fastify** | 中高 | 高 | ✅ | 丰富 |
| **Rust + Axum** | 极高 | 低 | ✅ | 较新，学习曲线陡峭 |

### 3.4 前端框架

| 框架 | 学习曲线 | 生态 | 性能 | 适合场景 |
| --- | --- | --- | --- | --- |
| **React + TypeScript** | 中 | 最丰富 | 高 | 复杂交互 UI |
| **Vue.js 3 + TypeScript** | 低 | 丰富 | 高 | 中小型管理后台 |
| **Svelte + TypeScript** | 低 | 较小 | 极高 | 轻量级场景 |

### 3.5 部署与自启动

| 方案 | 描述 | 一键部署 | 自启动 | 跨平台 |
| --- | --- | --- | --- | --- |
| **Docker + docker-compose** | 容器化部署，最简一键启动 | ✅ | ✅（配合 restart policy）| ✅ |
| **单体可执行文件** | 编译为单一二进制（Go/Rust）| ✅ | 需配置系统服务 | ✅ |
| **Python 打包（PyInstaller）** | 将 Python 应用打包为可执行文件 | ✅ | 需配置系统服务 | ✅ |
| **Electron** | 桌面应用，内嵌 Web UI | ✅ | ✅ | ✅ |

---

## 4. 备选方案

### 方案一：Python 生态全栈方案

**技术组成**

| 组件 | 技术选型 |
| --- | --- |
| 后端框架 | Python 3.11+ + FastAPI |
| 记忆存储 | ChromaDB（嵌入式向量数据库）|
| AI Agent 接口 | MCP Server（`mcp` Python SDK）+ REST API |
| 前端框架 | Vue.js 3 + TypeScript + Element Plus |
| 部署方式 | Docker + docker-compose |
| 自启动 | Docker restart policy `always` |
| 日志存储 | SQLite（记录存/查操作日志）|

**架构图**

```
AI Agent
  │
  ├─── MCP Protocol ────────┐
  └─── REST API (HTTP/JSON) ─┤
                             │
                     ┌───────▼──────────┐
                     │  FastAPI Backend  │
                     │  (Python 3.11+)   │
                     └───┬──────────┬───┘
                         │          │
               ┌─────────▼──┐  ┌────▼──────┐
               │  ChromaDB   │  │  SQLite    │
               │ (向量存储)  │  │ (操作日志) │
               └─────────────┘  └───────────┘
                         │
                 ┌────────▼───────┐
                 │  Vue.js 3 UI   │
                 │  (管理界面)    │
                 └────────────────┘
```

**优点**

- Python 在 AI/ML 生态中地位无可替代，ChromaDB、Embedding 模型库（sentence-transformers）等均为 Python 原生；
- FastAPI 自动生成 OpenAPI 文档，接口开发效率高；
- `mcp` Python SDK 官方支持，MCP Server 开发成本最低；
- Docker 部署方案在 macOS 和 Windows 均成熟稳定；
- 研发和测试工程师学习成本低，社区资源丰富。

**缺点**

- Python 运行时性能低于 Go/Rust，在高并发场景下需要额外调优；
- Docker Desktop 在 Windows 上需要 WSL2 支持，用户环境配置略复杂；
- ChromaDB 使用本地轻量级 Embedding 时，首次加载模型有一定延迟（但后续操作可在 100ms 内完成）；
- Python 环境打包（非 Docker 方式）较为繁琐。

---

### 方案二：Go 生态高性能方案

**技术组成**

| 组件 | 技术选型 |
| --- | --- |
| 后端框架 | Go 1.22+ + Gin |
| 记忆存储 | SQLite + sqlite-vec（向量搜索扩展）|
| AI Agent 接口 | MCP Server（`mark3labs/mcp-go`）+ REST API |
| 前端框架 | Vue.js 3 + TypeScript + Element Plus |
| 部署方式 | 单一可执行文件（内嵌前端静态资源）|
| 自启动 | macOS LaunchAgent / Windows 服务 / NSSM |
| 日志存储 | SQLite（同一数据库）|

**架构图**

```
AI Agent
  │
  ├─── MCP Protocol ───────────┐
  └─── REST API (HTTP/JSON) ───┤
                               │
                       ┌───────▼──────────────┐
                       │     Go + Gin Backend  │
                       │  (单一可执行文件)      │
                       │  内嵌 Vue.js 静态资源 │
                       └───────────┬───────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ SQLite + sqlite-vec │
                         │ (向量存储 + 日志)   │
                         └───────────────────┘
```

**优点**

- Go 编译为单一可执行文件，部署极简，无需 Docker 或额外运行时；
- 内存占用低，启动速度快，响应性能优于 Python；
- SQLite 嵌入式，无需独立数据库服务，sqlite-vec 支持向量相似度搜索；
- 跨平台编译（`GOOS=windows/darwin`）原生支持，分发方便；
- 自启动配置相对简单（macOS LaunchAgent plist / Windows 注册表服务）。

**缺点**

- `sqlite-vec` 向量搜索能力弱于专用向量数据库，百万级记忆量时性能存在瓶颈；
- Go 生态中 MCP SDK（`mcp-go`）为第三方维护，成熟度不及 Python 官方 SDK；
- Embedding 模型调用需借助外部服务（Ollama/OpenAI API）或通过 CGO 调用 ONNX Runtime，增加部署复杂度；
- 前端开发需分离项目或使用 `go:embed`，开发体验略低于一体化方案；
- 研发工程师需要有 Go 语言经验。

---

### 方案三：Node.js 全栈方案

**技术组成**

| 组件 | 技术选型 |
| --- | --- |
| 后端框架 | Node.js 20+ + TypeScript + Fastify |
| 记忆存储 | LanceDB（嵌入式向量数据库，Rust 实现，提供 Node.js SDK）|
| AI Agent 接口 | MCP Server（`@modelcontextprotocol/sdk`）+ REST API |
| 前端框架 | React 18 + TypeScript + Ant Design |
| 部署方式 | Docker + docker-compose / `pkg` 打包为单一可执行文件 |
| 自启动 | Docker restart policy / PM2 + 系统服务 |
| 日志存储 | LanceDB（同一数据库）|

**架构图**

```
AI Agent
  │
  ├─── MCP Protocol ────────────┐
  └─── REST API (HTTP/JSON) ────┤
                                │
                       ┌────────▼───────────────┐
                       │  Fastify Backend (Node) │
                       │  TypeScript             │
                       └───────────┬─────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │      LanceDB        │
                         │  (向量存储 + 日志)  │
                         └───────────────────┘
                                   │
                         ┌─────────▼──────────┐
                         │  React 18 + Ant Design │
                         │     (管理界面)         │
                         └───────────────────────┘
```

**优点**

- 前后端统一使用 TypeScript，代码风格一致，类型安全，维护成本低；
- `@modelcontextprotocol/sdk` 为 MCP 官方 JavaScript SDK，支持成熟；
- LanceDB Node.js SDK 直接调用 Rust 底层，向量搜索性能优异；
- 前后端开发者可以共享接口类型定义，减少沟通成本；
- Docker 部署和 PM2 自启动方案均成熟可靠。

**缺点**

- Node.js 单线程模型在计算密集型任务（如 Embedding 生成）时存在性能瓶颈；
- LanceDB Node.js SDK 相比 Python SDK 社区资源较少；
- `pkg` 打包单一可执行文件功能有限，Windows/macOS 原生服务配置较繁琐；
- Embedding 模型的 Node.js 生态（`@xenova/transformers`）成熟度不及 Python；
- 整体生态丰富度弱于 Python 方案，遇到 AI 相关问题时可参考资料较少。

---

## 5. 方案综合对比

| 评估维度 | 方案一（Python）| 方案二（Go）| 方案三（Node.js）|
| --- | --- | --- | --- |
| **跨平台部署** | ✅ Docker | ✅ 单一可执行文件 | ✅ Docker |
| **部署简单度** | 中（需 Docker）| 高（单文件）| 中（需 Docker）|
| **自启动配置** | 简单（Docker）| 中等（系统服务）| 中等（PM2/Docker）|
| **性能（存储）** | 中 | 高 | 中高 |
| **性能（查询）** | 中（可满足 100ms）| 高 | 中高 |
| **向量搜索能力** | 高（ChromaDB）| 中（sqlite-vec）| 高（LanceDB）|
| **MCP 支持** | 官方 SDK ✅ | 第三方 SDK ⚠️ | 官方 SDK ✅ |
| **Embedding 生态** | 最丰富 ✅ | 依赖外部服务 ⚠️ | 中等 ⚠️ |
| **前端开发效率** | 中 | 中 | 高（TS 统一）|
| **代码可维护性** | 高 | 高 | 高 |
| **学习成本** | 低 | 中 | 低 |
| **社区/生态** | 最丰富 ✅ | 良好 | 丰富 |
| **综合评分** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 6. 架构师推荐方案

### 推荐：方案一（Python 生态全栈方案）

**推荐理由：**

1. **AI 生态契合度最高**：AIR_Memory 是 AI Agent 的记忆系统，核心能力（向量 Embedding、语义搜索、MCP 协议）均在 Python 生态中最为成熟；
2. **性能可达标**：使用本地轻量级 Embedding 模型（如 `all-MiniLM-L6-v2`，向量维度 384），配合 ChromaDB 的 HNSW 索引，单次查询在毫秒级别，完全满足 100ms 要求；
3. **MCP 官方支持**：Python MCP SDK 由 Anthropic 官方维护，稳定性和兼容性最佳；
4. **部署方案成熟**：Docker + docker-compose 一键部署在 macOS 和 Windows 均有成熟方案，配合 `restart: always` 实现自启动；
5. **开发效率高**：FastAPI 自动生成 API 文档，ChromaDB API 简洁，Vue.js 3 上手容易，整体开发效率最高；
6. **风险最低**：团队 AI 成员对 Python 生态最为熟悉，社区资源最丰富，遇到问题解决成本低。

**性能保障措施：**

- 使用 `sentence-transformers` 库加载本地 Embedding 模型，在服务启动时预热模型，避免首次请求延迟；
- ChromaDB 使用 HNSW 索引，支持 ANN（近似最近邻）搜索，百万级记忆量查询可在 10ms 以内完成；
- FastAPI 使用 `asyncio` 异步处理，避免 I/O 阻塞；
- 日志写入使用异步操作，不阻塞主业务响应。

### 备选：方案二（Go 高性能方案）

若项目对**部署简便性**要求极高（不希望依赖 Docker），或对**资源占用**有严格限制（如内存 < 100MB），可考虑方案二。但需要接受 Embedding 能力依赖外部服务（Ollama）的约束。

---

## 7. 选型结论

**项目经理已审批通过，正式采用方案一（Python 生态全栈方案）。**

| 审批事项 | 决策结果 |
| --- | --- |
| 部署方式 | ✅ 采用 Docker + docker-compose，接受 Docker Desktop 作为必要依赖 |
| Embedding 策略 | ✅ 使用本地轻量级 Embedding 模型（`all-MiniLM-L6-v2`），无需联网，包体积增加约 100MB 可接受 |
| 技术栈选型 | ✅ **方案一：Python 3.11+ + FastAPI + ChromaDB + Vue.js 3** |

**最终技术栈：**

| 组件 | 技术选型 |
| --- | --- |
| 后端框架 | Python 3.11+ + FastAPI |
| 记忆存储 | ChromaDB（嵌入式向量数据库）|
| Embedding | sentence-transformers（`all-MiniLM-L6-v2`，本地运行）|
| AI Agent 接口 | MCP Server（`mcp` Python SDK）+ REST API |
| 前端框架 | Vue.js 3 + TypeScript + Element Plus |
| 部署方式 | Docker + docker-compose |
| 自启动 | Docker restart policy `always` |
| 日志存储 | SQLite + aiosqlite（记录存/查操作日志）|

本技术路线已确认，后续各研发工程师须严格遵循上述技术栈进行系统设计和研发。

---

## 附录：关键依赖版本参考（方案一）

| 依赖 | 推荐版本 | 说明 |
| --- | --- | --- |
| Python | 3.11+ | 主运行时 |
| FastAPI | 0.115+ | 后端框架 |
| ChromaDB | 0.6+ | 向量数据库 |
| sentence-transformers | 3.x | 本地 Embedding |
| mcp | 1.x | MCP Python SDK |
| Vue.js | 3.4+ | 前端框架 |
| Element Plus | 2.x | Vue UI 组件库 |
| Docker | 27+ | 容器运行时 |
| docker-compose | v2.x | 编排工具 |
