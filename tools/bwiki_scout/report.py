#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成侦察 Markdown 报告。"""

from pathlib import Path
from typing import Any


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_summary_report(
    reports_dir: Path,
    *,
    manifest: dict[str, Any],
    json_scan: dict[str, Any],
    json_search_hits: list[str],
) -> Path:
    lines = [
        "# BWIKI 侦察摘要",
        "",
        "## 条目数量",
        "",
    ]
    for kind, block in manifest.get("kinds", {}).items():
        lines.append(f"- **{kind}**：图鉴 {block.get('gallery_count', 0)}，分类补全 {block.get('category_count', 0)}，合并后 {block.get('merged_count', 0)}")
    lines.extend(
        [
            "",
            "## JSON 文件探测",
            "",
            f"- 页面内容内发现 JSON 线索：`{'是' if json_scan.get('any_hint') else '否'}`",
            f"- API 搜索 `.json` 相关标题：{len(json_search_hits)} 条",
            "",
        ]
    )
    if json_search_hits:
        lines.append("### 搜索命中标题")
        lines.append("")
        for title in json_search_hits:
            lines.append(f"- {title}")
        lines.append("")
    path = reports_dir / "summary.md"
    _write(path, "\n".join(lines))
    return path


def write_schema_diff_report(
    reports_dir: Path,
    local_schema: dict[str, Any],
    *,
    wiki_field_notes: dict[str, list[str]],
) -> Path:
    lines = [
        "# 字段结构对照（Wiki vs 本地）",
        "",
        "本地 `characters.json` / `weapons.json` 为**数组 + 中文键 + 等级曲线**；Wiki 为 **MediaWiki 模板/表格**，需解析后映射。",
        "",
    ]
    for kind in ("operator", "weapon", "equipment"):
        block = local_schema.get(kind, {})
        lines.append(f"## {kind}")
        lines.append("")
        if block.get("note"):
            lines.append(f"> {block['note']}")
            lines.append("")
        if block.get("path"):
            lines.append(f"- 本地文件：`{block['path']}`（{block.get('count', 0)} 条）")
            keys = block.get("top_level_keys") or []
            if keys:
                lines.append(f"- 本地顶层字段（样例）：`{'`, `'.join(keys)}`")
        notes = wiki_field_notes.get(kind) or []
        if notes:
            lines.append("- Wiki 常见片段（抽样）：")
            for note in notes:
                lines.append(f"  - {note}")
        lines.append("")
    path = reports_dir / "schema_diff.md"
    _write(path, "\n".join(lines))
    return path


def write_names_diff_report(
    reports_dir: Path,
    name_diff: dict[str, Any],
) -> Path:
    lines = ["# 名称对齐", ""]
    for kind, block in name_diff.items():
        lines.append(f"## {kind}")
        lines.append("")
        lines.append(f"- 完全一致：{len(block.get('matched', []))}")
        lines.append(f"- 规范化后匹配但原文不同：{len(block.get('title_matches_name_different', []))}")
        lines.append(f"- 仅 Wiki：{len(block.get('only_wiki', []))}")
        lines.append(f"- 仅本地：{len(block.get('only_local', []))}")
        if block.get("only_wiki"):
            lines.append("")
            lines.append("### 仅 Wiki（节选前 20）")
            for title in block["only_wiki"][:20]:
                lines.append(f"- {title}")
        if block.get("only_local"):
            lines.append("")
            lines.append("### 仅本地（节选前 20）")
            for name in block["only_local"][:20]:
                lines.append(f"- {name}")
        if block.get("title_matches_name_different"):
            lines.append("")
            lines.append("### 需人工映射")
            for pair in block["title_matches_name_different"][:20]:
                lines.append(f"- Wiki `{pair['wiki_title']}` ↔ 本地 `{pair['local_name']}`")
        lines.append("")
    path = reports_dir / "names_diff.md"
    _write(path, "\n".join(lines))
    return path


def write_sample_bundle(
    reports_dir: Path,
    kind: str,
    *,
    wiki_bundle: dict[str, Any] | None,
    local_sample: dict[str, Any] | None,
) -> None:
    import json

    samples_dir = reports_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    if wiki_bundle:
        base = samples_dir / f"{kind}_wiki"
        base.mkdir(parents=True, exist_ok=True)
        (base / "meta.json").write_text(
            json.dumps(
                {
                    "title": wiki_bundle.get("title"),
                    "pageid": wiki_bundle.get("pageid"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (base / "wikitext.txt").write_text(wiki_bundle.get("wikitext") or "", encoding="utf-8")
        (base / "html.html").write_text(wiki_bundle.get("html") or "", encoding="utf-8")
    if local_sample:
        (samples_dir / f"{kind}_local_sample.json").write_text(
            json.dumps(local_sample, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
