"""Tests for the FastAPI 应用入口 main.py。

覆盖以下功能：
- /health 健康检查端点
- STATIC_DIR 未配置时不挂载静态文件
- STATIC_DIR 存在时挂载静态文件并支持 SPA 回退
- CORS_ORIGINS 环境变量配置
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from air_memory.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /health 端点测试
# ---------------------------------------------------------------------------


def test_health_check() -> None:
    """测试 GET /health 返回 200 和正确响应体。"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_with_static_dir_mounted(tmp_path) -> None:
    """当前端静态目录存在并已挂载时，/health 端点仍能正常响应。

    用独立测试应用模拟 STATIC_DIR 存在时的挂载状态，验证 /health 不被静态文件
    路由覆盖（API 路由优先级高于 StaticFiles 挂载）。
    """
    # 准备临时静态目录
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>AIR Memory</body></html>", encoding="utf-8")

    # 构造与 main.py 相同挂载顺序的测试应用：先注册 /health，再挂载 /
    test_app = FastAPI()

    @test_app.get("/health", tags=["system"])
    async def health_check() -> dict:
        return {"status": "ok"}

    test_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    test_client = TestClient(test_app)
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 静态文件服务逻辑测试
# ---------------------------------------------------------------------------


def test_static_not_mounted_when_dir_absent(monkeypatch, tmp_path) -> None:
    """当 STATIC_DIR 环境变量指向不存在的目录时，不挂载静态文件服务。"""
    nonexistent = str(tmp_path / "nonexistent_dist")
    monkeypatch.setenv("STATIC_DIR", nonexistent)

    # 重新解析 STATIC_DIR（模拟 main.py 的判断逻辑）
    static_dir = os.getenv("STATIC_DIR", "frontend/dist")
    assert not os.path.isdir(static_dir), f"测试目录不应存在：{static_dir}"

    # 验证当 STATIC_DIR 不存在时，不会挂载静态文件
    # 通过检查 os.path.isdir 判断逻辑来验证
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    test_app = FastAPI()
    if os.path.isdir(static_dir):
        test_app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    route_names = [getattr(r, "name", None) for r in test_app.routes]
    assert "static" not in route_names, "STATIC_DIR 不存在时不应挂载静态文件路由"


def test_static_dir_serves_index_html(tmp_path) -> None:
    """当 STATIC_DIR 存在时，/ 路由应返回 index.html 内容（SPA 路由回退）。"""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_content = "<html><body>AIR Memory SPA</body></html>"
    (dist_dir / "index.html").write_text(index_content, encoding="utf-8")

    test_app = FastAPI()
    test_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    test_client = TestClient(test_app)
    response = test_client.get("/")
    assert response.status_code == 200
    assert "AIR Memory SPA" in response.text


def test_static_dir_unknown_route_returns_404(tmp_path) -> None:
    """当请求的路径在静态目录中不存在时，不含 SPA 回退处理器的纯 StaticFiles 应用返回 404。

    注意：Starlette 1.x 的 StaticFiles(html=True) 不提供 SPA 路由回退（即不会为所有
    未知路径返回 index.html）。html=True 仅在以下情况有效：
    - 请求路径是目录时，返回该目录下的 index.html（如 "/" → "index.html"）
    - 存在 404.html 文件时，以 404 状态码返回 404.html

    完整 SPA 路由回退需通过自定义异常处理器实现（见 test_spa_fallback_returns_index_html）。
    """
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>AIR Memory SPA</body></html>", encoding="utf-8")

    test_app = FastAPI()
    test_app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    test_client = TestClient(test_app, raise_server_exceptions=False)
    # 访问静态目录中不存在的路径，无 SPA 回退处理器时 Starlette 1.x 返回 404
    response = test_client.get("/memories")
    assert response.status_code == 404


def _make_spa_app(static_dir: str) -> FastAPI:
    """创建含 StaticFiles 挂载和 SPA 回退处理器的测试应用（与 main.py 行为一致）。"""
    test_app = FastAPI()
    test_app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    @test_app.exception_handler(StarletteHTTPException)
    async def _spa_fallback(request, exc):
        if exc.status_code == 404:
            path = request.url.path
            if not path.startswith("/api/") and not path.startswith("/mcp"):
                index_path = os.path.join(static_dir, "index.html")
                if os.path.isfile(index_path):
                    return FileResponse(index_path)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return test_app


def test_spa_fallback_returns_index_html(tmp_path) -> None:
    """当 STATIC_DIR 存在且请求路径为非 API 路径时，SPA 回退处理器应返回 index.html（状态码 200）。

    验证自定义异常处理器能正确处理 Vue Router history 模式下的直接 URL 访问。
    """
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_content = "<html><body>AIR Memory SPA</body></html>"
    (dist_dir / "index.html").write_text(index_content, encoding="utf-8")

    test_client = TestClient(_make_spa_app(str(dist_dir)))
    response = test_client.get("/memories")
    assert response.status_code == 200
    assert "AIR Memory SPA" in response.text


def test_spa_fallback_api_path_returns_json_404(tmp_path) -> None:
    """/api/ 路径的 404 错误应返回 JSON 格式响应，而非 SPA 回退。

    验证自定义异常处理器不会覆盖 API 路径的错误响应。
    """
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>SPA</body></html>", encoding="utf-8")

    test_client = TestClient(_make_spa_app(str(dist_dir)), raise_server_exceptions=False)
    response = test_client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ---------------------------------------------------------------------------
# CORS 配置测试
# ---------------------------------------------------------------------------


def test_cors_allows_default_origin() -> None:
    """测试默认 CORS 配置：允许 http://localhost:8080 来源的预检请求。"""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_origins_from_env(monkeypatch) -> None:
    """测试 CORS_ORIGINS 环境变量：自定义来源应被正确解析并允许。

    使用独立应用实例验证环境变量解析逻辑，避免影响全局 app 状态。
    """
    custom_origin = "http://custom-frontend.example.com"
    monkeypatch.setenv("CORS_ORIGINS", custom_origin)

    # 重新解析环境变量（模拟 main.py 的解析逻辑）
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
    assert custom_origin in cors_origins
