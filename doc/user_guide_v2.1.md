# AIR_Memory 用户手册

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-10 | 初稿，覆盖 Web 管理界面和 AI Agent 接口使用说明 |
| 1.1 | 2026-4-14 | 补充 Header 版本号显示说明；修正 MCP query_memory 返回示例格式（平铺列表 JSON 字符串）|
| 1.2 | 2026-4-14 | 2.4 节补充存储日志乱码徽章说明；重写 2.5 节反馈记录列表（新增时间段查询和分页）；3.2.3 节补充 GET /api/v1/logs/feedback 接口说明 |
| 1.3 | 2026-4-14 | 2.4 节修正乱码徽章说明，补充 v1.2.5 修复信息 |
| 1.4 | 2026-4-15 | 2.4 节补充 v1.2.6 根因修复说明 |
| 1.5 | 2026-4-15 | 3.2 节补充 REST API 编码约束，明确 JSON 请求必须显式指定 `charset=UTF-8` |
| 1.6 | 2026-4-15 | 2.3 节更新记忆管理 UI：默认最近列表、每页 20 条分页、按 ID/时间范围筛选、详情页字段说明；补充本次升级数据影响分析结论（无需迁移本地数据） |
| 1.7 | 2026-4-15 | 2.3 节补充记忆列表操作能力：操作列增加删除按钮、列表过滤已删除数据、新增评价值列展示 |
| 1.8 | 2026-4-15 | 2.4 节补充操作日志时间范围筛选与分页；2.3 节补充记忆列表评价值分级背景色说明 |
| 1.9 | 2026-4-16 | 3.2 节更新 REST API Content-Type 说明：v1.2.12 起服务端自动按 UTF-8 处理，客户端无需显式设置 charset |
| 2.0 | 2026-5-11 | 新增输入信息管理列表与详情页使用说明；更新查询接口返回 input_id 与固定配额规则；更新反馈接口参数为 input_id + memory_id + valuable；补充输入信息 REST API 与 MCP 调用示例；移除 fast_only 参数，查询接口统一执行分层配额检索；移除查询模式切换步骤及 query_mode 返回字段；更新日志表、MCP 工具签名与 REST API 示例；查询配额改为溢出填充模式；新增版本数据兼容性说明；更新反馈记录页面描述为关联反馈模型；删除关联评分总量面板 |
| 2.1 | 2026-5-13 | 修订分级存储说明：热层仅保留至少关联一个输入信息的记忆；新记忆初始仅进入冷层 |

---

## 1. 概述

本手册面向两类读者：

- **人类用户**：通过 Web 管理界面对记忆数据进行查询、删除、日志查看、关联反馈记录查看和输入信息管理。
- **AI Agent 集成方**：通过 MCP 协议或 REST API 将 AIR_Memory 集成至 AI Agent 工作流。

系统部署完成后，Web 管理界面访问地址为 `http://localhost:8080`。

---

## 2. Web 管理界面使用说明

### 2.1 界面总览

Web 管理界面基于 Vue.js 3 构建，提供五个主要页面，通过顶部导航栏切换：

```mermaid
graph LR
    Nav["顶部导航栏"] --> Home["首页 / - 记忆查询"]
    Nav --> Memories["/memories - 记忆管理"]
    Nav --> Logs["/logs - 操作日志"]
    Nav --> Feedback["/feedback - 关联反馈记录"]
    Nav --> Inputs["/inputs - 输入信息管理"]
```

顶部导航栏右侧动态显示当前运行的系统版本号（通过 `GET /api/v1/version` 接口获取），便于快速确认所运行的版本。

### 2.2 记忆查询（首页 `/`）

首页提供记忆的语义相似度查询功能。

**操作步骤**：

1. 在搜索框中输入查询关键词或语义描述。
2. 设置返回条目数（`top_k`，默认 10，最大 10）。
3. 点击搜索按钮发起查询。

**查询结果说明**：

| 字段 | 说明 |
| --- | --- |
| `input_id` | 本次查询输入信息 ID, 用于后续反馈接口 |
| `content` | 记忆原文内容 |
| `similarity` | 与查询内容的语义相似度（0.0 至 1.0，越高越相关） |
| `total_association_score` | 该记忆当前关联评分总量（历次有价值反馈积累的关联分之和） |
| `association_score` | 当前输入信息与该记忆的关联评分 |
| `source` | 结果来源: `associated`/`hot`/`cold` |
| `tier` | 所在层：`hot`（热层）或 `cold`（冷层） |
| `created_at` | 记忆创建时间 |

