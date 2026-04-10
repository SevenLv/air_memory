# Windows启动脚本_v1.0.3_CMD复合块括号解析异常修复_20260410

## 标签

Windows, start.bat, CMD, 复合块, 括号, 转义, enabledelayedexpansion, Windows 10 1809, Build 17763, 多字节字符, 解析异常, Hotfix, v1.0.4

## 问题描述

v1.0.3 在 Windows 10 1809 (Build 17763) 及以下版本上执行 `start.bat` 时, 脚本打印标题横幅后立即退出并报错:

```
需安装兼容版本 was unexpected at this time.
```

文件无全角符号, 无 BOM, CRLF 行尾均正常.

## 根因分析

`start.bat` 第 28 行位于嵌套 `if ( ... )` 复合块内:

```bat
if errorlevel 1 (
    ...
    if !WINBUILD! LEQ 17763 (
        echo        当前系统(Windows 10 Build !WINBUILD!)需安装兼容版本 Docker Desktop 4.15.0.
    ...
    )
)
```

Windows 10 1809 的 CMD 解析器在扫描复合块括号深度时存在已知缺陷: 当 `echo` 行中包含多字节中文字符时, 解析器对字节边界的计算出现偏差, 导致 `当前系统` 后的开括号 `(` 未被计入深度计数, 而 `!WINBUILD!` 后的 `)` 被误判为内层 `if` 块的闭合符. `需安装兼容版本 Docker Desktop 4.15.0.` 成为孤立语句, 触发 `was unexpected at this time` 错误.

## CMD 复合块括号解析机制

在 CMD 解析 `if ( ... )` 或 `for ( ... )` 等复合块时:
- 解析器维护一个括号深度计数器
- 遇到 `(` 时深度 +1, 遇到 `)` 时深度 -1, 深度归零时认为块结束
- **缺陷**: 在老版本 CMD (Windows 10 1809 及以下) 中, `echo` 行内含多字节字符时, 字符前的 `(` 可能不被计入深度计数, 导致后续 `)` 过早关闭块

## 修复方案

将复合块内 `echo` 语句中的括号改用 `^(` / `^)` 转义:

```bat
echo        当前系统^(Windows 10 Build !WINBUILD!^)需安装兼容版本 Docker Desktop 4.15.0.
```

**原理**:
- `^` 是 CMD 转义符, 在解析复合块时被消费, 后续字符 `(` / `)` 不参与括号深度计数
- 执行阶段 `^` 已被消费, `!WINBUILD!` 延迟展开后输出内容正确, 例如:
  `当前系统(Windows 10 Build 17763)需安装兼容版本 Docker Desktop 4.15.0.`
- `enabledelayedexpansion` 不影响 `^` 的转义行为

## 通用规则: 复合块内含中文的 echo 括号必须转义

**在以下场景中, `echo` 语句里的括号必须使用 `^(` / `^)` 转义:**

- `echo` 行处于 `if ( ... )` 或 `for ( ... )` 等复合块内 (任意嵌套深度)
- `echo` 行中同时包含中文字符和括号 `(` / `)`
- 目标兼容 Windows 10 1809 (Build 17763) 及以下版本

**不受影响的场景** (无需转义):
- `echo` 行在复合块外部 (顶层命令)
- `echo` 行只有 ASCII 字符
- `REM` 注释行

## 文件变更清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | 第 28 行: `当前系统(Windows 10 Build !WINBUILD!)` 改为 `当前系统^(Windows 10 Build !WINBUILD!^)` |
| `doc/release_notes_v1.0.4.md` | 新建, v1.0.4 发布说明 |
| `.github/workflows/release.yml` | `--notes-file` 更新为 `doc/release_notes_v1.0.4.md` |

## 最短修复路径

1. 搜索 `start.bat` 中所有位于复合块 (`if (` / `for (`) 内, 且包含中文字符的 `echo` 行
2. 将行内的 `(` 改为 `^(`, `)` 改为 `^)`
3. 保持 CRLF 行尾、UTF-8 without BOM 编码不变
4. 新建 `doc/release_notes_v1.0.4.md`
5. 更新 `.github/workflows/release.yml` 中 `--notes-file` 为 `doc/release_notes_v1.0.4.md`
6. 提交并推送; 由项目经理合并后触发 Actions 工作流发布 v1.0.4

## 历史上下文

| 版本 | 问题 | 修复 |
| --- | --- | --- |
| v1.0.0 | LF 行尾 + GBK 字节边界吃掉换行符, 导致 REM 内容被当命令执行 | 改为 CRLF + 添加 `chcp 65001` |
| v1.0.1 | 全角符号 (`：`, `，`, `（`, `）` 等) 在部分 Windows 的 GBK 模式下被误解析 | 全角符号全部替换为 ASCII 半角 |
| v1.0.2 | Docker 未安装时未区分系统版本, Windows 10 1809 被推荐了不兼容的最新版 Docker Desktop | 新增 Windows Build 号检测, 分支提供下载地址 |
| v1.0.3 | 复合块内含中文的 `echo` 行括号在老版 CMD 解析时计数偏差, `)` 过早关闭块 | 括号改用 `^(` / `^)` 转义 |
