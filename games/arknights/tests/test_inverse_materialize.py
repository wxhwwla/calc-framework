# SPDX-License-Identifier: AGPL-3.0
"""AK 成长参数物化测试。"""

from __future__ import annotations

from games.arknights.calc.inverse.materialize import materialize_operator_entity


def test_materialize_operator_segments_field():
    op = {
        "名称": "能天使",
        "星级": 6,
        "成长参数": {
            "segments": [
                {
                    "key": "e0.hp",
                    "length": 5,
                    "stat": "hp",
                    "base": 711,
                    "growth": 2,
                    "divisor": 1,
                    "offset": 0,
                },
            ]
        },
    }
    out = materialize_operator_entity(op)
    assert "段曲线" in out
    assert "e0.hp" in out["段曲线"]
    assert len(out["段曲线"]["e0.hp"]) == 5
