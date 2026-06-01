# SPDX-License-Identifier: AGPL-3.0
"""计算历史 API（内存 Ring Buffer）。"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api/history")

MAX_HISTORY = 10
_history: list[dict] = []


def list_history_payload() -> list[dict]:
    return list(reversed(_history))


def save_history_payload(entry: dict) -> dict:
    entry = dict(entry)
    entry["saved_at"] = datetime.now(timezone.utc).isoformat()
    _history.append(entry)
    while len(_history) > MAX_HISTORY:
        _history.pop(0)
    return {"message": "ok", "index": len(_history) - 1}


@router.get("")
def list_history():
    return list_history_payload()


@router.post("")
def save_history(entry: dict):
    return save_history_payload(entry)
