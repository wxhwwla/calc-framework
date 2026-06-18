# SPDX-License-Identifier: AGPL-3.0
"""Web 后端 pytest 共享 fixture。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_admin_runtime_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """将 Admin API Key / 用量数据隔离到临时目录，避免污染仓库内 .admin_data。"""
    import api.admin as admin

    data_dir = tmp_path / "admin_data"
    monkeypatch.setattr(admin, "_DATA_DIR", data_dir)
    monkeypatch.setattr(admin, "_KEYS_FILE", data_dir / "api_keys.json")
    monkeypatch.setattr(admin, "_USAGE_FILE", data_dir / "usage.json")

    # 设置测试用环境变量
    os.environ.setdefault("CALC_API_KEY_PEPPER", "test-pepper-16chars!" * 2)
    os.environ.setdefault("CALC_DISABLE_CSRF", "1")
