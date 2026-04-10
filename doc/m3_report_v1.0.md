# 单元测试报告 v1.0

**文档编号**：DOC-M3-REPORT-v1.0  
**里程碑**：M3 单元测试就绪  
**编制人**：Sparrow（测试工程师）  
**编制日期**：2026-04-10  
**状态**：✅ 里程碑完成，所有验收标准通过

---

## 1. 执行摘要

M3 里程碑全部 12 项工作条目已完成。后端 105 个测试用例全部通过，语句覆盖率 87%；前端 77 个测试用例全部通过，语句覆盖率 83.83%。测试过程中发现 1 个生产代码缺陷（MemoryService.demote() ChromaDB upsert 参数不完整），已在本里程碑内修复。

---

## 2. 验收标准检查清单

| 编号 | 验收标准 | 结果 | 说明 |
|---|---|---|---|
| M3-AC-01 | 所有后端单元测试通过（pytest 无 FAILED/ERROR） | ✅ **通过** | 105/105 PASSED |
| M3-AC-02 | 所有前端单元测试通过（vitest run 无 FAIL） | ✅ **通过** | 77/77 PASSED |
| M3-AC-03 | 后端测试覆盖率（语句覆盖）≥ 80% | ✅ **通过** | **87%**（TOTAL 553 stmts） |
| M3-AC-04 | 前端测试覆盖率（语句覆盖）≥ 80% | ✅ **通过** | **83.83%**（含组件、视图、Store） |
| M3-AC-05 | MemoryService 有响应时间断言（≤ 1000ms 宽松值） | ✅ **通过** | save/query 各有专项 |
| M3-AC-06 | DiskManager 168 小时保护规则有专项测试用例 | ✅ **通过** | 4 个专项测试用例 |
| M3-AC-07 | FeedbackService value_score 边界值（0.0/1.0）有专项测试 | ✅ **通过** | 6 个边界值测试用例 |
| M3-AC-08 | REST API 非法输入场景有测试用例，验证返回 422 | ✅ **通过** | 9 个 422 场景覆盖 |
| M3-AC-09 | 记忆数据正确性测试（content 字段一致，快速+深度查询均覆盖） | ✅ **通过** | 4 个 content 正确性用例 |
| M3-AC-10 | 日志内容正确性测试（各字段与操作输入一致） | ✅ **通过** | 12 个字段正确性用例 |
| M3-AC-11 | 单元测试报告已输出至 doc/m3_report_v1.0.md | ✅ **通过** | 本文档 |

---

## 3. 工作条目完成情况

### M3-01：后端单元测试方案设计

**完成状态**：✅ 完成

**测试模块清单**：

| 模块 | 文件 | 覆盖目标 |
|---|---|---|
| MemoryService | test_memory_service.py | 存储、快速查询、深度查询、层间迁移、响应时间 |
| TierManager | test_tier_manager.py | 热层恢复、预算检查、容量统计 |
| FeedbackService | test_feedback_service.py | 价值分更新、边界值、日志写入、迁移触发 |
| DiskManager | test_disk_manager.py | 淘汰触发、168h 保护、淘汰顺序 |
| LogService | test_log_service.py | 存储日志、查询日志、字段正确性 |
| REST API | test_api.py | 全接口正常/异常场景、Pydantic 校验 |

**技术决策**：
- 使用 `MockSentenceTransformer`（基于哈希的确定性向量）替代真实模型，避免加载 300MB+ 参数文件
- ChromaDB 1.x `EphemeralClient` 在同一进程内共享内存存储；通过在 `override_settings` fixture 中为每个测试用例生成唯一集合名称（UUID 后缀）实现测试隔离
- 异步测试使用 `pytest-asyncio` (asyncio mode=AUTO)，API 集成测试使用 `httpx.AsyncClient + ASGITransport`

---

### M3-02：MemoryService 单元测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_memory_service.py`  
**测试数量**：20 个

| 测试类 | 核心测试用例 |
|---|---|
| TestMemoryServiceSave | save 返回有效 ID、增加冷层计数、唯一 ID、响应时间 ≤ 1000ms |
| TestMemoryServiceDeepQuery | 返回存储记忆、content 字段一致（M3-AC-09）、tier=cold、响应时间、空库返回空、top_k 限制 |
| TestMemoryServiceFastQuery | 冷层记忆不出现在热层查询、升级后 content 一致（M3-AC-09）、tier=hot、响应时间 |
| TestMemoryServiceTierMigration | promote/demote/delete/load_hot_from_cold、不存在 ID 安全降级、内存估算 |

