# Windows启动脚本_v1.0.0 Windows启动失败修复_20260411

## 标签

Windows, start.bat, 编码, UTF-8, GBK, CRLF, LF, chcp, CP936, 兼容性, 行尾, 批处理

## 问题描述

v1.0.0 在 Windows 上执行 `start.bat` 出现以下错误:
1. `'art.bat锛屾垨鍦ㄥ懡浠ゆ彁绀虹涓墽琛?start.bat' 不是内部或外部命令` - REM 注释内容被当作命令执行
2. `AIR_Memory 涓€閿惎鍔?` - 中文乱码显示
3. `'涓嬭浇鍦板潃锛歨ttps:' 不是内部或外部命令` - URL 被当作命令执行
4. Docker 检测失败

## 根因分析

### 核心根因: UTF-8 + LF 行尾在 GBK 环境下的行边界丢失问题

**文件状态**: `start.bat` 使用 UTF-8 编码（无 BOM）+ LF 行尾（Unix 风格）

**Windows CMD 解析机制**:
- Windows CMD.EXE 默认使用系统 OEM 代码页（中文 Windows = CP936/GBK）读取 .bat 文件
- GBK 字符: 前导字节范围 0x81-0xFE，第二字节范围 0x40-0x7E 或 0x80-0xFE
- **关键问题**: UTF-8 中文字符（3字节序列）在 GBK 解析时发生字节边界错位

**具体机制**:
多个行末尾的 UTF-8 字节恰好是 GBK 前导字节（0x81-0xFE）。例如：
- Line 3 末尾: `）` = UTF-8 `EF BC 89`，最后字节 `0x89` 是 GBK 前导字节
- LF-only 行尾: `0x89 0x0A`，GBK 解析器将 `0x0A`（LF = 10，< 0x40）视为无效第二字节
- 当 CMD 的 GBK 解析器同时消费 `0x89` 和 `0x0A` 时，**行尾 LF 被吃掉**
- 相邻两行在 CMD 看来是同一行，导致 REM 注释内容被当作命令执行

**受影响的行（共12行）**: Line 3, 6, 11, 15, 18, 21, 27, 30, 35, 38, 46, 64

## 修复方案

### 修改 `start.bat`

**变更1**: 在 `@echo off` 后立即添加 `chcp 65001 >nul 2>&1`
- 将控制台代码页切换到 UTF-8，确保后续中文内容被正确解析和显示
- 在任何中文内容行之前执行，使 CMD 以 UTF-8 模式读取后续行和 IF 块

**变更2**: 将行尾从 LF（Unix）改为 CRLF（Windows）
- CRLF 确保行边界始终被保留:
  - 即使 GBK 解析器消费了 `0x0D`（CR，13 < 64，无效第二字节），`0x0A` 仍然保留行边界
  - 完全消除 "LF 被 GBK 解析器吃掉导致行合并" 的问题

### 新增 `.gitattributes`

```
*.bat text eol=crlf
*.sh text eol=lf
```

确保不同 Git 客户端（尤其是 Windows `core.autocrlf=true` 的用户）检出后能保持正确行尾。

## 为何不使用 GBK 编码

- 工程规则要求 UTF-8 编码（`ai_rules/file_rules/basic_rules.md`）
- .bat 文件不能使用 UTF-8 with BOM（BOM 字节 `EF BB BF` 会导致 `@echo off` 失败）
- `chcp 65001 + CRLF + UTF-8 without BOM` 在现代 Windows 10/11 上完全可靠

## 文件变更清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | 添加 `chcp 65001 >nul 2>&1`（第2行）；行尾 LF → CRLF |
| `.gitattributes` | 新建，指定 `*.bat eol=crlf`，`*.sh eol=lf` |

## 最短修复路径（快速复现）

1. 在 `start.bat` 第1行（`@echo off`）后插入: `chcp 65001 >nul 2>&1`
2. 将 `start.bat` 所有行尾从 LF 改为 CRLF（可用 Python `content.replace(b'\n', b'\r\n')` 或编辑器转换）
3. 新建 `.gitattributes` 文件，内容: `*.bat text eol=crlf`
4. 提交两个文件
