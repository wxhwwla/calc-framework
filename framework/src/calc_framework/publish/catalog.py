# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Catalog 生成器 — 生成社区分享平台的静态 HTML 目录。"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from ..config.manager import discover_adapters
from ..logging import get_logger

logger = get_logger(__name__)


CATALOG_HTML = """<!DOCTYPE html>

<html lang="zh-CN">

<head>

<meta charset="UTF-8">

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Calc Framework — 适配器市场</title>

<style>

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

          background: #f5f5f7; color: #1d1d1f; }}

  .container {{ max-width: 960px; margin: 0 auto; padding: 2rem; }}

  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}

  p.subtitle {{ color: #6e6e73; margin-bottom: 2rem; }}

  .card {{ background: #fff; border-radius: 12px; padding: 1.5rem;

          margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}

  .card h2 {{ font-size: 1.25rem; margin-bottom: 0.25rem; }}

  .card .meta {{ display: flex; gap: 1rem; font-size: 0.85rem; color: #6e6e73; margin: 0.5rem 0; }}

  .card .desc {{ color: #1d1d1f; margin: 0.5rem 0; }}

  .card .tags {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}

  .tag {{ background: #e8e8ed; border-radius: 6px; padding: 0.15rem 0.6rem; font-size: 0.8rem; }}

  .footer {{ text-align: center; color: #6e6e73; font-size: 0.85rem; margin-top: 3rem; }}

</style>

</head>

<body>

<div class="container">

  <h1>📦 适配器市场</h1>

  <p class="subtitle">Calc Framework 社区适配器目录</p>

  {cards}

  <p class="footer">由 calc_framework.publish 自动生成</p>

</div>

</body>

</html>

"""


def _build_card(name: str, meta: dict[str, Any]) -> str:
    """_build_card。"""
    tags = meta.get("tags", [])

    version = meta.get("version", "?")

    game = meta.get("game", name)

    author = meta.get("author", "未知")

    desc = meta.get("description", "")

    tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

    return f"""<div class="card">

  <h2>{name}</h2>

  <div class="meta"><span>v{version}</span><span>{game}</span><span>作者: {author}</span></div>

  <div class="desc">{desc}</div>

  <div class="tags">{tag_html}</div>

</div>"""


def build_catalog(output_dir: str | Path | None = None) -> str:
    """构建适配器目录 HTML 并写入（可选）输出目录。"""

    adapters = discover_adapters()

    cards: list[str] = []

    for name, path in adapters.items():
        meta_path = path / "meta.json"

        meta: dict[str, Any] = {}

        with contextlib.suppress(Exception):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

        cards.append(_build_card(name, meta))

    html = CATALOG_HTML.format(cards="\n".join(cards))

    if output_dir:
        out = Path(output_dir)

        out.mkdir(parents=True, exist_ok=True)

        (out / "index.html").write_text(html, encoding="utf-8")

        logger.info("Catalog 已写入: %s", out / "index.html")

    return html


def _format_json(data: Any) -> str:
    """_format_json。"""

    return json.dumps(data, ensure_ascii=False, indent=2)
