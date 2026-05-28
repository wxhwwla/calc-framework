import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "framework" / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.compute import router as compute_router
from api.adapters import router as adapters_router

app = FastAPI(title="Calc Framework Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compute_router)
app.include_router(adapters_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "framework_version": "1.0.0"}
