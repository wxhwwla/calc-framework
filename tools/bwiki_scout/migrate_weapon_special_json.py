#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 weapons.json 中旧 ``特殊能力`` 迁移为 ``特殊能力1`` / ``特殊能力2`` 占位。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_PKG = _REPO / "endfield_damage_calculator"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from character_weapon_equipment.weapon_data.special_fields import (  # noqa: E402
    read_weapon_special_slots,
    write_weapon_special_slots,
)

_WEAPONS = (
    _PKG / "character_weapon_equipment" / "weapon_data" / "weapons.json"
)


def main() -> int:
    rows = json.loads(_WEAPONS.read_text(encoding="utf-8"))
    for weapon in rows:
        slots = read_weapon_special_slots(weapon)
        write_weapon_special_slots(weapon, slots)
    _WEAPONS.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已迁移 {len(rows)} 把武器的 special 字段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
