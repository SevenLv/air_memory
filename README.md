# AIR Memory
Memory System for AI Agent

**当前版本**: v1.2.5

## 重要说明

所有 AI 在执行本项目任务之前必须阅读并遵守 /ai_rules/README.md

## 团队建设计划

所有 AI 在执行本项目任务之前必须阅读 /doc/tbp_v1.1.md, 以了解团队架构和职责分配, 确保能明确知道应该与谁合作.

---

## 快速开始

### 获取发布包

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest)，下载最新版本的发布包并解压。

### 环境前提

- Python 3.11 或更高版本

### 启动服务

**macOS / Linux**:

```bash
bash start.sh
```

**Windows**:

```cmd
start.bat
```

首次启动时脚本将自动创建虚拟环境、安装依赖并下载 Embedding 模型（约 90 MB），约需 3~8 分钟，请耐心等待。

启动成功后访问 `http://localhost:8080` 即可使用 Web 管理界面。

详细部署说明请参阅 `doc/deploy_guide.md`，使用说明请参阅 `doc/user_guide.md`。

---

## 目录结构

```mermaid
graph LR
    ROOT["air_memory/"]

    ROOT --> BACKEND["backend/"]
    ROOT --> FRONTEND["frontend/"]
    ROOT --> DOC["doc/"]
    ROOT --> DATA["data/（运行时生成）"]
    ROOT --> MODELS["models/（运行时生成）"]
    ROOT --> START_SH["start.sh"]
    ROOT --> START_BAT["start.bat"]
    ROOT --> README["README.md"]

    BACKEND --> BE_SRC["src/air_memory/"]
    BACKEND --> BE_TESTS["tests/"]
    BACKEND --> BE_PYPROJECT["pyproject.toml"]

    BE_SRC --> BE_MAIN["main.py（FastAPI 入口）"]
    BE_SRC --> BE_API["api/（REST API 路由）"]
    BE_SRC --> BE_MCP["mcp/（MCP Server）"]
    BE_SRC --> BE_MEM["memory/（记忆存储模块）"]
    BE_SRC --> BE_LOG["log/（操作日志模块）"]
    BE_SRC --> BE_MODELS["models/（Pydantic 数据模型）"]

    FRONTEND --> FE_SRC["src/（Vue.js 3 源代码）"]
    FRONTEND --> FE_DIST["dist/（预构建静态文件）"]
    FRONTEND --> FE_TESTS["tests/（Vitest 单元测试）"]

    DOC --> D1["pdd_v1.4.md（产品定义）"]
    DOC --> D2["sad_v1.11.md（系统架构设计）"]
    DOC --> D3["tsr_v1.3.md（技术路线选型）"]
    DOC --> D4["tbp_v1.1.md（团队建设计划）"]
    DOC --> D5["srd_v1.1.md（系统需求定义）"]
    DOC --> D6["deploy_guide.md（部署手册）"]
    DOC --> D7["user_guide.md（用户手册）"]
    DOC --> D8["release_notes_v1.2.4.md（发布说明）"]
```

### 目录说明

| 目录/文件 | 说明 |
| --- | --- |
| `backend/src/air_memory/` | 后端 Python 源代码，所有后端业务逻辑在此目录下开发 |
| `backend/tests/` | 后端单元测试，使用 pytest + pytest-asyncio + httpx |
| `frontend/src/` | 前端 Vue.js 3 源代码，所有前端业务逻辑在此目录下开发 |
| `frontend/dist/` | 预构建前端静态文件，随仓库分发，部署时无需安装 Node.js |
| `frontend/tests/` | 前端单元测试，使用 Vitest + Vue Test Utils |
| `data/` | 运行时数据目录（ChromaDB 冷层数据和 SQLite 日志），进程重启不丢失 |
| `models/` | Embedding 模型缓存目录（首次启动时自动下载） |
| `doc/` | 项目所有文档，包括产品定义、架构设计、部署手册和用户手册 |
