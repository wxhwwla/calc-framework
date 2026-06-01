# SPDX-License-Identifier: AGPL-3.0
"""
Arknights BWIKI 侦察入口（阶段 C）。

用法（仓库根目录）：
    python tools/arknights_scout/scout.py
    python tools/arknights_scout/scout.py --limit 5
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from arknights_scout.api import MediaWikiClient
from arknights_scout.config import (
    API_URL,
    CATEGORY_TITLES,
    GALLERY_PAGES,
    LOCAL_CHARACTERS_JSON,
    OUTPUT_ROOT,
    REQUEST_INTERVAL_SEC,
    USER_AGENT,
)
from arknights_scout.gallery import extract_gallery_entry_titles, merge_title_lists
from arknights_scout.json_scan import scan_pages_for_json
from arknights_scout.local_schema import compare_name_sets, load_local_name_sets, summarize_local_schema
from arknights_scout.names import normalize_name_for_match
from arknights_scout.report import (
    write_names_diff_report,
    write_sample_bundle,
    write_schema_diff_report,
    write_summary_report,
)
from arknights_scout.storage import load_page_bundle, save_page_bundle, write_manifest


def collect_titles_for_kind(
    client: MediaWikiClient,
    gallery_page: str,
    category_title: str,
) -> tuple[list[str], list[str], list[str]]:
    html = client.fetch_parsed_gallery_html(gallery_page)
    from_gallery = extract_gallery_entry_titles(html)
    from_category: list[str] = []
    try:
        from_category = client.fetch_category_members(category_title)
    except RuntimeError:
        from_category = []
    merged = merge_title_lists(from_category, from_gallery)
    return from_gallery, from_category, merged


def run_scout(
    *,
    output_root: Path = OUTPUT_ROOT,
    client: MediaWikiClient | None = None,
    per_kind_limit: int | None = None,
    only_kind: str | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    raw_dir = output_root / "raw"
    reports_dir = output_root / "reports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    wiki = client or MediaWikiClient(
        API_URL,
        user_agent=USER_AGENT,
        request_interval_sec=REQUEST_INTERVAL_SEC,
    )

    manifest_kinds: dict[str, Any] = {}
    all_pages: dict[str, dict[str, Any]] = {}
    titles_by_kind: dict[str, list[str]] = {}

    gallery_items = GALLERY_PAGES.items()
    if only_kind:
        if only_kind not in GALLERY_PAGES:
            raise ValueError(f"未知种类：{only_kind}")
        gallery_items = [(only_kind, GALLERY_PAGES[only_kind])]

    for kind, gallery_page in gallery_items:
        category = CATEGORY_TITLES.get(kind, "")
        gallery, category_list, merged = collect_titles_for_kind(wiki, gallery_page, category)
        if per_kind_limit is not None:
            merged = merged[:per_kind_limit]
        titles_by_kind[kind] = merged
        manifest_kinds[kind] = {
            "gallery_page": gallery_page,
            "category": category,
            "gallery_count": len(gallery),
            "category_count": len(category_list),
            "merged_count": len(merged),
            "titles": merged,
        }

    cache_hits = 0
    fetched_count = 0
    for kind, titles in titles_by_kind.items():
        if not titles:
            continue
        pending: list[str] = []
        for title in titles:
            cached = load_page_bundle(raw_dir, title)
            if cached:
                cache_hits += 1
                cached["kind"] = kind
                all_pages[title] = cached
            else:
                pending.append(title)
        if pending:
            bundles = wiki.fetch_pages_content(pending)
            fetched_count += len(bundles)
            for title, bundle in bundles.items():
                bundle["kind"] = kind
                save_page_bundle(raw_dir, title, bundle)
                all_pages[title] = bundle

    manifest = {
        "api_url": API_URL,
        "kinds": manifest_kinds,
        "fetched_pages": len(all_pages),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "cache_stats": {"from_cache": cache_hits, "fetched": fetched_count},
    }
    write_manifest(output_root, manifest)

    json_search_hits: list[str] = []
    try:
        json_search_hits = wiki.search_json_file_candidates()
    except RuntimeError:
        pass

    json_scan = scan_pages_for_json(all_pages)
    local_schema = summarize_local_schema(LOCAL_CHARACTERS_JSON)
    local_names = load_local_name_sets(LOCAL_CHARACTERS_JSON)

    name_diff: dict[str, Any] = {}
    for kind in ("operator",):
        wiki_set = set(titles_by_kind.get(kind, []))
        name_diff[kind] = compare_name_sets(wiki_set, local_names[kind], normalize=normalize_name_for_match)

    write_summary_report(reports_dir, manifest=manifest, json_scan=json_scan, json_search_hits=json_search_hits)
    write_schema_diff_report(reports_dir, local_schema)
    write_names_diff_report(reports_dir, name_diff)

    for kind, titles in titles_by_kind.items():
        if not titles:
            continue
        write_sample_bundle(reports_dir, kind, wiki_bundle=all_pages.get(titles[0]))

    return {
        "manifest_path": str(output_root / "manifest.json"),
        "reports_dir": str(reports_dir),
        "raw_dir": str(raw_dir),
        "page_count": len(all_pages),
        "cache_stats": manifest["cache_stats"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Arknights BWIKI 数据侦察（阶段 C）")
    parser.add_argument("--limit", type=int, default=None, help="每类最多拉取条目数（调试用）")
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT, help="输出目录")
    parser.add_argument("--only-kind", choices=tuple(GALLERY_PAGES.keys()), default=None, help="仅拉取指定种类")
    args = parser.parse_args(argv)
    result = run_scout(output_root=args.output, per_kind_limit=args.limit, only_kind=args.only_kind)
    stats = result.get("cache_stats") or {}
    print(f"完成：共 {result['page_count']} 页（本地复用 {stats.get('from_cache', 0)}，新拉取 {stats.get('fetched', 0)}）")
    print(f"原始缓存目录: {args.output / 'raw'}")
    print(f"manifest: {result['manifest_path']}")
    print(f"报告目录: {result['reports_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
