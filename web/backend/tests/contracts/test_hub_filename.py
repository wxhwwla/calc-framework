# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Hub 上传文件名与下载元数据契约。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
for _path in (str(_REPO / "framework" / "src"), str(_REPO), str(_REPO / "web" / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from web.backend.hub import storage


def test_uploaded_filename_is_kept_in_pack_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "_HUB_DIR", tmp_path)
    monkeypatch.setattr(storage, "_PACKS_DIR", tmp_path / "packs")
    monkeypatch.setattr(storage, "_DB_PATH", tmp_path / "catalog.db")
    pack = storage.create_pack("测试包", "1.0.0", "", "")

    storage.save_pack_file(pack.id, b"content", "demo.calcpack")

    assert storage.get_pack(pack.id)["filename"] == "demo.calcpack"
    assert storage.get_pack_file_path(pack.id, "demo.calcpack").read_bytes() == b"content"
