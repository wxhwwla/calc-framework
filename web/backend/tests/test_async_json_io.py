# SPDX-License-Identifier: AGPL-3.0
"""JSON 异步 I/O 工具测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import asyncio

from api._json_utils import aload_json, asave_json, load_json, save_json


def test_asave_and_aload_roundtrip(tmp_path: Path) -> None:
    async def _run() -> None:
        target = tmp_path / "sample.json"
        payload = {"items": [{"名称": "测试"}]}
        await asave_json(target, payload)
        loaded = await aload_json(target)
        assert loaded == payload

    asyncio.run(_run())


def test_sync_save_and_load_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "sync.json"
    save_json(target, [1, 2, 3])
    assert load_json(target) == [1, 2, 3]
