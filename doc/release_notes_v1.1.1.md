# AIR_Memory v1.1.1 发布说明

**发布日期**: 2026-04-13
**版本类型**: Hotfix

---

## 概述

本次发布为 v1.1.0 的 Hotfix 版本, 修复 Windows 环境下执行 `start.bat` 时因 pip 25.3+ 版本限制和全角中文符号导致启动失败的问题.

---

## 修复问题

### 1. Windows start.bat 使用 pip 25.3+ 时启动失败

**问题描述**

在 pip 25.3 及以上版本中执行 `start.bat` 时, pip 升级步骤报错并终止:

```
ERROR: To modify pip, please run the following command:
E:\..\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
```

**根因分析**

`start.bat` 第 65 行使用 `pip install --quiet --upgrade pip` 升级 pip 自身. pip 25.3+ 新增安全限制: 不允许通过 `pip` 可执行文件修改 pip 自身, 必须通过 `python -m pip` 方式调用.

**修复方案**

将 `start.bat` 和 `start.sh` 中的 pip 升级命令由:

```
pip install --quiet --upgrade pip
```

改为:

```
python -m pip install --quiet --upgrade pip
```

### 2. Windows start.bat 包含全角中文符号导致 CMD 解析异常

**问题描述**

在部分 Windows 系统 (主要是未完整支持 UTF-8 代码页的环境) 中, 执行 `start.bat` 时报错:

```
'art.bat' is not recognized as an internal or external command
```

**根因分析**

`start.bat` 中存在多处全角中文符号 (`，`、`（`、`）`、`！`), 其 UTF-8 编码字节序形如 `EF BC xx`, 第三字节落在 GBK 前导字节范围 (0x81-0xFE) 内. 在 `chcp 65001` 未能完全生效的环境中, CMD 仍以 GBK 方式解析部分字节, 导致字节边界错位, 相关行内容被当作命令执行. 另外, 上述全角符号违反 `ai_rules/README.md` 中"禁止使用全角中文符号"的规范要求.

**修复方案**

将 `start.bat` 中所有全角中文符号替换为 ASCII 半角等价符号:

| 全角符号 | 替换为 |
| --- | --- |
| `，` | `,` |
| `（` | `(` |
| `）` | `)` |
| `！` | `!` |

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `start.bat` | 修复 | pip 升级命令改为 `python -m pip`; 全角符号替换为 ASCII 半角 |
| `start.sh` | 修复 | pip 升级命令改为 `python -m pip` |

---

## 升级说明

直接拉取最新代码即可:

```bash
git pull
```

如已存在 `.venv` 目录, 建议删除后重新运行启动脚本以使修复生效:

```cmd
rmdir /s /q .venv
start.bat
```
