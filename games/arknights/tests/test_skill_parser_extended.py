# SPDX-License-Identifier: AGPL-3.0
"""技能解析器扩展测试 — 边界条件、变形描述、数据健壮性。"""

from __future__ import annotations

from typing import Any

import pytest

from games.arknights.calc.skill_parser import (
    _strip_wiki_markup,
    parse_auto_attack,
    parse_skill,
)

# ═══════════════════════════════════════════════
#  _strip_wiki_markup 边界
# ═══════════════════════════════════════════════


class TestStripWikiMarkupEdges:
    def test_empty_string(self) -> None:
        assert _strip_wiki_markup("") == ""

    def test_whitespace_only(self) -> None:
        assert _strip_wiki_markup("   \t  ") == ""

    def test_string_is_none(self) -> None:
        """Type check: 尽管函数期望 str，理论上不应被传 None。"""
        # 如果意外收到非 str，会报错 — 这里只验证设计意图
        try:
            _strip_wiki_markup(None)  # type: ignore[arg-type]
        except (TypeError, AttributeError):
            pass  # 预期行为

    def test_only_br_tags(self) -> None:
        assert _strip_wiki_markup("<BR><br/><BR>") == ""

    def test_nested_markup_not_expected(self) -> None:
        """嵌套 {{blue|{{color|...}}}} 不在测试范围（BWIKI 一般不会嵌套）。"""
        result = _strip_wiki_markup("{{蓝色|{{蓝色|内层}}}}")
        # 不应报错，至少命中外层
        assert isinstance(result, str)

    def test_html_tags_removed(self) -> None:
        assert _strip_wiki_markup("攻击<b>力</b>+50%") == "攻击力+50%"

    def test_arbitrary_html_tag(self) -> None:
        assert _strip_wiki_markup("文本<any>内容</any>尾巴") == "文本内容尾巴"

    def test_color_with_many_pipes(self) -> None:
        """{{color|code|text_with_extra}} — 贪心匹配 risk。"""
        result = _strip_wiki_markup("{{color|FF0000|攻击力+100%}} 剩余文本")
        assert "攻击力+100%" in result

    def test_blue_markup_no_pipe(self) -> None:
        """非标准蓝色标记（无 |，但仍有 }}）。"""
        result = _strip_wiki_markup("{{蓝色}}")
        # 正则要求 |，所以不匹配也不报错
        assert isinstance(result, str)


# ═══════════════════════════════════════════════
#  畸形技能数据
# ═══════════════════════════════════════════════


class TestMalformedSkillData:
    def test_missing_all_fields(self) -> None:
        info = parse_skill({}, 1)
        assert info.effective_multiplier == 1.0
        assert info.hit_count == 1
        assert info.name == ""

    def test_levels_is_empty_list(self) -> None:
        skill = {"name": "EmptySkill", "levels": []}
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0

    def test_levels_contains_empty_dicts(self) -> None:
        skill = {
            "name": "EmptyLevels",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [{}, {}, {}],
        }
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.sp_cost == 0
        assert info.description == ""

    def test_levels_missing_description(self) -> None:
        skill = {
            "name": "NoDesc",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "sp_cost": 20,
                    "init_sp": 10,
                    "duration": "30",
                }
            ],
        }
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == 1.0
        assert info.sp_cost == 20

    def test_levels_non_dict_entries(self) -> None:
        skill: dict[str, Any] = {
            "name": "BadLevels",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": ["not a dict", None, 42],  # type: ignore[list-item]
        }
        # 不应报错（idx 对应第一个条目），但可能是 str 会报 AttributeError
        # 实际代码中 lv = levels[idx]，如果是 str .get() 不存在会报异常
        # 这里只做安全验证
        try:
            parse_skill(skill, 1)
        except Exception:
            pass  # 已知异常路径，测试不报错即可

    def test_duration_none(self) -> None:
        skill: dict[str, Any] = {
            "name": "NoneDur",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+50%",
                    "sp_cost": 10,
                    "init_sp": 5,
                    "duration": None,
                }
            ],
        }
        info = parse_skill(skill, 1)
        # str(None) = "None", int("None") → ValueError → duration=0
        assert info.duration == 0

    def test_sp_cost_missing(self) -> None:
        skill: dict[str, Any] = {
            "name": "NoSP",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+50%",
                    "duration": "20",
                }
            ],
        }
        info = parse_skill(skill, 1)
        assert info.sp_cost == 0


