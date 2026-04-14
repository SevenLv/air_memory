# AIR_Memory 用户手册

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-10 | 初稿，覆盖 Web 管理界面和 AI Agent 接口使用说明 |
| 1.1 | 2026-4-14 | 补充 Header 版本号显示说明；修正 MCP query_memory 返回示例格式（平铺列表 JSON 字符串）|

---

## 1. 概述

本手册面向两类读者：

- **人类用户**：通过 Web 管理界面对记忆数据进行查询、删除、日志查看和价值评分查看。
- **AI Agent 集成方**：通过 MCP 协议或 REST API 将 AIR_Memory 集成至 AI Agent 工作流。

系统部署完成后，Web 管理界面访问地址为 `http://localhost:8080`。

---

## 2. Web 管理界面使用说明

### 2.1 界面总览

Web 管理界面基于 Vue.js 3 构建，提供四个主要页面，通过顶部导航栏切换：

```mermaid
graph LR
    Nav["顶部导航栏"] --> Home["首页 / - 记忆查询"]
    Nav --> Memories["/memories - 记忆管理"]
    Nav --> Logs["/logs - 操作日志"]
    Nav --> Feedback["/feedback - 价值评分"]
```

顶部导航栏右侧动态显示当前运行的系统版本号（通过 `GET /api/v1/version` 接口获取），便于快速确认所运行的版本。

### 2.2 记忆查询（首页 `/`）

首页提供记忆的语义相似度查询功能。

**操作步骤**：

1. 在搜索框中输入查询关键词或语义描述。
2. 选择查询模式：
   - **快速查询**（`fast_only=true`）：仅检索热层记忆，响应时间 ≤ 100ms，适合对速度敏感的场景。
   - **深度查询**（`fast_only=false`，默认）：同时检索热层和冷层记忆，返回更完整的结果，响应时间无严格限制。
3. 设置返回条目数（`top_k`，默认 5）。
4. 点击搜索按钮发起查询。

**查询结果说明**：

| 字段 | 说明 |
| --- | --- |
| `content` | 记忆原文内容 |
| `similarity` | 与查询内容的语义相似度（0.0 至 1.0，越高越相关） |
| `value_score` | 当前综合价值评分（0.0 至 1.0） |
| `tier` | 所在层：`hot`（热层）或 `cold`（冷层） |
| `created_at` | 记忆创建时间 |

### 2.3 记忆管理（`/memories`）

记忆管理页面提供记忆列表展示和删除功能。

**查看记忆列表**：

页面加载时自动获取并展示所有可查询的记忆条目，包含每条记忆的内容摘要、价值评分、所在层和创建时间。

**删除记忆**：

1. 在记忆列表中找到目标记忆条目。
2. 点击该条目右侧的"删除"按钮。
3. 在确认对话框中点击"确认"完成删除。

> **注意**：删除操作不可恢复。删除时系统将同时从热层 ChromaDB、冷层 ChromaDB、SQLite 价值评分表和反馈日志表中移除该记忆的所有相关数据。

**删除流程**：

```mermaid
sequenceDiagram
    actor 用户
    participant 前端
    participant 后端API

    用户->>前端: 点击删除按钮
    前端->>用户: 弹出确认对话框
    用户->>前端: 确认删除
    前端->>后端API: DELETE /api/v1/memories/{id}
    后端API-->>前端: {"message": "ok"}
    前端-->>用户: 从列表移除该条目
```

### 2.4 操作日志查看（`/logs`）

操作日志页面分别展示记忆的存储日志和查询日志，用于追溯 AI Agent 的历史操作。

**存储日志**：

显示每次通过 `POST /api/v1/memories` 或 MCP `save_memory` 工具存储的操作记录，包含：

| 字段 | 说明 |
| --- | --- |
| `memory_id` | 被存储记忆的唯一标识 |
| `content` | 存储的记忆内容 |
| `created_at` | 存储操作发生时间 |

**查询日志**：

显示每次通过 `GET /api/v1/memories` 或 MCP `query_memory` 工具发起的查询记录，包含：

| 字段 | 说明 |
| --- | --- |
| `query` | 查询关键词 |
| `fast_only` | 是否为快速查询模式 |
| `result_count` | 返回记忆条目数 |
| `created_at` | 查询操作发生时间 |

### 2.5 价值评分查看（`/feedback`）

价值评分页面用于查看每条记忆的当前综合价值评分及历史反馈记录，帮助了解 AI Agent 对各记忆的使用评价情况。

**查看当前价值评分**：

在页面中选择或搜索目标记忆，系统显示：

| 字段 | 说明 |
| --- | --- |
| `value_score` | 当前综合价值评分（0.0 至 1.0） |
| `tier` | 当前所在层：`hot` 或 `cold` |
| `feedback_count` | 累计收到的反馈次数 |

**价值评分规则说明**：

