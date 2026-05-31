# SPDX-License-Identifier: AGPL-3.0
import _path_setup  # noqa: F401 -- sets sys.path, no exported symbols
from pathlib import Path

from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse, Response, StreamingResponse

from fastapi.staticfiles import StaticFiles

from calc_framework.logging import setup_logging, get_logger



from api.compute import router as compute_router

from api.adapters import router as adapters_router

from api.data import router as data_router

from api.hub import router as hub_router

from api.layout import router as layout_router

from api.pack import router as pack_router

from api.search import router as search_router
from api.history import router as history_router
from api.ocr import router as ocr_router



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
app.include_router(history_router)
app.include_router(ocr_router)

# 生产环境：serve 前端构建产物（render.yaml build 阶段生成）
_REPO_ROOT = Path(__file__).resolve().parents[2]
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





@app.get("/api/health")

async def health():

    from calc_framework.config.manager import AdapterManager


    ADAPTER_ROOT = Path(__file__).resolve().parents[2] / "framework" / "adapters"

    mgr = AdapterManager(ADAPTER_ROOT)

    return {

        "status": "ok",

        "framework_version": "1.0.0",

        "adapters_count": len(mgr.available_adapters),

        "adapters": list(mgr.available_adapters.keys()),

    }


# ── 客户端下载 ────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]


@app.get("/api/download/client")
def download_client():
    """下载本地搜索服务器（PyInstaller 打包，双击即可运行）。"""
    # 尝试寻找预打包的 zip（dist/ 或 web/static/）
    for _dir in [_REPO_ROOT / "dist" / "终末地本地搜索服务器",
                 _REPO_ROOT / "static"]:
        _zip = _dir / "local-backend.zip"
        if _zip.exists():
            content = _zip.read_bytes()
            return Response(
                content=content,
                media_type="application/zip",
                headers={
                    "Content-Disposition":
                        'attachment; filename="local-backend.zip"',
                    "Content-Length": str(len(content)),
                },
            )

    # fallback: 动态生成包含下载说明的 zip
    import io as _io
    import zipfile as _zipfile
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt",
            "END FIELD DAMAGE CALCULATOR - Local Backend Server\n"
            "===============================================\n\n"
            "The pre-packaged local backend is not yet available.\n\n"
            "For developers, run in the project root:\n"
            "  python web/build_local_backend.py\n\n"
            "Then upload the zip to the server.\n"
        )
    buf.seek(0)
    content = buf.getvalue()
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition":
                'attachment; filename="local-backend-readme.zip"',
            "Content-Length": str(len(content)),
        },
    )

