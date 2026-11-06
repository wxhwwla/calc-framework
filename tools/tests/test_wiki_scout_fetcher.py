# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout 通用 Fetcher — 缓存、刷新、JSON 解析。"""

from __future__ import annotations

import sys
from email.message import Message
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.wiki_scout.fetcher import Fetcher


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200, charset: str = "utf-8") -> None:
        self._body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = f"text/plain; charset={charset}"

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        del exc
        return False


class _FakeOpener:
    def __init__(self, body: bytes = b'{"ok": true}') -> None:
        self.body = body
        self.calls: list[str] = []

    def open(self, request: object, timeout: float | None = None) -> _FakeResponse:
        del timeout
        self.calls.append(getattr(request, "full_url", ""))
        return _FakeResponse(self.body)


def test_fetcher_caches_text_and_refreshes(tmp_path: Path) -> None:
    opener = _FakeOpener()
    fetcher = Fetcher(tmp_path, user_agent="test-agent", rate_limit=0, opener=opener)

    assert fetcher.get_text("https://example.test/a") == '{"ok": true}'
    assert fetcher.get_text("https://example.test/a") == '{"ok": true}'
    assert len(opener.calls) == 1

    fetcher.get_text("https://example.test/a", refresh=True)
    assert len(opener.calls) == 2


def test_fetcher_get_json_parses_cached_body(tmp_path: Path) -> None:
    opener = _FakeOpener()
    fetcher = Fetcher(tmp_path, user_agent="test-agent", rate_limit=0, opener=opener)

    assert fetcher.get_json("https://example.test/b") == {"ok": True}
    assert fetcher.get_json("https://example.test/b") == {"ok": True}
    assert len(opener.calls) == 1


def test_fetcher_uses_separate_cache_keys_per_url(tmp_path: Path) -> None:
    opener = _FakeOpener()
    fetcher = Fetcher(tmp_path, user_agent="test-agent", rate_limit=0, opener=opener)

    fetcher.get_text("https://example.test/a")
    fetcher.get_text("https://example.test/b")

    assert len(opener.calls) == 2


def test_fetcher_default_opener_exposes_open(tmp_path: Path) -> None:
    fetcher = Fetcher(tmp_path, rate_limit=0)

    assert callable(getattr(fetcher.opener, "open", None))
