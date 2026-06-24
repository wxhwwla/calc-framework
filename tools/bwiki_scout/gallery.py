#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""从图鉴页 HTML 提取条目链接。"""

from html.parser import HTMLParser

from typing import Iterable

from urllib.parse import unquote, urlparse


# 图鉴页常见非条目前缀（小写比较用）

_SKIP_PREFIXES = (
    "category:",
    "file:",
    "media:",
    "特殊:",
    "template:",
    "模板:",
    "help:",
    "首页",
    "干员图鉴",
    "武器图鉴",
    "装备图鉴",
    "index.php",
    "设备图鉴",
)


class _GalleryLinkParser(HTMLParser):
    """_GalleryLinkParser 类。"""

    def __init__(self, site_prefix: str) -> None:
        super().__init__()

        self._site_prefix = site_prefix.rstrip("/")

        self.titles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """handle_starttag 实现。

        Args:
            tag: 参数描述。
            attrs: 参数描述。

        Returns:
            返回值描述。
        """
        if tag.lower() != "a":
            return

        href = ""

        for key, value in attrs:
            if key.lower() == "href" and value:
                href = value

                break

        if not href or href.startswith("#"):
            return

        title = _href_to_title(href, self._site_prefix)

        if title and _is_entry_title(title):
            self.titles.append(title)


def _href_to_title(href: str, site_prefix: str) -> str:
    """_href_to_title 实现。"""
    if href.startswith("/"):
        path = href

    else:
        parsed = urlparse(href)

        path = parsed.path or href

    prefix = f"{site_prefix}/"

    if not path.startswith(prefix):
        return ""

    tail = unquote(path[len(prefix) :])

    return tail.replace("_", " ").strip()


def _is_entry_title(title: str) -> bool:
    """_is_entry_title 实现。"""
    lower = title.lower()

    for skip in _SKIP_PREFIXES:
        if lower.startswith(skip.lower()) or title == skip:
            return False

    if ":" in title and not title.endswith("+"):
        return False

    return bool(title)


def extract_gallery_entry_titles(html: str, *, site_path: str = "/zmd") -> list[str]:
    """

    从图鉴 HTML 提取条目页面标题（去重、保持首次出现顺序）。



    参数：

        html: 图鉴页 parse 返回的 HTML

        site_path: Wiki 子站路径，默认终末地 /zmd

    """

    parser = _GalleryLinkParser(site_path)

    parser.feed(html or "")

    seen: set[str] = set()

    ordered: list[str] = []

    for title in parser.titles:
        if title in seen:
            continue

        seen.add(title)

        ordered.append(title)

    return ordered


def merge_title_lists(*lists: Iterable[str]) -> list[str]:
    """合并多来源标题列表，去重保序。"""

    seen: set[str] = set()

    merged: list[str] = []

    for items in lists:
        for title in items:
            if title in seen:
                continue

            seen.add(title)

            merged.append(title)

    return merged