> 查询返回策略采用溢出填充模式: 关联记忆最多 5 条；热层固定 3 条，若关联不足 5 条则热层可补充至关联+热层合计 8 条；冷层固定 2 条，若关联+热层合计不足 8 条则冷层补齐至总计 10 条；合并去重后总数最多 10 条。

### 2.3 记忆管理（`/memories`）

记忆管理页面用于浏览和检索已提交的记忆信息，默认按最近提交时间展示，并支持分页、删除和详情查看。

**默认列表与分页**：

1. 进入页面后系统自动加载最近记忆列表。
2. 列表按提交时间倒序展示（最新记录优先）。
3. 列表中会隐藏已删除记忆，仅展示有效记忆。
4. 列表提供关联评分总量列，显示该记忆当前的 total_association_score（保留两位小数）。
5. 分页固定每页 20 条，可通过分页器切换页码。
6. 列表按关联评分总量应用分级背景色（高分绿色、中分橙色、低分红色），鼠标悬停时会显示同色系加深高亮，兼顾可读性与 hover 反馈。

**按条件查询**：

1. 在"记忆 ID"输入框中输入完整 ID 或 ID 片段（可选）。
2. 在"时间范围"选择器中设置开始和结束时间（可选）。
3. 点击"查询"执行筛选；点击"重置"清空条件并恢复默认列表。

**查看详情页**：

1. 在列表中点击"查看详情"。
2. 系统跳转到详情页 `/memories/{memory_id}`。
3. 详情页展示该记忆的完整信息字段：
   - ID
   - 原始数据
   - 提交时间
   - 关联评分总量（total_association_score）

**删除记忆**：

1. 在列表中点击"删除"。
2. 系统调用删除接口并在成功后自动从列表移除该记忆。

```mermaid
sequenceDiagram
    actor 用户
    participant 前端
    participant 后端API

    用户->>前端: 打开 /memories
    前端->>后端API: GET /api/v1/logs/save
    后端API-->>前端: 最近记忆列表
    用户->>前端: 设置 ID 或时间范围并点击查询
    前端-->>用户: 展示筛选后的分页结果（每页20条）
    用户->>前端: 点击"查看详情"
    前端->>后端API: GET /api/v1/logs/save/{memory_id}
    后端API-->>前端: 记忆详情
    前端-->>用户: 展示完整记忆字段
```

### 2.4 操作日志查看（`/logs`）

操作日志页面分别展示记忆的存储日志和查询日志，用于追溯 AI Agent 的历史操作。两个日志列表均支持按时间范围筛选和分页浏览，交互形式与反馈记录列表一致。

**通用操作（存储日志/查询日志）**：

1. 在"时间范围"选择器中设置开始和结束时间（可选）。
2. 点击"查询"按钮应用筛选，点击"重置"清空筛选条件。
3. 点击"刷新"重新拉取最新日志数据。
4. 使用分页控件切换页码或调整每页条数（10 / 20 / 50 / 100）。

**存储日志**：

显示每次通过 `POST /api/v1/memories` 或 MCP `save_memory` 工具存储的操作记录，包含：

| 字段 | 说明 |
| --- | --- |
| `memory_id` | 被存储记忆的唯一标识 |
| `content` | 存储的记忆内容 |
| `created_at` | 存储操作发生时间 |

> **乱码徽章**：如果某条存储记录的原始内容疑似因历史编码问题损坏（内容中问号比例过高），该记录的"原始内容"列将显示橙色"乱码"徽章，鼠标悬停可查看说明。此为历史遗留数据问题，v1.2.6 已从根本上修复了中文内容在存储前被 CP1252 编码损坏为 `????` 的根因（启动脚本强制覆盖 `PYTHONUTF8=1`，运行时补充 `sys.stdin` UTF-8 重配），v1.2.6 及以后版本新增的记忆不再受影响。历史已损坏数据无法恢复，但"乱码"徽章（v1.2.5 修复）会正确标识这些记录。

**查询日志**：

显示每次通过 `GET /api/v1/memories` 或 MCP `query_memory` 工具发起的查询记录，包含：

| 字段 | 说明 |
| --- | --- |
| `query` | 查询关键词 |
| `result_count` | 返回记忆条目数 |
| `created_at` | 查询操作发生时间 |

### 2.5 关联反馈记录查询（`/feedback`）

