#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 B：将侦察缓存解析为 JSON 草案（不写入正式 characters.json / weapons.json）。

用法：
    python tools/bwiki_scout/parse_draft.py
    python tools/bwiki_scout/parse_draft.py --input tools/bwiki_scout/output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from bwiki_scout.config import OUTPUT_ROOT
from bwiki_scout.storage import safe_dirname

_PARAM_RE = re.compile(r"\|([^=\|\n}]+?)=([^|\n}]+)")


def extract_template_params(wikitext: str) -> dict[str, str]:
    """从 wikitext 模板参数提取键值（阶段 B 最小实现）。"""
    params: dict[str, str] = {}
    for key, value in _PARAM_RE.findall(wikitext or ""):
        k = key.strip()
        v = value.strip()
        if k and k not in params:
            params[k] = v
    return params


def build_draft_record(
    *,
    kind: str,
    title: str,
    wikitext: str,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """生成单条草案记录，字段尽量贴近本地 JSON 命名空间。"""
    params = extract_template_params(wikitext)
    record: dict[str, Any] = {
        "名称": title,
        "_source": "bwiki",
        "_kind": kind,
        "_pageid": meta.get("pageid"),
        "_wiki_params": params,
    }
    if kind == "operator":
        record.setdefault("类型", params.get("职业") or params.get("类型", ""))
        record.setdefault("星级", _parse_int(params.get("稀有度") or params.get("星级")))
        record.setdefault("武器", params.get("武器", ""))
        record["_missing_local_fields"] = [
            "等级",
            "力量",
            "敏捷",
            "智识",
            "意志",
            "基础攻击力",
            "战技倍率",
            "连携技倍率",
            "终结技倍率",
        ]
    elif kind == "weapon":
        record.setdefault("类型", params.get("类型", ""))
        record.setdefault("星级", _parse_int(params.get("稀有度") or params.get("星级")))
        record["_missing_local_fields"] = ["等级", "基础攻击力", "特殊能力"]
    else:
        record["_missing_local_fields"] = ["等级", "属性", "词条"]
    return record


def _parse_int(text: str | None) -> int | None:
    if not text:
        return None
    digits = re.search(r"\d+", text)
    return int(digits.group(0)) if digits else None


def run_parse_draft(
    *,
    input_root: Path = OUTPUT_ROOT,
    parsed_dir: Path | None = None,
) -> dict[str, str]:
    """读取 manifest 与 raw 缓存，写出 parsed/*.json 草案。"""
    manifest_path = input_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"缺少 manifest: {manifest_path}")

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    out_dir = parsed_dir or (input_root / "parsed")
    out_dir.mkdir(parents=True, exist_ok=True)

    buckets: dict[str, list[dict[str, Any]]] = {
        "operator": [],
        "weapon": [],
        "equipment": [],
    }

    raw_dir = input_root / "raw"
    for kind, block in manifest.get("kinds", {}).items():
        for title in block.get("titles", []):
            page_dir = raw_dir / safe_dirname(title)
            if not page_dir.is_dir():
                continue
            meta_path = page_dir / "meta.json"
            wikitext_path = page_dir / "wikitext.txt"
            meta = {}
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            wikitext = wikitext_path.read_text(encoding="utf-8") if wikitext_path.is_file() else ""
            record = build_draft_record(
                kind=kind,
                title=title,
                wikitext=wikitext,
                meta=meta,
            )
            buckets.setdefault(kind, []).append(record)

    output_paths = {}
    for kind, rows in buckets.items():
        filename = {
            "operator": "operators.json",
            "weapon": "weapons.json",
            "equipment": "equipment.json",
        }[kind]
        path = out_dir / filename
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        output_paths[kind] = str(path)

    return output_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BWIKI 解析草案（阶段 B）")
    parser.add_argument("--input", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    paths = run_parse_draft(input_root=args.input)
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
