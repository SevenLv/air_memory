# AIR_Memory 环境变量配置说明

> 文档版本：v1.1
> 对应里程碑：M4 — 部署配置就绪

## 概述

AIR_Memory 后端服务的所有性能阈值和路径配置均通过环境变量暴露，可在不重新构建的情况下通过 `.env` 文件覆盖配置值。

---

## 配置方式

### 方式一：使用 .env 文件（推荐）

在项目根目录创建 `.env` 文件，uvicorn 启动时会自动加载：

```env
STORE_RESPONSE_LIMIT_MS=200
HOT_MEMORY_BUDGET_MB=4096
```

### 方式二：设置系统环境变量

在启动服务前直接导出环境变量：

```bash
export STORE_RESPONSE_LIMIT_MS=200
export HOT_MEMORY_BUDGET_MB=4096
```

修改配置后重新启动服务即可生效：

```bash
./start.sh
```

---

## 环境变量列表

### 服务端口与静态文件配置

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `PORT` | `8080` | 服务监听端口（由启动脚本通过 uvicorn 命令行参数设置） |
| `STATIC_DIR` | `./frontend/dist` | 前端静态文件目录（预构建 Vue.js 3 产物），目录不存在时跳过挂载 |
| `CORS_ORIGINS` | `http://localhost:8080,http://127.0.0.1:8080` | 允许的 CORS 来源（逗号分隔，AI Agent 若来自其他端口需添加对应来源） |

### 存储路径配置

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `CHROMA_COLD_PATH` | `./data/chroma_cold` | 冷层 ChromaDB 持久化数据目录 |
| `DB_PATH` | `./data/logs.db` | SQLite 日志数据库文件路径 |

---

### Embedding 模型配置

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | 使用的 sentence-transformers 模型名称 |
| `HF_HOME` | `./models` | HuggingFace 模型缓存目录 |

> **注意**：如需替换 Embedding 模型，需确保模型已预先下载至 `HF_HOME` 目录。

---

### 响应时间阈值

| 变量名 | 默认值 | 单位 | 说明 |
| --- | --- | --- | --- |
| `STORE_RESPONSE_LIMIT_MS` | `100` | 毫秒 | 记忆存储接口响应时间上限；超过此值时日志记录警告 |
| `QUERY_RESPONSE_LIMIT_MS` | `100` | 毫秒 | 记忆查询接口响应时间上限；超过此值时日志记录警告 |

> **调试建议**：在测试环境中可适当调高（如 `1000`），以避免因环境限制导致的误报。

---

### 热层内存预算

| 变量名 | 默认值 | 单位 | 说明 |
| --- | --- | --- | --- |
| `HOT_MEMORY_BUDGET_MB` | `6144` | MB | 热层（EphemeralClient 内存中）的记忆总大小上限，默认 6GB；超出后触发降级到冷层 |

---

### 磁盘水位配置

| 变量名 | 默认值 | 单位 | 说明 |
| --- | --- | --- | --- |
| `DISK_TRIGGER_GB` | `38` | GB | 磁盘使用量触发淘汰阈值；超过此值开始淘汰低价值最旧记忆 |
| `DISK_SAFE_GB` | `35` | GB | 磁盘淘汰目标水位；淘汰操作持续到磁盘使用量降至此值以下 |
| `DISK_MAX_GB` | `40` | GB | 磁盘使用量硬上限；系统磁盘占用不超过此值（包含 ChromaDB 数据 + SQLite） |
| `DISK_CHECK_INTERVAL_S` | `3600` | 秒 | 磁盘占用定期检查间隔，默认 1 小时 |

---

### 新记忆保护时长

| 变量名 | 默认值 | 单位 | 说明 |
| --- | --- | --- | --- |
| `MEMORY_PROTECT_HOURS` | `168` | 小时 | 新存入记忆的保护时长（默认 7 天 × 24 小时 = 168 小时）；保护期内的记忆不参与磁盘淘汰 |

---

### 层间迁移阈值

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `PROMOTE_THRESHOLD` | `0.6` | 价值分升级阈值：冷层中价值分 ≥ 此值时，记忆升级至热层 |
| `DEMOTE_THRESHOLD` | `0.3` | 价值分降级阈值：热层中价值分 < 此值时，记忆降级至冷层 |

---

### 价值分配置

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `INITIAL_VALUE_SCORE` | `0.5` | 新存入记忆的初始价值分 |
| `FEEDBACK_STEP` | `0.1` | 每次反馈操作（helpful/unhelpful）引起的价值分变化步长 |

---

### ChromaDB 集合名称

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `HOT_COLLECTION` | `hot_memories` | 热层 ChromaDB 集合名称 |
| `COLD_COLLECTION` | `cold_memories` | 冷层 ChromaDB 集合名称 |

> **注意**：集合名称变更后，已有数据将无法访问，通常无需修改。

---

## 完整 .env 示例

```env
# AIR_Memory 环境变量配置示例

# 服务端口（由启动脚本通过 uvicorn 命令行参数设置，通常不需在 .env 中配置）
# PORT=8080

# 前端静态文件目录（预构建 Vue.js 3 产物）
STATIC_DIR=./frontend/dist

# 允许的 CORS 来源（逗号分隔）
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# 存储路径
CHROMA_COLD_PATH=./data/chroma_cold
DB_PATH=./data/logs.db

# Embedding 模型
EMBEDDING_MODEL=all-MiniLM-L6-v2
HF_HOME=./models

# 响应时间阈值（毫秒）
STORE_RESPONSE_LIMIT_MS=100
QUERY_RESPONSE_LIMIT_MS=100

# 热层内存预算（MB）
HOT_MEMORY_BUDGET_MB=6144

# 磁盘水位（GB）
DISK_TRIGGER_GB=38
DISK_SAFE_GB=35
DISK_MAX_GB=40
DISK_CHECK_INTERVAL_S=3600

# 新记忆保护时长（小时）
MEMORY_PROTECT_HOURS=168

# 层间迁移阈值
PROMOTE_THRESHOLD=0.6
DEMOTE_THRESHOLD=0.3

# 价值分配置
INITIAL_VALUE_SCORE=0.5
FEEDBACK_STEP=0.1

# ChromaDB 集合名称
HOT_COLLECTION=hot_memories
COLD_COLLECTION=cold_memories
```
