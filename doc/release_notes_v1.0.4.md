# AIR_Memory v1.0.4 发布说明

**发布日期**: 2026-04-10
**版本类型**: Hotfix

---

## 概述

本次发布为 v1.0.3 的 Hotfix 版本, 仅修复 Windows 10 1809 (Build 17763) 及以下版本上执行 `start.bat` 时脚本在启动阶段崩溃的问题, 不引入任何新功能或架构变更.

---

## 修复问题

### Windows start.bat 在 Windows 10 1809 上启动时报错 "was unexpected at this time"

**问题描述**

在 Windows 10 1809 (Build 17763) 及以下版本上执行 `start.bat` 时, 脚本打印标题横幅后立即退出并报错:

```
需安装兼容版本 was unexpected at this time.
```

**根因分析**

v1.0.3 的 `start.bat` 第 28 行:

```bat
echo        当前系统(Windows 10 Build !WINBUILD!)需安装兼容版本 Docker Desktop 4.15.0.
```

该行位于嵌套 `if ( ... )` 复合块内. Windows 10 1809 的 CMD 解析器在扫描复合块括号深度时存在已知缺陷: 当 `echo` 行中包含多字节中文字符时, 解析器对字节边界的计算出现偏差, 导致 `当前系统` 后的开括号 `(` 未被计入深度, 而 `!WINBUILD!` 后的 `)` 被误判为内层 `if` 块的闭合符. `需安装兼容版本 Docker Desktop 4.15.0.` 成为孤立语句, 触发 `was unexpected at this time` 错误.

**修复方案**

将第 28 行中的括号改用 `^(` / `^)` 转义, 阻止 CMD 解析器将其计入复合块括号深度计数:

```bat
echo        当前系统^(Windows 10 Build !WINBUILD!^)需安装兼容版本 Docker Desktop 4.15.0.
```

CMD 解析器在解析复合块时消费 `^` 并忽略后续括号的计数作用; 执行阶段 `^` 已被消费, `!WINBUILD!` 延迟展开后输出内容与预期一致, 例如:

```
当前系统(Windows 10 Build 17763)需安装兼容版本 Docker Desktop 4.15.0.
```

---

## 影响范围

| 平台 | 是否受影响 | 说明 |
| --- | --- | --- |
| Windows 10 1809 及以下 (Build <= 17763) | 是 | 受 v1.0.3 问题影响, 脚本无法启动, 需升级至 v1.0.4 |
| Windows 10 1903 及以上 / Windows 11 | 否 (建议升级) | 升级后脚本更健壮 |
| macOS | 否 | 使用 start.sh, 不受影响 |
| Linux | 否 | 使用 start.sh, 不受影响 |

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 修改 | 第 28 行括号改用 `^(` / `^)` 转义, 修复 Windows 10 1809 CMD 解析器对复合块内含中文的 `echo` 行括号计数偏差问题 |

---

## 升级说明

从 v1.0.3 升级至 v1.0.4 只需拉取最新代码, 无需重新构建镜像或迁移数据.

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

> **说明**: 本次 Hotfix 仅修改 `start.bat` 中一行内容, 后端/前端镜像无需重新构建, 现有数据完整保留, 升级过程对系统数据无任何影响.
