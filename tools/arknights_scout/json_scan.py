# SPDX-License-Identifier: AGPL-3.0
"""扫描已缓存的 wikitext 中是否含 JSON。"""

import json
import re
from typing import Any


_JSON_BLOCK_RE = re.compile(r"\{\s*\"[^}]+\}", re.DOTALL)


def scan_pages_for_json(pages: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for title, bundle in pages.items():
        text = bundle.get("wikitext") or ""
        blocks = _JSON_BLOCK_RE.findall(text)
        valid = []
        for block in blocks[:5]:
            try:
                json.loads(block)
                valid.append(block[:80])
            except json.JSONDecodeError:
                pass
        if valid:
            result[title] = valid
    return result
