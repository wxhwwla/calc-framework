# SPDX-License-Identifier: AGPL-3.0
"""Web 后端入口 — FastAPI 应用实例 + 路由注册 + 全局中间件/异常处理器 / 静态文件挂载。"""

try:
    from . import _path_setup  # noqa: F401  # sets sys.path for dev mode
except ImportError:
    import _path_setup  # noqa: F401  # fallback when run as top-level module
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from web.backend.bridge import setup_logging, get_logger

from api.adapters import router as adapters_router
from api.arknights import router as arknights_router
from api.compute import router as compute_router
from api.contribute import router as contribute_router
from api.data import router as data_router
from api.generator import router as generator_router
from api.history import router as history_router
from api.hub import router as hub_router
from api.layout import router as layout_router
from api.manual_buff import router as manual_buff_router
from api.ocr import router as ocr_router
from api.pack import router as pack_router
from api.search import router as search_router
from api.survival import router as survival_router



setup_logging(level="INFO", console=True)

logger = get_logger(__name__)



app = FastAPI(title="Calc Framework Web API", version="1.0.0",

              docs_url="/api/docs", redoc_url="/api/redoc")



app.add_middleware(

    CORSMiddleware,

    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



app.include_router(compute_router)

app.include_router(adapters_router)

app.include_router(data_router)

app.include_router(hub_router)

app.include_router(layout_router)

app.include_router(pack_router)

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

@app.get("/api/health")

async def health():

    from web.backend.bridge import AdapterManager


    ADAPTER_ROOT = Path(__file__).resolve().parents[2] / "framework" / "adapters"

    mgr = AdapterManager(ADAPTER_ROOT)

    return {

        "status": "ok",

        "framework_version": "1.0.0",

        "adapters_count": len(mgr.available_adapters),

        "adapters": list(mgr.available_adapters.keys()),

    }


# ── 客户端下载 ────────────────────────────────────────────────────────────────

@app.get("/api/download/client")
def download_client():
    """下载本地搜索服务器（PyInstaller 打包，双击即可运行）。"""
    from api.download_client import build_client_download

    content, filename, media_type = build_client_download()
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


# 生产环境：serve 前端构建产物（render.yaml build 阶段生成）
_FRONTEND_DIST = _REPO_ROOT / "web" / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
    logger.info("前端静态文件已挂载: %s", _FRONTEND_DIST)



@app.exception_handler(Exception)

async def global_exception_handler(request: Request, exc: Exception):

    logger.error("未捕获的异常: %s", exc, exc_info=True)

    return JSONResponse(

        status_code=500,

        content={"detail": f"服务器内部错误: {exc}"},

    )

