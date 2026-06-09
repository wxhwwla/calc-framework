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
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        referer: str | None = None,
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
        if referer:
            self.session.headers["Referer"] = referer
        self.rate_limit = rate_limit  # 请求间隔（秒）
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._last_request = 0.0

    def _wait(self) -> None:
        """遵守 rate limit。"""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def call(self, params: dict[str, str]) -> dict[str, Any]:
        """调用 MediaWiki API（含自动重试）。"""
        self._wait()
        params["format"] = "json"
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(
                    self.api_url,
                    params=params,
                    timeout=self.timeout,
                )
                if resp.status_code in (429, 503, 502):
                    logger.warning(
                        "HTTP %d on attempt %d/%d, retrying…", resp.status_code, attempt + 1, self.max_retries
                    )
                    time.sleep(self.retry_backoff * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
                logger.warning("请求失败 (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_backoff * (attempt + 1))
        raise last_error or RuntimeError(f"API 调用失败: {params.get('action', 'unknown')}")

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


def _matches_domain(hostname: str, domain: str) -> bool:
    """安全匹配域名或子域名，防止子串绕过。"""
    lower_host = hostname.lower()
    lower_domain = domain.lower()
    return lower_host == lower_domain or lower_host.endswith(f".{lower_domain}")


def detect_wiki_type(url: str) -> str:
    """根据 URL 检测 Wiki 平台类型。

    Returns:
        "bwiki" | "fandom" | "huiji" | "mediawiki" | "unknown"
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # 精确域名匹配，防止子串绕过
    if _matches_domain(hostname, "bilibili.com") or _matches_domain(hostname, "biligame.com"):
        return "bwiki"
    if _matches_domain(hostname, "fandom.com"):
        return "fandom"
    if _matches_domain(hostname, "huijiwiki.com") or _matches_domain(hostname, "wiki.biligame.com"):
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
