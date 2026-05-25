#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能搜索作业（无头）测试。"""

import unittest

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import WeaponCandidate
from calculation.single_skill_search_job import (
    build_weapon_candidates,
    prepare_single_skill_search_job,
)


class TestSingleSkillSearchJob(unittest.TestCase):
    def _char(self):
        return {
            "名称": "测试干员",
            "武器": "单手剑",
            "战技倍率": [[100] * 90],
            "基础攻击力": [100] * 90,
        }

    def _weapon(self, name: str, star: int = 5):
        return {
            "名称": name,
            "类型": "单手剑",
            "星级": star,
            "基础攻击力": [100] * 90,
        }

    def test_build_weapon_candidates_respects_current_weapon_scope(self):
        char = self._char()
        all_weapons = [self._weapon("A", 5), self._weapon("B", 4)]
        current = self._weapon("A", 5)
        candidates = build_weapon_candidates(
            all_weapons=all_weapons,
            char_data=char,
            current_weapon=current,
            weapon_scope_label="当前武器",
            char_level=1,
            weapon_level=1,
            trust_level=0,
        )
        self.assertEqual([c.name for c in candidates], ["A"])

    def test_prepare_job_returns_error_when_catalog_incomplete(self):
        job, err = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon("A")],
            current_weapon=self._weapon("A"),
            equipment_catalog={"chest": [], "gloves": [], "accessories": []},
        )
        self.assertIsNone(job)
        self.assertIn("装备", err or "")

    def test_prepare_job_builds_signature_and_context(self):
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": []}],
        }
        job, err = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.5,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon("A")],
            current_weapon=self._weapon("A"),
            equipment_catalog=catalog,
        )
        self.assertIsNone(err)
        assert job is not None
        self.assertEqual(job.skill_label, "战技")
        self.assertEqual(job.base_context.skill_multiplier, 1.5)
        self.assertEqual(len(job.run_signature), 16)
        self.assertEqual(len(job.weapon_candidates), 1)

    def test_prepare_job_honors_enemy_defense_parameter(self) -> None:
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": []}],
        }
        job, err = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon("A")],
            current_weapon=self._weapon("A"),
            equipment_catalog=catalog,
            enemy_defense=180.0,
        )
        self.assertIsNone(err)
        assert job is not None
        self.assertEqual(job.base_context.enemy_defense, 180.0)

    def test_run_signature_changes_when_spell_abnormal_counts_change(self) -> None:
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": []}],
        }
        job_a, err_a = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon("A")],
            current_weapon=self._weapon("A"),
            equipment_catalog=catalog,
            spell_abnormal_counts={"灼热爆发:1": 1},
        )
        job_b, err_b = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon("A")],
            current_weapon=self._weapon("A"),
            equipment_catalog=catalog,
            spell_abnormal_counts={"灼热爆发:1": 2},
        )
        self.assertIsNone(err_a)
        self.assertIsNone(err_b)
        assert job_a is not None and job_b is not None
        self.assertNotEqual(job_a.run_signature, job_b.run_signature)


if __name__ == "__main__":
    unittest.main()
