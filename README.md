# AIR Memory
Memory System for AI Agent

## 重要说明

所有 AI 在执行本项目任务之前必须阅读并遵守 /ai_rules/README.md

## 团队建设计划

所有 AI 在执行本项目任务之前必须阅读 /doc/tbp_v1.0.md, 以了解团队架构和职责分配, 确保能明确知道应该与谁合作.

---

## 目录规划

```
air_memory/                       # 仓库根目录
├── backend/                      # 后端服务（Python 3.11+ + FastAPI）
│   ├── src/
│   │   └── air_memory/           # 主 Python 包（源代码目录）
│   │       ├── __init__.py
│   │       ├── main.py           # FastAPI 应用入口
│   │       ├── api/              # REST API 路由模块
│   │       ├── mcp/              # MCP Server 模块
│   │       ├── memory/           # 记忆存储模块（ChromaDB）
│   │       ├── log/              # 操作日志模块（SQLite + aiosqlite）
│   │       └── models/           # Pydantic 数据模型
│   ├── tests/                    # 后端单元测试目录（pytest）
│   ├── pyproject.toml            # Python 项目配置
│   └── requirements.txt          # 运行时依赖
├── frontend/                     # 前端应用（Vue.js 3 + TypeScript + Element Plus）
│   ├── src/                      # 前端源代码目录
│   │   ├── api/                  # HTTP 请求模块（Axios）
│   │   ├── components/           # 公共 Vue 组件
│   │   ├── router/               # Vue Router 路由配置
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── views/                # 页面视图组件
│   │   ├── App.vue               # 根组件
│   │   └── main.ts               # 应用入口
│   ├── tests/                    # 前端单元测试目录（Vitest）
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── README.md                     # 本文件
└── doc/                          # 项目文档
    ├── pdd_v1.0.md               # 产品定义文档
    ├── tsr_v1.1.md               # 技术路线选型报告
    ├── tbp_v1.1.md               # 团队建设计划
    └── sad_v1.0.md               # 系统架构设计说明书
```

### 目录说明

| 目录/文件 | 说明 |
| --- | --- |
| `backend/src/air_memory/` | 后端 Python 源代码，所有后端业务逻辑在此目录下开发 |
| `backend/tests/` | 后端单元测试，使用 pytest + pytest-asyncio + httpx |
| `frontend/src/` | 前端 Vue.js 3 源代码，所有前端业务逻辑在此目录下开发 |
| `frontend/tests/` | 前端单元测试，使用 Vitest + Vue Test Utils |
| `doc/` | 项目所有文档，包括产品定义、技术路线和架构设计 |

### 快速开始

#### 后端开发环境

```bash
cd backend
pip install -e ".[dev]"
# 运行测试
pytest
# 启动开发服务器
uvicorn air_memory.main:app --reload
```

#### 前端开发环境

```bash
cd frontend
npm install
# 运行测试
npm run test
# 启动开发服务器
npm run dev
```
