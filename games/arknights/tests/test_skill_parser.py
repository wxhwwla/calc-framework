# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""测试 skill_parser — 技能倍率/连发数/条件/治疗/伤害类型解析。"""

from __future__ import annotations

from typing import Any

import pytest

from games.arknights.calc.skill_parser import (
    _strip_wiki_markup,
    parse_auto_attack,
    parse_skill,
)

# ═══════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════


def _make_skill(
    name: str = "测试技能",
    sp_type: str = "自动回复",
    trigger: str = "手动触发",
    descriptions: list[str] | None = None,
) -> dict[str, Any]:
    """创建技能字典用于测试。"""
    if descriptions is None:
        descriptions = ["攻击力+50%"]
    return {
        "name": name,
        "sp_type": sp_type,
        "trigger": trigger,
        "levels": [
            {
                "description": d,
                "sp_cost": 10 + i * 2,
                "init_sp": 5 + i,
                "duration": f"{20 + i * 2}",
            }
            for i, d in enumerate(descriptions)
        ],
    }


# ═══════════════════════════════════════════════
#  _strip_wiki_markup
# ═══════════════════════════════════════════════


class TestStripWikiMarkup:
    def test_blue_markup(self) -> None:
        assert _strip_wiki_markup("{{蓝色|攻击力+100%}}") == "攻击力+100%"

    def test_color_markup(self) -> None:
        assert _strip_wiki_markup("{{color|0098DC|攻击力+100%}}") == "攻击力+100%"

    def test_br_tag(self) -> None:
        assert _strip_wiki_markup("行1<BR>行2") == "行1 行2"

    def test_multiline_br(self) -> None:
        assert _strip_wiki_markup("A<br/>B<br/>C") == "A B C"

    def test_mixed_markup(self) -> None:
        raw = "攻击力+{{蓝色|80%}}，<BR>防御力-{{color|FF0000|30%}}"
        result = _strip_wiki_markup(raw)
        assert result == "攻击力+80%， 防御力-30%"

    def test_no_markup(self) -> None:
        text = "普通攻击"
        assert _strip_wiki_markup(text) == text


# ═══════════════════════════════════════════════
#  parse_auto_attack
# ═══════════════════════════════════════════════


class TestParseAutoAttack:
    def test_returns_defaults(self) -> None:
        info = parse_auto_attack()
        assert info.name == "普攻"
        assert info.effective_multiplier == 1.0
        assert info.hit_count == 1
        assert not info.is_healing
        assert info.damage_type == "physical"
        assert info.description == "普通攻击"


# ═══════════════════════════════════════════════
#  parse_skill — 倍率模式
# ═══════════════════════════════════════════════


