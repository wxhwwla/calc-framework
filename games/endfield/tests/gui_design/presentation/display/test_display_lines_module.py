#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""display_lines 模块：无 PySide6 依赖、技能解析可导入。"""

import unittestfrom games.endfield.gui_design.presentation import display_linesclass TestDisplayLinesModule(unittest.TestCase):
    def test_module_has_no_customtkinter_import(self) -> None:
        from gui_design.presentation import display_lines as display_lines_impl

        source_path = display_lines_impl.__file__
        assert source_path
        text = open(source_path, encoding="utf-8").read()
        self.assertNotIn("customtkinter", text)

    def test_resolve_skill_returns_multiplier(self) -> None:
        char = {
            "战技倍率": [[200, 300]],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        skill = display_lines.resolve_selected_skill_for_damage(
            char,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertIn("战技", skill.label)
        self.assertAlmostEqual(skill.multiplier, 2.0)
        self.assertEqual(skill.warning, "该段伤害类型未收录，按物理伤害计算。")
        self.assertEqual(skill.damage_type, "物理")


if __name__ == "__main__":
    unittest.main()
