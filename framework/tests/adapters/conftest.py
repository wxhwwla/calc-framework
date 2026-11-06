# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""适配器测试共用 fixture。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_ADAPTER_DIR = Path(__file__).resolve().parents[2] / "adapters" / "wjdlglr"


@pytest.fixture()
def adapter_pkg():
    """按目录加载适配包（每个测试独立实例）。"""
    from calc_framework.config.adapter import AdapterPackage

    return AdapterPackage(str(_ADAPTER_DIR))


@pytest.fixture(scope="module")
def weapon_records() -> list[dict[str, object]]:
    """读取适配器内置的 weapons.json 记录。"""
    path = _ADAPTER_DIR / "data" / "weapons.json"
    return json.loads(path.read_text(encoding="utf-8"))
