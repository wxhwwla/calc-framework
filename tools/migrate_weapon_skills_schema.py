#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

将 weapons.json 从旧字段迁移为新武器技能 schema。



用法（仓库根目录）：

    python tools/migrate_weapon_skills_schema.py

    python tools/migrate_weapon_skills_schema.py --apply

    python tools/migrate_weapon_skills_schema.py --apply --only 狼之绯 钢铁余音

"""

from __future__ import annotations


import argparse

import json

import sys

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

PKG_ROOT = REPO_ROOT / "games" / "endfield"

if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))


from games.endfield.calc.skills.special_fields import (
    migrate_weapon_record_to_skill_schema,
)


def _load_weapons(path: Path) -> list[dict]:
    """加载武器 JSON 文件并验证为数组格式。

    Args:
        path: weapons.json 文件路径

    Returns:
        武器数据列表

    Raises:
        ValueError: JSON 根节点不是数组
    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("weapons.json 根节点必须是数组")

    return data


def migrate_file(
    *,
    weapons_json: Path,
    only_names: set[str] | None = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """迁移 weapons.json 中的字段到新武器技能 schema。

    Args:
        weapons_json: weapons.json 文件路径
        only_names: 仅迁移指定武器名称集合
        dry_run: True 时仅预览不写入

    Returns:
        包含 dry_run、changed_count、changed_names 的字典
    """
    weapons = _load_weapons(weapons_json)

    changed_names: list[str] = []

    for row in weapons:
        name = str(row.get("名称", ""))

        if only_names and name not in only_names:
            continue

        if migrate_weapon_record_to_skill_schema(row):
            changed_names.append(name)

    if not dry_run and changed_names:
        with weapons_json.open("w", encoding="utf-8") as f:
            json.dump(weapons, f, ensure_ascii=False, indent=2)

    return {
        "dry_run": dry_run,
        "changed_count": len(changed_names),
        "changed_names": changed_names,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：解析参数并执行武器 schema 迁移。

    Args:
        argv: 命令行参数列表

    Returns:
        退出码
    """
    parser = argparse.ArgumentParser(description="迁移 weapons.json 到新技能 schema")

    parser.add_argument(
        "--weapons-json",
        type=Path,
        default=PKG_ROOT / "games/endfield/data" / "weapon_data" / "weapons.json",
        help="武器 JSON 路径",
    )

    parser.add_argument(
        "--only",
        nargs="*",
        help="仅迁移指定武器名称",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="写回文件（默认仅预览）",
    )

    args = parser.parse_args(argv)

    only_names = set(args.only or [])

    result = migrate_file(
        weapons_json=args.weapons_json,
        only_names=only_names if only_names else None,
        dry_run=not args.apply,
    )

    mode = "预览" if result["dry_run"] else "已写入"

    print(f"[{mode}] 迁移武器 {result['changed_count']} 把")

    for name in result["changed_names"]:
        print(f"  · {name}")

    if result["dry_run"] and result["changed_count"]:
        print("\n加 --apply 写入文件。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
