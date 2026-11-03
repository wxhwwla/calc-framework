# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""带离线缓存的 HTTP 抓取器 — Wiki Scout 所有 provider 共用。

设计目标：
- 仅依赖标准库（`urllib`），CI 无需额外安装 requests。
- 同一 URL 第二次抓取直接读缓存，支持 `refresh=True` 强制刷新。
- 遵守限速、失败重试，并在错误信息中保留 URL 与状态码。
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "endfield-damage-calculator-wiki-scout/0.1 (data collection; contact: repo maintainer)"

_RETRY_STATUS = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """抓取失败（网络错误、非重试状态码或重试耗尽）。"""


class Fetcher:
    """缓存型 HTTP 抓取器。

    用法:
        fetcher = Fetcher(Path("output/.cache"), user_agent="my-bot/1.0")
        data = fetcher.get_json("https://api.example.com/list")
    """

    def __init__(
        self,
        cache_dir: Path,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        rate_limit: float = 1.0,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 2.0,
        referer: str | None = None,
        opener: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.referer = referer
        self.opener = opener or build_opener()
        self.sleep = sleep
        self._last_request = 0.0

    def get_text(
        self,
        url: str,
        *,
        refresh: bool = False,
        referer: str | None = None,
        accept: str = "application/json, text/plain, */*",
    ) -> str:
        """抓取 URL 文本，命中缓存时直接返回。"""
        cache_file = self._cache_file(url)
        if not refresh and cache_file.exists():
            cached = self._read_cache(cache_file)
            if cached is not None and cached.get("url") == url:
                return cached["text"]

        text = self._request(url, referer=referer, accept=accept)
        self._write_cache(cache_file, url, text)
        return text

    def get_json(
        self,
        url: str,
        *,
        refresh: bool = False,
        referer: str | None = None,
    ) -> Any:
        """抓取并解析 JSON。"""
        return json.loads(self.get_text(url, refresh=refresh, referer=referer))

    def _cache_file(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path) -> dict[str, Any] | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_cache(self, path: Path, url: str, text: str) -> None:
        payload = {
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "text": text,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            self.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def _headers(self, referer: str | None, accept: str) -> dict[str, str]:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": accept,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        effective_referer = referer or self.referer
        if effective_referer:
            headers["Referer"] = effective_referer
        return headers

    def _request(self, url: str, *, referer: str | None, accept: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self._wait()
            request = Request(url, headers=self._headers(referer, accept))
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    body = response.read()
                    charset = self._charset(response)
                if status >= 400:
                    raise FetchError(f"HTTP {status} for {url}")
                return body.decode(charset, errors="replace")
            except HTTPError as exc:
                if exc.code in _RETRY_STATUS and attempt < self.max_retries - 1:
                    logger.warning(
                        "HTTP %s for %s (attempt %d/%d), retrying",
                        exc.code,
                        url,
                        attempt + 1,
                        self.max_retries,
                    )
                    self.sleep(self.backoff * (attempt + 1))
                    continue
                raise FetchError(f"HTTP {exc.code} for {url}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "请求失败 %s (attempt %d/%d): %s",
                        url,
                        attempt + 1,
                        self.max_retries,
                        exc,
                    )
                    self.sleep(self.backoff * (attempt + 1))
                    continue
        raise FetchError(f"抓取失败: {url}") from last_error

    @staticmethod
    def _charset(response: Any) -> str:
        headers = getattr(response, "headers", None)
        if headers is not None and hasattr(headers, "get_content_charset"):
            return headers.get_content_charset() or "utf-8"
        return "utf-8"
