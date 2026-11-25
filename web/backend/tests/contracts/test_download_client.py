# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""本地下载真实制品契约。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[4]
for _path in (str(_REPO), str(_REPO / "web" / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from api.internal import download_client


def test_public_dist_backend_zip_is_served(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(download_client, "REPO_ROOT", tmp_path)
    target = tmp_path / "web" / "frontend" / "dist" / "local-backend.zip"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"real-backend")

    assert download_client.build_client_download() == (b"real-backend", "local-backend.zip", "application/zip")


def test_missing_backend_never_returns_readme_placeholder(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(download_client, "REPO_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError):
        download_client.build_client_download()