```mermaid
flowchart TD
    A[新记忆存入] --> B[初始进入热层 hot\nvalue_score = 0.6（与升级阈值相同）]
    B --> C{AI Agent 提交反馈}
    C -->|valuable=true 有价值| D[value_score + 0.1, 上限 1.0]
    C -->|valuable=false 无价值| E[value_score - 0.1, 下限 0.0]
    D --> F{value_score >= 0.6?}
    E --> G{value_score < 0.3?}
    F -->|是| H[保持在热层 hot]
    F -->|否| I[维持当前层]
    G -->|是| J[降级至冷层 cold]
    G -->|否| I
```

**查看反馈历史**：

选中某条记忆后，下方列表展示该记忆的历史反馈记录：

| 字段 | 说明 |
| --- | --- |
| `valuable` | 反馈类型：`true`（有价值）或 `false`（无价值） |
| `created_at` | 反馈提交时间 |

---

## 3. AI Agent 接口调用说明

AIR_Memory 为 AI Agent 提供两种接口协议，可根据使用场景选择：

| 协议 | 适用场景 | 接入端点 |
| --- | --- | --- |
| MCP（Model Context Protocol） | 与支持 MCP 协议的 AI Agent 集成（如 Claude、Cursor 等） | `http://localhost:8080/mcp` |
| REST API | 通用 HTTP 接口，适合所有编程语言和 AI Agent | `http://localhost:8080/api/v1` |

### 3.1 MCP 接口调用说明

#### 3.1.1 MCP Server 配置

MCP Server 基于 Streamable HTTP 传输，接入端点为：

```
http://localhost:8080/mcp
```

在支持 MCP 协议的客户端（如 Claude Desktop、Cursor 等）中，将 AIR_Memory 配置为外部 MCP Server，URL 填入上述地址。

**Claude Desktop 配置示例**（`claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "air_memory": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

#### 3.1.2 MCP 工具列表

AIR_Memory MCP Server 暴露以下三个工具：

| Tool 名称 | 参数 | 说明 |
| --- | --- | --- |
| `save_memory` | `content: str` | 存储一条记忆，返回 `memory_id` |
| `query_memory` | `query: str`, `top_k: int = 5`, `fast_only: bool = False` | 查询语义相关记忆；`fast_only=True` 仅检索热层（≤ 100ms），`fast_only=False` 同时检索热/冷层 |
| `feedback_memory` | `memory_id: str`, `valuable: bool` | 对指定记忆提交价值反馈，影响其价值分及分层 |

#### 3.1.3 MCP 工具调用示例

**存储记忆**（`save_memory`）：

```json
{
  "tool": "save_memory",
  "arguments": {
    "content": "用户偏好使用深色主题，字体大小设置为 16px"
  }
}
```

返回示例：

```
"a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**查询记忆**（`query_memory`，快速模式）：

```json
{
  "tool": "query_memory",
  "arguments": {
    "query": "用户的界面偏好设置",
    "top_k": 3,
    "fast_only": true
  }
}
```

返回示例（JSON 字符串，内容为记忆条目平铺列表）：

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "content": "用户偏好使用深色主题，字体大小设置为 16px",
    "similarity": 0.92,
    "value_score": 0.6,
    "tier": "hot",
    "created_at": "2026-04-10T08:00:00Z"
  }
]
```

> **说明**：MCP `query_memory` 直接返回记忆条目的平铺列表（JSON 字符串），与 REST API 响应结构（含 `memories`、`count`、`query_mode` 字段的对象）不同。列表按相似度降序排列，最多返回 `top_k` 条。

**提交价值反馈**（`feedback_memory`）：

```json
{
  "tool": "feedback_memory",
  "arguments": {
    "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "valuable": true
  }
}
```

返回示例：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "value_score": 0.6,
  "tier": "hot",
  "message": "ok"
}
```

### 3.2 REST API 调用说明

#### 3.2.1 基本信息

| 项目 | 说明 |
| --- | --- |
| 基础 URL | `http://localhost:8080/api/v1` |
| 数据格式 | JSON（`Content-Type: application/json`） |
| API 文档 | `http://localhost:8080/api/v1/docs`（Swagger UI） |

**通用成功响应格式**：

```json
{
  "data": {},
  "message": "ok"
}
```

**错误响应格式**：

```json
{
  "detail": "错误描述"
}
```

#### 3.2.2 记忆接口

**存储记忆**

```
POST /api/v1/memories
```

请求体：

```json
{
  "content": "用户偏好使用深色主题，字体大小设置为 16px"
}
```

