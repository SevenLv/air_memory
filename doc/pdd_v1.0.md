# AIR_Memory 产品定义

## 变更记录

| 版本号 | 变更时间 | 变更内容 |
| --- | --- | --- |
| 1.0 | 2026-4-8 | 初稿 |

## 产品定义

### 产品概述

AIR_Memory 是一个为 AI Agent 设计的本地部署的记忆系统, AI Agent 可以通过 AIR_Memory 高效的存储记忆和查询相关记忆.

### 功能定义

- AIR_Memory 应支持 macOS 和 Windows 操作系统的本地一键部署;
- AIR_Memory 在默认情况下应自启动;
- AIR_Memory 向 AI Agent 提供接口, AI Agent 可以通过这个接口保存记忆;
- AIR_Memory 向 AI Agent 提供接口, AI Agent 可以通过这个接口查询自己所需的相关记忆;
- AIR_Memory 在保存记忆时的操作时间不应大于 100ms;
- AIR_Memory 在查询记忆时的操作时间不应大于 100ms;
- AIR_Memory 应向人类提供 UI 接口实现如下功能:
  - 查询记忆数据;
  - 删除指定的记忆数据;
  - 查看 AI 保存记忆的记录, 包括: 保存记忆的时间/原始内容;
  - 查看 AI 查询记忆的记录, 包括: 查询记忆的时间/查询条件和返回的查询结果;