反馈记录页面用于查询 AI Agent 历次通过反馈接口提交的 input_id + memory_id 关联反馈记录，支持按记忆 ID、输入信息 ID 和时间段筛选，并以分页列表展示结果。

**查询操作**：

1. 在"记忆 ID"输入框中填入目标记忆的 ID（可选，不填则查询全部反馈记录）。
2. 在"时间范围"选择器中选择开始时间和结束时间（可选）。
3. 点击"查询"按钮发起查询，或点击"重置"清空所有条件恢复初始状态。

**反馈记录字段说明**：

| 字段 | 说明 |
| --- | --- |
| `created_at` | 反馈发生的时间戳 |
| `input_id` | 触发本次反馈的输入信息 ID |
| `memory_id` | 被评价的记忆 ID |
| `valuable` | true 表示关联分增加，false 表示关联分降低 |

**层管理规则说明**：

记忆的层归属由系统根据所有记忆的 `total_association_score` 排名自动管理：

- 新记忆存入时默认仅进入冷层（初始 total_association_score = 0），建立至少一个输入信息关联后才可能进入热层。
- 每次收到有价值反馈（`valuable=true`）时，对应关联分提升，total_association_score 随之增加；收到无价值反馈时，关联分降低（至 0 时移除关联），total_association_score 随之减少。
- TierManager 根据 total_association_score 排名动态调整热层成员；热层始终保留排名靠前的记忆，直至达到内存预算上限。

**反馈记录列表**：

列表展示符合查询条件的反馈记录，按时间倒序排列，底部提供分页控件：

| 字段 | 说明 |
| --- | --- |
| `created_at` | 反馈提交时间 |
| `input_id` | 触发本次反馈的输入信息 ID |
| `memory_id` | 被评价记忆的唯一标识 |
| `valuable` | 反馈方向：`true`（关联分增加）或 `false`（关联分降低） |

每页默认显示 20 条，可通过分页控件切换页码或调整每页条数（10 / 20 / 50 / 100）。

### 2.6 输入信息管理（`/inputs`）

输入信息管理页面用于查看查询接口生成的输入信息记录, 交互风格与记忆管理和日志列表保持一致。

**列表功能**:

1. 页面默认按创建时间倒序展示输入信息。
2. 支持时间范围筛选和分页浏览（默认每页 20 条）。
3. 列表项可点击"查看详情"跳转 `/inputs/{input_id}`。

**详情页功能**:

1. 展示输入信息基础字段: `input_id`、查询原文、创建时间。
2. 展示该输入信息关联的全部记忆及对应评分。
3. 关联记忆列表至少包含 `memory_id`、`association_score`、`total_association_score`、`content`。

### 2.7 版本数据兼容性

如果你的系统中存有旧版本 AIR_Memory 的数据，在首次启动时系统会自动检测并升级数据结构。升级过程一次性执行，完成后系统正常启动。如果升级失败，系统会记录错误日志并安全退出，已有数据不会被破坏，请检查日志后重新启动。

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
| `query_memory` | `query: str`, `top_k: int = 10` | 查询语义相关记忆并返回 `input_id`；采用溢出填充配额策略（关联≤5，热层≤(8−关联实际数)，冷层补齐至10，总数≤10） |
| `feedback_memory` | `input_id: str`, `memory_id: str`, `valuable: bool` | 对指定输入信息中的记忆提交价值反馈，更新输入信息关联评分并根据 total_association_score 排名触发层迁移 |

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

**查询记忆**（`query_memory`）：

```json
{
  "tool": "query_memory",
  "arguments": {
    "query": "用户的界面偏好设置",
    "top_k": 10
  }
}
```

返回示例：

```json
{
  "input_id": "inp-4f3a5c2e",
  "memories": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "content": "用户偏好使用深色主题，字体大小设置为 16px",
      "similarity": 0.92,
      "total_association_score": 0,
      "association_score": 0.3,
      "source": "associated",
      "tier": "hot",
      "created_at": "2026-04-10T08:00:00Z"
    }
  ],
  "count": 1
}
```

> 返回中的 `input_id` 需在 `feedback_memory` 调用时回传, 用于建立或更新输入信息关联评分。

**提交价值反馈**（`feedback_memory`）：

```json
{
  "tool": "feedback_memory",
  "arguments": {
    "input_id": "inp-4f3a5c2e",
    "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "valuable": true
  }
}
```

返回示例：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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

