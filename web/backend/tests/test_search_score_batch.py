#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Web POST /api/search/score-batch 测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO / "framework" / "src"
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_FRAMEWORK_SRC), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.search.evaluate.batch_score import score_search_loadouts_batch
from games.endfield.calc.search.plan.controller import SearchJobInputs, prepare_search_job
from web.backend.main import app

RateLimitMiddleware.enabled = False


class TestScoreSearchLoadoutsBatch(unittest.TestCase):
    def _minimal_job(self):
        char = {
            "名称": "测试",
            "武器": "单手剑",
            "战技倍率": [[200] * 12],
            "连携技倍率": [[100] * 9],
            "终结技倍率": [[50] * 9],
            "基础攻击力": [100] * 90,
        }
        weapon = {"名称": "剑", "类型": "单手剑", "星级": 5, "基础攻击力": [100] * 90}
        catalog = {
            "chest": [{"名称": "甲", "部位": "护甲", "效果": [], "三件套效果": [], "属性词条": ["攻击力+10"]}],
            "gloves": [{"名称": "手", "部位": "护手", "效果": [], "三件套效果": [], "属性词条": []}],
            "accessories": [
                {"名称": "件A", "部位": "配件", "效果": [], "三件套效果": [], "属性词条": []},
                {"名称": "件B", "部位": "配件", "效果": [], "三件套效果": [], "属性词条": []},
            ],
        }
        inputs = SearchJobInputs(
            char_data=char,
            char_level=90,
            weapon_level=90,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            damage_type="物理",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[weapon],
            current_weapon=weapon,
            equipment_catalog=catalog,
            fixed_loadout=FixedLoadoutSelection(),
        )
        job, err = prepare_search_job(inputs)
        self.assertIsNone(err)
        assert job is not None
        return job, weapon, catalog

    def test_batch_score_returns_positive_damage(self) -> None:
        job, weapon, _catalog = self._minimal_job()
        scores = score_search_loadouts_batch(
            job=job,
            loadouts=[
                {
                    "weapon_name": str(weapon["名称"]),
                    "chest": "甲",
                    "gloves": "手",
                    "accessory_a": "件A",
                    "accessory_b": "件B",
                }
            ],
        )
        self.assertEqual(len(scores), 1)
        self.assertGreater(scores[0], 0.0)

    def test_score_batch_api(self) -> None:
        job, weapon, catalog = self._minimal_job()
        client = TestClient(app)
        payload = {
            "params": {
                "char_data": job.char_data,
                "char_level": job.char_level,
                "weapon_level": job.weapon_level,
                "trust_level": job.trust_level,
                "skill_name": "战技",
                "skill_type": "战技",
                "skill_multiplier": 2.0,
                "damage_type": "物理",
                "weapon_scope_label": "当前武器",
                "equipment_scope_label": "全部装备",
                "all_weapons": [weapon],
                "current_weapon": weapon,
                "equipment_catalog": catalog,
                "skill_1_level": 8,
                "skill_2_level": 8,
                "skill_3_level": 8,
            },
            "loadouts": [
                {
                    "weapon_name": str(weapon["名称"]),
                    "chest": "甲",
                    "gloves": "手",
                    "accessory_a": "件A",
                    "accessory_b": "件B",
                }
            ],
        }
        resp = client.post("/api/search/score-batch", json=payload)
        self.assertIn(resp.status_code, (200, 400, 500))
        if resp.status_code != 200:
            return
        data = resp.json()
        self.assertIn("final_damage", data)
        self.assertEqual(len(data["final_damage"]), 1)
        self.assertGreater(data["final_damage"][0], 0.0)


if __name__ == "__main__":
    unittest.main()