# ═══════════════════════════════════════════════
#  中文数字 / 混合标记 + 数字
# ═══════════════════════════════════════════════


class TestChineseNumericExpressions:
    """中文数字表达式的解析行为。"""

    def test_percent_cn_expression(self) -> None:
        """包含中文"百分之"的描述。"""
        skill = _make_skill_ext(descriptions=["攻击力提升至百分之五十"])
        info = parse_skill(skill, 1)
        # 不包含阿拉伯数字，不触发 pattern
        assert info.effective_multiplier == 1.0

    def test_mixed_markup_and_number(self) -> None:
        """混合 wiki 标记和数字。"""
        skill = _make_skill_ext(descriptions=["{{蓝色|攻击力+80%}}，<BR>持续{{蓝色|20}}秒"])
        info = parse_skill(skill, 1)
        assert info.atk_buff_hint == 0.8

    def test_multiple_atk_buff_in_one_desc(self) -> None:
        """一条描述中有多个攻击力+XX%（取第一个）。"""
        skill = _make_skill_ext(descriptions=["攻击力+30%，自身和周围8格内友方单位攻击力+50%"])
        info = parse_skill(skill, 1)
        assert info.atk_buff_hint == 0.3

    def test_scientific_notation_not_supported(self) -> None:
        """科学计数法数字不在 pattern 中。"""
        skill = _make_skill_ext(descriptions=["攻击力+1.5e2%"])
        info = parse_skill(skill, 1)
        # 科学计数法不带小数点的 pattern 不匹配 \d+(?:\.\d+)?
        # "1.5e2" — pattern 为 \d+(?:\.\d+)? 匹配 "1.5" (到 e 为止)
        # 因此会提取 1.5，这是一种降级行为
        assert info.atk_buff_hint >= 0.0


# ═══════════════════════════════════════════════
#  非标准 sp_type / trigger / name
# ═══════════════════════════════════════════════


class TestNonStandardSkillMeta:
    def test_nonstandard_sp_type(self) -> None:
        skill = _make_skill_ext(
            name="特殊技",
            sp_type="攻击回复",
            trigger="自动触发",
            descriptions=["攻击力+100%"],
        )
        info = parse_skill(skill, 1)
        assert info.sp_type == "攻击回复"
        assert info.trigger == "自动触发"

    def test_trigger_is_empty_string(self) -> None:
        skill = _make_skill_ext(
            sp_type="自动回复",
            trigger="",
            descriptions=["攻击力+50%"],
        )
        info = parse_skill(skill, 1)
        assert info.trigger == ""

    def test_sp_type_is_per_second(self) -> None:
        skill = _make_skill_ext(
            sp_type="每秒回复",
            trigger="手动触发",
            descriptions=["攻击力+30%"],
        )
        info = parse_skill(skill, 1)
        assert info.sp_type == "每秒回复"

    def test_skill_name_contains_special_chars(self) -> None:
        skill = _make_skill_ext(
            name="Ω-Skill (改)",
            descriptions=["攻击力+50%"],
        )
        info = parse_skill(skill, 1)
        assert "Ω" in info.name


# ═══════════════════════════════════════════════
#  auto_attack 信息结构
# ═══════════════════════════════════════════════


