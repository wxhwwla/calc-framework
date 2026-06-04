#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""MediaWiki API 客户端（只读）。"""

from __future__ import annotations


import json

import time

import urllib.error

import urllib.parse

import urllib.request

from typing import Any, Callable


class MediaWikiClient:
    """终末地 BWIKI MediaWiki API 封装。"""

    def __init__(
        self,
        api_url: str,
        *,
        user_agent: str,
        request_interval_sec: float = 0.5,
        opener: Callable[..., Any] | None = None,
        referer: str | None = None,
        max_retries: int = 3,
        retry_backoff_sec: float = 5.0,
    ) -> None:
        self.api_url = api_url

        self.user_agent = user_agent

        self.request_interval_sec = request_interval_sec

        self._opener = opener or urllib.request.urlopen

        self._last_request_at = 0.0

        self._referer = referer or (api_url.rsplit("/api.php", 1)[0] + "/")

        self._max_retries = max(0, max_retries)

        self._retry_backoff_sec = retry_backoff_sec

    def query(
        self,
        *,
        ignore_error_codes: frozenset[str] | None = None,
        **params: Any,
    ) -> dict[str, Any]:
        """query 实现。"""
        payload = {"format": "json", **params}

        return self._get(payload, ignore_error_codes=ignore_error_codes)

    def fetch_parsed_gallery_html(self, page_title: str) -> str:
        """fetch_parsed_gallery_html 实现。

        Args:
            page_title: 参数描述。

        Returns:
            返回值描述。
        """
        data = self.query(
            action="parse",
            page=page_title,
            prop="text",
            disabletoc="true",
            ignore_error_codes=frozenset({"missingtitle"}),
        )

        if "error" in data:
            return ""

        return data.get("parse", {}).get("text", {}).get("*", "") or ""

    def fetch_category_members(self, category_title: str, *, limit: int = 500) -> list[str]:
        """获取分类下的所有页面标题列表。

        Args:
            category_title: 分类标题（如 "Category:干员"）
            limit: 最大返回条数

        Returns:
            页面标题列表
        """

        members: list[str] = []

        continue_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category_title,
                "cmlimit": min(limit, 500),
                "cmtype": "page",
            }

            if continue_token:
                params["cmcontinue"] = continue_token

            data = self.query(**params)

            batch = data.get("query", {}).get("categorymembers", [])

            for item in batch:
                title = item.get("title")

                if title:
                    members.append(title)

            cont = data.get("continue", {})

            continue_token = cont.get("cmcontinue")

            if not continue_token or len(members) >= limit:
                break

        return members[:limit]

    def fetch_pages_content(self, titles: list[str]) -> dict[str, dict[str, Any]]:
        """拉取页面 wikitext（批量）与 HTML（逐页 parse）。"""

        if not titles:
            return {}

        result: dict[str, dict[str, Any]] = {}

        for i in range(0, len(titles), 50):
            chunk = titles[i : i + 50]

            joined = "|".join(chunk)

            data = self.query(
                action="query",
                prop="revisions",
                rvprop="content",
                rvslots="main",
                titles=joined,
                redirects="1",
            )

            pages = data.get("query", {}).get("pages", {})

            for page in pages.values():
                if page.get("missing"):
                    continue

                title = page.get("title", "")

                revs = page.get("revisions", [])

                wikitext = ""

                if revs:
                    slots = revs[0].get("slots", {})

                    main = slots.get("main", {})

                    wikitext = main.get("*", "") or ""

                result[title] = {
                    "pageid": page.get("pageid"),
                    "title": title,
                    "ns": page.get("ns"),
                    "wikitext": wikitext,
                    "html": "",
                }

        for title in titles:
            if title not in result:
                result[title] = {"title": title, "wikitext": "", "html": ""}

            if not result[title].get("wikitext") and not result[title].get("pageid"):
                continue

            result[title]["html"] = self.fetch_parsed_gallery_html(title)

        return result

    def search_json_file_candidates(self, *, limit: int = 20) -> list[str]:
        """轻量扫描标题含 .json 的页面。"""

        data = self.query(
            action="query",
            list="search",
            srsearch="filetype:json OR intitle:.json",
            srnamespace="0|6",
            srlimit=str(limit),
        )

        hits = data.get("query", {}).get("search", [])

        return [hit.get("title", "") for hit in hits if hit.get("title")]

    def _request_headers(self) -> dict[str, str]:
        # BWIKI WAF 会拦截仅带 User-Agent 的请求（HTTP 567）

        """_request_headers 实现。"""
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self._referer,
        }

    def _get(
        self,
        params: dict[str, Any],
        *,
        ignore_error_codes: frozenset[str] | None = None,
    ) -> dict[str, Any]:
        """_get 实现。"""
        self._throttle()

        query = urllib.parse.urlencode(params)

        url = f"{self.api_url}?{query}"

        request = urllib.request.Request(url, headers=self._request_headers())

        last_http_error: urllib.error.HTTPError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                with self._opener(request, timeout=60) as response:
                    raw = response.read().decode("utf-8", errors="replace")

                break

            except urllib.error.HTTPError as exc:
                last_http_error = exc

                if exc.code == 567 and attempt < self._max_retries:
                    time.sleep(self._retry_backoff_sec * (2**attempt))

                    continue

                body = exc.read().decode("utf-8", errors="replace")

                raise RuntimeError(f"MediaWiki API HTTP {exc.code}: {body[:500]}") from exc

            except (TimeoutError, ConnectionResetError, OSError, urllib.error.URLError) as exc:
                if attempt < self._max_retries:
                    time.sleep(self._retry_backoff_sec * (2**attempt))

                    continue

                raise RuntimeError(f"MediaWiki API 网络错误: {exc}") from exc

        else:
            assert last_http_error is not None

            body = last_http_error.read().decode("utf-8", errors="replace")

            raise RuntimeError(f"MediaWiki API HTTP {last_http_error.code}: {body[:500]}") from last_http_error

        data = json.loads(raw)

        if "error" in data:
            code = data["error"].get("code", "")

            if ignore_error_codes and code in ignore_error_codes:
                return data

            raise RuntimeError(f"MediaWiki API error: {data['error']}")

        return data

    def _throttle(self) -> None:
        """_throttle 实现。"""
        now = time.monotonic()

        elapsed = now - self._last_request_at

        if elapsed < self.request_interval_sec:
            time.sleep(self.request_interval_sec - elapsed)

        self._last_request_at = time.monotonic()
