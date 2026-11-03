# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Admin 用量文件持久化健壮性测试（损坏文件 / 并发写入）。"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import api.admin as admin


def test_load_json_returns_empty_for_corrupt_file(tmp_path: Path) -> None:
    """损坏的统计文件不应抛异常，否则限流中间件会对所有请求返回 500。"""
    target = tmp_path / "usage.json"
    target.write_text('{"request_timestamps": [], "by_endpoint": {}}}\n}', encoding="utf-8")

    assert admin._load_json(target) == {}


def test_record_usage_concurrent_updates_are_not_lost(tmp_path: Path, monkeypatch) -> None:
    """并发记录用量时读-改-写必须串行，否则计数丢失且文件可能被写坏。"""
    target = tmp_path / "usage.json"
    monkeypatch.setattr(admin, "_USAGE_FILE", target)

    async def _run() -> None:
        await asyncio.gather(*(admin.RateLimitMiddleware._record_usage_async("/api/x") for _ in range(20)))

    asyncio.run(_run())

    usage = json.loads(target.read_text(encoding="utf-8"))
    assert usage["by_endpoint"]["/api/x"] == 20
