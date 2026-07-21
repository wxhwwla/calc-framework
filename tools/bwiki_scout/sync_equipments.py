#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0


# SPDX-License-Identifier: AGPL-3.0
"""

以 BWIKI 装备草案为准同步本地装备 JSON。



默认仅预览；加 --apply 写入 games/endfield/data/equipments.json。

"""

from __future__ import annotations


import argparse

import sys

from pathlib import Path


_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent

if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))


from bwiki_scout.config import LOCAL_EQUIPMENTS_JSON, OUTPUT_ROOT

from bwiki_scout.equipment_sync import sync_equipments_from_parsed


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="BWIKI parsed 装备草案 -> 本地装备 JSON")

    parser.add_argument("--input", type=Path, default=OUTPUT_ROOT, help="scout 输出目录")

    parser.add_argument(
        "--apply",
        action="store_true",
        help="写入 equipments.json（默认仅预览）",
    )

    args = parser.parse_args(argv)

    parsed_path = args.input / "parsed" / "equipment.json"

    if not parsed_path.is_file():
        print(f"未找到装备草案：{parsed_path}")

        print("请先运行：python tools/bwiki_scout/parse_draft.py")

        return 1

    result = sync_equipments_from_parsed(
        parsed_equipment_json=parsed_path,
        local_equipments_json=LOCAL_EQUIPMENTS_JSON,
        dry_run=not args.apply,
    )

    mode = "预览" if result["dry_run"] else "已写入"

    print(f"[{mode}] 装备条目数：{result['count']}")

    if result.get("kind_counts"):
        print(f"  装备种类统计：{result['kind_counts']}")

    for name in result["sample_names"]:
        print(f"  - {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
