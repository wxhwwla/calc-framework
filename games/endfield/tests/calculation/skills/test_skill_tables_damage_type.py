#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""skill_tables 段伤害类型解析测试。"""

import unittest

from bwiki_scout.skill_tables import parse_skill_damage_rows_from_html, skill_tabs_to_seed_skills  # noqa: E402

from games.endfield.calc.damage.types import infer_segment_damage_type  # noqa: E402


class TestSkillTablesDamageType(unittest.TestCase):
    def test_infer_from_header_text(self) -> None:
        self.assertEqual(infer_segment_damage_type("灼热伤害倍率"), "法术-灼热")
        self.assertEqual(infer_segment_damage_type("伤害倍率"), "物理")

    def test_parse_row_damage_type_from_html(self) -> None:
        cells = "".join(f"<td>{v}%</td>" for v in range(142, 154))
        html = f"""
        <motion></motion>
        <div class="skill">
          <motion></motion>
          <div class="tab-content">
            <table class="wikitable">
              <tr><th>灼热伤害倍率</th>{cells}</tr>
            </table>
          </div>
        </div>
        """
        tabs = parse_skill_damage_rows_from_html(html)
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0][0].damage_type, "法术-灼热")
        self.assertEqual(len(tabs[0][0].curve), 12)
        seed = skill_tabs_to_seed_skills(tabs)
        self.assertEqual(seed["sk1_dt"], ["法术-灼热"])


if __name__ == "__main__":
    unittest.main()