---

### M3-03：TierManager 单元测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_tier_manager.py`  
**测试数量**：10 个

| 测试类 | 核心测试用例 |
|---|---|
| TestTierManagerRestoreHotTier | 加载高价值记忆、跳过低价值、遵守内存预算（HOT_MEMORY_BUDGET_MB=0）、空库安全执行 |
| TestTierManagerCheckMemoryBudget | 未超限不降级、超限触发降级 |
| TestTierManagerGetHotStats | 返回字典、初始状态、存储后 cold_count、升级后 hot_count |

---

### M3-04：FeedbackService 单元测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_feedback_service.py`  
**测试数量**：17 个

| 测试类 | 核心测试用例 |
|---|---|
| TestFeedbackServiceValueScore | 正负反馈增减、上限截断 1.0（M3-AC-07）、下限截断 0.0（M3-AC-07）、边界保持、返回 tier、不存在异常 |
| TestFeedbackServiceLogWriting | 日志写入 feedback_logs（M3-AC-10）、memory_id 一致、valuable 一致、created_at 非空、多次写入多条、get_feedback_logs 返回历史 |
| TestFeedbackServiceMigrationTrigger | 达到升级阈值触发 promote、低于降级阈值触发 demote、分值范围内不迁移、get_memory_value_score 正确 |

---

### M3-05：DiskManager 单元测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_disk_manager.py`  
**测试数量**：12 个

| 测试类 | 核心测试用例 |
|---|---|
| TestDiskManagerEvictionTrigger | 未超限不淘汰、超限触发淘汰、达到安全水位停止 |
| TestDiskManager168HourProtection | 保护期内不淘汰（M3-AC-06）、168h 外可淘汰（M3-AC-06）、保护期内外同存时只淘汰期外（M3-AC-06）、无候选安全退出（M3-AC-06） |
| TestDiskManagerEvictionOrder | value_score 最低的优先入队（验证 _get_evict_candidates 排序）、相同分值时创建时间早的优先 |
| TestDiskManagerStats | 统计字典字段完整、磁盘占用返回非负浮点数 |

---

### M3-06：LogService 单元测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_log_service.py`  
**测试数量**：16 个

| 测试类 | 核心测试用例 |
|---|---|
| TestLogServiceSaveLogs | 写入 save_logs（M3-AC-10）、memory_id 一致（M3-AC-10）、content 一致（M3-AC-10）、created_at 非空、memory_deleted 默认 false、返回列表、content 查询正确、按 id DESC 排序 |
| TestLogServiceQueryLogs | 写入 query_logs（M3-AC-10）、query 字段一致（M3-AC-10）、fast_only 字段一致、results 序列化 JSON、created_at 非空、返回列表、字段正确性、按 id DESC 排序 |

---

### M3-07：REST API 接口集成测试

**完成状态**：✅ 完成  
**文件**：`backend/tests/test_api.py`  
**测试数量**：29 个

| 接口 | 正常场景 | 异常场景（422/404） |
|---|---|---|
| POST /api/v1/memories | 201 + memory_id | 缺 content（422）、空 content（422）、非 JSON（422）（M3-AC-08） |
| GET /api/v1/memories | 200 + 记忆列表、content 正确（M3-AC-09）、fast/deep 模式 | 缺 query（422）、空 query（422）、top_k>100（422）（M3-AC-08） |
| DELETE /api/v1/memories/{id} | 200 | 不存在 ID（200 幂等） |
| POST /api/v1/memories/{id}/feedback | 200 + value_score | 不存在（404）、缺 valuable（422）、非法类型（422）（M3-AC-08） |
| GET /api/v1/memories/{id}/feedback/logs | 200 + 日志列表 | page_size>100（422）（M3-AC-08） |
| GET /api/v1/memories/{id}/value-score | 200 + 评分 | 不存在（404） |
| GET /api/v1/logs/save | 200 + 日志列表、存储后有记录 | - |
| GET /api/v1/logs/query | 200 + 日志列表、查询后有记录 | - |
| GET /api/v1/admin/tier-stats | 200 + 统计字段、存储后 cold_count 增加 | - |
| GET /api/v1/admin/disk-stats | 200 + 统计字段 | - |

