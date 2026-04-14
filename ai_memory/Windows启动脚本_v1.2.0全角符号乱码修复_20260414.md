# Windows启动脚本_v1.2.0全角符号乱码修复_20260414

## 标签

Windows, start.bat, 全角符号, 乱码, 编码, UTF-8, GBK, CMD, 页(CMD), v1.2.0, 兼容性, 批处理

## 问题描述

v1.2.0 start.bat 在 Windows 上执行时出现以下错误:

```
'页（CMD' is not recognized as an internal or external command,
```

错误发生在步骤 [3/4] 之后, [4/4] 之前.

## 根因分析

v1.2.0 在修复中文内容损坏问题时新增了 PYTHONUTF8 相关的解释性 REM 注释（lines 99-100）,
这些注释中包含全角中文符号:

- line 99: `，` (U+FF0C)
- line 100: `（` (U+FF08), `）` (U+FF09), `，` (U+FF0C)

全角符号 UTF-8 编码字节序形如 `EF BC xx`, 第三字节落在 GBK 前导字节范围 (0x81-0xFE),
在部分 Windows 系统 CMD 中 `chcp 65001` 未能完全生效时导致解析异常.

`'页（CMD'` 对应 line 100 中的 `代码页（CMD 显示` 片段.

违反 ai_rules/README.md 中"禁止使用全角中文符号"规范.

## 修复方案

将 start.bat lines 99-100 中的全角符号替换为 ASCII 半角等价符号:

- `，` → `,`
- `（` → `(`
- `）` → `)`

## 最短修复路径

1. 在 start.bat 中搜索全角符号: `，`、`（`、`）`
2. 逐一替换为对应半角符号: `,`、`(`、`)`
3. 保持 CRLF 行尾和 `chcp 65001` 不变
4. 新增测试 `test_start_bat_no_fullwidth_symbols` 防止回归
5. 提交

## 变更文件清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | lines 99-100 全角符号替换为 ASCII 半角符号 |
| `tests/test_start_bat_encoding.py` | 新增 `test_start_bat_no_fullwidth_symbols` 测试 |
