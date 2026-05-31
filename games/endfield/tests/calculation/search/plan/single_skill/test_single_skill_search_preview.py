#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单技能遍历快速预览文案测试。"""

import jsonimport osimport unittestfrom pathlib import Pathimport pytestfrom games.endfield.calc.loadout.optimizer import WeaponCandidatefrom games.endfield.data_loading.equipment_catalog import get_equipment_catalogfrom games.endfield.gui_design.presentation.preview_lines import build_single_skill_search_preview_linesfrom games.endfield.tests.conftest import DATA_DIR_CHARACTERS_JSON = DATA_DIR / "characters.json"
_WEAPONS_JSON = DATA_DIR / "weapons.json"


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


def _sample_catalog() -> dict:
    def row(n, slot):
        return {
            "名称": n,
            "装备种类": slot,
            "部位": slot,
            "套装": "",
            "效果": [],
            "三件套效果": [],
        }

    return {
        "chest": [row("胸甲A", "护甲")],
        "gloves": [row("护手A", "护手")],
        "accessories": [row("配件A", "配件")],
    }


class TestSingleSkillSearchPreview(unittest.TestCase):
    def test_preview_lines_include_top_result(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any(line.startswith("计算模式: 单技能遍历(快速预览)") for line in lines))
        self.assertTrue(any(line.startswith("预览组合数:") for line in lines))
        self.assertTrue(any(line.startswith("第1名:") for line in lines))

    def test_preview_lines_respect_candidate_scope_and_weapon_list(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_weapon_candidates=[
                WeaponCandidate(name="候选A", final_attack=1000.0),
                WeaponCandidate(name="候选B", final_attack=1200.0),
            ],
            preview_scope_label="同类型全部",
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any(line.startswith("候选范围: 同类型全部") for line in lines))
        self.assertTrue(any("第1名:" in line and "候选B" in line for line in lines))

    def test_preview_requires_explicit_catalog(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
        )
        self.assertTrue(any("未提供装备 catalog" in line for line in lines))

    def test_preview_uses_provided_equipment_catalog(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_weapon_candidates=[WeaponCandidate(name="候选A", final_attack=1000.0)],
            preview_scope_label="当前武器",
            preview_equipment_catalog={
                "chest": [
                    {"名称": "胸甲X", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}
                ],
                "gloves": [{"名称": "护手X", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
                "accessories": [{"名称": "配件X", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
            },
            preview_equipment_scope_label="仅散件装备",
        )
        self.assertTrue(any(line.startswith("装备范围: 仅散件装备") for line in lines))

    def test_preview_accepts_new_weapon_skill_kwargs(self) -> None:
        char = {
            "名称": "测试角色",
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
            "智识": [40.0] * 90,
            "意志": [30.0] * 90,
            "基础攻击力": [100.0] * 90,
            "战技倍率": [[100.0] * 12],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        weapon = {
            "名称": "测试武器",
            "基础攻击力": [100.0] * 90,
            "normal_skills": [
                {"zone": 2, "effect": "攻击力+", "curve": [10.0] * 9},
            ],
            "special_skills": [],
        }
        with_bonus = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            normal_skill_1_name="攻击力+",
            normal_skill_1_level=1,
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any(line.startswith("第1名:") for line in with_bonus))

    @pytest.mark.real_data
    @unittest.skipUnless(
        os.environ.get("ENDFIELD_RUN_REAL_DATA_TESTS") == "1",
        "需设置 ENDFIELD_RUN_REAL_DATA_TESTS=1 才跑真数据预览（防误占内存）",
    )
    def test_preview_with_real_local_equipments_when_available(self) -> None:
        """真数据契约：显式传入有限 catalog，禁止 preview 内隐式 get_equipments。"""
        equip_path = DATA_DIR / "equipments.json"
        if not equip_path.is_file():
            self.skipTest("无本地 equipments.json")
        rows = json.loads(equip_path.read_text(encoding="utf-8"))
        catalog = get_equipment_catalog(
            scope_label="全部装备",
            equipment_rows=rows[:80],
        )
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_equipment_catalog=catalog,
            preview_equipment_scope_label="全部装备",
        )
        joined = "\n".join(lines)
        self.assertNotIn("装备数据不完整", joined, msg=joined)
        self.assertTrue(any(line.startswith("第1名:") for line in lines), msg=joined)


if __name__ == "__main__":
    unittest.main()
