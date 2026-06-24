# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 后端入口 — FastAPI 应用实例 + 路由注册 + 全局中间件/异常处理器 / 静态文件挂载。"""

try:
    from . import _path_setup  # sets sys.path for dev mode  # type: ignore[unused-import]
except ImportError:
    import _path_setup  # noqa: F401  # fallback when run as top-level module  # type: ignore[unused-import]
import os
import sys
from pathlib import Path

from api.adapter_lib.layout import router as layout_router
from api.adapters import router as adapters_router
from api.admin import router as admin_router
from api.ai import router as ai_router
from api.arknights import router as arknights_router
from api.compute import router as compute_router
from api.data import router as data_router
from api.endfield.manual_buff import router as manual_buff_router
from api.endfield.survival import router as survival_router
from api.generator import router as generator_router
from api.history import router as history_router
from api.hub import router as hub_router
from api.internal.csrf import CSRFSkipMiddleware
from api.ocr import router as ocr_router
from api.packaging.contribute import router as contribute_router
from api.packaging.pack import router as pack_router
from api.plugins import router as plugins_router
from api.search import router as search_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from web.backend.bridge import get_logger, setup_logging

setup_logging(level="INFO", console=True)

logger = get_logger(__name__)


app = FastAPI(title="Calc Framework Web API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CSRFSkipMiddleware)


# 速率限制中间件（在所有路由之前）
from api.admin import RateLimitMiddleware


def _configure_rate_limit_middleware() -> None:
    """按环境变量配置限速；多 worker 场景见 docs/Web后端限速与多Worker.md。"""
    disable = os.environ.get("CALC_DISABLE_RATE_LIMIT", "").strip().lower()
    if disable in {"1", "true", "yes", "on"}:
        RateLimitMiddleware.enabled = False
        logger.warning(
            "RateLimitMiddleware 已禁用（CALC_DISABLE_RATE_LIMIT）；"
            "请在反向代理层限速，见 docs/Web后端限速与多Worker.md"
        )
        return

    for key in ("WEB_CONCURRENCY", "UVICORN_WORKERS", "CALC_WEB_WORKERS"):
        raw = os.environ.get(key, "").strip()
        if raw.isdigit() and int(raw) > 1:
            logger.warning(
                "检测到 %s=%s：内存限速与 usage 按进程独立，"
                "有效限额约为 tier×worker；建议单 worker 或 "
                "CALC_DISABLE_RATE_LIMIT=1 + 反向代理限速。"
                "详见 docs/Web后端限速与多Worker.md",
                key,
                raw,
            )
            break


_configure_rate_limit_middleware()

app.add_middleware(RateLimitMiddleware)

from api.internal.request_limits import ContentSizeLimitMiddleware, parse_max_body_bytes_env

if os.environ.get("CALC_DISABLE_BODY_LIMIT", "").strip().lower() not in {"1", "true", "yes", "on"}:
    _default_body_limit = parse_max_body_bytes_env(os.environ.get("CALC_MAX_BODY_BYTES"))
    app.add_middleware(ContentSizeLimitMiddleware, default_max_bytes=_default_body_limit)
    logger.info(
        "ContentSizeLimitMiddleware 已启用（默认 %s 字节；OCR/Hub 见 PATH_MAX_BODY_BYTES）",
        _default_body_limit if _default_body_limit is not None else "无全局上限",
    )

app.include_router(admin_router)

app.include_router(ai_router)

app.include_router(compute_router)

app.include_router(adapters_router)

app.include_router(data_router)

app.include_router(hub_router)

app.include_router(layout_router)

app.include_router(pack_router)

app.include_router(plugins_router)

app.include_router(search_router)
app.include_router(survival_router)
app.include_router(manual_buff_router)
app.include_router(history_router)
app.include_router(ocr_router)
app.include_router(arknights_router)
app.include_router(contribute_router)
app.include_router(generator_router)


def _resolve_repo_root() -> Path:
    """开发=仓库根；PyInstaller 本地后端=``_MEIPASS``。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return Path(__file__).resolve().parents[2]


_REPO_ROOT = _resolve_repo_root()


# 开发模式：若无前端构建产物，根路径重定向到 /compute
_FRONTEND_DIST = _REPO_ROOT / "web" / "frontend" / "dist"
if not _FRONTEND_DIST.is_dir():

    @app.get("/")
    async def root():
        return RedirectResponse(url="/compute")


# 捐赠二维码（与 GUI resources/donation/ 同源）
_DONATION_DIR = _REPO_ROOT / "resources" / "donation"


@app.get("/api/donation/manifest")
async def donation_manifest():
    """返回当前可用的捐赠二维码图片列表。"""
    from utils.donation_assets import resolve_donation_images

    return resolve_donation_images()


if _DONATION_DIR.is_dir():
    app.mount(
        "/api/donation",
        StaticFiles(directory=str(_DONATION_DIR)),
        name="donation",
    )
    logger.info("捐赠静态资源已挂载: %s", _DONATION_DIR)
else:
    logger.warning("捐赠目录不存在，跳过挂载: %s", _DONATION_DIR)


_ADAPTER_ROOT = Path(__file__).resolve().parents[2] / "framework" / "adapters"
from web.backend.bridge import AdapterManager

_health_mgr = AdapterManager(_ADAPTER_ROOT)


@app.get("/api/health")
async def health():
    """健康检查端点（生产环境不泄露适配器详情）。"""
    import os as _os

    if _os.environ.get("CALC_DEBUG", "").strip().lower() in ("1", "true", "yes", "on"):
        return {
            "status": "ok",
            "adapters_count": len(_health_mgr.available_adapters),
            "adapters": list(_health_mgr.available_adapters.keys()),
        }
    return {"status": "ok"}


# ── 客户端下载 ────────────────────────────────────────────────────────────────


@app.get("/api/download/client")
def download_client():
    """下载本地搜索服务器（PyInstaller 打包，双击即可运行）。"""
    from api.internal.download_client import build_client_download

    content, filename, media_type = build_client_download()
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


# 生产环境：serve 前端构建产物
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
    logger.info("前端静态文件已挂载: %s", _FRONTEND_DIST)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("未捕获的异常: %s", exc, exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )
