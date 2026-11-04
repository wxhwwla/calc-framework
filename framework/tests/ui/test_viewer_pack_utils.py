# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 数据工具 — 实体来源映射测试。"""

from calc_framework.ui.viewer_evaluator import build_viewer_context
from calc_framework.ui.viewer_pack_utils import (
    _DATA_FILE_TO_SOURCE,
    _SOURCE_DISPLAY_NAMES,
    _SOURCE_TO_DATA_FILE,
    build_context_from_entity,
)


def test_entity_source_mappings_include_enemy() -> None:
    assert _SOURCE_TO_DATA_FILE["enemy"] == "enemies"
    assert _DATA_FILE_TO_SOURCE["enemies"] == "enemy"
    assert _SOURCE_DISPLAY_NAMES["enemy"] == "敌人"
    assert _SOURCE_DISPLAY_NAMES["character"] == "角色"


def test_build_context_from_entity_flattens_enemy_scalars() -> None:
    ctx = build_context_from_entity(
        {"名称": "Boss", "等级": 50, "防御": 100, "韧性": [10, 20, 30]},
        "enemy",
        level=2,
    )

    assert ctx == {"防御": 100.0, "韧性": 20.0}


def test_build_viewer_context_uses_enemy_namespace_and_defaults() -> None:
    class _Var:
        default = 0.0

    variables = {"enemy.防御": _Var(), "enemy.抗性": _Var()}

    ctx = build_viewer_context(
        entity_selectors={"enemy": "Boss"},
        entity_data={"enemy": {"Boss": {"名称": "Boss", "防御": 100}}},
        variables=variables,
        level=90,
    )

    assert ctx["enemy"]["防御"] == 100.0
    assert ctx["enemy"]["抗性"] == 0.0