---

### M3-08：前端单元测试方案设计

**完成状态**：✅ 完成

**测试组件/视图清单**：

| 类型 | 文件 | 覆盖目标 |
|---|---|---|
| 公共组件 | MemoryCard.spec.ts | 渲染、层级标签、相似度、价值分、事件 |
| 公共组件 | LogTable.spec.ts | 渲染、data 传递、loading、空数据提示、slot |
| 视图 | MemoriesView.spec.ts | 查询表单、API 调用、结果展示 |
| 视图 | LogsView.spec.ts | 标签页、日志加载、JSON 解析 |
| 视图 | FeedbackView.spec.ts | 反馈查询、评分展示、颜色逻辑 |
| Pinia Store | stores.spec.ts | useMemoryStore、useLogStore 状态管理 |

**技术决策**：
- 使用 `vi.mock` + 内联数据 Mock API（避免 hoisting 引起的初始化顺序问题）
- 组件测试使用 `@vue/test-utils` mount，视图测试结合 `flushPromises` 处理异步
- 使用 `@vitest/coverage-v8@3.2.4`（与 vitest@3.2.4 版本匹配）
- 排除纯声明文件（`types.ts`）、路由配置（`router/index.ts`）、应用根组件（`App.vue`）

---

### M3-09：前端公共组件单元测试

**完成状态**：✅ 完成  
**文件**：`frontend/tests/MemoryCard.spec.ts`、`frontend/tests/LogTable.spec.ts`  
**测试数量**：25 个（MemoryCard 16 + LogTable 9）

**MemoryCard 核心断言**：
- 显示 content、ID、创建时间
- 冷层显示"冷层"标签，热层显示"热层"标签
- 相似度百分比格式化（85.0%、92.0%）
- 价值评分 2 位小数格式化（0.40、0.75、1.00）
- delete 事件携带 memory.id
- 边界值：similarity=0 显示 0.0%，value_score=1.0 显示 1.00

**LogTable 核心断言**：
- data 为空时显示"暂无日志数据"
- loading 属性传递
- slot 内容渲染

---

### M3-10：前端视图单元测试

**完成状态**：✅ 完成  
**文件**：`frontend/tests/MemoriesView.spec.ts`、`frontend/tests/LogsView.spec.ts`、`frontend/tests/FeedbackView.spec.ts`  
**测试数量**：26 个

**核心交互逻辑覆盖**：
- MemoriesView：空查询不调用 API、有效查询调用 API、结果展示"共找到"、空结果显示"未找到相关记忆"
- LogsView：挂载时加载 getSaveLogs（延迟加载 getQueryLogs）、parseResultsSummary 正确解析 JSON / 异常处理
- FeedbackView：空 ID 不调用 API、scoreColor 颜色分级逻辑（绿/橙/红）、不存在时显示错误提示

---

### M3-11：测试覆盖率报告

**完成状态**：✅ 完成

#### 后端覆盖率（coverage.py）

运行命令：
```bash
cd backend && python -m pytest tests/ --cov=air_memory --cov-report=term-missing
```

| 模块 | 语句数 | 覆盖率 |
|---|---|---|
| air_memory/api/admin.py | 10 | **100%** |
| air_memory/api/logs.py | 13 | **100%** |
| air_memory/api/memory.py | 69 | **100%** |
| air_memory/api/router.py | 8 | **100%** |
| air_memory/config.py | 20 | **100%** |
| air_memory/db.py | 7 | **100%** |
| air_memory/disk/manager.py | 54 | **93%** |
| air_memory/feedback/service.py | 62 | **95%** |
| air_memory/log/service.py | 28 | **100%** |
| air_memory/memory/service.py | 91 | **95%** |
| air_memory/memory/tier_manager.py | 33 | **97%** |
| air_memory/models/（所有） | 60 | **100%** |
| **TOTAL（核心模块）** | **553** | **87%** |

> main.py（45%）和 mcp/server.py（33%）为启动引导和 MCP 服务器代码，不在单元测试范围内。

#### 前端覆盖率（Vitest coverage-v8）

运行命令：
```bash
cd frontend && npx vitest run --coverage
```

