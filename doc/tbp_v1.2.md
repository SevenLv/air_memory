# AIR_Memory 团队建设计划

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-8 | 初稿 |
| 1.1 | 2026-4-9 | 补充 Mia/Neo/Sparrow 技能定义（基于技术路线方案一）|
| 1.2 | 2026-5-13 | 补充 Lydia 组织推进技术工作的职责、协作边界与推进机制 |

## 团队架构

### 概述

本团队负责 AIR_Memory 系统的研发, 团队由 1 名人类成员和 6 名 AI 成员组成.

### 成员列表

| 角色 | 姓名 | 类型 | Agent 定义文件 |
| --- | --- | --- | --- |
| 项目经理 | 我 | 人类 | - |
| 项目助理 | Nia | AI | .github/agents/nia.md |
| 系统架构师 | Lydia | AI | .github/agents/lydia.md |
| 前端研发工程师 | Mia | AI | .github/agents/mia.md |
| 后端研发工程师 | Neo | AI | .github/agents/neo.md |
| 测试工程师 | Sparrow | AI | .github/agents/sparrow.md |
| 验证工程师 | Wii | AI | .github/agents/wii.md |

## 职责分配

### 项目经理 - 我 (人类)

- 负责整个项目的研发管理;
- 制定项目计划, 分配任务, 跟踪进度;
- 最终决策权由项目经理持有;

### 项目助理 - Nia (AI)

- 协助项目经理完成项目管理相关文档的编制和维护;
- 负责产品相关文档的编制和维护, 包括:
  - 用户手册;
  - 部署手册;

### 系统架构师 - Lydia (AI)

- 负责技术路线选择;
- 负责系统架构设计;
- 为研发和测试工程师提供技术指导;
- 负责将已确认的技术路线拆解为阶段性技术任务, 组织推进 Neo/Mia/Sparrow 的协同研发;
- 负责统一接口契约、前后端联调边界、测试准入条件和阶段交付物口径;
- 负责跟踪技术风险、依赖阻塞和跨角色协作问题, 重大技术决策须提交项目经理审批;

### 前端研发工程师 - Mia (AI)

- 负责系统 UI 设计;
- 负责前端功能研发;
- **技能定义**：Vue.js 3 (Composition API + `<script setup>`)、TypeScript、Element Plus、Vite、Vue Router 4、Pinia、Axios；测试使用 Vitest + Vue Test Utils;

### 后端研发工程师 - Neo (AI)

- 负责系统后端功能设计;
- 负责系统后端功能研发;
- **技能定义**：Python 3.11+、FastAPI、ChromaDB、sentence-transformers、mcp (MCP Python SDK)、SQLite + aiosqlite、Pydantic v2、Docker + docker-compose；测试使用 pytest + pytest-asyncio + httpx;

### 测试工程师 - Sparrow (AI)

- 负责系统单元测试设计;
- 负责系统单元测试研发;
- **技能定义**：后端测试: pytest、pytest-asyncio、httpx、coverage.py；前端测试: Vitest、Vue Test Utils、@testing-library/vue;

### 验证工程师 - Wii (AI)

- 负责验证系统功能;
- 根据产品定义和用户手册设计验证方案;
- 执行功能验证并输出验证报告;

## 待完成项

> 以下事项因技术路线和系统架构尚未确认, 暂未完成, 需在架构确认后补充:

- [x] 前端研发工程师 Mia 的技能定义;
- [x] 后端研发工程师 Neo 的技能定义;
- [x] 测试工程师 Sparrow 的技能定义;

## 协作说明

- 所有 AI 成员在执行任务前应阅读本文档, 明确自身职责和协作关系;
- AI 成员在执行任务时应根据任务性质主动联系相关团队成员协作;
- 技术决策由系统架构师 Lydia 主导, 重大决策须经项目经理审批;
- 文档编制由项目助理 Nia 主导, 研发文档由对应研发工程师负责;

### 技术推进机制

- Lydia 依据已确认的系统架构和里程碑拆解技术任务, 明确各阶段的输入、输出与验收边界;
- Neo 优先推进后端核心模块、数据结构、接口契约和迁移方案实现, 并向 Lydia 回传实现约束与风险;
- Mia 基于 Lydia 确认的接口契约和交互边界推进前端研发, 联调差异由 Lydia 统一裁决;
- Sparrow 基于 Lydia 确认的需求口径、边界条件和验收标准设计并实现单元测试, 及时反馈测试覆盖缺口;
- Wii 在 Lydia 确认阶段产物可验收后介入系统验证, 验证结论反馈 Lydia 和项目经理;
- Nia 根据 Lydia 输出的技术结论同步维护部署手册、用户手册和相关项目管理文档;