class TestSkillMultiplierPatterns:
    """测试各种倍率描述模式的提取。"""

    def test_atk_buff_percent(self) -> None:
        """攻击力+XX% → 1.0x + atk_buff_hint"""
        skill = _make_skill(descriptions=["攻击力+80%"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 0.8

    def test_atk_buff_max_level(self) -> None:
        """攻击力+200% (Lv.10)"""
        skill = _make_skill(descriptions=[f"攻击力+{v}%" for v in [100, 120, 140, 160, 180, 200, 220, 240, 260, 280]])
        info = parse_skill(skill, 10)
        assert info.atk_buff_hint == 2.8

    def test_direct_atk_set(self) -> None:
        """攻击力提升至XX% → direct_atk_mult = XX/100"""
        skill = _make_skill(descriptions=["攻击力提升至190%"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.9
        assert info._direct_atk_mult == 1.9

    def test_equiv_damage(self) -> None:
        """相当于攻击力XX%的伤害 → equiv_damage_mult = XX/100"""
        skill = _make_skill(descriptions=["相当于攻击力230%的物理伤害"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 2.3

    def test_equiv_damage_with_color(self) -> None:
        """带颜色标记的相当于攻击力XX%"""
        skill = _make_skill(descriptions=["造成相当于攻击力{{蓝色|230%}}的物理伤害"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 2.3

    def test_pct_of_atk(self) -> None:
        """攻击力XX%的 (variant)"""
        skill = _make_skill(descriptions=["攻击力33%的6连发"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == pytest.approx(0.33, abs=0.01)

    def test_aspeed_only(self) -> None:
        """纯攻速技能 → 1.0x"""
        skill = _make_skill(descriptions=["攻击速度+30"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 0.0


# ═══════════════════════════════════════════════
#  parse_skill — 连发数
# ═══════════════════════════════════════════════


class TestHitCount:
    def test_standard_rapid_fire(self) -> None:
        """N连发"""
        skill = _make_skill(descriptions=["攻击力33%的6连发"])
        info = parse_skill(skill, 1)
        assert info.hit_count == 6

    def test_shots(self) -> None:
        """N次射击"""
        skill = _make_skill(descriptions=["相当于攻击力105%的3次射击"])
        info = parse_skill(skill, 1)
        assert info.hit_count == 3
        assert info.effective_multiplier == pytest.approx(1.05, abs=0.01)

    def test_consecutive_attacks(self) -> None:
        """连续攻击N次"""
        skill = _make_skill(descriptions=["连续攻击5次，每次造成攻击力200%的伤害"])
        info = parse_skill(skill, 1)
        assert info.hit_count == 5

    def test_single_hit_default(self) -> None:
        """默认 1 段"""
        skill = _make_skill(descriptions=["攻击力+100%"])
        info = parse_skill(skill, 1)
        assert info.hit_count == 1


# ═══════════════════════════════════════════════
#  parse_skill — 条件触发
# ═══════════════════════════════════════════════


class TestConditional:
    def test_conditional_detected(self) -> None:
        """仅攻击到一人时提升至XX%"""
        skill = _make_skill(descriptions=["攻击力+50%，攻击距离+1，仅攻击到一个敌人时对其攻击力提升至140%"])
        info = parse_skill(skill, 1)
        assert info.has_conditional
        assert info.conditional_mult == 1.4

    def test_conditional_not_set(self) -> None:
        """无条件技能"""
        skill = _make_skill(descriptions=["攻击力提升至240%"])
        info = parse_skill(skill, 1)
        assert not info.has_conditional
        assert info.conditional_mult == 1.0


# ═══════════════════════════════════════════════
#  parse_skill — 伤害类型 & 治疗
# ═══════════════════════════════════════════════


class TestDamageTypeAndHealing:
    def test_physical_damage(self) -> None:
        skill = _make_skill(descriptions=["相当于攻击力230%的物理伤害"])
        info = parse_skill(skill, 1)
        assert info.damage_type == "physical"

    def test_magical_damage(self) -> None:
        skill = _make_skill(descriptions=["相当于攻击力130%的法术伤害"])
        info = parse_skill(skill, 1)
        assert info.damage_type == "magical"

    def test_true_damage(self) -> None:
        skill = _make_skill(descriptions=["相当于攻击力100%的真实伤害"])
        info = parse_skill(skill, 1)
        assert info.damage_type == "true"

    def test_true_damage_blue_label(self) -> None:
        skill = _make_skill(descriptions=["{{蓝色|真实}}伤害，攻击力+50%"])
        info = parse_skill(skill, 1)
        assert info.damage_type == "true"

    def test_healing_skill(self) -> None:
        """「治疗」+「攻击力」标记为治疗"""
        skill = _make_skill(descriptions=["相当于攻击力110%的生命"])
        info = parse_skill(skill, 1)
        assert info.is_healing

    def test_aspeed_skill_not_healing(self) -> None:
        """攻速技能不应标记为治疗"""
        skill = _make_skill(descriptions=["攻击速度+30"])
        info = parse_skill(skill, 1)
        assert not info.is_healing

    def test_hp_buff_not_healing(self) -> None:
        """「生命上限+XX%」不应标记为治疗"""
        skill = _make_skill(descriptions=["生命上限+25%，攻击范围扩大"])
        info = parse_skill(skill, 1)
        assert not info.is_healing

    def test_healing_via_treatment_explicit(self) -> None:
        """「治疗」+「攻击力」路径触发 line 97（非 regex 匹配）"""
        skill = _make_skill(descriptions=["攻击力+50%\n治疗友方单位"])
        info = parse_skill(skill, 1)
        assert info.is_healing
        assert info.effective_multiplier == 1.0


# ═══════════════════════════════════════════════
#  parse_skill — SP / Duration
# ═══════════════════════════════════════════════


class TestSkillMeta:
    def test_sp_cost(self) -> None:
        skill = _make_skill(descriptions=["攻击力+50%", "攻击力+80%"])
        info = parse_skill(skill, 2)
        assert info.sp_cost == 12
        assert info.init_sp == 6

    def test_duration_parsed(self) -> None:
        skill = _make_skill(descriptions=["攻击力+50%", "攻击力+80%"])
        info = parse_skill(skill, 2)
        assert info.duration == 22

    def test_level_out_of_range_high(self) -> None:
        """超过 10 级 → 取最大值"""
        skill = _make_skill(descriptions=[f"攻击力+{i * 10}%" for i in range(1, 11)])
        info = parse_skill(skill, 99)
        assert info.atk_buff_hint == 1.0

    def test_level_out_of_range_low(self) -> None:
        """等级 < 1 → 取最小值"""
        skill = _make_skill(descriptions=["攻击力+50%", "攻击力+80%"])
        info = parse_skill(skill, -1)
        assert info.atk_buff_hint == 0.5

    def test_no_levels(self) -> None:
        """空 levels → 默认值"""
        skill = _make_skill(descriptions=[])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0

    def test_non_numeric_duration_fallback(self) -> None:
        """非数值 duration → 降级为 0"""
        skill: dict[str, Any] = {
            "name": "测试",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+50%",
                    "sp_cost": 10,
                    "init_sp": 5,
                    "duration": "—",
                }
            ],
        }
        info = parse_skill(skill, 1)
        assert info.duration == 0
        assert info.atk_buff_hint == 0.5


# ═══════════════════════════════════════════════
#  parse_skill — 组合场景（真实运营商）
# ═══════════════════════════════════════════════


class TestRealOperatorScenarios:
    """模拟真实干员技能组合。"""

    def test_amiya_chimera_true_damage(self) -> None:
        """奇美拉：攻击力+100%，真实伤害"""
        skill = _make_skill(
            name="奇美拉",
            descriptions=["攻击力+100%，攻击范围扩大，伤害类型变为{{蓝色|真实}}"],
        )
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 1.0
        assert info.damage_type == "true"
        assert not info.is_healing

    def test_amiya_spirit_burst_rapid_fire(self) -> None:
        """精神爆发：攻击力33%的6连发"""
        skill = _make_skill(
            name="精神爆发",
            descriptions=["攻击力{{蓝色|33%}}的6连发"],
        )
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == pytest.approx(0.33, abs=0.01)
        assert info.hit_count == 6
        assert info.total_mult == pytest.approx(1.98, abs=0.01)

    def test_surtr_flame_sword_direct(self) -> None:
        """烈焰魔剑：攻击力提升至240%"""
        skill = _make_skill(
            name="烈焰魔剑",
            descriptions=["下次攻击的攻击力提升至{{蓝色|240%}}，如果将目标击倒则立即恢复所有技力"],
        )
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == pytest.approx(2.4, abs=0.01)
        assert not info.is_healing

    def test_surtr_twilight_buff(self) -> None:
        """黄昏：攻击力+240%，生命上限+5000（不标记为治疗）"""
        skill = _make_skill(
            name="黄昏",
            descriptions=["攻击力+240%，生命上限+5000，防御力+200，逐渐失去生命"],
        )
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 2.4
        assert not info.is_healing

    def test_surtr_molten_giant_conditional(self) -> None:
        """熔核巨影：攻击力+80% + 条件触发"""
        skill = _make_skill(
            name="熔核巨影",
            descriptions=["攻击力+80%，攻击距离+1，攻击目标数+1，仅攻击到一个敌人时对其攻击力提升至150%"],
        )
        info = parse_skill(skill, 1)
        assert info.atk_buff_hint == 0.8
        assert info.has_conditional
        assert info.conditional_mult == 1.5
        assert info._direct_atk_mult == 1.0  # 条件内的提升至不应被提取为直接设值

    def test_silverash_true_slash_buff(self) -> None:
        """真银斩：攻击力+200%，防御力-70%"""
        skill = _make_skill(
            name="真银斩",
            descriptions=["攻击力+200%，防御力-70%，攻击范围扩大"],
        )
        info = parse_skill(skill, 1)
        assert info.atk_buff_hint == 2.0
        assert info.effective_multiplier == 1.0

    def test_blue_poison_proliferation_rapid(self) -> None:
        """能天使过载模式：攻击速度+XX"""
        skill = _make_skill(
            name="过载模式",
            descriptions=["攻击速度+45，攻击力提升至110%"],
        )
        info = parse_skill(skill, 1)
        # 包含攻速 AND 攻击力提升至 → 应提取 direct_atk
        assert info.effective_multiplier == pytest.approx(1.1, abs=0.01)

    def test_angelina_true_nova(self) -> None:
        """W 红桃K：相当于攻击力270%的物理伤害（Lv.10）"""
        skill = _make_skill(
            name="红桃K",
            descriptions=[
                "相当于攻击力230%的物理伤害",
                "相当于攻击力240%的物理伤害",
                "相当于攻击力250%的物理伤害",
                "相当于攻击力260%的物理伤害",
                "相当于攻击力270%的物理伤害",
                "相当于攻击力290%的物理伤害",
                "相当于攻击力310%的物理伤害",
                "相当于攻击力330%的物理伤害",
                "相当于攻击力340%的物理伤害",
                "相当于攻击力350%的物理伤害",
            ],
        )
        info = parse_skill(skill, 10)
        assert info.effective_multiplier == pytest.approx(3.5, abs=0.01)
        assert info.damage_type == "physical"


# ═══════════════════════════════════════════════
#  total_mult 计算
# ═══════════════════════════════════════════════


class TestTotalMultiplier:
    def test_single_strike(self) -> None:
        skill = _make_skill(descriptions=["攻击力提升至300%"])
        info = parse_skill(skill, 1)
        assert info.total_mult == 3.0

    def test_multi_strike(self) -> None:
        skill = _make_skill(descriptions=["攻击力200%的3连发"])
        info = parse_skill(skill, 1)
        assert info.total_mult == 6.0  # 2.0 * 3

    def test_rapid_fire_total(self) -> None:
        skill = _make_skill(descriptions=["攻击力33%的6连发"])
        info = parse_skill(skill, 1)
        assert info.total_mult == pytest.approx(1.98, abs=0.01)

    def test_auto_attack_total(self) -> None:
        info = parse_auto_attack()
        assert info.total_mult == 1.0
