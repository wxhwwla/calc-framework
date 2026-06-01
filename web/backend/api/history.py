# SPDX-License-Identifier: AGPL-3.0
"""计算历史 API（文件持久化，PA 重启不丢）。"""

from datetime import datetime, timezone

from fastapi import APIRouter

from api.persistent_store import load_list, save_list

router = APIRouter(prefix="/api/history")

MAX_HISTORY = 10
_STORE_KEY = "compute_history"
_history: list[dict] = load_list(_STORE_KEY)


def list_history_payload() -> list[dict]:
    return list(reversed(_history))


def save_history_payload(entry: dict) -> dict:
    global _history
    entry = dict(entry)
    entry["saved_at"] = datetime.now(timezone.utc).isoformat()
    _history.append(entry)
    while len(_history) > MAX_HISTORY:
        _history.pop(0)
    save_list(_STORE_KEY, _history)
    return {"message": "ok", "index": len(_history) - 1}


@router.get("")
def list_history():
    return list_history_payload()


@router.post("")
def save_history(entry: dict):
    return save_history_payload(entry)
