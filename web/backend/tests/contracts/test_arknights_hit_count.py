# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Web 连发总伤害契约。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
for _path in (str(_REPO / "framework" / "src"), str(_REPO), str(_REPO / "web" / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from api.arknights import ComputeRequest, compute_damage_payload


def _request(hit_count: int) -> ComputeRequest:
    return ComputeRequest(
        operator_name="风笛",
        skill_multiplier=1.0,
        enemy_def=200.0,
        enemy_res=50.0,
        hit_count=hit_count,
    )


def test_hit_count_multiplies_damage_once() -> None:
    single = compute_damage_payload(_request(1))
    double = compute_damage_payload(_request(2))

    assert double.physical_damage == single.physical_damage * 2
    assert double.magical_damage == single.magical_damage * 2
    assert double.true_damage == single.true_damage * 2
    assert double.final_atk == single.final_atk
