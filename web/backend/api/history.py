# SPDX-License-Identifier: AGPL-3.0
"""计算历史 API（文件持久化，PA 重启不丢）。"""

import json
import threading
from datetime import datetime, timezone

from api.internal.persistent_store import load_list, save_list
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/history")

MAX_HISTORY = 10
_MAX_ENTRY_BYTES = 1024 * 100  # 100KB 单条上限
_STORE_KEY = "compute_history"
_history: list[dict] = load_list(_STORE_KEY)
_history_lock = threading.Lock()


def list_history_payload() -> list[dict]:
    """获取历史记录列表（倒序，最新在前）。"""
    return list(reversed(_history))


def _validate_history_entry(entry: object) -> dict:
    """校验历史记录条目的基本合法性。"""
    if not isinstance(entry, dict):
        raise HTTPException(status_code=400, detail="历史记录必须是一个 JSON 对象")
    raw = json.dumps(entry, ensure_ascii=False)
    if len(raw.encode("utf-8")) > _MAX_ENTRY_BYTES:
        raise HTTPException(status_code=413, detail=f"单条历史记录不能超过 {_MAX_ENTRY_BYTES // 1024}KB")
    return dict(entry)


def save_history_payload(entry: dict) -> dict:
    """保存一条计算历史记录（超出上限时丢弃最旧记录）。"""
    global _history
    entry["saved_at"] = datetime.now(timezone.utc).isoformat()
    with _history_lock:
        _history.append(entry)
        while len(_history) > MAX_HISTORY:
            _history.pop(0)
        save_list(_STORE_KEY, _history)
    return {"message": "ok", "index": len(_history) - 1}


@router.get("")
def list_history():
    """获取计算历史列表（最近 10 条，倒序）。"""
    return list_history_payload()


@router.post("")
def save_history(entry: object):
    """保存一条计算历史记录。"""
    validated = _validate_history_entry(entry)
    return save_history_payload(validated)


__all__: list[str] = []