响应（HTTP 201）：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tier": "hot",
  "message": "ok"
}
```

curl 示例：

```bash
curl -X POST http://localhost:8080/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{"content": "用户偏好使用深色主题，字体大小设置为 16px"}'
```

---

**查询记忆**

```
GET /api/v1/memories?query=<查询词>&top_k=5&fast_only=false
```

| 查询参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `query` | string | 必填 | 语义查询关键词 |
| `top_k` | integer | 5 | 返回最相关的记忆条数 |
| `fast_only` | boolean | false | `true` 仅查热层，`false` 同时查热/冷层 |

响应（HTTP 200）：

```json
{
  "memories": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "content": "用户偏好使用深色主题，字体大小设置为 16px",
      "similarity": 0.92,
      "value_score": 0.6,
      "tier": "hot",
      "created_at": "2026-04-10T08:00:00Z"
    }
  ],
  "count": 1,
  "query_mode": "fast"
}
```

curl 示例：

```bash
curl "http://localhost:8080/api/v1/memories?query=用户界面偏好&top_k=3&fast_only=true"
```

---

**删除记忆**

```
DELETE /api/v1/memories/{memory_id}
```

响应（HTTP 200）：

```json
{
  "message": "ok"
}
```

curl 示例：

```bash
curl -X DELETE http://localhost:8080/api/v1/memories/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

**提交价值反馈**

```
POST /api/v1/memories/{memory_id}/feedback
```

请求体：

```json
{
  "valuable": true
}
```

响应（HTTP 200）：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "value_score": 0.6,
  "tier": "hot",
  "message": "ok"
}
```

curl 示例：

```bash
curl -X POST http://localhost:8080/api/v1/memories/a1b2c3d4-e5f6-7890-abcd-ef1234567890/feedback \
  -H "Content-Type: application/json" \
  -d '{"valuable": true}'
```

---

**查询反馈历史**

```
GET /api/v1/memories/{memory_id}/feedback/logs?page=1&page_size=20
```

响应（HTTP 200）：

```json
{
  "logs": [
    {
      "id": 1,
      "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "valuable": true,
      "created_at": "2026-04-10T08:05:00Z"
    }
  ],
  "count": 1
}
```

---

**查询价值评分**

```
GET /api/v1/memories/{memory_id}/value-score
```

响应（HTTP 200）：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "value_score": 0.6,
  "tier": "hot",
  "feedback_count": 1
}
```

#### 3.2.3 日志接口

**查询存储操作日志**

```
GET /api/v1/logs/save
```

响应（HTTP 200）：

```json
{
  "logs": [
    {
      "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "content": "用户偏好使用深色主题，字体大小设置为 16px",
      "created_at": "2026-04-10T08:00:00Z"
    }
  ],
  "count": 1
}
```

**查询查询操作日志**

```
GET /api/v1/logs/query
```

响应（HTTP 200）：

```json
{
  "logs": [
    {
      "query": "用户界面偏好",
      "fast_only": true,
      "result_count": 1,
      "created_at": "2026-04-10T08:10:00Z"
    }
  ],
  "count": 1
}
```

#### 3.2.4 系统接口

**健康检查**

```
GET /health
```

响应（HTTP 200）：

```json
{"status": "ok"}
```

**分级存储统计**

```
GET /api/v1/admin/tier-stats
```

响应（HTTP 200）：

```json
{
  "hot_count": 42,
  "cold_count": 158,
  "hot_memory_mb": 512,
  "memory_budget_mb": 6144
}
```

**磁盘占用统计**

```
GET /api/v1/admin/disk-stats
```

响应（HTTP 200）：

```json
{
  "disk_used_gb": 12.5,
  "disk_budget_gb": 40,
  "disk_safe_gb": 35
}
```

### 3.3 AI Agent 接口调用流程

以下序列图描述 AI Agent 完整的记忆使用流程（以 REST API 为例，MCP 调用流程相同）：

```mermaid
sequenceDiagram
    actor Agent as AI Agent
    participant API as AIR_Memory API

    Note over Agent,API: 1. 存储记忆
    Agent->>API: POST /api/v1/memories {"content": "..."}
    API-->>Agent: {"memory_id": "...", "tier": "hot", "message": "ok"}

    Note over Agent,API: 2. 查询相关记忆
    Agent->>API: GET /api/v1/memories?query=...&fast_only=true
    API-->>Agent: {"memories": [...], "count": N, "query_mode": "fast"}

    Note over Agent,API: 3. 提交价值反馈
    Agent->>API: POST /api/v1/memories/{id}/feedback {"valuable": true}
    API-->>Agent: {"memory_id": "...", "value_score": 0.6, "tier": "hot", "message": "ok"}
```

---

## 4. 分级存储说明

AIR_Memory 采用热层/冷层两级存储架构，AI Agent 无需感知层的细节，系统会根据价值评分自动管理：

| 层级 | 存储介质 | 默认容量上限 | 特点 |
| --- | --- | --- | --- |
| 热层（hot） | ChromaDB 内存（EphemeralClient） | 6 GB | 查询速度快，≤ 100ms |
| 冷层（cold） | ChromaDB 磁盘（PersistentClient） | 40 GB | 持久存储，支持深度查询 |

**升/降层规则**：

- 新记忆存入时默认同时进入热层和冷层，初始价值分为 0.6（与升级阈值相同），确保重启后可被优先恢复至热层。
- 当价值分 ≥ 0.6 时，记忆升级至热层。
- 当价值分 < 0.3 时，记忆从热层降级至冷层。
- 热层内存超出预算时，自动将最低价值记忆降级至冷层。
