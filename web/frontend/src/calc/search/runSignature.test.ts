import { describe, expect, it } from "vitest";
import type { SearchRequest } from "../../api/search";
import { buildSearchRunSignature } from "./runSignature";

const counts = { weaponCount: 1, chestCount: 1, loadoutCombos: 1 };
const base = {
  char_data: { 名称: "角色" },
  char_level: 90,
  weapon_level: 90,
  trust_level: 0,
  skill_name: "战技",
  skill_type: "战技",
  skill_multiplier: 1,
  damage_type: "物理",
  current_weapon: { 名称: "武器" },
  weapon_scope_label: "当前武器",
  equipment_scope_label: "全部装备",
  fixed_equipment_names: {},
  use_manual_multi_skill_counts: false,
  manual_counts: {},
  enemy_defense: 100,
  extra_crit_rate: 0,
  weapon_skill_values: { normal_skill_1_level: 1 },
  skill_1_level: 8,
  skill_2_level: 8,
  skill_3_level: 8,
} as SearchRequest;

describe("buildSearchRunSignature", () => {
  it("changes when calculation inputs change", () => {
    const signature = buildSearchRunSignature(base, counts);

    for (const changed of [
      { enemy_defense: 300 },
      { extra_crit_rate: 0.2 },
      { weapon_skill_values: { normal_skill_1_level: 2 } },
      { skill_1_level: 9 },
    ]) {
      expect(buildSearchRunSignature({ ...base, ...changed }, counts)).not.toBe(signature);
    }
  });

  it("separates different candidates and TopN sizes", () => {
    const a = { ...counts, candidateNames: { weapons: ["武器A"], chest: ["护甲"], gloves: [], accessories: [] }, topN: 10 };
    const b = { ...a, candidateNames: { ...a.candidateNames, weapons: ["武器B"] } };
    const larger = { ...a, topN: 20 };

    expect(buildSearchRunSignature(base, a)).not.toBe(buildSearchRunSignature(base, b));
    expect(buildSearchRunSignature(base, a)).not.toBe(buildSearchRunSignature(base, larger));
  });
});
