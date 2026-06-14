#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""将 weapons.json 中旧 ``特殊能力`` 迁移为 ``特殊能力1`` / ``特殊能力2`` 占位。"""

from __future__ import annotations


import json

import sys

from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent.parent

_PKG = _REPO / "games" / "endfield"

if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))


from games.endfield.calc.skills.special_fields import (
    read_weapon_special_slots,
    write_weapon_special_slots,
)


_WEAPONS = _PKG / "games/endfield/data" / "weapon_data" / "weapons.json"


def main() -> int:
    """CLI 入口。"""
    rows = json.loads(_WEAPONS.read_text(encoding="utf-8"))

    for weapon in rows:
        slots = read_weapon_special_slots(weapon)

        write_weapon_special_slots(weapon, slots)  # type: ignore[arg-type]

    _WEAPONS.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已迁移 {len(rows)} 把武器的 special 字段")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
