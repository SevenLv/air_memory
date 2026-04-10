# AIR_Memory v1.0.3 发布说明

**发布日期**: 2026-04-11
**版本类型**: Hotfix

---

## 概述

本次发布为 v1.0.2 的 Hotfix 版本, 仅修复 Windows 10 1809 (Build 17763) 及以下版本上 `start.bat` 提供错误的 Docker Desktop 下载地址问题, 不引入任何新功能或架构变更.

---

## 修复问题

### Windows start.bat 在 Windows 10 1809 上提供不兼容的 Docker Desktop 下载地址

**问题描述**

在 Windows 10 1809 (Build 17763) 及以下版本上执行 `start.bat` 时, 若用户未安装 Docker, 脚本提示的 Docker Desktop 下载地址指向最新版本. 然而最新版 Docker Desktop 不兼容 Windows 10 1809, 导致用户下载安装后无法正常运行.

**根因分析**

v1.0.2 的 `start.bat` 在 Docker 未安装时统一提示同一个最新版 Docker Desktop 下载链接, 未考虑 Windows 10 1809 (Build <= 17763) 的兼容性限制. Docker Desktop 4.16.0 及以上版本要求 Windows 10 1903 (Build 18362) 或更高版本.

**修复方案**

在 `start.bat` 中新增 Windows Build 号检测逻辑, 根据检测结果提供对应版本的 Docker Desktop 下载地址:

| Windows 版本 | Build 号 | 提示下载的 Docker Desktop 版本 |
| --- | --- | --- |
| Windows 10 1809 及以下 | <= 17763 | 4.15.0 (兼容版本) |
| Windows 10 1903 及以上 / Windows 11 | >= 18362 | 最新版 |

**检测原理**

使用 `ver` 命令获取 Windows 版本字符串, 提取其中的 Build 号进行比较判断:

- `ver` 输出格式示例: `Microsoft Windows [Version 10.0.17763.914]`
- 通过 `for /f` 提取 Build 号字段 (`17763`)
- 检测失败时默认设为 `99999`, 视为新版系统, 提供最新版下载地址

---

## 影响范围

| 平台 | 是否受影响 | 说明 |
| --- | --- | --- |
| Windows 10 1809 及以下 (Build <= 17763) | 是 | 受 v1.0.2 问题影响, 需升级至 v1.0.3 |
| Windows 10 1903 及以上 / Windows 11 | 否 (建议升级) | 升级后脚本更健壮 |
| macOS | 否 | 使用 start.sh, 不受影响 |
| Linux | 否 | 使用 start.sh, 不受影响 |

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 修改 | 新增 Windows Build 号检测逻辑; 根据 Build 号分支提供对应版本的 Docker Desktop 下载地址 |

---

## 升级说明

从 v1.0.2 升级至 v1.0.3 只需拉取最新代码, 无需重新构建镜像或迁移数据.

**升级步骤**

1. 停止当前运行的服务:

```bat
docker compose stop
```

2. 拉取最新代码:

```bat
git pull
```

3. 重新启动服务:

```bat
start.bat
```

> **说明**: 本次 Hotfix 仅修改 `start.bat` 中的下载地址提示逻辑, 后端/前端镜像无需重新构建, 现有数据完整保留, 升级过程对系统数据无任何影响.
