#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BWIKI 一键同步：干员 + 武器 + 装备。

默认仅预览；加 --apply 才会写入本地 JSON/seed。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from bwiki_scout.config import (  # noqa: E402
    LOCAL_CHARACTERS_JSON,
    LOCAL_EQUIPMENTS_JSON,
    LOCAL_WEAPONS_JSON,
    OUTPUT_ROOT,
)
from bwiki_scout.equipment_sync import sync_equipments_from_parsed  # noqa: E402
from bwiki_scout.parse_draft import run_parse_draft  # noqa: E402
from bwiki_scout.wiki_sync import (  # noqa: E402
    sync_operators_from_cache,
    sync_weapons_from_cache,
)

_SEED_CHAR_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "endfield_damage_calculator"
    / "scripts"
    / "seed_characters.py"
)
_SEED_WEAPON_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "endfield_damage_calculator"
    / "scripts"
    / "seed_weapons.py"
)


def _print_part(title: str, result: dict) -> None:
    mode = "预览" if result.get("dry_run", True) else "已写入"
    print(f"\n[{title}][{mode}]")
    if "planned" in result:
        print(
            f"计划 {len(result['planned'])} 条（更新 {len(result.get('updated', []))}，"
            f"新增 {len(result.get('added', []))}）"
        )
        for name in result["planned"][:20]:
            print(f"  - {name}")
        if len(result["planned"]) > 20:
            print(f"  ... 其余 {len(result['planned']) - 20} 条省略")
    else:
        print(f"条目数：{result.get('count', 0)}")
        for name in result.get("sample_names", [])[:20]:
            print(f"  - {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BWIKI 一键同步（干员/武器/装备）")
    parser.add_argument("--input", type=Path, default=OUTPUT_ROOT, help="scout 输出目录")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="写入本地 JSON/seed（默认仅预览）",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="干员/武器同步时同时导入 manifest 中本地尚无条目",
    )
    parser.add_argument("--only-operators", nargs="*", help="仅处理指定干员名称")
    parser.add_argument("--only-weapons", nargs="*", help="仅处理指定武器名称")
    args = parser.parse_args(argv)

    dry_run = not args.apply

    op_result = sync_operators_from_cache(
        output_root=args.input,
        characters_json=LOCAL_CHARACTERS_JSON,
        seed_path=_SEED_CHAR_PATH,
        names=args.only_operators,
        include_new=args.new,
        dry_run=dry_run,
    )
    _print_part("干员", op_result)

    weapon_result = sync_weapons_from_cache(
        output_root=args.input,
        weapons_json=LOCAL_WEAPONS_JSON,
        seed_path=_SEED_WEAPON_PATH,
        names=args.only_weapons,
        include_new=args.new,
        dry_run=dry_run,
    )
    _print_part("武器", weapon_result)

    parsed_path = args.input / "parsed" / "equipment.json"
    if not parsed_path.is_file():
        run_parse_draft(input_root=args.input)
    if not parsed_path.is_file():
        print("\n[装备] 未找到 parsed/equipment.json，跳过装备同步。")
        return 0
    equip_result = sync_equipments_from_parsed(
        parsed_equipment_json=parsed_path,
        local_equipments_json=LOCAL_EQUIPMENTS_JSON,
        dry_run=dry_run,
    )
    _print_part("装备", equip_result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
