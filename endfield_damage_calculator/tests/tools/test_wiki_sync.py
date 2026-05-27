#!/usr/bin/env python3
"""Wiki 数据同步到 characters.json / seed_characters 测试。"""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.fixtures.path_roots import REPO_ROOT

_RAW_QIULI = REPO_ROOT / "tools/bwiki_scout/output/raw/秋栗"
_RAW_QIULI_DETAIL = REPO_ROOT / "tools/bwiki_scout/output/raw/秋栗_详细数据"

from bwiki_scout.seed_persist import (  # noqa: E402
    _flatten_seed_list,
    load_seed_character_specs,
    replace_seed_specs,
    write_seed_character_specs,
)
from bwiki_scout.skill_tables import (  # noqa: E402
    parse_skill_damage_rows_from_html,
    skill_tabs_to_seed_skills,
    verify_skill_params,
)
from bwiki_scout.weapon_wiki import (  # noqa: E402
    build_weapon_seed_spec_from_wiki,
    fit_weapon_base_atk_from_endpoints,
    has_weapon_growth_block,
)
from bwiki_scout.wiki_sync import (  # noqa: E402
    build_seed_spec_from_wiki,
    fit_growth_params_from_curve,
    needs_sync_with_wiki,
)

from calculation.damage.formula import calculate_growth_curve  # noqa: E402

_RAW_ZHULIN = REPO_ROOT / "tools/bwiki_scout/output/raw/逐鳞3.0"
_RAW_JET = REPO_ROOT / "tools/bwiki_scout/output/raw/J.E.T"


