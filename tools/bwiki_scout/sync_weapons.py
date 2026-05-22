#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以 BWIKI 武器 wikitext 为准，反推基础攻击与词条潜能曲线。

仅处理 Wiki 含「基础攻击力 + 满级基础攻击力 + 词条1rank1…」的页面；简表武器会跳过。
默认仅预览；加 --apply 写入 weapons.json 与 seed_weapons.py。

用法（仓库根目录）：
    python tools/bwiki_scout/sync_weapons.py
    python tools/bwiki_scout/sync_weapons.py --apply
    python tools/bwiki_scout/sync_weapons.py --apply --only 逐鳞3.0

说明见 tools/bwiki_scout/README.md、docs/操作指令集.md §9。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from bwiki_scout.config import LOCAL_WEAPONS_JSON, OUTPUT_ROOT
from bwiki_scout.wiki_sync import sync_weapons_from_cache

_SEED_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "endfield_damage_calculator"
    / "scripts"
    / "seed_weapons.py"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BWIKI → 本地武器 JSON/seed 同步")
    parser.add_argument(
        "--input",
        type=Path,
        default=OUTPUT_ROOT,
        help="scout 输出目录",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="写入 weapons.json 与 seed_weapons.py（默认仅预览）",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="仅处理指定武器名称",
    )
    args = parser.parse_args(argv)

    result = sync_weapons_from_cache(
        output_root=args.input,
        weapons_json=LOCAL_WEAPONS_JSON,
        seed_path=_SEED_PATH,
        names=args.only,
        dry_run=not args.apply,
    )
    mode = "预览" if result["dry_run"] else "已写入"
    print(f"[{mode}] 计划更新 {len(result['planned'])} 把武器：")
    for name in result["planned"]:
        print(f"  - {name}")
    if result["skipped"]:
        print(f"跳过 {len(result['skipped'])} 项：")
        for item in result["skipped"][:20]:
            print(f"  - {item}")
    if not result["dry_run"]:
        print(f"已更新 weapons.json 与 seed：{result['updated_count']} 把")
    return 0


if __name__ == "__main__":
    sys.exit(main())