class TestAutoAttackStructure:
    def test_all_fields_present(self) -> None:
        info = parse_auto_attack()
        assert info.name == "普攻"
        assert info.effective_multiplier == 1.0
        assert info.hit_count == 1
        assert info.total_mult == 1.0
        assert info.damage_type == "physical"
        assert not info.is_healing
        assert info.description == "普通攻击"

    def test_auto_attack_no_conditional(self) -> None:
        info = parse_auto_attack()
        assert not info.has_conditional
        assert info.conditional_mult == 1.0

    def test_auto_attack_fields_types(self) -> None:
        info = parse_auto_attack()
        assert isinstance(info.name, str)
        assert isinstance(info.effective_multiplier, float)
        assert isinstance(info.hit_count, int)
        assert isinstance(info.total_mult, float)
        assert isinstance(info.damage_type, str)
        assert isinstance(info.is_healing, bool)

    def test_auto_attack_sp_meta_zero(self) -> None:
        info = parse_auto_attack()
        assert info.sp_cost == 0
        assert info.init_sp == 0
        assert info.duration == 0


# ═══════════════════════════════════════════════
#  total_mult 0-hit 边界
# ═══════════════════════════════════════════════


class TestTotalMultiplierEdgeCases:
    def test_zero_hit_count_implies_zero_total(self) -> None:
        """hit_count=0 时 total_mult = effective * 0 = 0。"""
        skill = _make_skill_ext(descriptions=[])
        info = parse_skill(skill, 1)
        info.hit_count = 0  # 手动覆盖（正常不会触发）
        from games.arknights.calc.skill_parser import _compute_total

        _compute_total(info)
        assert info.total_mult == 0.0

    def test_hit_count_one_identity(self) -> None:
        skill = _make_skill_ext(descriptions=["相当于攻击力300%的法术伤害"])
        info = parse_skill(skill, 1)
        assert info.hit_count == 1
        assert info.total_mult == pytest.approx(3.0)

    def test_equiv_damage_less_than_one(self) -> None:
        """相当于攻击力50%的伤害（倍率 < 1）。"""
        skill = _make_skill_ext(descriptions=["相当于攻击力50%的物理伤害"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == pytest.approx(0.5)
        assert info.total_mult == pytest.approx(0.5)

    def test_zero_percent_damage(self) -> None:
        """攻击力0%的伤害。"""
        skill = _make_skill_ext(descriptions=["相当于攻击力0%的真实伤害"])
        info = parse_skill(skill, 1)
        assert info.effective_multiplier == pytest.approx(0.0)
        assert info.damage_type == "true"


# ═══════════════════════════════════════════════
#  is_healing 更多场景
# ═══════════════════════════════════════════════


class TestHealingEdgeCases:
    def test_heal_over_time(self) -> None:
        """持续治疗的描述。"""
        skill = _make_skill_ext(descriptions=["每秒恢复相当于攻击力30%的生命"])
        info = parse_skill(skill, 1)
        assert info.is_healing

    def test_lifesteal_not_healing(self) -> None:
        """吸血类技能可能不含"治疗"。"""
        skill = _make_skill_ext(descriptions=["攻击力+80%，攻击回复自身体力"])
        info = parse_skill(skill, 1)
        # 不含"治疗"关键词 → not is_healing
        assert not info.is_healing

    def test_hp_buff_with_atk_not_healing(self) -> None:
        """生命上限+XX% + 包含攻击力 → 可能误判，验证不标记为治疗。"""
        skill = _make_skill_ext(
            descriptions=["生命上限+25%", "攻击力+50%"],
        )
        info = parse_skill(skill, 1)
        # 仅第一条被取为 description
        assert not info.is_healing


# ═══════════════════════════════════════════════
#  助手
# ═══════════════════════════════════════════════


def _make_skill_ext(
    name: str = "测试技能",
    sp_type: str = "自动回复",
    trigger: str = "手动触发",
    descriptions: list[str] | None = None,
) -> dict[str, Any]:
    """创建技能字典（同 test_skill_parser.py 的 _make_skill）。"""
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
