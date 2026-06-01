# SPDX-License-Identifier: AGPL-3.0
"""本地 JSON schema 扫描与 wiki/local 名称对比。"""

from pathlib import Path
from typing import Any


def load_local_name_sets(characters_json: Path, *extra: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {"operator": set()}
    if characters_json.is_file():
        import json
        chars = json.loads(characters_json.read_text(encoding="utf-8"))
        for c in chars:
            name = c.get("名称") or c.get("name") or ""
            if name:
                result["operator"].add(name)
    return result


def summarize_local_schema(characters_json: Path, *extra: Path) -> list[dict[str, Any]]:
    if not characters_json.is_file():
        return []
    import json
    chars = json.loads(characters_json.read_text(encoding="utf-8"))
    if not chars:
        return []
    sample = chars[0]
    return [{"file": str(characters_json), "fields": list(sample.keys())[:20]}]


def compare_name_sets(
    wiki_set: set[str],
    local_set: set[str],
    *,
    normalize,
) -> dict[str, Any]:
    wiki_norm = {normalize(n): n for n in wiki_set}
    local_norm = {normalize(n): n for n in local_set}
    wiki_only = wiki_norm.keys() - local_norm.keys()
    local_only = local_norm.keys() - wiki_norm.keys()
    matched = wiki_norm.keys() & local_norm.keys()
    return {
        "wiki_count": len(wiki_set),
        "local_count": len(local_set),
        "matched": len(matched),
        "wiki_only": [wiki_norm[k] for k in sorted(wiki_only)],
        "local_only": [local_norm[k] for k in sorted(local_only)],
    }
