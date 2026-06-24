#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

从 BWIKI 缓存回填武器特殊能力 max_stack（仅第 4 元素，不改曲线）。



用法（仓库根目录）：

    python tools/bwiki_scout/scout.py --only-kind weapon   # 先拉取 Wiki

    python tools/bwiki_scout/backfill_weapon_max_stack.py

    python tools/bwiki_scout/backfill_weapon_max_stack.py --apply

    python tools/bwiki_scout/backfill_weapon_max_stack.py --apply --only 狼之绯 钢铁余音

"""

from __future__ import annotations


import argparse


import sys

from pathlib import Path


_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent

if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))


from bwiki_scout.config import LOCAL_WEAPONS_JSON, OUTPUT_ROOT

from bwiki_scout.weapon_wiki import backfill_weapon_max_stack_from_cache


_SEED_PATH = Path(__file__).resolve().parent.parent.parent / "games" / "endfield" / "scripts" / "seed_weapons.py"


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="BWIKI → 武器 max_stack 回填")

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

    result = backfill_weapon_max_stack_from_cache(
        output_root=args.input,
        weapons_json=LOCAL_WEAPONS_JSON,
        seed_path=_SEED_PATH,
        names=args.only,
        dry_run=not args.apply,
    )

    mode = "预览" if result["dry_run"] else "已写入"

    print(f"[{mode}] max_stack 变更 {len(result['planned'])} 把武器")

    for item in result["changes"]:
        print(f"  · {item['name']}")

        for slot in item["slots"]:
            print(f"    特殊能力{slot['slot']}: {slot['old']} → {slot['new']} ({slot['source']})")

    if result["skipped"]:
        print(f"跳过: {len(result['skipped'])}")

    if result["dry_run"] and result["planned"]:
        print("\n加 --apply 写入本地 JSON/seed。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
