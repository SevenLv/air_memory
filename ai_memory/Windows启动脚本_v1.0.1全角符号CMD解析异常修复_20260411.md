# Windows启动脚本_v1.0.1全角符号CMD解析异常修复_20260411

## 标签

Windows, start.bat, 全角符号, 半角符号, UTF-8, GBK, CMD, 解析异常, 编码规范, Hotfix, v1.0.2

## 问题描述

v1.0.1 在部分 Windows 系统（主要是 Windows 7 或特定 Windows 10 配置）下执行 `start.bat` 出现以下错误:
1. `'或在命令提示符中执行' is not recognized as an internal or external command`
2. `'下载地址：https:' is not recognized as an internal or external command`

## 根因分析

`start.bat` 中包含全角中文符号（`：`、`，`、`（`、`）`、`。`、`！`）, 其 UTF-8 编码字节序形如 `EF BC xx`, 第三字节落在 GBK 前导字节范围（0x81-0xFE）内. 在部分 Windows 系统的 CMD 中, `chcp 65001` 未能完全生效, CMD 仍以 GBK 方式解析部分字节, 导致字节边界错位, 相关行内容被当作命令执行.

另外, 上述全角符号违反 `ai_rules/README.md` 中"禁止使用全角中文符号"的规范要求.

## 修复方案

将 `start.bat` 中所有全角中文符号替换为 ASCII 半角等价符号:

| 全角符号 | 替换为 |
| --- | --- |
| `：` | `:` |
| `，` | `,` |
| `（` | `(` |
| `）` | `)` |
| `。` | `.` |
| `！` | `!` |

保留: 中文文字内容, `chcp 65001`, CRLF 行尾.

## 文件变更清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | 所有全角中文符号替换为 ASCII 半角等价符号 |

## 最短修复路径（快速复现）

1. 在 `start.bat` 中搜索所有全角符号: `：`、`，`、`（`、`）`、`。`、`！`
2. 逐一替换为对应半角符号: `:`、`,`、`(`、`)`、`.`、`!`
3. 保持 CRLF 行尾和 `chcp 65001` 不变
4. 提交 `start.bat`