class TestWikiSync(unittest.TestCase):
    def test_fit_growth_params_reproduces_known_formula_curve(self):
        params = {"base": 30, "growth": 13, "divisor": 4, "offset": 1}
        curve = calculate_growth_curve(**params)
        with redirect_stdout(io.StringIO()):
            fitted = fit_growth_params_from_curve(curve)
        rebuilt = calculate_growth_curve(**fitted)
        self.assertEqual(rebuilt, curve)

    @unittest.skipUnless(
        _RAW_QIULI.is_dir() and _RAW_QIULI_DETAIL.is_dir(),
        "需要 BWIKI 缓存 raw/秋栗 与 raw/秋栗_详细数据",
    )
    def test_build_seed_spec_from_cached_qiuli(self):
        main_wt = (_RAW_QIULI / "wikitext.txt").read_text(encoding="utf-8")
        detail_wt = (_RAW_QIULI_DETAIL / "wikitext.txt").read_text(encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            spec = build_seed_spec_from_wiki(
                name="秋栗",
                main_wikitext=main_wt,
                detail_wikitext=detail_wt,
                preserve_skills={"sk1": [], "sk2": [], "sk3": []},
            )
        self.assertEqual(spec["name"], "秋栗")
        self.assertEqual(spec["char_type"], "先锋")
        self.assertEqual(spec["star"], 4)
        self.assertEqual(spec["weapon"], "单手剑")
        rebuilt_atk = calculate_growth_curve(**spec["base_atk"])
        self.assertEqual(rebuilt_atk[0], 30)
        self.assertEqual(rebuilt_atk[-1], 319)

    @unittest.skipUnless(
        _RAW_QIULI_DETAIL.is_dir(),
        "需要 BWIKI 详细数据缓存",
    )
    def test_needs_sync_when_local_attack_differs(self):
        main_wt = (_RAW_QIULI / "wikitext.txt").read_text(encoding="utf-8")
        detail_wt = (_RAW_QIULI_DETAIL / "wikitext.txt").read_text(encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            spec = build_seed_spec_from_wiki(
                name="秋栗",
                main_wikitext=main_wt,
                detail_wikitext=detail_wt,
            )
        local = {
            "名称": "秋栗",
            "类型": "先锋",
            "星级": 4,
            "武器": "单手剑",
            "主能力": "敏捷",
            "副能力": "智识",
            "基础攻击力": [999] * 90,
            "等级": list(range(1, 91)),
            "力量": [0] * 90,
            "敏捷": [0] * 90,
            "智识": [0] * 90,
            "意志": [0] * 90,
        }
        self.assertTrue(needs_sync_with_wiki(spec, local))

    def test_write_and_load_seed_specs_roundtrip(self):
        spec = {
            "name": "测试干员",
            "char_type": "近卫",
            "star": 4,
            "primary": "力量",
            "secondary": "敏捷",
            "weapon": "单手剑",
            "strength": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "agility": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "intellect": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "will": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "base_atk": {"base": 30, "growth": 3, "divisor": 1, "offset": 0},
            "sk1": [],
            "sk2": [],
            "sk3": [],
        }
        header = (
            "# -*- coding: utf-8 -*-\n"
            "from character_weapon_equipment.character_data.add_character import add_character\n\n"
            "_SEED_CHARACTERS = [\n]\n\n\ndef main():\n    pass\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seed_characters.py"
            path.write_text(header, encoding="utf-8")
            write_seed_character_specs(path, [spec])
            loaded = load_seed_character_specs(path)
            self.assertEqual(loaded[0]["name"], "测试干员")

    def test_flatten_nested_seed_list(self):
        inner = [{"name": "秋栗", "star": 4}]
        self.assertEqual(_flatten_seed_list([inner])[0]["name"], "秋栗")

    @unittest.skipUnless(
        _RAW_QIULI.is_dir(),
        "需要 BWIKI 缓存 raw/秋栗",
    )
    def test_parse_qiuli_skill_damage_row_from_html(self):
        html = (_RAW_QIULI / "html.html").read_text(encoding="utf-8")
        tabs = parse_skill_damage_rows_from_html(html)
        self.assertGreaterEqual(len(tabs), 2)
        sk = skill_tabs_to_seed_skills(tabs)
        self.assertEqual(len(sk["sk1"]), 1)
        curve = verify_skill_params(sk["sk1"][0])
        self.assertEqual(curve[0], 142)
        self.assertEqual(curve[-1], 320)

    @unittest.skipUnless(
        _RAW_QIULI.is_dir() and _RAW_QIULI_DETAIL.is_dir(),
        "需要 BWIKI 秋栗主页与详细数据缓存",
    )
    def test_build_seed_spec_includes_skills_from_html(self):
        main_wt = (_RAW_QIULI / "wikitext.txt").read_text(encoding="utf-8")
        detail_wt = (_RAW_QIULI_DETAIL / "wikitext.txt").read_text(encoding="utf-8")
        html = (_RAW_QIULI / "html.html").read_text(encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            spec = build_seed_spec_from_wiki(
                name="秋栗",
                main_wikitext=main_wt,
                detail_wikitext=detail_wt,
                main_html=html,
            )
        self.assertEqual(verify_skill_params(spec["sk1"][0])[-1], 320)

    @unittest.skipUnless(
        _RAW_ZHULIN.is_dir(),
        "需要 BWIKI 缓存 raw/逐鳞3.0",
    )
    def test_build_weapon_seed_spec_from_cached_zhulin(self):
        wikitext = (_RAW_ZHULIN / "wikitext.txt").read_text(encoding="utf-8")
        self.assertTrue(has_weapon_growth_block(wikitext))
        with redirect_stdout(io.StringIO()):
            spec = build_weapon_seed_spec_from_wiki(name="逐鳞3.0", wikitext=wikitext)
        rebuilt = calculate_growth_curve(**spec["base_atk"])
        self.assertEqual(rebuilt[0], 42)
        self.assertEqual(rebuilt[-1], 411)
        self.assertIn("力量+", spec["bonus_attrs"])
        self.assertIn("寒冷伤害+", spec["bonus_attrs"])
        self.assertIn("攻击力+", spec["bonus_attrs"])
        self.assertIn("攻击力+", spec["bonus_attrs"])
        self.assertEqual(spec["special_1"]["name"], "目标受到的寒冷伤害+")
        self.assertTrue(spec["special_1"]["enabled"])

    @unittest.skipUnless(
        _RAW_JET.is_dir(),
        "需要 BWIKI 缓存 raw/J.E.T",
    )
    def test_jet_slot3_unconditional_is_third_bonus_conditional_is_special(self):
        """词条3：副1 为第三技能；副2+ 为特殊能力（非副1）。"""
        wikitext = (_RAW_JET / "wikitext.txt").read_text(encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            spec = build_weapon_seed_spec_from_wiki(name="J.E.T.", wikitext=wikitext)
        self.assertIn("法术伤害+", spec["bonus_attrs"])
        self.assertEqual(spec["special_2"]["name"], "施放连携技后，法术伤害+")
        self.assertTrue(spec["special_2"]["enabled"])
        self.assertEqual(spec["special_1"]["name"], "施放战技后，法术伤害+")

    def test_fit_weapon_base_atk_preserves_shape_with_reference(self):
        ref = list(range(100, 190))
        with redirect_stdout(io.StringIO()):
            params = fit_weapon_base_atk_from_endpoints(50, 500, reference_curve=ref)
        rebuilt = calculate_growth_curve(**params)
        self.assertEqual(rebuilt[0], 50)
        self.assertEqual(rebuilt[-1], 500)

    def test_replace_seed_character_specs_updates_one(self):
        old = {
            "name": "秋栗",
            "star": 3,
            "char_type": "先锋",
            "primary": "敏捷",
            "secondary": "智识",
            "weapon": "单手剑",
            "strength": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "agility": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "intellect": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "will": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "base_atk": {"base": 1, "growth": 1, "divisor": 1, "offset": 0},
            "sk1": [],
            "sk2": [],
            "sk3": [],
        }
        new = dict(old)
        new["star"] = 4
        merged = replace_seed_specs([old], {"秋栗": new}, admin_first=True)
        self.assertEqual(merged[0]["star"], 4)


if __name__ == "__main__":
    unittest.main()
