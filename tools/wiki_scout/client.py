# SPDX-License-Identifier: AGPL-3.0
"""通用 MediaWiki 客户端 — 支持任何 MediaWiki API。"""

from __future__ import annotations

import time
import logging
from typing import Any

try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class MediaWikiClient:
    """通用 MediaWiki API 客户端。

    用法:
        client = MediaWikiClient("https://wiki.example.com/api.php")
        pages = client.query_category("角色", limit=50)
    """

    def __init__(
        self,
        api_url: str,
        user_agent: str | None = None,
        rate_limit: float = 0.5,
        timeout: int = 30,
    ) -> None:
        if requests is None:
            raise ImportError("需要安装 requests 库: pip install requests")
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent or "WikiScout/1.0 (calc-framework)",
                "Accept": "application/json",
            }
        )
        self.rate_limit = rate_limit  # 请求间隔（秒）
        self.timeout = timeout
        self._last_request = 0.0

    def _wait(self) -> None:
        """遵守 rate limit。"""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def call(self, params: dict[str, str]) -> dict[str, Any]:
        """调用 MediaWiki API。"""
        self._wait()
        params["format"] = "json"
        resp = self.session.get(
            self.api_url,
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def query_category(self, category: str, limit: int = 50) -> list[dict[str, Any]]:
        """获取分类下的所有页面。"""
        pages = []
        cmcontinue: str | None = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": str(min(limit, 500)),
                "cmtype": "page",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            data = self.call(params)
            members = data.get("query", {}).get("categorymembers", [])
            pages.extend(members)

            if "continue" in data and "cmcontinue" in data.get("continue", {}):
                cmcontinue = data["continue"]["cmcontinue"]
            else:
                break
        return pages

    def get_page_text(self, title: str) -> str | None:
        """获取页面的 wikitext 内容。"""
        params = {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "formatversion": "2",
        }
        data = self.call(params)
        parse = data.get("parse")
        if parse and "wikitext" in parse:
            return parse["wikitext"]
        return None

    def get_page_html(self, title: str) -> str | None:
        """获取页面的 HTML 内容。"""
        params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "formatversion": "2",
        }
        data = self.call(params)
        parse = data.get("parse")
        if parse and "text" in parse:
            return parse["text"]["content"] if isinstance(parse["text"], dict) else parse["text"]
        return None

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """搜索页面。"""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
        }
        data = self.call(params)
        return data.get("query", {}).get("search", [])

    def get_page_info(self, title: str) -> dict[str, Any] | None:
        """获取页面基本信息（ID、标题、分类等）。"""
        params = {
            "action": "query",
            "titles": title,
            "prop": "info|categories",
            "formatversion": "2",
        }
        data = self.call(params)
        pages = data.get("query", {}).get("pages", [])
        return pages[0] if pages else None


def detect_wiki_type(url: str) -> str:
    """根据 URL 检测 Wiki 平台类型。

    Returns:
        "bwiki" | "fandom" | "huiji" | "mediawiki" | "unknown"
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    hostname_lower = hostname.lower()

    # 精确域名匹配，防止子串绕过
    if hostname_lower == "bilibili.com" or hostname_lower.endswith(".bilibili.com"):
        return "bwiki"
    if hostname_lower == "biligame.com" or hostname_lower.endswith(".biligame.com"):
        return "bwiki"
    if hostname_lower == "fandom.com" or hostname_lower.endswith(".fandom.com"):
        return "fandom"
    if hostname_lower == "huijiwiki.com" or hostname_lower.endswith(".huijiwiki.com"):
        return "bwiki"
    if hostname_lower == "wiki.biligame.com" or hostname_lower.endswith(".wiki.biligame.com"):
        return "bwiki"
    return "mediawiki"


def get_api_url(wiki_url: str) -> str:
    """从 Wiki 页面 URL 推导 API 端点。

    "https://wiki.biligame.com/arknights/" → "https://wiki.biligame.com/arknights/api.php"
    "https://arknights.fandom.com/wiki/" → "https://arknights.fandom.com/api.php"
    """
    api_url = wiki_url.rstrip("/")
    if not api_url.endswith("/api.php"):
        # 尝试常见位置
        from urllib.parse import urlparse

        parsed = urlparse(api_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or ""
        # 如果路径以 /wiki/xxx 或 /zh/xxx 开头，取域名根 + /api.php
        for prefix in ["/wiki/", "/zh/", "/index.php"]:
            if path.startswith(prefix):
                api_url = f"{base}/api.php"
                break
        else:
            api_url = f"{api_url}/api.php"
    return api_url
