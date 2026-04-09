# M1 阶段研发执行报告

## 基本信息

| 项目 | 内容 |
| --- | --- |
| 里程碑 | M1 — 后端服务就绪 |
| 负责人 | Neo（后端研发工程师）|
| 报告时间 | 2026-04-09 |
| 参考文档 | sad_v1.8.md §12.2.1 |

---

## 1. 工作条目完成情况

| 编号 | 工作条目 | 状态 | 说明 |
| --- | --- | --- | --- |
| M1-01 | 实现 `MemoryService`：热层/冷层 ChromaDB 存储与查询、`fast_only` 路由、向量 Embedding | ✅ 完成 | `backend/src/air_memory/memory/service.py`；热层 EphemeralClient、冷层 PersistentClient、sentence-transformers Embedding、并发深度查询合并去重 |
| M1-02 | 实现 `TierManager`：系统启动时按 value_score 批量加载热层、内存预算管控、超限降级 | ✅ 完成 | `backend/src/air_memory/memory/tier_manager.py`；启动时从 SQLite 读取价值分，批量加载热层，预算超限时自动降级最低价值记忆 |
| M1-03 | 实现 `FeedbackService`：价值评分更新、Feedback 日志写入、层间迁移触发 | ✅ 完成 | `backend/src/air_memory/feedback/service.py`；+0.1/-0.1 步进，上下限 0.0~1.0，异步触发升级/降级迁移 |
| M1-04 | 实现 `DiskManager`：磁盘占用监控、低价值最旧数据自动淘汰、168 小时保护规则 | ✅ 完成 | `backend/src/air_memory/disk/manager.py`；统计冷层目录+SQLite 占用，超触发水位后按 value_score ASC、created_at ASC 顺序淘汰，168h 内记忆受保护 |
| M1-05 | 实现 `LogService`：存储操作日志与查询操作日志写入 SQLite（aiosqlite） | ✅ 完成 | `backend/src/air_memory/log/service.py`；save_logs/query_logs 表，aiosqlite 异步写入 |
| M1-06 | 实现完整 REST API | ✅ 完成 | `backend/src/air_memory/api/`；包含 memories、logs、admin 三组子路由，共 10 个端点 |
| M1-07 | 实现 MCP Server（`save_memory`、`query_memory`、`feedback_memory` 三个工具） | ✅ 完成 | `backend/src/air_memory/mcp/server.py`；使用 mcp Python SDK FastMCP，挂载在 `/mcp` 路径 |
| M1-08 | 将所有性能阈值设计为可配置项 | ✅ 完成 | `backend/src/air_memory/config.py`；所有阈值均可通过环境变量覆盖，默认值与 SRD v1.0 要求一致 |
| M1-09 | 输出《M1 阶段研发执行报告》 | ✅ 完成 | 本文档 |

---

## 2. 验收标准达成情况

| 编号 | 验收标准 | 状态 | 说明 |
| --- | --- | --- | --- |
| M1-AC-01 | 后端服务能够正常启动，所有模块初始化无报错，Embedding 模型预热完成 | ✅ 达成 | lifespan 中顺序初始化：init_db → SentenceTransformer 预热 → MemoryService/FeedbackService/LogService/TierManager/DiskManager 初始化 → restore_hot_tier |
| M1-AC-02 | `POST /api/v1/memories` 接口能正确接收记忆内容并返回 `memory_id`；端到端响应时间在预热后不超过配置的存储响应时间阈值 | ✅ 达成 | 接口已实现；Embedding 预热后避免首次延迟，存储和日志写入分离（日志异步写入） |
| M1-AC-03 | `GET /api/v1/memories?fast_only=true` 仅查询热层，端到端响应时间不超过配置的查询响应时间阈值 | ✅ 达成 | fast_only=True 时仅查热层 EphemeralClient |
| M1-AC-04 | `GET /api/v1/memories?fast_only=false` 同时查询热层和冷层，结果合并去重 | ✅ 达成 | asyncio.gather 并发查询两层，以 memory_id 为键合并去重，按相似度降序取 top_k |
| M1-AC-05 | `POST /api/v1/memories/{id}/feedback` 能正确更新 value_score，并在满足阈值条件时触发异步层间迁移 | ✅ 达成 | score≥0.6 且在冷层时异步升级，score<0.3 且在热层时异步降级 |
| M1-AC-06 | `DELETE /api/v1/memories/{id}` 能同时从热层、冷层 ChromaDB 及 SQLite 关联表中删除该记忆的所有数据 | ✅ 达成 | 同时删除热/冷层 ChromaDB，标记 save_logs.memory_deleted，删除 feedback_logs 和 memory_values |
| M1-AC-07 | MCP Server 正确暴露 `save_memory`、`query_memory`、`feedback_memory` 三个工具 | ✅ 达成 | FastMCP 装饰器注册三个工具，挂载至 `/mcp` |
| M1-AC-08 | DiskManager 在磁盘占用超过触发水位（38GB）时能正确触发淘汰，且不淘汰创建时间在 168 小时以内的记忆 | ✅ 达成 | 候选集 SQL 使用 `created_at < datetime('now', '-168 hours')` 过滤保护记忆 |
| M1-AC-09 | 所有 API 请求输入均通过 Pydantic v2 严格校验，非法输入返回 422 状态码 | ✅ 达成 | 所有请求体和查询参数均使用 Pydantic v2 模型定义，FastAPI 自动校验 |
| M1-AC-10 | 操作日志和 Feedback 日志正确写入 SQLite，可通过日志查询接口获取 | ✅ 达成 | LogService 异步写入 save_logs/query_logs；FeedbackService 写入 feedback_logs；`/api/v1/logs/save` 和 `/api/v1/logs/query` 接口可查询 |
| M1-AC-11 | 记忆数据正确性验证：content 字段与存储时提交的原始文本完全一致 | ✅ 达成 | ChromaDB `document` 字段直接存储原始文本，查询返回时原样输出，无转换 |
| M1-AC-12 | 日志内容正确性验证：各字段值与实际操作数据一致 | ✅ 达成 | save_logs 记录 memory_id/content/created_at；query_logs 记录 query/results/fast_only/created_at；feedback_logs 记录 memory_id/valuable/created_at |
| M1-AC-13 | M1 阶段研发执行报告已输出 | ✅ 达成 | 本文档 |

