# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地逆推曲线蓝图（N=1 / 多技能段）。"""

from __future__ import annotations

from calc_framework.inverse.curve import CurveBlueprint, single_segment_blueprint

_ATTR_SEARCH = {
    "divisor_range": (1, 201),
    "growth_range": (1, 301),
    "offset_search_limit": 200,
}

ENDFIELD_ATTRIBUTE_BLUEPRINT = single_segment_blueprint(
    90,
    key="attr_90",
    label="属性成长 (1-90 级)",
    search_options=dict(_ATTR_SEARCH),
)

ENDFIELD_SKILL_12_BLUEPRINT = single_segment_blueprint(
    12,
    key="skill_12",
    label="技能倍率 (1-12 级，10-12 特殊值)",
    special_indices=[9, 10, 11],
)

ENDFIELD_SKILL_9_BLUEPRINT = single_segment_blueprint(
    9,
    key="skill_9",
    label="技能倍率 (1-9 级)",
)

ENDFIELD_INVERSE_BLUEPRINTS: tuple[CurveBlueprint, ...] = (
    ENDFIELD_ATTRIBUTE_BLUEPRINT,
    ENDFIELD_SKILL_12_BLUEPRINT,
    ENDFIELD_SKILL_9_BLUEPRINT,
)
