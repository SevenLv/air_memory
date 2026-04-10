# Windows启动脚本_v1.0.2_Docker版本兼容性修复_20260411

## 标签

Windows, start.bat, Docker Desktop, 版本兼容性, Windows 10 1809, Build 17763, 下载地址, 批处理, for /f, ver, WINBUILD

## 问题描述

Windows 10 1809 (Build 17763) 用户无法使用脚本提示的 Docker Desktop 下载地址安装 Docker.
原因: 脚本提供的是最新版 Docker Desktop 下载链接, 而该版本不兼容 Windows 10 1809.

## 版本兼容性信息

| Windows 版本 | Build 号 | 最大兼容 Docker Desktop 版本 | 下载地址 |
| --- | --- | --- | --- |
| Windows 10 1809 及以下 | <= 17763 | 4.15.0 | https://desktop.docker.com/win/main/amd64/93002/Docker%20Desktop%20Installer.exe |
| Windows 10 1903 及以上 / Windows 11 | >= 18362 | 最新版 | https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe |

## 修复方案

在 `start.bat` 中添加 Windows Build 号检测逻辑, 根据检测结果提供对应版本的下载地址.

### Windows Build 号检测方法

```batch
REM 检测 Windows 版本以提供兼容的 Docker Desktop 下载地址
for /f "tokens=2 delims=[]" %%a in ('ver') do set "WINVERSTR=%%a"
for /f "tokens=3 delims=." %%b in ("!WINVERSTR!") do set "WINBUILD=%%b"
if "!WINBUILD!"=="" set "WINBUILD=99999"
```

原理:
- `ver` 输出格式: `Microsoft Windows [Version 10.0.17763.914]`
- 第一个 for: 提取 `[...]` 内容, 得到 `Version 10.0.17763.914`
- 第二个 for: 按 `.` 分割, 取第3个 token, 得到 Build 号 `17763`
- 检测失败时默认设为 `99999` (视为新版系统, 提供最新 URL)

### 条件判断与下载地址提示

```batch
if errorlevel 1 (
    echo [错误] 未检测到 Docker,请先安装 Docker Desktop.
    if !WINBUILD! LEQ 17763 (
        echo        当前系统(Windows 10 Build !WINBUILD!)需安装兼容版本 Docker Desktop 4.15.0.
        echo        下载地址:https://desktop.docker.com/win/main/amd64/93002/Docker%%20Desktop%%20Installer.exe
    ) else (
        echo        下载地址:https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe
    )
    pause
    exit /b 1
)
```

## 关键编码注意事项

- URL 中的 `%20` 在批处理中必须写为 `%%20`, 否则 CMD 会将 `%2` 解析为第2个命令行参数
- `%%20` 在批处理 echo 语句中输出为 `%20` (正确的 URL 编码)
- 需要 `setlocal enabledelayedexpansion` 才能使用 `!WINBUILD!` 延迟展开
- 文件编码: UTF-8 without BOM + CRLF 行尾 (与 v1.0.0/v1.0.1 一致)
- 所有新增内容均使用 ASCII 半角符号 (无全角符号)

## 文件变更清单

| 文件 | 变更内容 |
| --- | --- |
| `start.bat` | 新增 Windows Build 号检测 (3行); 将 Docker 未安装提示改为根据 Build 号显示对应下载地址 |

## 最短修复路径

1. 在 `echo ==========================================` (第16行) 之后添加 Windows 版本检测代码 (3行)
2. 将 Docker 未安装错误提示中的固定 URL 替换为基于 `!WINBUILD! LEQ 17763` 的条件分支
3. URL 中的 `%20` 写为 `%%20`
4. 保持 CRLF 行尾和 UTF-8 without BOM 编码不变
5. 提交 `start.bat`
