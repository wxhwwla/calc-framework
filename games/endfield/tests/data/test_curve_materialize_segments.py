# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 segments[] 双读物化测试。"""

from __future__ import annotations

from games.endfield.data_loading.curve_materialize import materialize_character_entity


def test_materialize_character_segments_format():
    char = {
        "名称": "测试干员",
        "成长参数": {
            "segments": [
                {
                    "key": "力量",
                    "length": 5,
                    "base": 10,
                    "growth": 2,
                    "divisor": 1,
                    "offset": 0,
                },
            ]
        },
    }
    out = materialize_character_entity(char)
    assert out["力量"] == [10.0, 12.0, 14.0, 16.0, 18.0]
    assert out["等级"] == [1, 2, 3, 4, 5]
