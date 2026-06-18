#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""确认刷新去重逻辑测试。"""

import unittest

from games.endfield.gui.app.confirm_refresh import (
    build_confirm_refresh_signature,
    skill_count_commit_changed,
)


class TestConfirmRefresh(unittest.TestCase):
    def test_skill_count_focus_out_without_edit_is_no_op(self):
        normalized, changed = skill_count_commit_changed("2", "2")

        self.assertEqual(normalized, "2")

        self.assertFalse(changed)

    def test_skill_count_edit_triggers_change(self):
        normalized, changed = skill_count_commit_changed("3", "2")

        self.assertEqual(normalized, "3")

        self.assertTrue(changed)

    def test_signature_stable_for_same_inputs(self):
        kwargs = dict(
            calculation_mode="zone_snapshot",
            char_name="A",
            char_level=90,
            weapon_name="W",
            weapon_level=90,
            trust_level=4,
            skill_levels=(10, 10, 10),
            weapon_specials=("敏捷+", 9, "", 0, "", 0, "", 0, "", 0),
            use_manual_multi_skill_counts=False,
            multi_skill_manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            preview_scope_label="当前武器",
            preview_equipment_scope_label="全部装备",
            fixed_loadout_token="empty",
        )

        self.assertEqual(
            build_confirm_refresh_signature(**kwargs),  # type: ignore[arg-type]
            build_confirm_refresh_signature(**kwargs),  # type: ignore[arg-type]
        )


if __name__ == "__main__":
    unittest.main()
