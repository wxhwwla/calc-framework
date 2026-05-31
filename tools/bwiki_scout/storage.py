#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""原始页面缓存与 manifest 写入。"""

import json
import re
from pathlib import Path
from typing import Any


def safe_dirname(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", title)
    return cleaned or "untitled"


def save_page_bundle(raw_dir: Path, title: str, bundle: dict[str, Any]) -> Path:
    """将单页 wikitext/html/meta 写入 raw 子目录。"""
    page_dir = raw_dir / safe_dirname(title)
    page_dir.mkdir(parents=True, exist_ok=True)
    meta_path = page_dir / "meta.json"
    meta = {
        "title": bundle.get("title", title),
        "pageid": bundle.get("pageid"),
        "ns": bundle.get("ns"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (page_dir / "wikitext.txt").write_text(bundle.get("wikitext") or "", encoding="utf-8")
    (page_dir / "html.html").write_text(bundle.get("html") or "", encoding="utf-8")
    return page_dir


def load_page_bundle(raw_dir: Path, title: str) -> dict[str, Any] | None:
    """从 raw 缓存读取单页；无有效 wikitext 时返回 None。"""
    page_dir = raw_dir / safe_dirname(title)
    wikitext_path = page_dir / "wikitext.txt"
    if not wikitext_path.is_file():
        return None
    wikitext = wikitext_path.read_text(encoding="utf-8")
    if not wikitext.strip():
        return None
    meta: dict[str, Any] = {"title": title}
    meta_path = page_dir / "meta.json"
    if meta_path.is_file():
        meta.update(json.loads(meta_path.read_text(encoding="utf-8")))
    html_path = page_dir / "html.html"
    html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
    return {
        "title": meta.get("title", title),
        "pageid": meta.get("pageid"),
        "ns": meta.get("ns"),
        "wikitext": wikitext,
        "html": html,
    }


def write_manifest(output_root: Path, manifest: dict[str, Any]) -> Path:
    path = output_root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
