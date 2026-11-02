# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "web" / "backend"
for _p in [str(_REPO), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.internal.download_client import build_client_download, find_local_backend_zip


def test_find_local_backend_zip_optional():
    path = find_local_backend_zip()
    if path is not None:
        assert path.name == "local-backend.zip"


def test_build_client_download_returns_zip():
    body, filename, ctype = build_client_download()
    assert body[:2] == b"PK"
    assert filename.endswith(".zip")
    assert ctype == "application/zip"


def test_history_payload_roundtrip(monkeypatch):
    from web.backend.api import history as hist
    from web.backend.api.internal.persistent_store import _path

    store_path = _path("compute_history")
    before = store_path.stat().st_mtime_ns if store_path.is_file() else None

    saved: dict[str, list[dict]] = {}
    monkeypatch.setattr(hist, "_history", [])
    monkeypatch.setattr(hist, "save_list", lambda key, items: saved.setdefault(key, list(items)))

    hist.save_history_payload({"char_name": "测试", "weapon_name": "武器"})
    items = hist.list_history_payload()
    assert len(items) == 1
    assert items[0]["char_name"] == "测试"
    assert saved["compute_history"][0]["char_name"] == "测试"

    after = store_path.stat().st_mtime_ns if store_path.is_file() else None
    assert after == before, "测试不得改写受跟踪的 compute_history.json"
