# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""手动 Buff 模型的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations


class TestManualBuffModel:
    """ManualBuffEntry, empty_buff_dict, get/set_buffs_for_key."""

    def test_manual_buff_entry_creation(self):
        from games.endfield.calc.manual_buff.model import ManualBuffEntry

        entry = ManualBuffEntry(effect_type="暴击率", value=0.10)
        assert entry.effect_type == "暴击率"
        assert entry.value == 0.10

    def test_empty_buff_dict(self):
        from games.endfield.calc.manual_buff.model import empty_buff_dict

        d = empty_buff_dict()
        assert d == {}

    def test_get_buffs_for_key_empty(self):
        from games.endfield.calc.manual_buff.model import get_buffs_for_key

        result = get_buffs_for_key({}, "暴击率")
        assert result == []

    def test_set_and_get_buffs(self):
        from games.endfield.calc.manual_buff.model import get_buffs_for_key, set_buffs_for_key

        store = {}
        set_buffs_for_key(store, "暴击率", [{"effect_type": "暴击率", "value": 0.10}])
        result = get_buffs_for_key(store, "暴击率")
        assert len(result) == 1
        assert result[0]["value"] == 0.10

    def test_set_buffs_empty_removes_key(self):
        from games.endfield.calc.manual_buff.model import set_buffs_for_key

        store = {"暴击率": [{"effect_type": "暴击率", "value": 0.10}]}
        set_buffs_for_key(store, "暴击率", [])
        assert "暴击率" not in store

    def test_build_active_keys_skills_only(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 2, "终结技": 1},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        assert set(keys) == {"战技:1", "战技:2", "终结技:1"}

    def test_build_active_keys_skills_ordered(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"终结技": 1, "战技": 2, "连携技": 3},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        # All expected keys should be present (order may depend on dict insertion)
        expected = {"战技:1", "战技:2", "连携技:1", "连携技:2", "连携技:3", "终结技:1"}
        assert set(keys) == expected

    def test_build_active_keys_zero_counts_skipped(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 0, "终结技": 2},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        assert "战技:" not in str(keys)
        assert "终结技:1" in keys

    def test_build_active_keys_with_physical_abnormal(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={},
            physical_abnormal_counts={"燃烧": 2},
            spell_abnormal_counts={},
        )
        assert "燃烧:1" in keys
        assert "燃烧:2" in keys

    def test_build_active_keys_with_spell_abnormal(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={},
            physical_abnormal_counts={},
            spell_abnormal_counts={"冰冻": 1},
        )
        assert "冰冻:1" in keys

    def test_build_active_keys_mixed_all(self):
        from games.endfield.calc.manual_buff.model import build_active_keys_from_counts

        keys = build_active_keys_from_counts(
            skill_counts={"战技": 1},
            physical_abnormal_counts={"燃烧": 1},
            spell_abnormal_counts={"冰冻": 1},
        )
        assert "战技:1" in keys
        assert "燃烧:1" in keys
        assert "冰冻:1" in keys
