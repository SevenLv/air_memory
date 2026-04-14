# AIR_Memory v1.2.2 发布说明

**发布日期**: 2026-04-14
**版本类型**: Patch Release

---

## 概述

v1.2.2 修复了用户手册中记录的 Swagger UI 地址 `http://localhost:8080/api/v1/docs` 不可访问的问题. 此问题导致 AI 无法通过浏览器或程序读取 OpenAPI 接口规范, 进而影响 REST API 的正常使用. 不包含 Breaking Change, 直接升级即可.

---

## 修复问题

### Swagger UI 地址 /api/v1/docs 不可访问 (Issue #33)

**问题描述**

用户手册 3.2.1 节记录的 API 文档地址 `http://localhost:8080/api/v1/docs` 返回 404 或被 Vue SPA 路由拦截, 无法访问 Swagger UI.

**根因分析**

`backend/src/air_memory/main.py` 创建 `FastAPI` 实例时未指定 `docs_url` 参数, FastAPI 默认将 Swagger UI 挂载到 `/docs`. 实际可访问地址与用户手册记录不一致, 导致 AI 客户端或用户按文档操作时无法获取接口规范.

**修复方案**

在 `FastAPI` 构造函数中显式指定 OpenAPI 相关 URL, 使其与 API 路由前缀 `/api/v1/` 保持一致:

```python
app = FastAPI(
    ...
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)
```

修复后可访问的文档地址:

| 地址 | 说明 |
| --- | --- |
| `http://localhost:8080/api/v1/docs` | Swagger UI（交互式 API 文档） |
| `http://localhost:8080/api/v1/redoc` | ReDoc（只读 API 文档） |
| `http://localhost:8080/api/v1/openapi.json` | OpenAPI Schema（JSON 格式） |

上述路径均以 `/api/` 为前缀, SPA 回退处理器已正确排除该前缀, 不会被 Vue Router 拦截.

---

## 变更文件

| 文件 | 变更类型 | 说明 |
| --- | --- | --- |
| `backend/src/air_memory/main.py` | 修复 | `FastAPI` 构造添加 `docs_url="/api/v1/docs"`, `redoc_url="/api/v1/redoc"`, `openapi_url="/api/v1/openapi.json"`; 版本号更新为 `1.2.2` |
| `backend/pyproject.toml` | 版本更新 | version `1.2.1` -> `1.2.2` |
| `start.bat` | 版本更新 | Banner 版本号 v1.2.1 -> v1.2.2 |
| `start.sh` | 版本更新 | Banner 版本号 v1.2.1 -> v1.2.2 |

---

## 升级说明

直接拉取最新代码并重新启动即可:

```bash
git pull
```

**macOS / Linux**:

```bash
bash start.sh
```

**Windows**:

```cmd
start.bat
```

升级不影响已有数据, `data/` 目录完整保留.
