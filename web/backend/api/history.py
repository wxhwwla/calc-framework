"""计算历史 API（内存 Ring Buffer）。"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api/history")

MAX_HISTORY = 10
_history: list[dict] = []


@router.get("")
async def list_history():
    return list(reversed(_history))


@router.post("")
async def save_history(entry: dict):
    entry["saved_at"] = datetime.now(timezone.utc).isoformat()
    _history.append(entry)
    while len(_history) > MAX_HISTORY:
        _history.pop(0)
    return {"message": "ok", "index": len(_history) - 1}
