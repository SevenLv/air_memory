# Windows启动脚本_v1.1.1_pip升级命令修复与全角符号清理_20260413

## 标签

Windows, start.bat, pip, python -m pip, pip 25.3, 全角符号, UTF-8, GBK, CMD, 解析异常, Hotfix, v1.1.1

## 问题描述

v1.1.0 在 pip 25.3+ 环境下执行 `start.bat` 时, pip 升级步骤报错并终止启动流程:

```
ERROR: To modify pip, please run the following command:
E:\..\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
```

同时, `start.bat` 包含多处全角中文符号 (`，`、`（`、`）`、`！`), 在部分 Windows 系统中导致 CMD 解析异常 (如 `'art.bat' is not recognized`).

## 根因分析

1. pip 25.3+ 禁止通过 `pip` 可执行文件修改 pip 自身, 必须使用 `python -m pip`.
2. `start.bat` 中全角中文符号的 UTF-8 编码字节序 (`EF BC xx`) 在 `chcp 65001` 未完全生效的 CMD 环境中被 GBK 方式解析, 导致字节边界错位.

## 修复方案

1. 将 `start.bat` 和 `start.sh` 中的 `pip install --quiet --upgrade pip` 改为 `python -m pip install --quiet --upgrade pip`.
2. 将 `start.bat` 中所有全角符号替换为 ASCII 半角: `，`→`,`, `（`→`(`, `）`→`)`, `！`→`!`.

## 文件变更清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | pip 升级命令改为 `python -m pip`; 16处全角符号替换为 ASCII 半角 |
| `start.sh` | pip 升级命令改为 `python -m pip` |
| `doc/release_notes_v1.1.1.md` | 新建 v1.1.1 Hotfix 发布说明 |

## 最短修复路径

1. 在 `start.bat` 中将 `pip install --quiet --upgrade pip` 改为 `python -m pip install --quiet --upgrade pip`
2. 在 `start.bat` 中搜索并替换全角符号: `，`→`,`, `（`→`(`, `）`→`)`, `！`→`!`
3. 在 `start.sh` 中将 `pip install --quiet --upgrade pip` 改为 `python -m pip install --quiet --upgrade pip`
4. 保持 CRLF 行尾和 UTF-8 without BOM 编码不变
