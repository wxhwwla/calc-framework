# SPDX-License-Identifier: AGPL-3.0
import _path_setup  # noqa: F401 -- sets sys.path, no exported symbols
from pathlib import Path

from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from fastapi.staticfiles import StaticFiles

from calc_framework.logging import setup_logging, get_logger



from api.compute import router as compute_router

from api.adapters import router as adapters_router

from api.data import router as data_router

from api.hub import router as hub_router

from api.layout import router as layout_router

from api.pack import router as pack_router

from api.search import router as search_router



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