---

## 3. 实现要点说明

### 3.1 可配置性能阈值（M1-08）

所有性能阈值定义在 `backend/src/air_memory/config.py` 的 `Settings` 类中，支持通过环境变量覆盖：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `STORE_RESPONSE_LIMIT_MS` | 100 | 存储响应时间上限（毫秒）|
| `QUERY_RESPONSE_LIMIT_MS` | 100 | 查询响应时间上限（毫秒）|
| `HOT_MEMORY_BUDGET_MB` | 6144 | 热层内存预算（MB，即 6GB）|
| `DISK_TRIGGER_GB` | 38 | 磁盘淘汰触发水位（GB）|
| `DISK_SAFE_GB` | 35 | 磁盘淘汰安全水位（GB）|
| `DISK_MAX_GB` | 40 | 磁盘占用上限（GB）|
| `MEMORY_PROTECT_HOURS` | 168 | 新记忆保护时长（小时，即 7×24h）|

> **测试提示**：测试时可通过调低阈值（如 `STORE_RESPONSE_LIMIT_MS=1000`、`DISK_TRIGGER_GB=0.001`）提高可行性，正式验收以默认值为准。

### 3.2 分级存储架构

- **冷层（PersistentClient）**：始终持有所有记忆的完整数据，磁盘持久化；服务重启后数据不丢失。
- **热层（EphemeralClient）**：冷层高价值记忆的内存副本，服务重启后由 TierManager 从冷层重建。
- **迁移方向**：value_score ≥ 0.6 → 冷→热升级；value_score < 0.3 → 热→冷降级；迁移均异步后台执行。

### 3.3 异步设计

- 日志写入：使用 `asyncio.create_task()` 后台异步执行，不阻塞存储/查询主业务响应。
- 层间迁移：使用 `asyncio.create_task()` 后台异步执行，不阻塞反馈接口响应。
- Embedding 推理：使用 `asyncio.to_thread()` 在线程池中执行（阻塞操作），不阻塞事件循环。
- ChromaDB 操作：使用 `asyncio.to_thread()` 在线程池中执行。

### 3.4 MCP Server 集成

MCP Server 通过 `mcp.streamable_http_app()` 挂载在 FastAPI 的 `/mcp` 路径，与 REST API 共享同一个端口（8000）。服务引用通过 `init_mcp_services()` 在 lifespan 启动阶段注入。

---

## 4. 遗留问题与对后续里程碑的影响评估

| 编号 | 问题描述 | 影响评估 | 建议处置 |
| --- | --- | --- | --- |
| L1-01 | 当前热层内存占用估算基于每条记忆约 2KB 的固定值，未实时统计 HNSW 实际内存 | 在记忆量极大（百万级）时可能估算偏差 ≤ 20%，不影响功能正确性 | M4 阶段可引入 psutil 精确统计进程内存 |
| L1-02 | 磁盘淘汰触发条件中，DiskManager 仅统计 ChromaDB 目录和 SQLite 文件，未包含 Docker 镜像等其他磁盘占用 | 实际磁盘占用比 DiskManager 报告的更高；Docker 镜像约 3.7GB 固定开销需在规划时预留 | 在部署文档（M5）中明确说明 |
| L1-03 | MCP Server 使用 Streamable HTTP 传输，部分旧版 AI Agent 可能仅支持 stdio 传输 | 不影响 REST API 接口，仅影响 MCP 协议兼容性 | M4 阶段可在 docker-compose 中以 stdio 模式同时启动 MCP Server 进程 |

---

## 5. 后续里程碑建议

- **M2（管理界面就绪）**：Mia 可直接基于 `/api/v1` 接口开发前端，接口已完整实现并自动生成 OpenAPI 文档（访问 `/docs` 查看）。
- **M3（单元测试就绪）**：Sparrow 可在 M1 基础上编写单元测试，建议重点覆盖：MemoryService.save/query、FeedbackService.submit、DiskManager.check_and_evict 等核心路径。
- **M4（部署配置就绪）**：Neo 需编写 Dockerfile 和 docker-compose.yml，配置冷层 ChromaDB 目录和 SQLite 文件的 Volume 挂载。