> 说明: 对所有包含 JSON 请求体的 REST API 调用, 需设置 `Content-Type: application/json`。
> v1.2.12 起, 服务端新增 UTF-8 强制中间件, 即使客户端未声明 `charset`, 服务端也会自动按 UTF-8 处理请求体, 中文内容不再乱码。
> 兼容性: 若客户端仍设置 `Content-Type: application/json; charset=UTF-8`, 服务端行为不变。

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
GET /api/v1/memories?query=<查询词>&top_k=10
```

| 查询参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `query` | string | 必填 | 语义查询关键词 |
| `top_k` | integer | 10 | 返回记忆条数上限（最大 10） |

响应（HTTP 200）：

```json
{
  "input_id": "inp-4f3a5c2e",
  "memories": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "content": "用户偏好使用深色主题，字体大小设置为 16px",
      "similarity": 0.92,
      "total_association_score": 0,
      "association_score": 0.3,

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
  "input_id": "inp-4f3a5c2e",
  "valuable": true
}
```

响应（HTTP 200）：

```json
{
  "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "ok"
}
```
  -H "Content-Type: application/json" \
  -d '{"input_id": "inp-4f3a5c2e", "valuable": true}'
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
      "input_id": "inp-4f3a5c2e",
      "result_count": 1,
      "created_at": "2026-04-10T08:10:00Z"
    }
  ],
  "count": 1
}
```

**查询反馈记录列表**

```
GET /api/v1/logs/feedback
```

| 查询参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 1 | 页码（从 1 开始） |
| `page_size` | integer | 20 | 每页条数（1 至 100） |
| `memory_id` | string | - | 按记忆 ID 过滤（可选） |
| `start_time` | string | - | 开始时间，ISO 8601 格式（可选） |
| `end_time` | string | - | 结束时间，ISO 8601 格式（可选） |

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
  "count": 1,
  "total": 42
}
```

> `total` 为符合过滤条件的总记录数，`count` 为当前页实际返回条数，用于分页计算。

curl 示例：

```bash
curl "http://localhost:8080/api/v1/logs/feedback?page=1&page_size=20&start_time=2026-04-01T00:00:00&end_time=2026-04-14T23:59:59"
```

#### 3.2.4 输入信息接口

**查询输入信息列表**

```
GET /api/v1/inputs?page=1&page_size=20
```

响应（HTTP 200）:

```json
{
  "inputs": [
    {
      "input_id": "inp-4f3a5c2e",
      "query": "用户界面偏好",
      "created_at": "2026-04-10T08:10:00Z"
    }
  ],
  "count": 1,
  "total": 1
}
```

**查询输入信息详情**

```
GET /api/v1/inputs/{input_id}
```

响应（HTTP 200）:

```json
{
  "input_id": "inp-4f3a5c2e",
  "query": "用户界面偏好",
  "created_at": "2026-04-10T08:10:00Z",
  "memories": [
    {
      "memory_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "association_score": 0.3,
      "total_association_score": 0.0,
      "content": "用户偏好使用深色主题，字体大小设置为 16px"
    }
  ]
}
```

#### 3.2.5 系统接口

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
    API-->>Agent: {"memory_id": "...", "message": "ok"}

    Note over Agent,API: 2. 查询相关记忆
    Agent->>API: GET /api/v1/memories?query=...
    API-->>Agent: {"input_id":"...","memories": [...], "count": N}

    Note over Agent,API: 3. 提交价值反馈
    Agent->>API: POST /api/v1/memories/{id}/feedback {"input_id":"...","valuable": true}
    API-->>Agent: {"memory_id": "...", "message": "ok"}
```

---

## 4. 分级存储说明

AIR_Memory 采用热层/冷层两级存储架构，AI Agent 无需感知层的细节，系统会先根据是否已建立输入信息关联，再结合关联评分总量自动管理：

| 层级 | 存储介质 | 默认容量上限 | 特点 |
| --- | --- | --- | --- |
| 热层（hot） | ChromaDB 内存（EphemeralClient） | 6 GB | 仅保留至少关联一个输入信息的记忆，检索性能高 |
| 冷层（cold） | ChromaDB 磁盘（PersistentClient） | 40 GB | 持久存储全部记忆；未关联记忆仅驻留于此 |

**升/降层规则**：

- 新记忆存入时默认仅进入冷层，初始 total_association_score = 0，待建立至少一个输入信息关联后方可进入热层。
- TierManager 仅在“已建立至少一个输入信息关联”的候选集中，根据 total_association_score 排名动态调整热层成员。
- 热层内存超出预算或某条记忆关联被清零时，系统会将其降级至冷层。