| 模块 | 语句覆盖率 |
|---|---|
| src/components/LogTable.vue | **100%** |
| src/components/MemoryCard.vue | **100%** |
| src/stores/log.ts | **100%** |
| src/stores/memory.ts | **100%** |
| src/views/FeedbackView.vue | **100%** |
| src/views/LogsView.vue | 91.46% |
| src/views/MemoriesView.vue | 95.18% |
| src/views/HomeView.vue | 74.57% |
| src/api/index.ts | 25.37% |
| **All files（含排除项后）** | **83.83%** |

> 排除文件：`src/api/types.ts`（纯 TS 接口声明）、`src/router/index.ts`（路由配置）、`src/App.vue`（应用根组件）、`src/stores/index.ts`（仅 re-export）

---

### M3-12：单元测试报告输出

**完成状态**：✅ 完成  
**输出位置**：`doc/m3_report_v1.0.md`（本文档）

---

## 4. 测试运行汇总

### 后端测试

```
平台：linux, Python 3.12.3
工具：pytest-9.0.3, pytest-asyncio-1.3.0, httpx-0.28.1, coverage-7.13.5

测试文件：6 个
测试用例：105 个
通过：105 ✅
失败：0
总耗时：约 16s
语句覆盖率：87%
```

### 前端测试

```
平台：linux, Node.js, jsdom
工具：vitest@3.2.4, @vue/test-utils, @vitest/coverage-v8@3.2.4

测试文件：7 个
测试用例：77 个（含原有 HomeView 2 个）
通过：77 ✅
失败：0
总耗时：约 12s
语句覆盖率：83.83%
```

---

## 5. 测试中发现的缺陷

### BUG-001：MemoryService.demote() ChromaDB upsert 参数不完整

**发现时机**：`test_demote_removes_from_hot`（M3-02）执行时  
**缺陷描述**：`demote()` 方法调用 `_cold_col.upsert()` 时仅传入 `metadatas`，未传入 ChromaDB 1.x 必需的 `documents` 和 `embeddings` 参数，导致 `ValueError: Exactly one of documents, images must be provided in upsert`  
**影响范围**：降级操作（feedback 触发 demote、TierManager.check_memory_budget() 触发 demote）  
**修复方案**：修改 `demote()` 中的 `get()` 调用以包含 `["documents", "embeddings", "metadatas"]`，并在 `upsert()` 中传入完整参数  
**修复文件**：`backend/src/air_memory/memory/service.py`（第 111-128 行）  
**状态**：✅ 已修复，回归测试通过

---

## 6. 测试环境说明

| 项目 | 版本 |
|---|---|
| Python | 3.12.3 |
| pytest | 9.0.3 |
| pytest-asyncio | 1.3.0 |
| httpx | 0.28.1 |
| coverage | 7.13.5 |
| ChromaDB | 1.5.7 |
| FastAPI | 0.135.3 |
| Node.js | 系统版本 |
| Vitest | 3.2.4 |
| @vue/test-utils | 已安装 |
| @vitest/coverage-v8 | 3.2.4 |

---

## 7. 测试文件清单

### 后端测试文件

```
backend/tests/
├── conftest.py              # 公共 Fixture（MockSentenceTransformer、数据库初始化、服务注入）
├── test_memory_service.py   # MemoryService 单元测试（20 个用例）
├── test_tier_manager.py     # TierManager 单元测试（10 个用例）
├── test_feedback_service.py # FeedbackService 单元测试（17 个用例）
├── test_disk_manager.py     # DiskManager 单元测试（12 个用例）
├── test_log_service.py      # LogService 单元测试（16 个用例）
├── test_api.py              # REST API 集成测试（29 个用例）
└── test_main.py             # 健康检查测试（1 个用例，已有）
```

### 前端测试文件

```
frontend/tests/
├── MemoryCard.spec.ts    # MemoryCard 组件测试（16 个用例）
├── LogTable.spec.ts      # LogTable 组件测试（9 个用例）
├── MemoriesView.spec.ts  # MemoriesView 视图测试（9 个用例）
├── LogsView.spec.ts      # LogsView 视图测试（8 个用例）
├── FeedbackView.spec.ts  # FeedbackView 视图测试（12 个用例）
├── stores.spec.ts        # Pinia Store 测试（21 个用例）
└── HomeView.spec.ts      # HomeView 测试（2 个用例，已有）
```

---

*本报告由测试工程师 Sparrow 编制，对应 AIR_Memory 项目 M3（单元测试就绪）里程碑。*
