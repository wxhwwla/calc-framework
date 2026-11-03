# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""能力乘区模块拆分结构测试（P2-07）。

锁定 ``attribute_zone`` / ``attribute_zone_base`` / ``attribute_zone_details``
≤400 行，并保证原导入路径仍可取得全部公开符号。
"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.calc.multiplicative_zones.attribute_zone",
    "games.endfield.calc.multiplicative_zones.attribute_zone_base",
    "games.endfield.calc.multiplicative_zones.attribute_zone_details",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_attribute_zone_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_attribute_zone_reexports_public_symbols() -> None:
    from games.endfield.calc.multiplicative_zones import (
        attribute_zone,
        attribute_zone_base,
        attribute_zone_details,
    )

    assert attribute_zone.AttributeMultiplierZone is attribute_zone_base.AttributeMultiplierZone
    assert attribute_zone.AttributeZoneManager is attribute_zone_base.AttributeZoneManager
    assert (
        attribute_zone.calculate_attribute_zones_with_details
        is attribute_zone_details.calculate_attribute_zones_with_details
    )
