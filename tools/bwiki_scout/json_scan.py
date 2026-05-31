#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""检测页面内容中是否引用 JSON 资源。"""



import re

from typing import Any



_JSON_LINK_RE = re.compile(r"\.json\b", re.IGNORECASE)

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]{0,2000}?\}", re.MULTILINE)





def find_json_hints(text: str) -> dict[str, list[str]]:

    """

    在 wikitext/HTML 中查找 JSON 相关线索。



    返回：

        link_hits: 含 .json 的片段

        brace_snippets: 疑似 JSON 对象的前 120 字符（最多 5 条）

    """

    link_hits: list[str] = []

    for line in (text or "").splitlines():

        if _JSON_LINK_RE.search(line):

            link_hits.append(line.strip()[:200])



    brace_snippets: list[str] = []

    for match in _JSON_BLOCK_RE.finditer(text or ""):

        snippet = match.group(0).strip()

        if '"' in snippet or "'" in snippet:

            brace_snippets.append(snippet[:120])

        if len(brace_snippets) >= 5:

            break



    return {"link_hits": link_hits, "brace_snippets": brace_snippets}





def scan_pages_for_json(pages: dict[str, dict]) -> dict[str, Any]:

    """汇总多页面的 JSON 线索。"""

    per_page: dict[str, Any] = {}

    any_hint = False

    for title, bundle in pages.items():

        combined = (bundle.get("wikitext") or "") + "\n" + (bundle.get("html") or "")

        hints = find_json_hints(combined)

        if hints["link_hits"] or hints["brace_snippets"]:

            any_hint = True

            per_page[title] = hints

    return {"any_hint": any_hint, "pages": per_page}

