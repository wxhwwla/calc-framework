# SPDX-License-Identifier: AGPL-3.0
from pathlib import Path

from web.backend.api.download_client import build_client_download, find_local_backend_zip


def test_find_local_backend_zip_optional():
    path = find_local_backend_zip()
    if path is not None:
        assert path.name == "local-backend.zip"


def test_build_client_download_returns_zip():
    body, filename, ctype = build_client_download()
    assert body[:2] == b"PK"
    assert filename.endswith(".zip")
    assert ctype == "application/zip"


def test_history_payload_roundtrip():
    from web.backend.api import history as hist

    hist._history.clear()
    hist.save_history_payload({"char_name": "测试", "weapon_name": "武器"})
    items = hist.list_history_payload()
    assert len(items) == 1
    assert items[0]["char_name"] == "测试"
    hist._history.clear()
