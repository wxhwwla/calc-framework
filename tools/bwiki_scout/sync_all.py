#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
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

from bwiki_scout.bump_data_version import bump_data_version, read_data_version  # noqa: E402

from bwiki_scout.wiki_sync import (  # noqa: E402

    sync_operators_from_cache,

    sync_weapons_from_cache,

)



_SEED_CHAR_PATH = (

    Path(__file__).resolve().parent.parent.parent

    / "games"

    / "endfield"

    / "scripts"

    / "seed_characters.py"

)

_SEED_WEAPON_PATH = (

    Path(__file__).resolve().parent.parent.parent

    / "games"

    / "endfield"

    / "scripts"

    / "seed_weapons.py"

)





def _print_part(title: str, result: dict) -> None:

    """_print_part 实现。"""
    mode = "预览" if result.get("dry_run", True) else "已写入"

    print(f"\n[{title}][{mode}]")

    skipped_inc = result.get("skipped_by_incremental", [])

    inc_info = f"，增量跳过 {len(skipped_inc)} 条" if skipped_inc else ""

    if "planned" in result:

        print(

            f"计划 {len(result['planned'])} 条（更新 {len(result.get('updated', []))}，"

            f"新增 {len(result.get('added', []))}）{inc_info}"

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

    """CLI 入口。"""
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

    parser.add_argument(

        "--full",

        action="store_true",

        help="全量同步（默认增量模式，--full 时重新处理所有条目）",

    )

    parser.add_argument(

        "--bump-version",

        action="store_true",

        help="数据写入后自动更新 data_version.json 版本号",

    )

    parser.add_argument(

        "--verify",

        action="store_true",

        help="数据写入后运行数据验证测试",

    )

    args = parser.parse_args(argv)



    dry_run = not args.apply

    incremental = not args.full



    op_result = sync_operators_from_cache(

        output_root=args.input,

        characters_json=LOCAL_CHARACTERS_JSON,

        seed_path=_SEED_CHAR_PATH,

        names=args.only_operators,

        include_new=args.new,

        incremental=incremental,

        dry_run=dry_run,

    )

    _print_part("干员", op_result)



    weapon_result = sync_weapons_from_cache(

        output_root=args.input,

        weapons_json=LOCAL_WEAPONS_JSON,

        seed_path=_SEED_WEAPON_PATH,

        names=args.only_weapons,

        include_new=args.new,

        incremental=incremental,

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

    sync_results = [op_result, weapon_result, equip_result]

    if not dry_run and args.bump_version:
        new_ver = bump_data_version(sync_results)
        if new_ver:
            print(f"\n📦 数据版本：{read_data_version()['version']} → {new_ver}")
        else:
            current = read_data_version()["version"]
            print(f"\n📦 数据版本：{current}（无变更，未 bump）")

    if not dry_run and args.verify:
        from bwiki_scout.bump_data_version import run_verify_tests
        print("\n正在验证数据...")
        verify_result = run_verify_tests()
        if verify_result["passed"]:
            print("✅ 数据验证通过")
        else:
            print("❌ 数据验证失败:")
            if verify_result["stdout"]:
                print(verify_result["stdout"][:300])
            if verify_result["stderr"]:
                print(verify_result["stderr"][:300])

    return 0





if __name__ == "__main__":

    sys.exit(main())

