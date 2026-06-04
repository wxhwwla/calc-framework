# SPDX-License-Identifier: AGPL-3.0
"""测试 adapter.py — get_parsed_skill_info。"""

from __future__ import annotations

from typing import Any

from games.arknights.calc.dag_adapter.adapter import get_parsed_skill_info


def _make_operator(skills: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "测试干员",
        "职业": "狙击",
    }
    if skills is not None:
        data["技能"] = skills
    return data


class TestGetParsedSkillInfo:
    def test_skill_index_negative_returns_auto_attack(self) -> None:
        """skill_index < 0 → 返回普攻（倍率 1.0，物理，1 段）"""
        op = _make_operator()
        info = get_parsed_skill_info(op, skill_index=-1)
        assert info.effective_multiplier == 1.0
        assert info.damage_type == "physical"
        assert info.hit_count == 1
        assert not info.is_healing

    def test_skill_index_out_of_range_returns_auto_attack(self) -> None:
        """skill_index >= len(skills) → 返回普攻"""
        op = _make_operator(skills=[])
        info = get_parsed_skill_info(op, skill_index=0)
        assert info.effective_multiplier == 1.0
        assert info.damage_type == "physical"

    def test_skill_index_valid_returns_parsed_skill(self) -> None:
        """skill_index 在范围内 → 正常解析技能"""
        skill = {
            "name": "战术咏唱",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+50%",
                    "sp_cost": 10,
                    "init_sp": 5,
                    "duration": "20",
                }
            ],
        }
        op = _make_operator(skills=[skill])
        info = get_parsed_skill_info(op, level=7, skill_index=0)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 0.5
        assert info.sp_cost == 10
        assert info.duration == 20
