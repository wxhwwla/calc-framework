# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""parse_operator 精英里程碑解析测试。"""

from __future__ import annotations

from tools.arknights_scout.parse_operator import parse_base_stats

_SAMPLE_KV = """
|星级=6
|初始生命=711
|初始生命max=1016
|精1生命max=1338
|精2生命max=1673
|初始攻击=217
|初始攻击max=305
|精1攻击max=437
|精2攻击max=540
|攻击间隔=1.0
|阻挡数=1
|部署费用=12
"""


def test_parse_elite_milestones():
    kv = {k: v for line in _SAMPLE_KV.strip().splitlines() for k, v in [line.strip("|").split("=", 1)]}
    stats = parse_base_stats(kv, 6)
    assert stats["hp"] == 1016
    ms = stats["属性里程碑"]
    assert ms["hp"]["e0_lv1"] == 711
    assert ms["hp"]["e2_max"] == 1673
    assert ms["atk"]["e1_max"] == 437
