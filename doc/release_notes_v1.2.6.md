# AIR_Memory v1.2.6 发布说明

**发布日期**: 2026-04-15
**版本类型**: Patch Release

---

## 概述

v1.2.6 包含 1 项 Bug 深度修复。针对"存储操作日志中依然存在大量问号"问题，从根因出发进行了彻底修复：确保 `PYTHONUTF8=1` 在任何情况下都强制生效，并在运行时补充 `sys.stdin` 的 UTF-8 重配置，从源头阻断中文内容在存储前被 CP1252 编码损坏为 `????`。不包含 Breaking Change，直接升级即可。

---

## 修复问题

### 存储操作日志中文内容变为问号的根因修复

**问题描述**

自 v1.2.0 起，"存储操作日志"中的原始内容字段持续出现大量 `????`（问号），v1.2.4 和 v1.2.5 的修复均只针对问题的"展示层"（乱码徽章检测），未触及中文内容在写入数据库前就已损坏的根本原因。

**根因分析**

Lydia（系统架构师）从以下两个问题入手进行了深度分析：

1. **为什么"查询操作日志"没有乱码？**

   查询日志的 `results` 字段存储的是包含记忆内容的 JSON 字符串，但前端 `parseResultsSummary()` 函数只将其解析为"N 条结果"显示，**从不渲染内容本身**。查询日志实际上也可能含有 `????`，只是 UI 层将其完全隐藏，因此用户感知不到乱码。

2. **乱码是存储前还是存储后产生的？**

   **存储前已产生**。`save_memory(content)` 中，`memory_service.save(content)` 与 `log_service.log_save(content, memory_id)` 使用同一个 Python str 对象。若 `save_logs.content` 是 `????`，ChromaDB 中存储的内容也同样是 `????`。

经过代码审查，发现两处关键漏洞导致 `PYTHONUTF8=1` 在特定情况下不能强制生效：

**漏洞一：启动脚本使用了"不覆盖已有值"的语法**

```bat
REM v1.2.5 start.bat（有漏洞）
if not defined PYTHONUTF8 set "PYTHONUTF8=1"
```

```bash
# v1.2.5 start.sh（有漏洞）
export PYTHONUTF8="${PYTHONUTF8:-1}"
```

若用户系统环境变量中已设置 `PYTHONUTF8=0`，或某些工具在启动前设置了 `PYTHONUTF8=0`，上述语法均不会覆盖，导致 Python 进程仍以 CP1252 处理字符串，新写入的中文依然变成 `????`。

**漏洞二：`main.py` 运行时重配遗漏 `sys.stdin`**

```python
# v1.2.5 main.py（遗漏 stdin）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
# sys.stdin 未重配
```

MCP stdio 传输模式从 `sys.stdin` 读取 JSON-RPC 消息（记忆内容通过此通道传入），若 `sys.stdin` 以 CP1252 编码打开，中文字节在读取时即被替换为 `?`。

**修复方案**

1. **`start.bat`**：移除 `if not defined` 条件检查，改为无条件强制设置：

   ```bat
   set "PYTHONUTF8=1"
   set "PYTHONIOENCODING=utf-8"
   ```

2. **`start.sh`**：移除 `${:-}` Shell 默认值语法，改为无条件强制导出：

   ```bash
   export PYTHONUTF8=1
   export PYTHONIOENCODING=utf-8
   ```

3. **`main.py`**：在应用启动时补充 `sys.stdin` 的 UTF-8 重配置，作为运行时兜底保障：

   ```python
   if hasattr(sys.stdin, 'reconfigure'):
       try:
           sys.stdin.reconfigure(encoding='utf-8', errors='replace')
       except Exception:
           pass
   ```

**修复效果**

- 无论系统环境变量如何设置，`PYTHONUTF8=1` 均强制生效；
- 即使 `PYTHONUTF8=1` 因某种原因未生效，`sys.stdin` 运行时重配作为双重兜底；
- 新存储的记忆内容不再被损坏为 `????`；
- 历史已损坏数据（`????`）因信息熵损失无法恢复，但乱码徽章（v1.2.5 修复）会正确标识这些记录。

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 修复 | 版本号更新至 1.2.6；补充 `sys.stdin` UTF-8 重配置；移除无用的 `import io` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.5` -> `1.2.6` |
| `start.bat` | 修复 | Banner 版本号 v1.2.5 -> v1.2.6；`PYTHONUTF8=1` 改为强制覆盖（移除 `if not defined`） |
| `start.sh` | 修复 | Banner 版本号 v1.2.5 -> v1.2.6；`PYTHONUTF8=1` 改为强制覆盖（移除 `${:-}` 默认值语法） |
| `backend/tests/test_main.py` | 测试新增 | 新增 v1.2.6 版本号验证、stdin 重配代码存在性验证、stdin encoding 验证共 4 个测试 |
| `doc/release_notes_v1.2.6.md` | 新增 | 本文件 |
| `doc/user_guide.md` | 文档更新 | 2.4 节补充 v1.2.6 根因修复说明 |

---

## 升级说明

前往 [GitHub Releases 页面](https://github.com/SevenLv/air_memory/releases/latest) 下载 v1.2.6 发布包，解压后将旧版本 `data/` 目录复制到新目录下，然后启动服务即可。

**macOS / Linux**：

```bash
unzip air_memory-v1.2.6.zip
cp -r old_dir/data air_memory-v1.2.6/
cd air_memory-v1.2.6
bash start.sh
```

**Windows**：

解压 `air_memory-v1.2.6.zip`，将旧版本 `data\` 目录复制到新目录下，双击 `start.bat` 或在 CMD 中执行：

```cmd
start.bat
```

升级不影响已有数据，`data/` 目录完整保留。历史乱码数据（`????`）无法恢复，但"乱码"徽章会正确标识这些记录（v1.2.5 修复）。v1.2.6 升级后，新存储的记忆内容将正常显示中文，不再出现问号。
